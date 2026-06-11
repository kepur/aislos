import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.audit_log import RiskLevel
from app.models.category import Category
from app.models.intent import Intent, IntentStatus
from app.models.platform_setting import PlatformSetting
from app.models.user import User, UserRole
from app.schemas.intent import IntentCreate, IntentResponse, IntentUpdate
from app.services.audit_service import create_audit_log
from app.services.matching_service import find_matching_suppliers
from app.services.notification_service import notify_user
from app.services.ranking_service import rank_supplier_candidates


router = APIRouter(tags=["Intents"])

MAX_ATTACHMENTS_DEFAULT = 10
MAX_ATTACHMENTS_HARD_CAP = 20


class CandidateBindRequest(BaseModel):
    note: str | None = None


async def _get_intent_max_attachments(db: AsyncSession) -> int:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == "INTENT_MAX_ATTACHMENTS"))
    row = result.scalar_one_or_none()
    if not row:
        return MAX_ATTACHMENTS_DEFAULT
    try:
        return max(0, min(MAX_ATTACHMENTS_HARD_CAP, int(row.value)))
    except ValueError:
        return MAX_ATTACHMENTS_DEFAULT


@router.post("/intents", response_model=IntentResponse, status_code=201)
async def create_intent(
    req: IntentCreate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    max_attachments = await _get_intent_max_attachments(db)
    if req.attachments and len(req.attachments) > max_attachments:
        raise HTTPException(status_code=400, detail=f"Maximum {max_attachments} images are allowed")

    cat = await db.execute(select(Category).where(Category.id == req.category_id))
    if not cat.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category not found")

    intent = Intent(buyer_id=user.id, **req.model_dump())
    db.add(intent)
    await db.flush()

    await create_audit_log(
        db, action="INTENT_CREATED", entity_type="Intent", entity_id=intent.id,
        actor_id=user.id, actor_role=user.role.value,
    )

    matches = await find_matching_suppliers(db, intent)
    for m in matches:
        await notify_user(
            db, user_id=m["owner_user_id"],
            notification_type="NEW_INTENT_FOR_SUPPLIER",
            body=f"New purchase request: {intent.title}",
        )

    await db.commit()
    await db.refresh(intent)
    return intent


@router.get("/intents/my", response_model=list[IntentResponse])
async def list_my_intents(user: User = Depends(require_roles(UserRole.BUYER)), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Intent).where(Intent.buyer_id == user.id).order_by(Intent.created_at.desc()))
    return result.scalars().all()


@router.get("/intents/{intent_id}", response_model=IntentResponse)
async def get_intent(intent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    return intent


@router.patch("/intents/{intent_id}", response_model=IntentResponse)
async def update_intent(
    intent_id: str, req: IntentUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    max_attachments = await _get_intent_max_attachments(db)
    if req.attachments is not None and len(req.attachments) > max_attachments:
        raise HTTPException(status_code=400, detail=f"Maximum {max_attachments} images are allowed")

    result = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    if intent.status not in (IntentStatus.DRAFT, IntentStatus.ACTIVE):
        raise HTTPException(status_code=400, detail="Cannot update intent in current status")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(intent, field, value)
    await db.commit()
    await db.refresh(intent)
    return intent


@router.post("/intents/{intent_id}/cancel", response_model=IntentResponse)
async def cancel_intent(
    intent_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    if intent.status not in (IntentStatus.DRAFT, IntentStatus.ACTIVE):
        raise HTTPException(status_code=400, detail="Cannot cancel intent in current status")
    intent.status = IntentStatus.CANCELED
    await create_audit_log(db, action="INTENT_CANCELED", entity_type="Intent", entity_id=intent.id, actor_id=user.id, actor_role=user.role.value)
    await db.commit()
    await db.refresh(intent)
    return intent


@router.get("/supplier/intents/matching", response_model=list[IntentResponse])
async def matching_intents(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intent).where(Intent.status == IntentStatus.ACTIVE).order_by(Intent.created_at.desc()).limit(100))
    return result.scalars().all()


@router.get("/intents/{intent_id}/supplier-candidates")
async def supplier_candidates(
    intent_id: str,
    sort: str = Query("comprehensive", pattern="^(comprehensive|cost|trust|distance|delivery)$"),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Return ranked supplier candidates for an intent with score breakdowns."""
    res = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = res.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    candidates = await rank_supplier_candidates(db, intent, sort=sort, limit=limit)
    return {"sort": sort, "total": len(candidates), "candidates": candidates}


@router.get("/intents/{intent_id}/supplier-candidates/{catalog_item_id}")
async def supplier_candidate_detail(
    intent_id: str,
    catalog_item_id: str,
    sort: str = Query("comprehensive", pattern="^(comprehensive|cost|trust|distance|delivery)$"),
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Return one ranked candidate with complete score details for the buyer's intent."""
    res = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = res.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    candidates = await rank_supplier_candidates(db, intent, sort=sort, limit=100)
    candidate = next((c for c in candidates if c["catalog_item_id"] == catalog_item_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Supplier candidate not found")
    return candidate


@router.post("/intents/{intent_id}/supplier-candidates/{catalog_item_id}/bind")
async def bind_supplier_candidate(
    intent_id: str,
    catalog_item_id: str,
    req: CandidateBindRequest | None = None,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Bind a buyer intent to a preferred supplier/catalog item for follow-up ranking and quoting."""
    res = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = res.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    if intent.status not in (IntentStatus.ACTIVE, IntentStatus.AWARDED):
        raise HTTPException(status_code=400, detail="Cannot bind suppliers for this request status")

    candidates = await rank_supplier_candidates(db, intent, sort="comprehensive", limit=100)
    candidate = next((c for c in candidates if c["catalog_item_id"] == catalog_item_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Supplier candidate not found")

    attrs = dict(intent.attrs_jsonb or {})
    attrs.update(
        {
            "catalog_item_id": candidate["catalog_item_id"],
            "supplier_company_id": candidate["company_id"],
            "supplier_user_id": candidate["supplier_id"],
            "supplier_candidate_bound": True,
            "supplier_candidate_bound_note": req.note if req else None,
        }
    )
    intent.attrs_jsonb = attrs

    await create_audit_log(
        db,
        action="INTENT_SUPPLIER_CANDIDATE_BOUND",
        entity_type="Intent",
        entity_id=intent.id,
        actor_id=user.id,
        actor_role=user.role.value,
        after_json={
            "catalog_item_id": candidate["catalog_item_id"],
            "company_id": candidate["company_id"],
            "ranking_score": candidate["ranking_score"],
            "note": req.note if req else None,
        },
        risk_level=RiskLevel.LOW,
    )
    await notify_user(
        db,
        user_id=uuid.UUID(candidate["supplier_id"]),
        notification_type="BUYER_BOUND_SUPPLIER_CANDIDATE",
        body=f"A buyer selected your catalog item for request: {intent.title}",
    )
    await db.commit()

    refreshed_candidates = await rank_supplier_candidates(db, intent, sort="comprehensive", limit=100)
    refreshed = next((c for c in refreshed_candidates if c["catalog_item_id"] == catalog_item_id), candidate)
    return {"bound": True, "candidate": refreshed, "intent_attrs": intent.attrs_jsonb}


@router.post("/intents/{intent_id}/ranking-preferences")
async def set_ranking_preferences(
    intent_id: str,
    body: dict,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Store buyer's preferred sort mode for candidate ranking (stateless — returns sorted list)."""
    sort = body.get("sort_preference", "comprehensive")
    valid = {"comprehensive", "cost", "trust", "distance", "delivery"}
    if sort not in valid:
        raise HTTPException(status_code=400, detail=f"sort_preference must be one of {valid}")
    res = await db.execute(select(Intent).where(Intent.id == intent_id, Intent.buyer_id == user.id))
    intent = res.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    candidates = await rank_supplier_candidates(db, intent, sort=sort, limit=20)
    return {"sort_preference": sort, "total": len(candidates), "candidates": candidates}

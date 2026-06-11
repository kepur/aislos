import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.audit_log import RiskLevel
from app.models.company import Company
from app.models.trust import TrustEntityType
from app.models.user import User, UserRole
from app.schemas.trust import TrustAdjustRequest, TrustProfileResponse
from app.services.audit_service import create_audit_log
from app.services.trust_service import adjust_trust_profile, recalculate_trust_profile

router = APIRouter(prefix="/admin/trust", tags=["Admin Trust"])


ADMIN_TRUST_ROLES = (
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
    UserRole.OPS_MANAGER,
    UserRole.RISK_ANALYST,
    UserRole.SUPPORT_AGENT,
    UserRole.AUDITOR,
)

MUTATING_TRUST_ROLES = (
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
    UserRole.OPS_MANAGER,
    UserRole.RISK_ANALYST,
)


@router.get("/users", response_model=list[TrustProfileResponse])
async def list_user_trust(
    admin: User = Depends(require_roles(*ADMIN_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    users = (
        await db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
    ).scalars().all()
    profiles = [
        await recalculate_trust_profile(
            db,
            entity_type=TrustEntityType.USER,
            entity_id=user.id,
            actor_id=admin.id,
            reason="admin_list_recalculate",
        )
        for user in users
    ]
    await db.commit()
    return profiles


@router.get("/users/{user_id}", response_model=TrustProfileResponse)
async def get_user_trust(
    user_id: uuid.UUID,
    admin: User = Depends(require_roles(*ADMIN_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.USER,
        entity_id=user_id,
        actor_id=admin.id,
        reason="admin_detail_recalculate",
    )
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/companies/{company_id}", response_model=TrustProfileResponse)
async def get_company_trust(
    company_id: uuid.UUID,
    admin: User = Depends(require_roles(*ADMIN_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.COMPANY,
        entity_id=company_id,
        actor_id=admin.id,
        reason="admin_detail_recalculate",
    )
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/users/{user_id}/recalculate", response_model=TrustProfileResponse)
async def recalculate_user_trust(
    user_id: uuid.UUID,
    admin: User = Depends(require_roles(*MUTATING_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.USER,
        entity_id=user_id,
        actor_id=admin.id,
        reason="admin_manual_recalculate",
    )
    await create_audit_log(
        db,
        action="ADMIN_MANUAL_ACTION",
        entity_type="TrustProfile",
        entity_id=profile.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"action": "recalculate_user_trust", "user_id": str(user_id)},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/companies/{company_id}/recalculate", response_model=TrustProfileResponse)
async def recalculate_company_trust(
    company_id: uuid.UUID,
    admin: User = Depends(require_roles(*MUTATING_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.COMPANY,
        entity_id=company_id,
        actor_id=admin.id,
        reason="admin_manual_recalculate",
    )
    await create_audit_log(
        db,
        action="ADMIN_MANUAL_ACTION",
        entity_type="TrustProfile",
        entity_id=profile.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"action": "recalculate_company_trust", "company_id": str(company_id)},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/{entity_type}/{entity_id}/adjust", response_model=TrustProfileResponse)
async def adjust_trust(
    entity_type: TrustEntityType,
    entity_id: uuid.UUID,
    req: TrustAdjustRequest,
    admin: User = Depends(require_roles(*MUTATING_TRUST_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    profile = await adjust_trust_profile(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        score_delta=req.score_delta,
        reason=req.reason,
        actor_id=admin.id,
        freeze=req.freeze,
    )
    await create_audit_log(
        db,
        action="ADMIN_MANUAL_ACTION",
        entity_type="TrustProfile",
        entity_id=profile.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={
            "action": "adjust_trust",
            "entity_type": entity_type.value,
            "entity_id": str(entity_id),
            "score_delta": req.score_delta,
            "reason": req.reason,
            "freeze": req.freeze,
        },
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    await db.refresh(profile)
    return profile

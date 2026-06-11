import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.proposal import crud_bom_item, crud_proposal_plan
from app.models.proposal import BOMItem, ProposalPlan
from app.schemas.proposal import (
    BOMItemCreate,
    BOMItemRead,
    BOMItemUpdate,
    ProposalPlanCreate,
    ProposalPlanRead,
    ProposalPlanUpdate,
)

router = APIRouter(prefix="/proposals", tags=["proposals"])


# ── Proposal Plans ──────────────────────────────────────────────

@router.get("")
async def list_proposals(
    db: DB,
    current_user: CurrentUser,
    lead_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    tier: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    filters = []
    if lead_id:
        filters.append(ProposalPlan.lead_id == lead_id)
    if project_id:
        filters.append(ProposalPlan.project_id == project_id)
    if tier:
        filters.append(ProposalPlan.tier == tier)
    items, total = await crud_proposal_plan.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [ProposalPlanRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=ProposalPlanRead)
async def get_proposal(id: uuid.UUID, db: DB, current_user: CurrentUser):
    plan = await crud_proposal_plan.get(db, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    return plan


@router.post("", response_model=ProposalPlanRead, status_code=201)
async def create_proposal(data: ProposalPlanCreate, db: DB, admin: AdminUser):
    return await crud_proposal_plan.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=ProposalPlanRead)
async def update_proposal(id: uuid.UUID, data: ProposalPlanUpdate, db: DB, admin: AdminUser):
    plan = await crud_proposal_plan.get(db, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    return await crud_proposal_plan.update(db, db_obj=plan, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}")
async def delete_proposal(id: uuid.UUID, db: DB, admin: AdminUser):
    plan = await crud_proposal_plan.get(db, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    await crud_proposal_plan.delete(db, id=id)
    return {"ok": True}


# ── BOM Items ───────────────────────────────────────────────────

@router.get("/{plan_id}/bom")
async def list_bom_items(
    plan_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    plan = await crud_proposal_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    items, total = await crud_bom_item.get_multi(
        db, skip=skip, limit=limit, filters=[BOMItem.proposal_plan_id == plan_id]
    )
    return {"items": [BOMItemRead.model_validate(i) for i in items], "total": total}


@router.post("/{plan_id}/bom", response_model=BOMItemRead, status_code=201)
async def create_bom_item(plan_id: uuid.UUID, data: BOMItemCreate, db: DB, admin: AdminUser):
    plan = await crud_proposal_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    obj = data.model_dump()
    obj["proposal_plan_id"] = plan_id
    return await crud_bom_item.create(db, obj_in=obj)


@router.put("/{plan_id}/bom/{item_id}", response_model=BOMItemRead)
async def update_bom_item(
    plan_id: uuid.UUID, item_id: uuid.UUID, data: BOMItemUpdate, db: DB, admin: AdminUser
):
    item = await crud_bom_item.get(db, item_id)
    if not item or item.proposal_plan_id != plan_id:
        raise HTTPException(status_code=404, detail="BOM item not found for this plan")
    return await crud_bom_item.update(db, db_obj=item, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{plan_id}/bom/{item_id}")
async def delete_bom_item(plan_id: uuid.UUID, item_id: uuid.UUID, db: DB, admin: AdminUser):
    item = await crud_bom_item.get(db, item_id)
    if not item or item.proposal_plan_id != plan_id:
        raise HTTPException(status_code=404, detail="BOM item not found for this plan")
    await crud_bom_item.delete(db, id=item_id)
    return {"ok": True}

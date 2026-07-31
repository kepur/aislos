import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
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
from app.services.project_access import resolve_linked_resource_workspace

router = APIRouter(prefix="/proposals", tags=["proposals"])


# ── Proposal Plans ──────────────────────────────────────────────

@router.get("")
async def list_proposals(
    db: DB,
    admin: AdminUser,
    lead_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    workspace_id: uuid.UUID | None = Query(None),
    tier: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    filters = []
    if lead_id:
        filters.append(ProposalPlan.lead_id == lead_id)
    if project_id:
        filters.append(ProposalPlan.project_id == project_id)
    if workspace_id:
        filters.append(ProposalPlan.workspace_id == workspace_id)
    if tier:
        filters.append(ProposalPlan.tier == tier)
    items, total = await crud_proposal_plan.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [ProposalPlanRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=ProposalPlanRead)
async def get_proposal(id: uuid.UUID, db: DB, admin: AdminUser):
    plan = await crud_proposal_plan.get(db, id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    return plan


@router.post("", response_model=ProposalPlanRead, status_code=201)
async def create_proposal(data: ProposalPlanCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    try:
        obj["workspace_id"] = await resolve_linked_resource_workspace(
            db,
            requested_workspace_id=data.workspace_id,
            lead_id=data.lead_id,
            project_id=data.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return await crud_proposal_plan.create(db, obj_in=obj)


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
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    plan = await crud_proposal_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    item_filters = [BOMItem.proposal_plan_id == plan_id]
    if plan.workspace_id is not None:
        item_filters.append(BOMItem.workspace_id == plan.workspace_id)
    else:
        item_filters.append(BOMItem.workspace_id.is_(None))
    items, total = await crud_bom_item.get_multi(
        db, skip=skip, limit=limit, filters=item_filters
    )
    return {"items": [BOMItemRead.model_validate(i) for i in items], "total": total}


@router.post("/{plan_id}/bom", response_model=BOMItemRead, status_code=201)
async def create_bom_item(plan_id: uuid.UUID, data: BOMItemCreate, db: DB, admin: AdminUser):
    plan = await crud_proposal_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Proposal plan not found")
    obj = data.model_dump()
    obj["proposal_plan_id"] = plan_id
    obj["workspace_id"] = plan.workspace_id
    return await crud_bom_item.create(db, obj_in=obj)


@router.put("/{plan_id}/bom/{item_id}", response_model=BOMItemRead)
async def update_bom_item(
    plan_id: uuid.UUID, item_id: uuid.UUID, data: BOMItemUpdate, db: DB, admin: AdminUser
):
    item = await crud_bom_item.get(db, item_id)
    plan = await crud_proposal_plan.get(db, plan_id)
    if (
        not item
        or not plan
        or item.proposal_plan_id != plan_id
        or item.workspace_id != plan.workspace_id
    ):
        raise HTTPException(status_code=404, detail="BOM item not found for this plan")
    return await crud_bom_item.update(db, db_obj=item, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{plan_id}/bom/{item_id}")
async def delete_bom_item(plan_id: uuid.UUID, item_id: uuid.UUID, db: DB, admin: AdminUser):
    item = await crud_bom_item.get(db, item_id)
    plan = await crud_proposal_plan.get(db, plan_id)
    if (
        not item
        or not plan
        or item.proposal_plan_id != plan_id
        or item.workspace_id != plan.workspace_id
    ):
        raise HTTPException(status_code=404, detail="BOM item not found for this plan")
    await crud_bom_item.delete(db, id=item_id)
    return {"ok": True}

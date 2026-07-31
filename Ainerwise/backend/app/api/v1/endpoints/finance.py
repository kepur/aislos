"""Project finance + platform fee + margin/LTV endpoints (FI.4.1, 4.2, 4.6).

Admin-only. ProjectFinance create/update auto-recompute derived margin and LTV
metrics so they never go stale.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import DB, FinanceUser
from app.crud.finance import crud_platform_fee_rule, crud_project_finance
from app.models.finance import PlatformFeeRule, ProjectFinance
from app.schemas.finance import (
    PlatformFeeRuleCreate,
    PlatformFeeRuleRead,
    PlatformFeeRuleUpdate,
    ProjectFinanceCreate,
    ProjectFinanceRead,
    ProjectFinanceUpdate,
)
from app.services import finance as finance_svc
from app.services.finance_access import (
    finance_workspace_ids,
    require_finance_workspace_access,
    resolve_financial_workspace,
)

router = APIRouter(tags=["finance"])


# --- FI.4.1 / FI.4.6 Project finance ---------------------------------------

@router.get("/project-finances")
async def list_project_finances(
    db: DB,
    admin: FinanceUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    project_id: uuid.UUID | None = None,
    solution_line: str | None = None,
):
    filters = []
    accessible_workspace_ids = await finance_workspace_ids(db, admin)
    if accessible_workspace_ids is not None:
        filters.append(ProjectFinance.workspace_id.in_(accessible_workspace_ids))
    if project_id is not None:
        filters.append(ProjectFinance.project_id == project_id)
    if solution_line is not None:
        filters.append(ProjectFinance.solution_line == solution_line)
    items, total = await crud_project_finance.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [ProjectFinanceRead.model_validate(i) for i in items], "total": total}


@router.get("/project-finances/{id}", response_model=ProjectFinanceRead)
async def get_project_finance(id: uuid.UUID, db: DB, admin: FinanceUser):
    obj = await crud_project_finance.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await require_finance_workspace_access(db, admin, obj.workspace_id)
    return obj


@router.post("/project-finances", response_model=ProjectFinanceRead, status_code=201)
async def create_project_finance(data: ProjectFinanceCreate, db: DB, admin: FinanceUser):
    payload = data.model_dump()
    try:
        payload["workspace_id"] = await resolve_financial_workspace(
            db,
            requested_workspace_id=data.workspace_id,
            project_id=data.project_id,
            customer_id=data.customer_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await require_finance_workspace_access(db, admin, payload["workspace_id"])
    payload.update(finance_svc.compute_finance(payload))
    return await crud_project_finance.create(db, obj_in=payload)


@router.put("/project-finances/{id}", response_model=ProjectFinanceRead)
async def update_project_finance(id: uuid.UUID, data: ProjectFinanceUpdate, db: DB, admin: FinanceUser):
    obj = await crud_project_finance.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await require_finance_workspace_access(db, admin, obj.workspace_id)
    updates = data.model_dump(exclude_unset=True)
    if "project_id" in updates or "customer_id" in updates:
        try:
            await resolve_financial_workspace(
                db,
                requested_workspace_id=obj.workspace_id,
                project_id=updates.get("project_id", obj.project_id),
                customer_id=updates.get("customer_id", obj.customer_id),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
    obj = await crud_project_finance.update(db, db_obj=obj, obj_in=updates)
    # Recompute derived metrics from the merged record and persist.
    derived = finance_svc.compute_finance(obj)
    return await crud_project_finance.update(db, db_obj=obj, obj_in=derived)


@router.delete("/project-finances/{id}")
async def delete_project_finance(id: uuid.UUID, db: DB, admin: FinanceUser):
    obj = await crud_project_finance.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await require_finance_workspace_access(db, admin, obj.workspace_id)
    if not await crud_project_finance.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


class FinanceComputeRequest(ProjectFinanceCreate):
    pass


@router.post("/project-finances/compute")
async def compute_finance_preview(data: FinanceComputeRequest, admin: FinanceUser):
    """What-if margin/LTV preview without persisting."""
    return finance_svc.compute_finance(data.model_dump())


# --- FI.4.2 Platform fee rules ---------------------------------------------

@router.get("/platform-fee-rules")
async def list_platform_fee_rules(
    db: DB,
    admin: FinanceUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud_platform_fee_rule.get_multi(db, skip=skip, limit=limit)
    return {"items": [PlatformFeeRuleRead.model_validate(i) for i in items], "total": total}


@router.post("/platform-fee-rules", response_model=PlatformFeeRuleRead, status_code=201)
async def create_platform_fee_rule(data: PlatformFeeRuleCreate, db: DB, admin: FinanceUser):
    return await crud_platform_fee_rule.create(db, obj_in=data.model_dump())


@router.put("/platform-fee-rules/{id}", response_model=PlatformFeeRuleRead)
async def update_platform_fee_rule(id: uuid.UUID, data: PlatformFeeRuleUpdate, db: DB, admin: FinanceUser):
    obj = await crud_platform_fee_rule.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return await crud_platform_fee_rule.update(db, db_obj=obj, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/platform-fee-rules/{id}")
async def delete_platform_fee_rule(id: uuid.UUID, db: DB, admin: FinanceUser):
    if not await crud_platform_fee_rule.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


class PlatformFeeComputeRequest(BaseModel):
    rule_id: uuid.UUID
    project_value: float


@router.post("/platform-fee-rules/compute")
async def compute_platform_fee(data: PlatformFeeComputeRequest, db: DB, admin: FinanceUser):
    rule = await crud_platform_fee_rule.get(db, data.rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return finance_svc.compute_platform_fee(rule, data.project_value)

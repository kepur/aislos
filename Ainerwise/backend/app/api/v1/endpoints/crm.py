"""CRM endpoints: renewal queue (FI.6.5) + supplier scorecards (FI.6.6). Admin-only."""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.base import CRUDBase
from app.models.crm import SCORECARD_DIMENSIONS, SupplierScorecard
from app.schemas.crm import (
    SupplierScorecardCreate,
    SupplierScorecardRead,
    SupplierScorecardUpdate,
)
from app.services import renewal_queue

router = APIRouter(tags=["crm"])

crud_scorecard = CRUDBase[SupplierScorecard](SupplierScorecard)


# --- FI.6.5 renewal opportunity queue --------------------------------------

@router.get("/renewal-queue")
async def get_renewal_queue(db: DB, admin: AdminUser, within_days: int = Query(90, ge=1, le=365)):
    return await renewal_queue.build_renewal_queue(db, within_days=within_days)


# --- FI.6.6 supplier scorecards --------------------------------------------

def _with_overall(payload: dict) -> dict:
    scores = [payload.get(d) for d in SCORECARD_DIMENSIONS if payload.get(d) is not None]
    if scores:
        payload["overall_score"] = round(sum(scores) / len(scores), 2)
    return payload


@router.get("/supplier-scorecards")
async def list_scorecards(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = await crud_scorecard.get_multi(
        db, skip=skip, limit=limit, order_by=SupplierScorecard.overall_score.desc().nullslast(),
    )
    return {"items": [SupplierScorecardRead.model_validate(i) for i in items], "total": total}


@router.get("/supplier-scorecards/{id}", response_model=SupplierScorecardRead)
async def get_scorecard(id: uuid.UUID, db: DB, admin: AdminUser):
    obj = await crud_scorecard.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


@router.post("/supplier-scorecards", response_model=SupplierScorecardRead, status_code=201)
async def create_scorecard(data: SupplierScorecardCreate, db: DB, admin: AdminUser):
    return await crud_scorecard.create(db, obj_in=_with_overall(data.model_dump()))


@router.put("/supplier-scorecards/{id}", response_model=SupplierScorecardRead)
async def update_scorecard(id: uuid.UUID, data: SupplierScorecardUpdate, db: DB, admin: AdminUser):
    obj = await crud_scorecard.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    obj = await crud_scorecard.update(db, db_obj=obj, obj_in=data.model_dump(exclude_unset=True))
    # Recompute overall from the merged record.
    merged = {d: getattr(obj, d) for d in SCORECARD_DIMENSIONS}
    return await crud_scorecard.update(db, db_obj=obj, obj_in=_with_overall(merged))


@router.delete("/supplier-scorecards/{id}")
async def delete_scorecard(id: uuid.UUID, db: DB, admin: AdminUser):
    if not await crud_scorecard.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

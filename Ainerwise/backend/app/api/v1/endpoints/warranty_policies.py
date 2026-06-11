import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.certification import crud_warranty_policy
from app.models.certification import WarrantyPolicy
from app.schemas.certification import (
    WarrantyPolicyCreate,
    WarrantyPolicyRead,
    WarrantyPolicyUpdate,
)

router = APIRouter(prefix="/warranty-policies", tags=["warranty-policies"])


@router.get("")
async def list_warranty_policies(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_id: uuid.UUID | None = Query(None),
    region: str | None = Query(None),
    active_only: bool = Query(False),
):
    filters = []
    if product_id:
        filters.append(WarrantyPolicy.product_id == product_id)
    if region:
        filters.append(WarrantyPolicy.region == region)
    if active_only:
        filters.append(WarrantyPolicy.active == True)
    items, total = await crud_warranty_policy.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [WarrantyPolicyRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=WarrantyPolicyRead)
async def get_warranty_policy(id: uuid.UUID, db: DB, admin: AdminUser):
    policy = await crud_warranty_policy.get(db, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Warranty policy not found")
    return policy


@router.post("", response_model=WarrantyPolicyRead, status_code=201)
async def create_warranty_policy(data: WarrantyPolicyCreate, db: DB, admin: AdminUser):
    return await crud_warranty_policy.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=WarrantyPolicyRead)
async def update_warranty_policy(id: uuid.UUID, data: WarrantyPolicyUpdate, db: DB, admin: AdminUser):
    policy = await crud_warranty_policy.get(db, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Warranty policy not found")
    return await crud_warranty_policy.update(db, db_obj=policy, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}")
async def delete_warranty_policy(id: uuid.UUID, db: DB, admin: AdminUser):
    policy = await crud_warranty_policy.get(db, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Warranty policy not found")
    await crud_warranty_policy.delete(db, id=id)
    return {"ok": True}

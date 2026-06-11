import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.product_compatibility import crud_product_compatibility
from app.models.product import ProductCompatibility
from app.schemas.product_compatibility import (
    ProductCompatibilityCreate,
    ProductCompatibilityRead,
    ProductCompatibilityUpdate,
)

router = APIRouter(prefix="/product-compatibility", tags=["product-compatibility"])


@router.get("")
async def list_product_compatibility(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    product_id: uuid.UUID | None = Query(None),
    protocol: str | None = Query(None),
):
    filters = []
    if product_id:
        filters.append(ProductCompatibility.product_id == product_id)
    if protocol:
        filters.append(ProductCompatibility.protocol == protocol)
    items, total = await crud_product_compatibility.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [ProductCompatibilityRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=ProductCompatibilityRead)
async def get_product_compatibility(id: uuid.UUID, db: DB, current_user: CurrentUser):
    record = await crud_product_compatibility.get(db, id)
    if not record:
        raise HTTPException(status_code=404, detail="Compatibility record not found")
    return record


@router.post("", response_model=ProductCompatibilityRead, status_code=201)
async def create_product_compatibility(data: ProductCompatibilityCreate, db: DB, admin: AdminUser):
    return await crud_product_compatibility.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=ProductCompatibilityRead)
async def update_product_compatibility(
    id: uuid.UUID, data: ProductCompatibilityUpdate, db: DB, admin: AdminUser
):
    record = await crud_product_compatibility.get(db, id)
    if not record:
        raise HTTPException(status_code=404, detail="Compatibility record not found")
    return await crud_product_compatibility.update(
        db, db_obj=record, obj_in=data.model_dump(exclude_unset=True)
    )


@router.delete("/{id}")
async def delete_product_compatibility(id: uuid.UUID, db: DB, admin: AdminUser):
    record = await crud_product_compatibility.get(db, id)
    if not record:
        raise HTTPException(status_code=404, detail="Compatibility record not found")
    await crud_product_compatibility.delete(db, id=id)
    return {"ok": True}

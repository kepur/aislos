import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.region import crud_region
from app.schemas.region import RegionCreate, RegionRead, RegionUpdate

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("")
async def list_regions(
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = False,
):
    from app.models.region import Region

    filters = []
    if active_only:
        filters.append(Region.is_active == True)
    items, total = await crud_region.get_multi(
        db, skip=skip, limit=limit, filters=filters or None,
        order_by=Region.name,
    )
    return {"items": [RegionRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=RegionRead)
async def get_region(id: uuid.UUID, db: DB):
    region = await crud_region.get(db, id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.post("", response_model=RegionRead, status_code=201)
async def create_region(data: RegionCreate, db: DB, admin: AdminUser):
    return await crud_region.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=RegionRead)
async def update_region(id: uuid.UUID, data: RegionUpdate, db: DB, admin: AdminUser):
    region = await crud_region.get(db, id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return await crud_region.update(db, db_obj=region, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}")
async def delete_region(id: uuid.UUID, db: DB, admin: AdminUser):
    deleted = await crud_region.delete(db, id=id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Region not found")
    return {"ok": True}

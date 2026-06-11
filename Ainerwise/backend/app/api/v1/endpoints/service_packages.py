import uuid

from fastapi import APIRouter, HTTPException, status
from slugify import slugify

from app.api.deps import AdminUser, DB
from app.crud.service_package import crud_service_package
from app.schemas.service_package import ServicePackageCreate, ServicePackageRead, ServicePackageUpdate

router = APIRouter(prefix="/service-packages", tags=["service-packages"])


@router.get("", response_model=list[ServicePackageRead])
async def list_service_packages(db: DB):
    return await crud_service_package.get_public(db)


@router.post("", response_model=ServicePackageRead, status_code=status.HTTP_201_CREATED)
async def create_service_package(data: ServicePackageCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    if not obj.get("slug"):
        obj["slug"] = slugify(obj["name"])
    return await crud_service_package.create(db, obj_in=obj)


@router.put("/{id}", response_model=ServicePackageRead)
async def update_service_package(id: uuid.UUID, data: ServicePackageUpdate, db: DB, admin: AdminUser):
    pkg = await crud_service_package.get(db, id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Service package not found")
    return await crud_service_package.update(db, db_obj=pkg, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_package(id: uuid.UUID, db: DB, admin: AdminUser):
    deleted = await crud_service_package.delete(db, id=id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service package not found")

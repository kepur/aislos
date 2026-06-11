import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.certification import crud_certification
from app.models.certification import CertificationRecord
from app.schemas.certification import (
    CertificationRecordCreate,
    CertificationRecordRead,
    CertificationRecordUpdate,
)

router = APIRouter(prefix="/certifications", tags=["certifications"])


@router.get("")
async def list_certifications(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    owner_type: str | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = []
    if owner_type:
        filters.append(CertificationRecord.owner_type == owner_type)
    if owner_id:
        filters.append(CertificationRecord.owner_id == owner_id)
    if status_filter:
        filters.append(CertificationRecord.status == status_filter)
    items, total = await crud_certification.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [CertificationRecordRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=CertificationRecordRead)
async def get_certification(id: uuid.UUID, db: DB, admin: AdminUser):
    cert = await crud_certification.get(db, id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    return cert


@router.post("", response_model=CertificationRecordRead, status_code=201)
async def create_certification(data: CertificationRecordCreate, db: DB, admin: AdminUser):
    return await crud_certification.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=CertificationRecordRead)
async def update_certification(id: uuid.UUID, data: CertificationRecordUpdate, db: DB, admin: AdminUser):
    cert = await crud_certification.get(db, id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    return await crud_certification.update(db, db_obj=cert, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}")
async def delete_certification(id: uuid.UUID, db: DB, admin: AdminUser):
    cert = await crud_certification.get(db, id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    await crud_certification.delete(db, id=id)
    return {"ok": True}

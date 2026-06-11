import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.service_partner import crud_service_partner
from app.schemas.service_partner import (
    ServicePartnerCreate,
    ServicePartnerRead,
    ServicePartnerStatusUpdate,
    ServicePartnerUpdate,
)

router = APIRouter(prefix="/service-partners", tags=["service-partners"])


@router.get("")
async def list_service_partners(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="verification_status"),
    partner_type: str | None = None,
):
    from app.models.service import ServicePartner

    filters = []
    if status_filter:
        filters.append(ServicePartner.verification_status == status_filter)
    if partner_type:
        filters.append(ServicePartner.partner_type == partner_type)
    items, total = await crud_service_partner.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [ServicePartnerRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=ServicePartnerRead)
async def get_service_partner(id: uuid.UUID, db: DB, admin: AdminUser):
    partner = await crud_service_partner.get(db, id)
    if not partner:
        raise HTTPException(status_code=404, detail="Service partner not found")
    return partner


@router.post("", response_model=ServicePartnerRead, status_code=201)
async def create_service_partner(data: ServicePartnerCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    obj["verification_status"] = "pending"
    obj["availability_status"] = "available"
    return await crud_service_partner.create(db, obj_in=obj)


@router.put("/{id}", response_model=ServicePartnerRead)
async def update_service_partner(id: uuid.UUID, data: ServicePartnerUpdate, db: DB, admin: AdminUser):
    partner = await crud_service_partner.get(db, id)
    if not partner:
        raise HTTPException(status_code=404, detail="Service partner not found")
    return await crud_service_partner.update(db, db_obj=partner, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=ServicePartnerRead)
async def update_service_partner_status(id: uuid.UUID, data: ServicePartnerStatusUpdate, db: DB, admin: AdminUser):
    partner = await crud_service_partner.get(db, id)
    if not partner:
        raise HTTPException(status_code=404, detail="Service partner not found")
    return await crud_service_partner.update(
        db, db_obj=partner, obj_in={"verification_status": data.verification_status}
    )


@router.delete("/{id}")
async def delete_service_partner(id: uuid.UUID, db: DB, admin: AdminUser):
    deleted = await crud_service_partner.delete(db, id=id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service partner not found")
    return {"ok": True}

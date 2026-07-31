import uuid

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import AdminUser, DB
from app.crud.vendor import crud_vendor
from app.schemas.vendor import VendorApply, VendorRead, VendorStatusUpdate
from app.services.event_bus import emit_event
from app.services.rate_limit import enforce_public_rate_limit

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.post("/apply", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def apply_vendor(data: VendorApply, request: Request, db: DB):
    await enforce_public_rate_limit(request, bucket="vendor-application", limit=10)
    contact = data.contact_info or {}
    contact["email"] = data.email
    if data.phone:
        contact["phone"] = data.phone
    if data.company_type:
        contact["company_type"] = data.company_type
    obj = {
        "name": data.company_name,
        "type": "vendor",
        "country": data.country,
        "city": data.city,
        "address": data.address,
        "website": data.website,
        "description": data.description,
        "verification_status": "pending",
        "contact_info": contact,
    }
    vendor = await crud_vendor.create_in_transaction(db, obj_in=obj)
    await emit_event(
        db,
        event_type="vendor.applied",
        payload={
            "vendor_id": str(vendor.id),
            "company_name": vendor.name,
            "country": vendor.country,
            "city": vendor.city,
            "email": data.email,
            "company_type": data.company_type,
        },
        aggregate_type="company",
        aggregate_id=vendor.id,
        target_channel="telegram_admin",
    )
    await db.commit()
    await db.refresh(vendor)
    return vendor


@router.get("")
async def list_vendors(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    items, total = await crud_vendor.get_vendors(db, skip=skip, limit=limit)
    return {"items": [VendorRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=VendorRead)
async def get_vendor(id: uuid.UUID, db: DB, admin: AdminUser):
    vendor = await crud_vendor.get(db, id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.patch("/{id}/status", response_model=VendorRead)
async def update_vendor_status(id: uuid.UUID, data: VendorStatusUpdate, db: DB, admin: AdminUser):
    vendor = await crud_vendor.get(db, id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return await crud_vendor.update(db, db_obj=vendor, obj_in={"verification_status": data.verification_status})

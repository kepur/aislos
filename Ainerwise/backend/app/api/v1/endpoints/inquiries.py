import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.inquiry import crud_inquiry
from app.schemas.inquiry import InquiryCreate, InquiryRead, InquiryStatusUpdate, InquiryUpdate
from app.services.marketing_automation import ensure_inquiry_follow_up, resolve_campaign_id

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.get("")
async def list_inquiries(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    product_id: uuid.UUID | None = Query(None),
):
    from app.models.inquiry import Inquiry

    filters = []
    if status_filter:
        filters.append(Inquiry.status == status_filter)
    if product_id:
        filters.append(Inquiry.product_id == product_id)
    items, total = await crud_inquiry.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [InquiryRead.model_validate(i) for i in items], "total": total}


@router.get("/my")
async def list_my_inquiries(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    from app.models.inquiry import Inquiry

    filters = [Inquiry.buyer_user_id == current_user.id]
    items, total = await crud_inquiry.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [InquiryRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=InquiryRead)
async def get_inquiry(id: uuid.UUID, db: DB, current_user: CurrentUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry


@router.post("", response_model=InquiryRead, status_code=201)
async def create_inquiry(data: InquiryCreate, db: DB, current_user: CurrentUser):
    """Create a product inquiry. Works for both authenticated and anonymous users."""
    obj = data.model_dump()
    obj["status"] = "new"
    obj["source_channel"] = obj.get("source_channel") or (
        "campaign" if obj.get("utm_source") else "website"
    )
    if not obj.get("campaign_id"):
        obj["campaign_id"] = await resolve_campaign_id(db, obj.get("utm_campaign"))
    if current_user:
        obj["buyer_user_id"] = current_user.id
        obj["buyer_company_id"] = current_user.company_id
        if not obj.get("contact_name"):
            obj["contact_name"] = current_user.full_name
        if not obj.get("contact_email"):
            obj["contact_email"] = current_user.email

    # Look up the product to set vendor_company_id
    if obj.get("product_id"):
        from app.crud.product import crud_product
        product = await crud_product.get(db, obj["product_id"])
        if product and product.owner_company_id:
            obj["vendor_company_id"] = product.owner_company_id

    inquiry = await crud_inquiry.create(db, obj_in=obj)

    # Create integration event for notification
    try:
        from app.services.integration_events import create_integration_event
        await create_integration_event(
            db,
            event_type="inquiry.created",
            payload={
                "inquiry_id": str(inquiry.id),
                "product_id": str(inquiry.product_id) if inquiry.product_id else None,
                "contact_name": inquiry.contact_name or "Unknown",
                "contact_email": inquiry.contact_email or "",
                "message": (inquiry.message or "")[:200],
            },
        )
    except Exception:
        pass  # Don't fail inquiry creation if notification fails
    try:
        await ensure_inquiry_follow_up(db, inquiry)
    except Exception:
        pass

    return inquiry


@router.post("/public", response_model=InquiryRead, status_code=201)
async def create_public_inquiry(data: InquiryCreate, db: DB):
    """Create a product inquiry from public/anonymous users (no auth required)."""
    obj = data.model_dump()
    obj["status"] = "new"
    obj["source_channel"] = obj.get("source_channel") or (
        "campaign" if obj.get("utm_source") else "website"
    )
    if not obj.get("campaign_id"):
        obj["campaign_id"] = await resolve_campaign_id(db, obj.get("utm_campaign"))

    if obj.get("product_id"):
        from app.crud.product import crud_product
        product = await crud_product.get(db, obj["product_id"])
        if product and product.owner_company_id:
            obj["vendor_company_id"] = product.owner_company_id

    inquiry = await crud_inquiry.create(db, obj_in=obj)

    try:
        from app.services.integration_events import create_integration_event
        await create_integration_event(
            db,
            event_type="inquiry.created",
            payload={
                "inquiry_id": str(inquiry.id),
                "product_id": str(inquiry.product_id) if inquiry.product_id else None,
                "contact_name": inquiry.contact_name or "Anonymous",
                "contact_email": inquiry.contact_email or "",
                "message": (inquiry.message or "")[:200],
            },
        )
    except Exception:
        pass
    try:
        await ensure_inquiry_follow_up(db, inquiry)
    except Exception:
        pass

    return inquiry


@router.put("/{id}", response_model=InquiryRead)
async def update_inquiry(id: uuid.UUID, data: InquiryUpdate, db: DB, admin: AdminUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return await crud_inquiry.update(db, db_obj=inquiry, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=InquiryRead)
async def update_inquiry_status(id: uuid.UUID, data: InquiryStatusUpdate, db: DB, admin: AdminUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return await crud_inquiry.update(db, db_obj=inquiry, obj_in={"status": data.status})


@router.delete("/{id}")
async def delete_inquiry(id: uuid.UUID, db: DB, admin: AdminUser):
    success = await crud_inquiry.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return {"ok": True}

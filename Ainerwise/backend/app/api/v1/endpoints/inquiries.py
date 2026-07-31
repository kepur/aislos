import uuid

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import or_

from app.api.deps import CRMUser, CurrentUser, DB
from app.core.product_catalog import PUBLIC_PRODUCT_STATUSES
from app.crud.inquiry import crud_inquiry
from app.schemas.inquiry import (
    InquiryCreate,
    InquiryCustomerRead,
    InquiryRead,
    InquiryStatusUpdate,
    InquiryUpdate,
)
from app.services.event_bus import emit_event
from app.services.marketing_automation import ensure_inquiry_follow_up, resolve_campaign_id
from app.services.rate_limit import enforce_public_rate_limit
from app.modules.commerce.access import CommerceAccessDenied, resolve_commerce_workspace
from app.services.crm_access import (
    crm_workspace_ids,
    customer_workspace_ids,
    require_crm_workspace_access,
)
from app.services.portal_access import get_default_workspace

router = APIRouter(prefix="/inquiries", tags=["inquiries"])

PUBLIC_INQUIRY_FIELDS = {
    "product_id",
    "contact_name",
    "contact_email",
    "contact_phone",
    "message",
    "quantity",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "landing_page",
    "referrer",
}


async def _intake_object(data: InquiryCreate, db: DB) -> dict:
    obj = data.model_dump(include=PUBLIC_INQUIRY_FIELDS)
    obj["status"] = "new"
    obj["source_channel"] = "campaign" if obj.get("utm_source") else "website"
    obj["campaign_id"] = await resolve_campaign_id(db, obj.get("utm_campaign"))
    return obj


@router.get("")
async def list_inquiries(
    db: DB,
    admin: CRMUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    product_id: uuid.UUID | None = Query(None),
):
    from app.models.inquiry import Inquiry

    filters = []
    accessible_workspace_ids = await crm_workspace_ids(db, admin)
    if accessible_workspace_ids is not None:
        filters.append(Inquiry.workspace_id.in_(accessible_workspace_ids))
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

    workspace_ids = await customer_workspace_ids(db, current_user)
    company_scope = (
        (Inquiry.buyer_company_id == current_user.company_id)
        & (
            or_(Inquiry.workspace_id.in_(workspace_ids), Inquiry.workspace_id.is_(None))
            if workspace_ids
            else Inquiry.workspace_id.is_(None)
        )
    )
    filters = [
        or_(Inquiry.buyer_user_id == current_user.id, company_scope)
        if current_user.company_id
        else Inquiry.buyer_user_id == current_user.id
    ]
    items, total = await crud_inquiry.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [InquiryCustomerRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=InquiryRead)
async def get_inquiry(id: uuid.UUID, db: DB, admin: CRMUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    await require_crm_workspace_access(db, admin, inquiry.workspace_id)
    return inquiry


@router.post("", response_model=InquiryCustomerRead, status_code=201)
async def create_inquiry(data: InquiryCreate, db: DB, current_user: CurrentUser):
    """Create a product inquiry for the authenticated customer."""
    obj = await _intake_object(data, db)
    if current_user:
        try:
            obj["workspace_id"] = await resolve_commerce_workspace(
                db,
                user=current_user,
                requested_workspace_id=data.workspace_id,
            )
        except CommerceAccessDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from None
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
        if not product or product.status not in PUBLIC_PRODUCT_STATUSES:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.owner_company_id:
            obj["vendor_company_id"] = product.owner_company_id

    inquiry = await crud_inquiry.create_in_transaction(db, obj_in=obj)
    await _queue_inquiry_created(db, inquiry, anonymous=False)
    await db.commit()
    await db.refresh(inquiry)
    try:
        await ensure_inquiry_follow_up(db, inquiry)
    except Exception:
        pass

    return inquiry


@router.post("/public", response_model=InquiryCustomerRead, status_code=201)
async def create_public_inquiry(data: InquiryCreate, request: Request, db: DB):
    """Create a product inquiry from public/anonymous users (no auth required)."""
    await enforce_public_rate_limit(request, bucket="public-inquiry", limit=30)
    obj = await _intake_object(data, db)
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise HTTPException(status_code=503, detail="Inquiry intake Workspace is unavailable")
    obj["workspace_id"] = workspace.id

    if obj.get("product_id"):
        from app.crud.product import crud_product
        product = await crud_product.get(db, obj["product_id"])
        if not product or product.status not in PUBLIC_PRODUCT_STATUSES:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.owner_company_id:
            obj["vendor_company_id"] = product.owner_company_id

    inquiry = await crud_inquiry.create_in_transaction(db, obj_in=obj)
    await _queue_inquiry_created(db, inquiry, anonymous=True)
    await db.commit()
    await db.refresh(inquiry)
    try:
        await ensure_inquiry_follow_up(db, inquiry)
    except Exception:
        pass

    return inquiry


async def _queue_inquiry_created(db: DB, inquiry, *, anonymous: bool) -> None:
    await emit_event(
        db,
        event_type="inquiry.created",
        payload={
            "inquiry_id": str(inquiry.id),
            "product_id": str(inquiry.product_id) if inquiry.product_id else None,
            "contact_name": inquiry.contact_name or ("Anonymous" if anonymous else "Unknown"),
            "contact_email": inquiry.contact_email or "",
            "message": (inquiry.message or "")[:200],
        },
        aggregate_type="inquiry",
        aggregate_id=inquiry.id,
        target_channel="telegram_admin",
    )


@router.put("/{id}", response_model=InquiryRead)
async def update_inquiry(id: uuid.UUID, data: InquiryUpdate, db: DB, admin: CRMUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    await require_crm_workspace_access(db, admin, inquiry.workspace_id)
    return await crud_inquiry.update(db, db_obj=inquiry, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=InquiryRead)
async def update_inquiry_status(id: uuid.UUID, data: InquiryStatusUpdate, db: DB, admin: CRMUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    await require_crm_workspace_access(db, admin, inquiry.workspace_id)
    return await crud_inquiry.update(db, db_obj=inquiry, obj_in={"status": data.status})


@router.delete("/{id}")
async def delete_inquiry(id: uuid.UUID, db: DB, admin: CRMUser):
    inquiry = await crud_inquiry.get(db, id)
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    await require_crm_workspace_access(db, admin, inquiry.workspace_id)
    success = await crud_inquiry.delete(db, id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return {"ok": True}

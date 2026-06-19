"""P3-06: Legacy Cebu API path aliases -> Core commerce services.

Frontends can point `NUXT_PUBLIC_API_BASE` at `/api/v1/cebu-compat` for a
drop-in migration window. New work should call `/api/v1/commerce/*` directly.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DB
from app.models.commerce import (
    CommerceOrder,
    ProcurementRequest,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
)
from app.models.notification import NotificationPreference
from app.models.user import Company, User
from app.modules.cebu_trade.models import RegionPaymentConfig
from app.modules.commerce.access import (
    CommerceAccessDenied,
    CommerceResourceNotFound,
    require_procurement_request_owner,
    require_supplier_company,
    user_is_order_party,
    resolve_commerce_workspace,
)
from app.schemas.commerce import (
    OrderDeliveryCreate,
    OrderDisputeCreate,
    SupplierListingRead,
    SupplierOfferCreate,
)
from app.schemas.user import UserRead, UserUpdate
from app.services.commerce_trade import (
    CommerceTradeError,
    award_offer,
    bind_listing_to_request,
    complete_order,
    create_delivery,
    create_procurement_request,
    list_orders_for_user,
    match_supplier_candidates,
    open_dispute,
    publish_request,
    submit_offer,
)
from app.services.commerce_messaging import (
    CommerceMessagingError,
    list_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.services.demo_mode import is_demo_mode_enabled

router = APIRouter(prefix="/cebu-compat", tags=["cebu-legacy-compat"])


class LegacyTelegramUpdate(BaseModel):
    telegram_chat_id: str | None = None


class LegacyNotificationPreferencesUpdate(BaseModel):
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    telegram_chat_id: str | None = None
    email: str | None = None
    whatsapp_number: str | None = None
    alerts_enabled: bool | None = None
    reports_enabled: bool | None = None
    maintenance_enabled: bool | None = None
    renewal_enabled: bool | None = None


@router.get("/system-mode")
async def legacy_system_mode(db: DB):
    return {
        "demo_mode": await is_demo_mode_enabled(db),
        "registration_enabled": True,
        "app_name": "AinerWise Procurement",
        "intent_max_attachments": 10,
    }


def _payment_region_config_as_legacy(row: RegionPaymentConfig | None, country: str) -> dict:
    normalized = (country or "PH").upper()[:2]
    if row is None:
        local_currency = "PHP" if normalized == "PH" else "USD"
        return {
            "country_code": normalized,
            "country_name": "Philippines" if normalized == "PH" else normalized,
            "local_currency": local_currency,
            "default_settlement_currency": local_currency,
            "default_transaction_mode": "LOCAL_ONLY",
            "enabled_currencies": [local_currency, "USD"] if local_currency != "USD" else ["USD"],
            "enabled_payment_methods": ["WALLET", "BANK_TRANSFER", "CASH_ON_DELIVERY"],
            "cross_border_currencies": ["USD"],
            "force_usd_bridge": False,
            "allow_supplier_payout_currency": True,
            "is_active": True,
            "source": "fallback",
        }
    return {
        "id": row.id,
        "country_code": row.country_code,
        "country_name": row.country_name,
        "local_currency": row.local_currency,
        "default_settlement_currency": row.default_settlement_currency,
        "default_transaction_mode": row.default_transaction_mode,
        "enabled_currencies": row.enabled_currencies or [row.local_currency],
        "enabled_payment_methods": row.enabled_payment_methods or ["WALLET"],
        "cross_border_currencies": row.cross_border_currencies or [],
        "force_usd_bridge": row.force_usd_bridge,
        "allow_supplier_payout_currency": row.allow_supplier_payout_currency,
        "is_active": row.is_active,
        "source": "core",
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _legacy_status(status: str | None, *, kind: str) -> str:
    value = (status or "").lower()
    maps = {
        "intent": {
            "draft": "DRAFT",
            "published": "ACTIVE",
            "matching": "ACTIVE",
            "offer_received": "ACTIVE",
            "awarded": "AWARDED",
            "closed": "CLOSED",
            "cancelled": "CANCELED",
        },
        "offer": {
            "draft": "DRAFT",
            "submitted": "SUBMITTED",
            "withdrawn": "WITHDRAWN",
            "awarded": "AWARDED",
            "rejected": "REJECTED",
        },
        "order": {
            "pending": "CREATED",
            "confirmed": "PAID_IN_ESCROW",
            "in_delivery": "IN_PROGRESS",
            "completed": "ACCEPTED",
            "disputed": "DISPUTED",
            "cancelled": "CANCELED",
        },
        "delivery": {
            "scheduled": "PENDING",
            "shipped": "DISPATCHED",
            "in_transit": "DISPATCHED",
            "delivered": "DELIVERED",
            "accepted": "ACCEPTED",
            "failed": "FAILED",
            "returned": "FAILED",
        },
        "dispute": {
            "open": "OPENED",
            "under_review": "UNDER_REVIEW",
            "resolved_buyer": "RESOLVED_REFUND",
            "resolved_supplier": "RESOLVED_RELEASE",
            "closed": "CANCELED",
            "withdrawn": "CANCELED",
        },
    }
    return maps.get(kind, {}).get(value, (status or "").upper())


def _legacy_role(role: str | None) -> str:
    value = (role or "").lower()
    if value == "buyer":
        return "BUYER"
    if value == "vendor":
        return "SUPPLIER_ADMIN"
    if value in {"admin", "super_admin"}:
        return value.upper()
    if value == "finance":
        return "FINANCE_OFFICER"
    return (role or "").upper()


def _user_as_legacy(user: User) -> dict:
    data = UserRead.model_validate(user).model_dump()
    data["role"] = _legacy_role(user.role)
    data["status"] = "ACTIVE" if user.is_active else "INACTIVE"
    data["two_fa_enabled"] = False
    return data


def _intent_as_legacy(row: ProcurementRequest) -> dict:
    requirements = row.requirements_json or {}
    attrs = {**(row.attrs_json or {}), **requirements}
    return {
        "id": row.id,
        "buyer_id": row.buyer_user_id,
        "category_id": row.category_schema_id,
        "title": row.title,
        "attrs_jsonb": attrs,
        "qty": int(requirements.get("qty") or attrs.get("qty") or 1),
        "unit": str(requirements.get("unit") or attrs.get("unit") or "pcs"),
        "budget_min_minor": requirements.get("budget_min_minor") or attrs.get("budget_min_minor"),
        "budget_max_minor": requirements.get("budget_max_minor") or attrs.get("budget_max_minor"),
        "currency": str(requirements.get("currency") or attrs.get("currency") or "PHP"),
        "country": requirements.get("country") or attrs.get("country"),
        "city": requirements.get("city") or attrs.get("city"),
        "lat": requirements.get("lat") or attrs.get("lat"),
        "lng": requirements.get("lng") or attrs.get("lng"),
        "radius_km": int(requirements.get("radius_km") or attrs.get("radius_km") or 30),
        "delivery_window_start": requirements.get("delivery_window_start"),
        "delivery_window_end": requirements.get("delivery_window_end"),
        "notes": row.description,
        "attachments": requirements.get("attachments") or attrs.get("attachments") or [],
        "status": _legacy_status(row.status, kind="intent"),
        "expires_at": requirements.get("expires_at") or attrs.get("expires_at"),
        "project_id": row.lead_id,
        "project_line_item_id": None,
        "created_at": row.created_at,
        "offer_count": None,
    }


def _offer_as_legacy(row: SupplierOffer) -> dict:
    terms = row.terms_json or {}
    qty = int(terms.get("qty_available") or 1)
    delivery_fee = int(terms.get("delivery_fee_minor") or 0)
    unit_price = int(terms.get("unit_price_minor") or row.price_minor)
    total = int(row.price_minor or (unit_price * qty + delivery_fee))
    return {
        "id": row.id,
        "intent_id": row.procurement_request_id,
        "company_id": row.supplier_company_id,
        "branch_id": terms.get("branch_id"),
        "catalog_item_id": row.supplier_listing_id,
        "supplier_user_id": terms.get("supplier_user_id"),
        "unit_price_minor": unit_price,
        "qty_available": qty,
        "delivery_fee_minor": delivery_fee,
        "total_price_minor": total,
        "currency": row.currency,
        "eta_date": terms.get("eta_date"),
        "warranty": terms.get("warranty"),
        "tier": terms.get("tier") or "CUSTOM",
        "stock_confidence": terms.get("stock_confidence") or "UNKNOWN",
        "message": terms.get("message"),
        "status": _legacy_status(row.status, kind="offer"),
        "expires_at": terms.get("expires_at"),
        "created_at": row.created_at,
    }


async def _order_as_legacy(db: DB, row: CommerceOrder) -> dict:
    request = await db.get(ProcurementRequest, row.procurement_request_id)
    return {
        "id": row.id,
        "intent_id": row.procurement_request_id,
        "offer_id": row.winning_offer_id,
        "buyer_id": request.buyer_user_id if request else None,
        "company_id": row.supplier_company_id,
        "company_name": None,
        "branch_id": None,
        "total_amount_minor": row.total_minor,
        "currency": row.currency,
        "status": _legacy_status(row.status, kind="order"),
        "notes": None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "escrow": None,
        "delivery": row.delivery_json,
    }


def _notification_as_legacy(row) -> dict:
    status = "READ" if row.status == "read" else "UNREAD"
    return {
        "id": row.id,
        "user_id": row.user_id,
        "channel": "IN_APP",
        "notification_type": row.event_type,
        "subject": row.title,
        "body": row.body or "",
        "status": status,
        "read_at": row.read_at,
        "created_at": row.created_at,
        "is_read": status == "READ",
    }


def _category_as_legacy(row: TradeCategorySchema) -> dict:
    return {
        "id": row.id,
        "slug": row.slug,
        "name": row.name,
        "name_zh": None,
        "description": (row.schema_json or {}).get("description"),
        "icon": (row.schema_json or {}).get("icon"),
        "schema_json": row.schema_json or {},
        "status": "ACTIVE" if row.status == "active" else row.status.upper(),
        "created_at": row.created_at,
    }


async def _owned_intent(db: DB, user: CurrentUser, intent_id: uuid.UUID):
    try:
        return await require_procurement_request_owner(db, user=user, request_id=intent_id)
    except CommerceResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None


def _listing_as_legacy(item) -> dict:
    data = SupplierListingRead.model_validate(item).model_dump()
    data["catalog_item_id"] = str(data["id"])
    return data


@router.get("/users/me")
async def legacy_get_me(user: CurrentUser):
    return _user_as_legacy(user)


@router.patch("/users/me")
async def legacy_update_me(data: UserUpdate, db: DB, user: CurrentUser):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return _user_as_legacy(user)


@router.patch("/users/me/telegram")
async def legacy_update_telegram(data: LegacyTelegramUpdate, db: DB, user: CurrentUser):
    company = await db.get(Company, user.company_id) if user.company_id else None
    if company is not None:
        company.telegram_chat_id = data.telegram_chat_id
    await db.commit()
    await db.refresh(user)
    return _user_as_legacy(user)


async def _notification_preference(db: DB, user: CurrentUser) -> NotificationPreference:
    row = (
        await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user.id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = NotificationPreference(user_id=user.id, company_id=user.company_id, email=user.email)
        db.add(row)
        await db.flush()
    return row


def _notification_preference_as_legacy(row: NotificationPreference) -> dict:
    return {
        "telegram_enabled": row.telegram_enabled,
        "email_enabled": row.email_enabled,
        "whatsapp_enabled": row.whatsapp_enabled,
        "telegram_chat_id": row.telegram_chat_id,
        "email": row.email,
        "whatsapp_number": row.whatsapp_number,
        "alerts_enabled": row.alerts_enabled,
        "reports_enabled": row.reports_enabled,
        "maintenance_enabled": row.maintenance_enabled,
        "renewal_enabled": row.renewal_enabled,
    }


@router.get("/users/me/notification-preferences")
async def legacy_get_notification_preferences(db: DB, user: CurrentUser):
    row = await _notification_preference(db, user)
    await db.commit()
    return _notification_preference_as_legacy(row)


@router.patch("/users/me/notification-preferences")
async def legacy_update_notification_preferences(
    data: LegacyNotificationPreferencesUpdate,
    db: DB,
    user: CurrentUser,
):
    row = await _notification_preference(db, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return _notification_preference_as_legacy(row)


@router.get("/categories")
async def legacy_categories(db: DB):
    rows = list(
        (
            await db.execute(
                select(TradeCategorySchema)
                .where(TradeCategorySchema.status == "active")
                .order_by(TradeCategorySchema.name.asc())
            )
        ).scalars()
    )
    return [_category_as_legacy(row) for row in rows]


@router.get("/categories/{category_id}/schema")
async def legacy_category_schema(category_id: uuid.UUID, db: DB):
    row = await db.get(TradeCategorySchema, category_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"id": row.id, "name": row.name, "schema_json": row.schema_json or {}}


@router.get("/payments/region-config")
async def legacy_payment_region_config(db: DB, country: str = Query(default="PH")):
    normalized = (country or "PH").upper()[:2]
    row = (
        await db.execute(
            select(RegionPaymentConfig).where(
                RegionPaymentConfig.country_code == normalized,
                RegionPaymentConfig.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    return _payment_region_config_as_legacy(row, normalized)


@router.get("/marketplace/feed")
async def legacy_marketplace_feed(
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_id: uuid.UUID | None = None,
    keyword: str | None = None,
):
    stmt = select(SupplierListing, Company.name.label("company_name")).join(
        Company,
        Company.id == SupplierListing.company_id,
        isouter=True,
    ).where(SupplierListing.status == "active")
    if category_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_id)
    if keyword:
        stmt = stmt.where(SupplierListing.title.ilike(f"%{keyword.strip()}%"))
    offset = (page - 1) * page_size
    rows = list((await db.execute(stmt.order_by(SupplierListing.created_at.desc()).offset(offset).limit(page_size))).all())
    items = []
    for listing, company_name in rows:
        attrs = listing.attributes_json or {}
        items.append(
            {
                "id": listing.id,
                "title": listing.title,
                "description": attrs.get("description"),
                "price_minor": listing.price_minor or 0,
                "currency": listing.currency,
                "unit": attrs.get("unit") or "pcs",
                "stock_qty": attrs.get("stock_qty") or 0,
                "images": attrs.get("images") or [],
                "tags": attrs.get("tags") or [],
                "market_mode": attrs.get("market_mode") or "B2B",
                "min_order_qty": attrs.get("min_order_qty") or 1,
                "origin_country": attrs.get("origin_country"),
                "view_count": attrs.get("view_count") or 0,
                "order_count": attrs.get("order_count") or 0,
                "status": "ACTIVE",
                "category_id": listing.category_schema_id,
                "category_name": None,
                "company_id": listing.company_id,
                "company_name": company_name,
                "company_trust_score": None,
                "is_sponsored": False,
                "created_at": listing.created_at,
            }
        )
    return {
        "items": items,
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "has_next": len(items) == page_size,
    }


@router.get("/marketplace/items/{item_id}")
async def legacy_marketplace_item(item_id: uuid.UUID, db: DB):
    row = (
        await db.execute(
            select(SupplierListing, Company.name.label("company_name"))
            .join(Company, Company.id == SupplierListing.company_id, isouter=True)
            .where(SupplierListing.id == item_id, SupplierListing.status == "active")
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    listing, company_name = row
    attrs = listing.attributes_json or {}
    return {
        "id": listing.id,
        "title": listing.title,
        "description": attrs.get("description"),
        "price_minor": listing.price_minor or 0,
        "currency": listing.currency,
        "unit": attrs.get("unit") or "pcs",
        "stock_qty": attrs.get("stock_qty") or 0,
        "images": attrs.get("images") or [],
        "tags": attrs.get("tags") or [],
        "market_mode": attrs.get("market_mode") or "B2B",
        "min_order_qty": attrs.get("min_order_qty") or 1,
        "origin_country": attrs.get("origin_country"),
        "view_count": attrs.get("view_count") or 0,
        "order_count": attrs.get("order_count") or 0,
        "status": "ACTIVE",
        "category_id": listing.category_schema_id,
        "category_name": None,
        "company_id": listing.company_id,
        "company_name": company_name,
        "company_trust_score": None,
        "is_sponsored": False,
        "created_at": listing.created_at,
    }


@router.post("/intents", status_code=201)
async def legacy_create_intent(data: dict, db: DB, user: CurrentUser):
    requirements = dict(data.get("attrs_jsonb") or data.get("requirements_json") or {})
    for key in (
        "qty",
        "unit",
        "budget_min_minor",
        "budget_max_minor",
        "currency",
        "country",
        "city",
        "lat",
        "lng",
        "radius_km",
        "delivery_window_start",
        "delivery_window_end",
        "attachments",
        "expires_at",
    ):
        if key in data and key not in requirements:
            requirements[key] = data[key]
    payload = {
        "title": data.get("title") or "Procurement request",
        "description": data.get("description") or data.get("notes"),
        "category_schema_id": data.get("category_schema_id") or data.get("category_id"),
        "region_id": data.get("region_id"),
        "requirements_json": requirements,
        "portal_key": "cebu",
        "workspace_id": data.get("workspace_id"),
    }
    try:
        payload["workspace_id"] = await resolve_commerce_workspace(
            db,
            user=user,
            requested_workspace_id=payload["workspace_id"],
        )
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await create_procurement_request(
        db,
        buyer_user_id=user.id,
        buyer_company_id=user.company_id,
        **payload,
    )
    await db.commit()
    await db.refresh(row)
    return _intent_as_legacy(row)


@router.get("/intents/my")
async def legacy_my_intents(db: DB, user: CurrentUser):
    scope = ProcurementRequest.buyer_user_id == user.id
    if user.company_id is not None:
        scope = scope | (ProcurementRequest.buyer_company_id == user.company_id)
    rows = list(
        (
            await db.execute(
                select(ProcurementRequest)
                .where(scope)
                .order_by(ProcurementRequest.created_at.desc())
                .limit(100)
            )
        ).scalars()
    )
    return [_intent_as_legacy(row) for row in rows]


@router.get("/supplier/intents/matching")
async def legacy_supplier_matching_intents(db: DB, user: CurrentUser):
    try:
        require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    rows = list(
        (
            await db.execute(
                select(ProcurementRequest)
                .where(ProcurementRequest.status.in_(("published", "matching", "offer_received")))
                .order_by(ProcurementRequest.published_at.desc(), ProcurementRequest.created_at.desc())
                .limit(100)
            )
        ).scalars()
    )
    return [_intent_as_legacy(row) for row in rows]


@router.get("/intents/{intent_id}")
async def legacy_get_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(ProcurementRequest, intent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Intent not found")
    if user.role == "vendor":
        if row.status not in ("published", "matching", "offer_received", "awarded"):
            raise HTTPException(status_code=403, detail="Intent is not visible to suppliers")
    else:
        await _owned_intent(db, user, intent_id)
    return _intent_as_legacy(row)


@router.patch("/intents/{intent_id}")
async def legacy_update_intent(intent_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row = await _owned_intent(db, user, intent_id)
    if row.status not in ("draft", "published", "matching"):
        raise HTTPException(status_code=409, detail="Cannot update intent in current status")
    if "title" in data:
        row.title = data["title"]
    if "notes" in data or "description" in data:
        row.description = data.get("description") or data.get("notes")
    requirements = dict(row.requirements_json or {})
    for key in (
        "qty",
        "unit",
        "budget_min_minor",
        "budget_max_minor",
        "attachments",
        "currency",
        "city",
        "country",
        "radius_km",
    ):
        if key in data:
            requirements[key] = data[key]
    row.requirements_json = requirements
    await db.commit()
    await db.refresh(row)
    return _intent_as_legacy(row)


@router.post("/intents/{intent_id}/cancel")
async def legacy_cancel_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await _owned_intent(db, user, intent_id)
    if row.status not in ("draft", "published", "matching", "offer_received"):
        raise HTTPException(status_code=409, detail="Cannot cancel intent in current status")
    row.status = "cancelled"
    await db.commit()
    await db.refresh(row)
    return _intent_as_legacy(row)


@router.post("/intents/{intent_id}/publish")
async def legacy_publish_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_intent(db, user, intent_id)
    try:
        row = await publish_request(db, intent_id)
        await db.commit()
        await db.refresh(row)
        return _intent_as_legacy(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/intents/{intent_id}/offers")
async def legacy_list_offers(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_intent(db, user, intent_id)
    rows = list(
        (
            await db.execute(
                select(SupplierOffer)
                .where(SupplierOffer.procurement_request_id == intent_id)
                .order_by(SupplierOffer.created_at.desc())
            )
        ).scalars()
    )
    return [_offer_as_legacy(row) for row in rows]


@router.post("/intents/{intent_id}/offers", status_code=201)
async def legacy_submit_offer(intent_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    unit_price = int(data.get("unit_price_minor") or data.get("price_minor") or 0)
    qty = int(data.get("qty_available") or 1)
    delivery_fee = int(data.get("delivery_fee_minor") or 0)
    total = int(data.get("total_price_minor") or (unit_price * qty + delivery_fee))
    payload = SupplierOfferCreate(
        supplier_listing_id=data.get("supplier_listing_id") or data.get("catalog_item_id"),
        supplier_company_id=data.get("supplier_company_id") or data.get("company_id"),
        price_minor=total,
        currency=data.get("currency") or "PHP",
        terms_json={
            **(data.get("terms_json") or {}),
            "unit_price_minor": unit_price,
            "qty_available": qty,
            "delivery_fee_minor": delivery_fee,
            "branch_id": data.get("branch_id"),
            "eta_date": data.get("eta_date"),
            "warranty": data.get("warranty"),
            "tier": data.get("tier"),
            "stock_confidence": data.get("stock_confidence"),
            "message": data.get("message"),
            "supplier_user_id": str(user.id),
        },
    )
    try:
        supplier_company_id = require_supplier_company(
            user,
            requested_company_id=payload.supplier_company_id,
        )
        if payload.supplier_listing_id:
            listing = await db.get(SupplierListing, payload.supplier_listing_id)
            if listing is None or listing.company_id != supplier_company_id:
                raise HTTPException(status_code=403, detail="Cannot use another supplier listing")
        row = await submit_offer(
            db,
            procurement_request_id=intent_id,
            supplier_company_id=supplier_company_id,
            supplier_listing_id=payload.supplier_listing_id,
            price_minor=payload.price_minor,
            currency=payload.currency,
            terms_json=payload.terms_json,
        )
        await db.commit()
        await db.refresh(row)
        return _offer_as_legacy(row)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/supplier/offers")
async def legacy_supplier_offers(db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    rows = list(
        (
            await db.execute(
                select(SupplierOffer)
                .where(SupplierOffer.supplier_company_id == company_id)
                .order_by(SupplierOffer.created_at.desc())
                .limit(100)
            )
        ).scalars()
    )
    return [_offer_as_legacy(row) for row in rows]


@router.post("/offers/{offer_id}/withdraw")
async def legacy_withdraw_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await db.get(SupplierOffer, offer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if row.supplier_company_id != company_id:
        raise HTTPException(status_code=403, detail="Cannot withdraw another supplier's offer")
    if row.status not in ("draft", "submitted"):
        raise HTTPException(status_code=409, detail="Only draft or submitted offers can be withdrawn")
    row.status = "withdrawn"
    await db.commit()
    await db.refresh(row)
    return _offer_as_legacy(row)


@router.post("/offers/{offer_id}/award")
async def legacy_award_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    offer = await db.get(SupplierOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    await _owned_intent(db, user, offer.procurement_request_id)
    try:
        order = await award_offer(db, offer_id)
        await db.commit()
        await db.refresh(order)
        return await _order_as_legacy(db, order)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/orders/my")
async def legacy_my_orders(db: DB, user: CurrentUser):
    rows = await list_orders_for_user(db, user)
    return [await _order_as_legacy(db, row) for row in rows]


@router.get("/orders/{order_id}")
async def legacy_get_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role not in ("admin", "super_admin") and not await user_is_order_party(db, user, row):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    return await _order_as_legacy(db, row)


@router.post("/orders/{order_id}/accept")
async def legacy_accept_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    party = await user_is_order_party(db, user, row)
    if party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer can accept order")
    try:
        updated = await complete_order(db, order_id=order_id)
        await db.commit()
        await db.refresh(updated)
        return await _order_as_legacy(db, updated)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/delivery", status_code=201)
async def legacy_create_delivery(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    party = await user_is_order_party(db, user, row)
    if party not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Only supplier can create delivery")
    payload = OrderDeliveryCreate(
        carrier=data.get("carrier"),
        tracking_number=data.get("tracking_number"),
        ship_from_json=data.get("ship_from_json"),
        ship_to_json=data.get("ship_to_json"),
        estimated_at=data.get("estimated_at"),
    )
    try:
        delivery = await create_delivery(db, order_id, **payload.model_dump())
        await db.commit()
        await db.refresh(delivery)
        return {
            "id": delivery.id,
            "order_id": delivery.commerce_order_id,
            "status": _legacy_status(delivery.status, kind="delivery"),
            "tracking_number": delivery.tracking_number,
            "carrier": delivery.carrier,
            "notes": None,
            "proofs": (delivery.proof_json or {}).get("proofs") if delivery.proof_json else [],
            "actor_id": user.id,
            "created_at": delivery.created_at,
            "updated_at": delivery.updated_at,
        }
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/dispute", status_code=201)
async def legacy_open_dispute(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role not in ("admin", "super_admin") and not await user_is_order_party(db, user, row):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    payload = OrderDisputeCreate(
        reason_code=data.get("reason_code") or data.get("reason") or "general",
        description=data.get("description") or data.get("reason"),
    )
    try:
        dispute = await open_dispute(
            db,
            order_id=order_id,
            user=user,
            reason_code=payload.reason_code,
            description=payload.description,
        )
        await db.commit()
        await db.refresh(dispute)
        return {
            "id": dispute.id,
            "order_id": dispute.commerce_order_id,
            "opened_by_user_id": user.id,
            "reason": dispute.reason_code,
            "evidence_json": [],
            "admin_notes": None,
            "status": _legacy_status(dispute.status, kind="dispute"),
            "resolution": None,
            "refund_amount_minor": None,
            "created_at": dispute.created_at,
            "updated_at": dispute.updated_at,
        }
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/notifications/my")
async def legacy_notifications(db: DB, user: CurrentUser):
    rows = await list_user_notifications(db, user_id=user.id, portal_key="cebu")
    return [_notification_as_legacy(row) for row in rows]


@router.post("/notifications/{notification_id}/read")
async def legacy_mark_notification_read(notification_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        row = await mark_notification_read(db, notification_id, user.id)
        await db.commit()
        await db.refresh(row)
        return _notification_as_legacy(row)
    except CommerceMessagingError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/notifications/read-all")
async def legacy_mark_all_notifications_read(db: DB, user: CurrentUser):
    count = await mark_all_notifications_read(db, user.id)
    await db.commit()
    return {"marked_read": count}


@router.get("/intents/{intent_id}/supplier-candidates")
async def legacy_supplier_candidates(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_intent(db, user, intent_id)
    try:
        items = await match_supplier_candidates(db, intent_id)
        legacy_items = [_listing_as_legacy(i) for i in items]
        return {"intent_id": str(intent_id), "items": legacy_items, "total": len(legacy_items)}
    except CommerceTradeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/intents/{intent_id}/supplier-candidates/{catalog_item_id}")
async def legacy_supplier_candidate_detail(
    intent_id: uuid.UUID, catalog_item_id: uuid.UUID, db: DB, user: CurrentUser
):
    await _owned_intent(db, user, intent_id)
    try:
        items = await match_supplier_candidates(db, intent_id)
        match = next((i for i in items if i.id == catalog_item_id), None)
        if match is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return {"intent_id": str(intent_id), "item": _listing_as_legacy(match)}
    except CommerceTradeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/intents/{intent_id}/supplier-candidates/{catalog_item_id}/bind")
async def legacy_bind_supplier_candidate(
    intent_id: uuid.UUID, catalog_item_id: uuid.UUID, db: DB, user: CurrentUser
):
    await _owned_intent(db, user, intent_id)
    try:
        row = await bind_listing_to_request(db, intent_id, catalog_item_id)
        await db.commit()
        return {
            "intent_id": str(intent_id),
            "catalog_item_id": str(catalog_item_id),
            "status": row.status,
            "attrs_json": row.attrs_json,
        }
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None

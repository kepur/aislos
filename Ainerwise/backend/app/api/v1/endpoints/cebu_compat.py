"""P3-06: Legacy Cebu API path aliases -> Core commerce services.

Frontends can point `NUXT_PUBLIC_API_BASE` at `/api/v1/cebu-compat` for a
drop-in migration window. New work should call `/api/v1/commerce/*` directly.
"""
import uuid
import io
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DB
from app.api.v1.endpoints.files import BUCKET_NAME, get_minio_client
from app.core.object_storage import new_user_upload_key
from app.models.commerce import (
    CommerceMessage,
    CommerceOrder,
    CommerceThread,
    OrderDelivery,
    ProcurementRequest,
    SupplierListing,
    SupplierOffer,
    TransactionReview,
    TradeCategorySchema,
)
from app.models.notification import NotificationPreference
from app.models.user import Company, User
from app.modules.cebu_trade.models import (
    AdCampaign,
    EscrowTransaction,
    RegionPaymentConfig,
    WalletDeposit,
    WalletTransaction,
)
from app.modules.cebu_trade.schemas import (
    WalletDepositRead,
    WalletRead,
    WalletTransactionRead,
)
from app.modules.cebu_trade.service import (
    CebuTradeError,
    capture_escrow,
    create_ad_campaign,
    create_deposit,
    create_escrow,
    get_or_create_wallet,
    get_escrow_for_order,
    list_ad_campaigns,
    list_deposits,
    list_wallet_transactions,
    release_escrow,
    update_ad_campaign_status,
    wallet_balance,
)
from app.modules.buyer_project.models import (
    BuyerProject,
    ProjectAIRun,
    ProjectFile,
    ProjectLineItem,
    ProjectMessage,
    ProjectReport,
    ProjectReportChangeLog,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportVersion,
)
from app.modules.buyer_project.schemas import ProjectCreate, ProjectUpdate
from app.modules.buyer_project.service import (
    BuyerProjectError,
    add_message as add_buyer_project_message,
    create_project as create_buyer_project,
    estimate_prices as estimate_buyer_project_prices,
    freeze_report as freeze_buyer_project_report,
    get_metrics as get_buyer_project_metrics,
    get_project as get_buyer_project,
    get_report as get_buyer_project_report,
    list_line_items as list_buyer_project_line_items,
    list_messages as list_buyer_project_messages,
    list_projects as list_buyer_projects,
    list_report_versions as list_buyer_project_report_versions,
    recalculate_report as recalculate_buyer_project_report,
    report_detail as buyer_project_report_detail,
    update_line_item as update_buyer_project_line_item,
    update_project as update_buyer_project,
    update_report_row as update_buyer_project_report_row,
)
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
    advance_delivery,
    award_offer,
    bind_listing_to_request,
    complete_order,
    create_listing,
    create_delivery,
    create_procurement_request,
    list_deliveries,
    list_orders_for_user,
    match_supplier_candidates,
    open_dispute,
    publish_request,
    submit_offer,
)
from app.services.commerce_trust import CommerceTrustError, submit_transaction_review
from app.services.commerce_messaging import (
    CommerceMessagingAccessDenied,
    CommerceMessagingError,
    get_or_create_thread_for_order,
    list_thread_messages,
    list_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    post_thread_message,
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


class LegacyWalletDepositCreate(BaseModel):
    amount_minor: int
    currency: str = "PHP"
    network: str = "LOCAL_BANK"
    provider: str = "MANUAL_BANK"
    payment_method: str = "PHP_MANUAL_BANK"
    source_currency: str | None = None
    target_currency: str | None = None
    deposit_address: str | None = None
    tx_hash: str | None = None
    submitter_note: str | None = None


class LegacyWalletSubmitTx(BaseModel):
    tx_hash: str | None = None
    submitter_note: str | None = None


class LegacyProjectMessageCreate(BaseModel):
    content: str
    workflow_node: str | None = None
    file_ids: list[uuid.UUID] | None = None


class LegacyProjectReportCellChange(BaseModel):
    row_id: uuid.UUID
    field: str
    value: object | None = None


class LegacyProjectReportCellsPatch(BaseModel):
    changes: list[LegacyProjectReportCellChange]
    message: str | None = None


class LegacyProjectReportColumnCreate(BaseModel):
    key: str
    label: str
    data_type: str = "text"
    editable: bool = True


class LegacyProjectReportRowCreate(BaseModel):
    name: str
    description: str | None = None
    qty: float = 1
    unit: str = "pcs"
    currency: str = "PHP"
    quality_tier: str = "MID_RANGE"
    selected_tier: str = "MID_RANGE"
    notes: str | None = None


class LegacyProjectReportChatRequest(BaseModel):
    message: str


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


def _require_legacy_admin(user: User) -> None:
    if user.role not in ("admin", "super_admin", "finance"):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _uuid_or_none(value: object | None) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid UUID value") from exc


def _company_as_legacy(row: Company) -> dict:
    contact_info = row.contact_info or {}
    return {
        "id": row.id,
        "name": row.name,
        "type": row.type,
        "country": row.country,
        "city": row.city,
        "address": row.address,
        "phone": contact_info.get("phone"),
        "email": contact_info.get("email"),
        "website": row.website,
        "description": row.description,
        "verification_status": row.verification_status,
        "contact_info": contact_info,
        "logo_url": row.logo_url,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _catalog_status_to_core(status: str | None) -> str | None:
    if status is None:
        return None
    maps = {
        "ACTIVE": "active",
        "INACTIVE": "inactive",
        "DRAFT": "draft",
        "ARCHIVED": "archived",
        "DELETED": "archived",
    }
    return maps.get(str(status).upper(), str(status).lower())


def _catalog_status_as_legacy(status: str | None) -> str:
    maps = {
        "active": "ACTIVE",
        "inactive": "INACTIVE",
        "draft": "DRAFT",
        "archived": "DELETED",
    }
    return maps.get((status or "").lower(), (status or "").upper())


def _catalog_attrs_from_payload(data: dict, existing: dict | None = None) -> dict:
    attrs = dict(existing or {})
    for key in (
        "description",
        "unit",
        "stock_qty",
        "images",
        "tags",
        "market_mode",
        "min_order_qty",
        "origin_country",
        "view_count",
        "order_count",
    ):
        if key in data:
            attrs[key] = data.get(key)
    extra = data.get("attributes_json") or data.get("attrs_json") or {}
    if isinstance(extra, dict):
        attrs.update(extra)
    return attrs


def _catalog_item_as_legacy(row: SupplierListing, *, company_name: str | None = None) -> dict:
    attrs = row.attributes_json or {}
    return {
        "id": row.id,
        "company_id": row.company_id,
        "company_name": company_name,
        "category_id": row.category_schema_id,
        "category_schema_id": row.category_schema_id,
        "title": row.title,
        "description": attrs.get("description"),
        "price_minor": row.price_minor or 0,
        "currency": row.currency,
        "unit": attrs.get("unit") or "pcs",
        "stock_qty": attrs.get("stock_qty") or 0,
        "images": attrs.get("images") or [],
        "tags": attrs.get("tags") or [],
        "market_mode": attrs.get("market_mode") or "B2B",
        "min_order_qty": attrs.get("min_order_qty") or 1,
        "origin_country": attrs.get("origin_country"),
        "view_count": attrs.get("view_count") or 0,
        "order_count": attrs.get("order_count") or 0,
        "status": _catalog_status_as_legacy(row.status),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _ad_status_to_core(status: str) -> str:
    value = (status or "").upper()
    if value not in {"DRAFT", "PENDING_REVIEW", "ACTIVE", "PAUSED", "REJECTED", "COMPLETED"}:
        raise HTTPException(status_code=422, detail="Unsupported campaign status")
    return value


def _ad_campaign_as_legacy(row: AdCampaign) -> dict:
    return {
        "id": row.id,
        "company_id": row.company_id,
        "catalog_item_id": row.listing_id,
        "listing_id": row.listing_id,
        "title": row.title,
        "name": row.title,
        "placement": row.placement,
        "target_category_id": row.target_category_id,
        "target_keywords": row.target_keywords or [],
        "target_countries": row.target_countries or [],
        "budget_minor": row.budget_minor,
        "spent_minor": row.spent_minor,
        "bid_per_click_minor": row.bid_per_click_minor,
        "currency": row.currency,
        "status": row.status,
        "rejection_reason": row.rejection_reason,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
        "impressions": row.impressions,
        "clicks": row.clicks,
        "conversions": row.conversions,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


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


def _escrow_as_legacy(row: EscrowTransaction | None) -> dict | None:
    if row is None:
        return None
    status_map = {
        "AUTH_PENDING": "PENDING",
        "AUTH_HELD": "AUTHORIZED",
        "CAPTURED": "CAPTURED",
        "RELEASED": "RELEASED",
        "REFUNDED": "REFUNDED",
        "PARTIALLY_REFUNDED": "REFUNDED",
        "FAILED": "FAILED",
    }
    return {
        "id": row.id,
        "order_id": row.order_id,
        "provider": row.provider,
        "provider_reference": row.provider_reference,
        "amount_minor": row.auth_amount_minor,
        "auth_amount_minor": row.auth_amount_minor,
        "captured_amount_minor": row.captured_amount_minor,
        "released_amount_minor": row.released_amount_minor,
        "refunded_amount_minor": row.refunded_amount_minor,
        "currency": row.currency,
        "status": status_map.get(row.status, row.status),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _delivery_as_legacy(row: OrderDelivery | None, *, actor_id: uuid.UUID | None = None) -> dict | None:
    if row is None:
        return None
    proof_json = row.proof_json or {}
    return {
        "id": row.id,
        "order_id": row.commerce_order_id,
        "status": _legacy_status(row.status, kind="delivery"),
        "tracking_number": row.tracking_number,
        "carrier": row.carrier,
        "notes": proof_json.get("notes"),
        "proofs": proof_json.get("proofs") or [],
        "ship_from_json": row.ship_from_json,
        "ship_to_json": row.ship_to_json,
        "estimated_at": row.estimated_at,
        "shipped_at": row.shipped_at,
        "delivered_at": row.delivered_at,
        "accepted_at": row.accepted_at,
        "actor_id": actor_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def _order_latest_delivery(db: DB, row: CommerceOrder) -> OrderDelivery | None:
    deliveries = await list_deliveries(db, row)
    return deliveries[-1] if deliveries else None


async def _order_escrow(db: DB, row: CommerceOrder) -> EscrowTransaction | None:
    try:
        return await get_escrow_for_order(db, row.id)
    except CebuTradeError:
        return (
            await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == row.id))
        ).scalar_one_or_none()


async def _order_as_legacy(db: DB, row: CommerceOrder) -> dict:
    request = await db.get(ProcurementRequest, row.procurement_request_id)
    escrow = await _order_escrow(db, row)
    latest_delivery = await _order_latest_delivery(db, row)
    status = _legacy_status(row.status, kind="order")
    if row.status == "confirmed" and escrow is None:
        status = "AWAITING_PAYMENT"
    elif row.status == "confirmed" and escrow.status in ("AUTH_HELD", "CAPTURED"):
        status = "PAID_IN_ESCROW"
    elif row.status == "in_delivery" and latest_delivery and latest_delivery.status == "delivered":
        status = "DELIVERED"
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
        "status": status,
        "notes": None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "escrow": _escrow_as_legacy(escrow),
        "delivery": _delivery_as_legacy(latest_delivery) or row.delivery_json,
    }


async def _require_legacy_order_party(
    db: DB,
    user: User,
    order_id: uuid.UUID,
    *,
    allowed: set[str] | None = None,
) -> tuple[CommerceOrder, str]:
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    party = await user_is_order_party(db, user, row)
    if party is None:
        raise HTTPException(status_code=403, detail="Not a party to this order")
    if allowed and party not in allowed:
        label = " or ".join(sorted(allowed))
        raise HTTPException(status_code=403, detail=f"Operation requires {label}")
    return row, party


_LEGACY_DELIVERY_TO_CORE = {
    "PENDING": "scheduled",
    "READY_FOR_PICKUP": "scheduled",
    "DISPATCHED": "shipped",
    "DELIVERED": "delivered",
    "ACCEPTED": "accepted",
    "FAILED": "failed",
}


async def _advance_delivery_to_legacy_status(
    db: DB,
    delivery: OrderDelivery,
    legacy_status: str | None,
    *,
    proof_json: dict | None = None,
) -> OrderDelivery:
    target = _LEGACY_DELIVERY_TO_CORE.get((legacy_status or "PENDING").upper(), "scheduled")
    if delivery.status == target:
        if proof_json:
            delivery.proof_json = proof_json
            await db.flush()
        return delivery

    if target == "failed":
        return await advance_delivery(db, delivery.id, new_status="failed", proof_json=proof_json)

    path = ["scheduled", "shipped", "in_transit", "delivered", "accepted"]
    if delivery.status not in path or target not in path:
        return await advance_delivery(db, delivery.id, new_status=target, proof_json=proof_json)

    current_index = path.index(delivery.status)
    target_index = path.index(target)
    if target_index <= current_index:
        return delivery

    row = delivery
    for next_status in path[current_index + 1 : target_index + 1]:
        row = await advance_delivery(
            db,
            row.id,
            new_status=next_status,
            proof_json=proof_json if next_status == target else None,
        )
    return row


def _wallet_transaction(
    *,
    wallet_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    tx_type: str,
    amount_delta_minor: int,
    currency: str,
    available_after: int,
    locked_after: int,
    reference_type: str,
    reference_id: uuid.UUID,
    note: str,
) -> WalletTransaction:
    return WalletTransaction(
        wallet_id=wallet_id,
        owner_user_id=owner_user_id,
        tx_type=tx_type,
        amount_delta_minor=amount_delta_minor,
        available_balance_after_minor=available_after,
        locked_balance_after_minor=locked_after,
        currency=currency,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
    )


async def _wallet_tx_exists(
    db: DB,
    *,
    owner_user_id: uuid.UUID,
    tx_type: str,
    reference_id: uuid.UUID,
) -> bool:
    return (
        await db.execute(
            select(WalletTransaction.id).where(
                WalletTransaction.owner_user_id == owner_user_id,
                WalletTransaction.tx_type == tx_type,
                WalletTransaction.reference_id == reference_id,
            )
        )
    ).first() is not None


async def _credit_supplier_wallet_from_escrow(
    db: DB,
    *,
    order: CommerceOrder,
    escrow: EscrowTransaction,
) -> None:
    if not order.supplier_company_id:
        return
    supplier_user = (
        await db.execute(
            select(User)
            .where(User.company_id == order.supplier_company_id)
            .order_by(User.created_at.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if supplier_user is None:
        return
    if await _wallet_tx_exists(
        db,
        owner_user_id=supplier_user.id,
        tx_type="ESCROW_RELEASED_TO_SUPPLIER",
        reference_id=escrow.id,
    ):
        return
    amount = escrow.released_amount_minor or escrow.captured_amount_minor or escrow.auth_amount_minor
    if amount <= 0:
        return
    wallet = await get_or_create_wallet(db, supplier_user.id, escrow.currency)
    wallet.available_balance_minor += amount
    db.add(
        _wallet_transaction(
            wallet_id=wallet.id,
            owner_user_id=supplier_user.id,
            tx_type="ESCROW_RELEASED_TO_SUPPLIER",
            amount_delta_minor=amount,
            currency=escrow.currency,
            available_after=wallet.available_balance_minor,
            locked_after=wallet.locked_balance_minor,
            reference_type="escrow_transaction",
            reference_id=escrow.id,
            note=f"Escrow released for order {order.id}",
        )
    )


def _rating_average(*values: object) -> int:
    ratings = []
    for value in values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= number <= 5:
            ratings.append(number)
    if not ratings:
        return 5
    return max(1, min(5, round(sum(ratings) / len(ratings))))


def _message_as_legacy(row: CommerceMessage) -> dict:
    attachments = row.attachments_json or {}
    if isinstance(attachments, dict):
        attachment_list = attachments.get("attachments") or []
    elif isinstance(attachments, list):
        attachment_list = attachments
    else:
        attachment_list = []
    return {
        "id": row.id,
        "thread_type": "ORDER",
        "thread_id": row.thread_id,
        "sender_id": row.sender_user_id,
        "sender_role": row.sender_role,
        "body": row.body,
        "attachments": attachment_list,
        "read_at": row.read_at,
        "created_at": row.created_at,
    }


def _notification_type_as_legacy(event_type: str | None) -> str:
    maps = {
        "commerce.message.received": "MESSAGE_RECEIVED",
        "procurement.offer.submitted": "OFFER_RECEIVED",
        "procurement.offer.awarded": "OFFER_AWARDED_SUPPLIER",
        "commerce.order.awarded": "ORDER_CREATED",
        "commerce.delivery.shipped": "DELIVERY_UPDATED_SUPPLIER",
        "commerce.delivery.delivered": "DELIVERY_UPDATED_SUPPLIER",
        "commerce.dispute.opened": "DISPUTE_OPENED",
        "commerce.order.completed": "ORDER_ACCEPTED_SUPPLIER",
        "cebu.admin.test": "ADMIN_TEST",
    }
    if not event_type:
        return "SYSTEM"
    return maps.get(event_type, event_type.upper().replace(".", "_"))


def _notification_as_legacy(row) -> dict:
    status = "READ" if row.status == "read" else "UNREAD"
    return {
        "id": row.id,
        "user_id": row.user_id,
        "channel": "IN_APP",
        "notification_type": _notification_type_as_legacy(row.event_type),
        "event_type": row.event_type,
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


def _wallet_instruction_address(data: LegacyWalletDepositCreate, user: CurrentUser) -> str:
    provided = (data.deposit_address or "").strip()
    if provided:
        return provided
    currency = (data.currency or "PHP").upper()
    network = (data.network or "LOCAL_BANK").upper()
    method = (data.payment_method or "PHP_MANUAL_BANK").upper()
    user_ref = str(user.id).replace("-", "")[:10].upper()
    return f"AINERWISE-PROCUREMENT-{currency}-{network}-{method}-{user_ref}"


def _row_dict(row) -> dict:
    if row is None:
        return {}
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _with_jsonb_aliases(value):
    if isinstance(value, list):
        return [_with_jsonb_aliases(item) for item in value]
    if not isinstance(value, dict):
        return value
    data = {}
    for key, item in value.items():
        converted = _with_jsonb_aliases(item)
        data[key] = converted
        if key.endswith("_json"):
            data[f"{key}b"] = converted
    return data


def _line_item_as_legacy(row: ProjectLineItem) -> dict:
    data = _with_jsonb_aliases(_row_dict(row))
    data["intent_id"] = data.get("procurement_request_id")
    data.setdefault("price_tiers_jsonb", data.get("price_tiers_json") or {})
    data.setdefault("specs_jsonb", data.get("specs_json") or {})
    return data


def _file_as_legacy(row: ProjectFile) -> dict:
    return _with_jsonb_aliases(_row_dict(row))


def _ai_run_as_legacy(row: ProjectAIRun | None) -> dict | None:
    if row is None:
        return None
    return _with_jsonb_aliases(_row_dict(row))


async def _latest_project_ai_run(db: DB, project_id: uuid.UUID) -> ProjectAIRun | None:
    return (
        await db.execute(
            select(ProjectAIRun)
            .where(ProjectAIRun.project_id == project_id)
            .order_by(ProjectAIRun.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _project_files(db: DB, project_id: uuid.UUID) -> list[ProjectFile]:
    return list(
        (
            await db.execute(
                select(ProjectFile)
                .where(ProjectFile.project_id == project_id)
                .order_by(ProjectFile.created_at.asc())
            )
        ).scalars()
    )


async def _buyer_project_as_legacy(db: DB, project: BuyerProject, *, detail: bool = False) -> dict:
    data = _with_jsonb_aliases(_row_dict(project))
    data.setdefault("missing_questions_jsonb", data.get("missing_questions_json") or [])
    data.setdefault("assumptions_jsonb", data.get("assumptions_json") or [])
    data.setdefault("risk_notes_jsonb", data.get("risk_notes_json") or [])
    data.setdefault("acceptance_criteria_jsonb", data.get("acceptance_criteria_json") or [])
    data.setdefault("estimated_budget_jsonb", data.get("estimated_budget_json"))
    data.setdefault("scale_jsonb", data.get("scale_json"))
    if detail:
        data["files"] = [_file_as_legacy(row) for row in await _project_files(db, project.id)]
        data["line_items"] = [
            _line_item_as_legacy(row) for row in await list_buyer_project_line_items(db, project.id)
        ]
        data["latest_ai_run"] = _ai_run_as_legacy(await _latest_project_ai_run(db, project.id))
    return data


def _metric_payload_as_legacy(payload: dict) -> dict:
    data = _with_jsonb_aliases(payload)
    for row in data.get("values") or []:
        if "value_json" in row and "value_jsonb" not in row:
            row["value_jsonb"] = row["value_json"]
    for row in data.get("templates") or []:
        if "unit_options_json" in row and "unit_options_jsonb" not in row:
            row["unit_options_jsonb"] = row["unit_options_json"]
    return data


def _report_payload_as_legacy(payload: dict) -> dict:
    return _with_jsonb_aliases(payload)


def _project_line_item_templates(project: BuyerProject) -> list[dict]:
    description = (project.description or "").lower()
    project_type = (project.project_type or "GENERAL").upper()
    if project_type == "SOLAR" or "solar" in description or "光伏" in description:
        return [
            {"name": "Solar PV panels", "category_hint": "solar", "unit": "lot", "share": 0.48},
            {"name": "Hybrid inverter and electrical protection", "category_hint": "solar_electrical", "unit": "set", "share": 0.28},
            {"name": "Mounting, cabling and commissioning", "category_hint": "installation", "unit": "lot", "share": 0.24},
        ]
    if project_type in {"CONSTRUCTION", "RENOVATION"} or any(word in description for word in ("hotel", "villa", "renovation", "装修", "别墅", "酒店")):
        return [
            {"name": "Core materials and fixtures package", "category_hint": "building_materials", "unit": "lot", "share": 0.42},
            {"name": "Electrical, lighting and smart-control package", "category_hint": "smart_building", "unit": "lot", "share": 0.34},
            {"name": "Installation, testing and handover service", "category_hint": "field_service", "unit": "lot", "share": 0.24},
        ]
    if project_type == "TECH_BUILD" or any(word in description for word in ("network", "cctv", "access", "门禁", "监控", "网络")):
        return [
            {"name": "Network backbone and cabinet package", "category_hint": "network", "unit": "lot", "share": 0.36},
            {"name": "CCTV, access control and sensors", "category_hint": "security", "unit": "lot", "share": 0.38},
            {"name": "Configuration, testing and documentation", "category_hint": "commissioning", "unit": "lot", "share": 0.26},
        ]
    return [
        {"name": "Primary procurement package", "category_hint": "general_procurement", "unit": "lot", "share": 0.5},
        {"name": "Delivery and installation package", "category_hint": "delivery_installation", "unit": "lot", "share": 0.3},
        {"name": "Warranty, acceptance and support package", "category_hint": "support", "unit": "lot", "share": 0.2},
    ]


def _project_budget_base(project: BuyerProject) -> int:
    if project.budget_max:
        return max(int(project.budget_max), 10000)
    if project.budget_min:
        return max(int(project.budget_min * 1.35), 10000)
    if project.area_value:
        return max(int(float(project.area_value) * 12000), 10000)
    return 250000


def _tier_prices(total: float) -> dict:
    return {
        "BUDGET": {
            "unit_price": round(total * 0.8, 2),
            "total_price": round(total * 0.8, 2),
            "source": "CORE_RULE_ESTIMATE",
            "notes": "Lean option based on current project facts",
        },
        "MID_RANGE": {
            "unit_price": round(total, 2),
            "total_price": round(total, 2),
            "source": "CORE_RULE_ESTIMATE",
            "notes": "Balanced option based on current project facts",
        },
        "PREMIUM": {
            "unit_price": round(total * 1.35, 2),
            "total_price": round(total * 1.35, 2),
            "source": "CORE_RULE_ESTIMATE",
            "notes": "Premium option based on current project facts",
        },
    }


async def _run_core_project_analysis(db: DB, project: BuyerProject, user: CurrentUser) -> ProjectAIRun:
    started_at = datetime.now(timezone.utc)
    run = ProjectAIRun(
        project_id=project.id,
        provider="AINERWISE_CORE",
        model="project-forge-rule-analyzer-v1",
        prompt_version="compat-v1",
        status="RUNNING",
        started_at=started_at,
        input_snapshot_json={
            "title": project.title,
            "project_type": project.project_type,
            "description": project.description,
            "budget_min": project.budget_min,
            "budget_max": project.budget_max,
            "currency": project.currency,
        },
    )
    db.add(run)
    await db.flush()

    existing_items = await list_buyer_project_line_items(db, project.id)
    if not existing_items:
        base_total = _project_budget_base(project)
        for template in _project_line_item_templates(project):
            total = float(base_total) * float(template["share"])
            db.add(
                ProjectLineItem(
                    project_id=project.id,
                    ai_run_id=run.id,
                    name=template["name"],
                    description=f"Generated from project facts for {project.title}.",
                    qty=1,
                    unit=template["unit"],
                    quality_tier=project.quality_preference
                    if project.quality_preference in {"BUDGET", "MID_RANGE", "PREMIUM"}
                    else "MID_RANGE",
                    estimated_unit_price=round(total, 2),
                    estimated_total_price=round(total, 2),
                    currency=project.currency or "PHP",
                    confidence=0.72,
                    sourcing_notes="Review quantities and specifications before publishing RFQ.",
                    price_tiers_json=_tier_prices(total),
                    category_hint=template["category_hint"],
                    source="AI",
                    status="DRAFT",
                )
            )
    project.status = "AI_ANALYZED"
    base_total = _project_budget_base(project)
    project.ai_summary = (
        "AinerWise Core analyzed the project facts and generated a draft procurement "
        "package. Confirm quantities, missing site details, and preferred quality tier before sourcing."
    )
    project.missing_questions_json = [
        {
            "key": "delivery_site",
            "question": "Confirm the exact delivery or installation site and access restrictions.",
            "importance": "HIGH",
        },
        {
            "key": "preferred_brands",
            "question": "List any preferred or prohibited brands before RFQ publishing.",
            "importance": "MEDIUM",
        },
    ]
    project.assumptions_json = [
        "Budget is treated as an estimate until supplier quotes are received.",
        "Line items are grouped for procurement and can be edited before publishing.",
    ]
    project.risk_notes_json = [
        "AI estimate should not be used as a final commercial offer.",
        "Site conditions, delivery constraints, taxes and warranties must be reviewed before award.",
    ]
    project.acceptance_criteria_json = [
        "Buyer confirms line items and quantities.",
        "Supplier quotations include warranty, tax mode and delivery terms.",
    ]
    project.estimated_budget_json = {
        "currency": project.currency or "PHP",
        "min": int(base_total * 0.8),
        "max": int(base_total * 1.35),
        "confidence": 0.72,
        "by_tier": {
            "BUDGET": {"min": int(base_total * 0.72), "max": int(base_total * 0.9)},
            "MID_RANGE": {"min": int(base_total * 0.9), "max": int(base_total * 1.1)},
            "PREMIUM": {"min": int(base_total * 1.15), "max": int(base_total * 1.35)},
        },
    }
    run.status = "SUCCESS"
    run.finished_at = datetime.now(timezone.utc)
    run.structured_output_json = {
        "line_item_count": len(await list_buyer_project_line_items(db, project.id)),
        "confidence": 0.72,
        "requires_human_review": True,
    }
    run.token_usage_json = {"input_tokens": 0, "output_tokens": 0, "mode": "rule_based_core"}
    await db.flush()
    return run


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


@router.get("/companies/me")
async def legacy_get_my_company(db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=404, detail="Company not found")
    company = await db.get(Company, user.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return _company_as_legacy(company)


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


@router.get("/wallets/me")
async def legacy_wallets_me(
    db: DB,
    user: CurrentUser,
    currency: str = Query(default="PHP"),
):
    normalized_currency = (currency or "PHP").upper()
    await get_or_create_wallet(db, user.id, normalized_currency)
    await db.commit()
    wallets = await wallet_balance(db, user.id)
    wallets.sort(key=lambda wallet: (wallet.currency != normalized_currency, wallet.currency))
    items = [WalletRead.model_validate(wallet).model_dump() for wallet in wallets]
    return {"wallets": items, "items": items, "total": len(items)}


@router.get("/wallets/transactions")
async def legacy_wallet_transactions(
    db: DB,
    user: CurrentUser,
    currency: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    normalized_currency = currency.upper() if currency else None
    wallets = await wallet_balance(db, user.id)
    txs = []
    for wallet in wallets:
        if normalized_currency and wallet.currency != normalized_currency:
            continue
        txs.extend(await list_wallet_transactions(db, wallet.id, limit=limit))
    txs.sort(key=lambda tx: tx.created_at.isoformat() if tx.created_at else "", reverse=True)
    return [WalletTransactionRead.model_validate(tx).model_dump() for tx in txs[:limit]]


@router.get("/wallets/deposits")
async def legacy_wallet_deposits(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    items = await list_deposits(db, user_id=user.id, status=status, limit=limit)
    data = [WalletDepositRead.model_validate(deposit).model_dump() for deposit in items]
    return {"items": data, "total": len(data)}


@router.post("/wallets/deposits", status_code=201)
async def legacy_create_wallet_deposit(
    data: LegacyWalletDepositCreate,
    db: DB,
    user: CurrentUser,
):
    if data.amount_minor <= 0:
        raise HTTPException(status_code=422, detail="amount_minor must be greater than 0")
    currency = (data.currency or "PHP").upper()
    wallet = await get_or_create_wallet(db, user.id, currency)
    fields = data.model_dump()
    fields["currency"] = currency
    fields["network"] = (fields.get("network") or "LOCAL_BANK").upper()
    fields["provider"] = fields.get("provider") or "MANUAL_BANK"
    fields["payment_method"] = fields.get("payment_method") or "PHP_MANUAL_BANK"
    fields["deposit_address"] = _wallet_instruction_address(data, user)
    deposit = await create_deposit(
        db,
        wallet_id=wallet.id,
        owner_user_id=user.id,
        **fields,
    )
    await db.commit()
    await db.refresh(deposit)
    return WalletDepositRead.model_validate(deposit)


@router.post("/wallets/deposits/{deposit_id}/submit-tx")
async def legacy_submit_wallet_deposit_tx(
    deposit_id: uuid.UUID,
    data: LegacyWalletSubmitTx,
    db: DB,
    user: CurrentUser,
):
    tx_hash = (data.tx_hash or "").strip()
    if not tx_hash:
        raise HTTPException(status_code=422, detail="tx_hash is required")
    deposit = await db.get(WalletDeposit, deposit_id)
    if deposit is None or deposit.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Deposit not found")
    if deposit.status not in ("PENDING_TX", "SUBMITTED", "UNDER_REVIEW"):
        raise HTTPException(status_code=409, detail=f"Cannot submit tx in status {deposit.status}")
    deposit.tx_hash = tx_hash
    deposit.submitter_note = data.submitter_note
    deposit.status = "SUBMITTED"
    await db.commit()
    await db.refresh(deposit)
    return WalletDepositRead.model_validate(deposit)


async def _owned_buyer_project(db: DB, user: CurrentUser, project_id: uuid.UUID) -> BuyerProject:
    try:
        return await get_buyer_project(db, project_id, user.id)
    except BuyerProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/buyer/projects")
async def legacy_list_buyer_projects(db: DB, user: CurrentUser):
    rows = await list_buyer_projects(db, user.id, limit=100)
    return [await _buyer_project_as_legacy(db, row) for row in rows]


@router.post("/buyer/projects", status_code=201)
async def legacy_create_buyer_project(data: ProjectCreate, db: DB, user: CurrentUser):
    row = await create_buyer_project(db, buyer_id=user.id, **data.model_dump())
    await db.commit()
    await db.refresh(row)
    return await _buyer_project_as_legacy(db, row, detail=True)


@router.get("/buyer/projects/{project_id}")
async def legacy_get_buyer_project(project_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await _owned_buyer_project(db, user, project_id)
    return await _buyer_project_as_legacy(db, row, detail=True)


@router.patch("/buyer/projects/{project_id}")
async def legacy_update_buyer_project(
    project_id: uuid.UUID, data: ProjectUpdate, db: DB, user: CurrentUser
):
    try:
        row = await update_buyer_project(
            db, project_id, user.id, **data.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(row)
        return await _buyer_project_as_legacy(db, row, detail=True)
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/buyer/projects/{project_id}/messages")
async def legacy_buyer_project_messages(project_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_buyer_project(db, user, project_id)
    rows = await list_buyer_project_messages(db, project_id)
    return [_with_jsonb_aliases(_row_dict(row)) for row in rows]


@router.post("/buyer/projects/{project_id}/messages", status_code=201)
async def legacy_create_buyer_project_message(
    project_id: uuid.UUID,
    data: LegacyProjectMessageCreate,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    if data.file_ids:
        files = await _project_files(db, project.id)
        owned = {row.id for row in files}
        missing = [str(file_id) for file_id in data.file_ids if file_id not in owned]
        if missing:
            raise HTTPException(status_code=400, detail=f"Files do not belong to project: {', '.join(missing)}")
    user_msg = await add_buyer_project_message(
        db,
        project_id=project.id,
        role="USER",
        content=data.content,
        workflow_node=data.workflow_node or "intake_chat",
    )
    metrics = await get_buyer_project_metrics(db, project)
    missing = metrics.get("missing_required") or []
    prompt = (
        f"Captured. Next, please provide: {missing[0]['label']}."
        if missing
        else "Captured. You can run analysis now, or add more details such as delivery site, preferred brands, timeline, and warranty expectations."
    )
    assistant_msg = await add_buyer_project_message(
        db,
        project_id=project.id,
        role="ASSISTANT",
        content=prompt,
        workflow_node="gap_question" if missing else "intake_chat",
    )
    if project.status == "DRAFT":
        project.status = "COLLECTING_INFO"
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)
    return [_with_jsonb_aliases(_row_dict(user_msg)), _with_jsonb_aliases(_row_dict(assistant_msg))]


@router.get("/buyer/projects/{project_id}/metrics")
async def legacy_buyer_project_metrics(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    return _metric_payload_as_legacy(await get_buyer_project_metrics(db, project))


@router.patch("/buyer/projects/{project_id}/metrics")
async def legacy_patch_buyer_project_metrics(
    project_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    from app.modules.buyer_project.service import update_metrics as update_buyer_project_metrics

    metrics = data.get("metrics") if isinstance(data, dict) else None
    if not isinstance(metrics, list):
        raise HTTPException(status_code=422, detail="metrics must be a list")
    result = await update_buyer_project_metrics(db, project, metrics)
    await db.commit()
    return _metric_payload_as_legacy(result)


@router.post("/buyer/projects/{project_id}/files", status_code=201)
async def legacy_upload_buyer_project_file(
    project_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    project = await _owned_buyer_project(db, user, project_id)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 20MB")
    object_name = new_user_upload_key(user.id, file.filename or "project-file")
    client = get_minio_client()
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
    client.put_object(
        BUCKET_NAME,
        object_name,
        io.BytesIO(content),
        length=len(content),
        content_type=file.content_type or "application/octet-stream",
    )
    row = ProjectFile(
        project_id=project.id,
        url=f"minio://{BUCKET_NAME}/{object_name}",
        file_name=file.filename or "project-file",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        extracted_text=content[:8192].decode("utf-8", errors="ignore") if (file.content_type or "").startswith("text/") else None,
        status="EXTRACTED" if (file.content_type or "").startswith("text/") else "UPLOADED",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _file_as_legacy(row)


@router.delete("/buyer/projects/{project_id}/files/{file_id}", status_code=204)
async def legacy_delete_buyer_project_file(
    project_id: uuid.UUID, file_id: uuid.UUID, db: DB, user: CurrentUser
):
    project = await _owned_buyer_project(db, user, project_id)
    row = await db.get(ProjectFile, file_id)
    if row is None or row.project_id != project.id:
        raise HTTPException(status_code=404, detail="File not found")
    await db.delete(row)
    await db.commit()
    return None


@router.post("/buyer/projects/{project_id}/ai/analyze", status_code=202)
async def legacy_start_buyer_project_analysis(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    run = await _run_core_project_analysis(db, project, user)
    await db.commit()
    await db.refresh(run)
    return _ai_run_as_legacy(run)


@router.get("/buyer/projects/{project_id}/ai-runs/{run_id}")
async def legacy_get_buyer_project_ai_run(
    project_id: uuid.UUID, run_id: uuid.UUID, db: DB, user: CurrentUser
):
    project = await _owned_buyer_project(db, user, project_id)
    run = await db.get(ProjectAIRun, run_id)
    if run is None or run.project_id != project.id:
        raise HTTPException(status_code=404, detail="AI run not found")
    return _ai_run_as_legacy(run)


@router.post("/buyer/projects/{project_id}/ai-runs/{run_id}/retry", status_code=202)
async def legacy_retry_buyer_project_ai_run(
    project_id: uuid.UUID, run_id: uuid.UUID, db: DB, user: CurrentUser
):
    project = await _owned_buyer_project(db, user, project_id)
    old_run = await db.get(ProjectAIRun, run_id)
    if old_run is None or old_run.project_id != project.id:
        raise HTTPException(status_code=404, detail="AI run not found")
    run = await _run_core_project_analysis(db, project, user)
    await db.commit()
    await db.refresh(run)
    return _ai_run_as_legacy(run)


@router.get("/buyer/projects/{project_id}/comparison")
async def legacy_buyer_project_comparison(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    items = []
    for item in await list_buyer_project_line_items(db, project.id):
        legacy_item = _line_item_as_legacy(item)
        items.append(
            {
                "line_item_id": item.id,
                "line_item": legacy_item,
                "matched_suppliers": 0,
                "price_snapshot": {
                    "samples": [],
                    "price_tiers_jsonb": legacy_item.get("price_tiers_jsonb") or {},
                    "source_summary": "AinerWise Core estimate. Publish RFQ to collect supplier quotes.",
                },
                "issues": [] if item.confidence and item.confidence >= 0.6 else ["Low confidence; review before publishing"],
            }
        )
    return {"project_id": project.id, "items": items}


@router.post("/buyer/projects/{project_id}/price-estimate")
async def legacy_buyer_project_price_estimate(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    rows = await estimate_buyer_project_prices(db, project)
    await db.commit()
    return {"project_id": project.id, "items": [_with_jsonb_aliases(_row_dict(row)) for row in rows]}


@router.get("/buyer/projects/{project_id}/report")
async def legacy_get_buyer_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    await db.commit()
    return _report_payload_as_legacy(result)


@router.get("/buyer/projects/{project_id}/report/versions")
async def legacy_buyer_project_report_versions(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    versions = await list_buyer_project_report_versions(db, result["id"])
    await db.commit()
    return _with_jsonb_aliases(versions)


@router.post("/buyer/projects/{project_id}/report/recalculate")
async def legacy_recalculate_buyer_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    report = await recalculate_buyer_project_report(db, project, actor_id=user.id)
    result = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(result)


@router.post("/buyer/projects/{project_id}/report/freeze")
async def legacy_freeze_buyer_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    report = await freeze_buyer_project_report(db, project, actor_id=user.id)
    result = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(result)


@router.patch("/buyer/projects/{project_id}/report/cells")
async def legacy_patch_buyer_project_report_cells(
    project_id: uuid.UUID,
    data: LegacyProjectReportCellsPatch,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    report = None
    for change in data.changes:
        report = await update_buyer_project_report_row(
            db,
            project,
            change.row_id,
            actor_id=user.id,
            fields={change.field: change.value},
        )
    if report is None:
        raise HTTPException(status_code=422, detail="No report cell changes provided")
    result = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(result)


@router.post("/buyer/projects/{project_id}/report/columns", status_code=201)
async def legacy_add_buyer_project_report_column(
    project_id: uuid.UUID,
    data: LegacyProjectReportColumnCreate,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    report = await db.get(ProjectReport, result["id"])
    if report is None or report.current_version_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    db.add(
        ProjectReportColumn(
            report_version_id=report.current_version_id,
            key=data.key,
            label=data.label,
            data_type=data.data_type,
            sort_order=1000,
            editable=data.editable,
            system=False,
        )
    )
    await db.flush()
    detail = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(detail)


@router.post("/buyer/projects/{project_id}/report/rows", status_code=201)
async def legacy_add_buyer_project_report_row(
    project_id: uuid.UUID,
    data: LegacyProjectReportRowCreate,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    report = await db.get(ProjectReport, result["id"])
    if report is None or report.current_version_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    row_count = len(result.get("rows") or [])
    db.add(
        ProjectReportRow(
            report_version_id=report.current_version_id,
            project_id=project.id,
            name=data.name,
            description=data.description,
            qty=data.qty,
            unit=data.unit,
            currency=data.currency,
            quality_tier=data.quality_tier,
            selected_tier=data.selected_tier,
            notes=data.notes,
            price_tiers_json=_tier_prices(0),
            sort_order=row_count + 1,
        )
    )
    await db.flush()
    detail = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(detail)


@router.post("/buyer/projects/{project_id}/report/versions/{version_id}/restore")
async def legacy_restore_buyer_project_report_version(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    report = await db.get(ProjectReport, result["id"])
    version = await db.get(ProjectReportVersion, version_id)
    if report is None or version is None or version.report_id != report.id:
        raise HTTPException(status_code=404, detail="Report version not found")
    report.current_version_id = version.id
    db.add(
        ProjectReportChangeLog(
            project_id=project.id,
            report_id=report.id,
            version_id=version.id,
            actor_id=user.id,
            change_type="RESTORE_VERSION",
            status="APPLIED",
            after_json={"version_id": str(version.id)},
        )
    )
    detail = await buyer_project_report_detail(db, report)
    await db.commit()
    return _report_payload_as_legacy(detail)


@router.post("/buyer/projects/{project_id}/report/chat", status_code=201)
async def legacy_create_buyer_project_report_patch(
    project_id: uuid.UUID,
    data: LegacyProjectReportChatRequest,
    db: DB,
    user: CurrentUser,
):
    project = await _owned_buyer_project(db, user, project_id)
    result = await get_buyer_project_report(db, project, actor_id=user.id)
    row = ProjectReportChangeLog(
        project_id=project.id,
        report_id=result["id"],
        version_id=(result.get("current_version") or {}).get("id"),
        actor_id=user.id,
        change_type="CHAT_PATCH_REQUEST",
        status="PENDING",
        user_message=data.message,
        patch_json={"requires_review": True, "message": data.message},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _with_jsonb_aliases(_row_dict(row))


@router.post("/buyer/projects/{project_id}/report/patches/{patch_id}/apply")
async def legacy_apply_buyer_project_report_patch(
    project_id: uuid.UUID, patch_id: uuid.UUID, db: DB, user: CurrentUser
):
    project = await _owned_buyer_project(db, user, project_id)
    row = await db.get(ProjectReportChangeLog, patch_id)
    if row is None or row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Report patch not found")
    row.status = "APPLIED"
    row.applied_at = datetime.now(timezone.utc)
    row.after_json = {"applied_without_auto_mutation": True}
    await db.commit()
    await db.refresh(row)
    return _with_jsonb_aliases(_row_dict(row))


@router.post("/buyer/projects/{project_id}/report/patches/{patch_id}/reject")
async def legacy_reject_buyer_project_report_patch(
    project_id: uuid.UUID, patch_id: uuid.UUID, db: DB, user: CurrentUser
):
    project = await _owned_buyer_project(db, user, project_id)
    row = await db.get(ProjectReportChangeLog, patch_id)
    if row is None or row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Report patch not found")
    row.status = "REJECTED"
    await db.commit()
    await db.refresh(row)
    return _with_jsonb_aliases(_row_dict(row))


@router.patch("/buyer/projects/{project_id}/line-items/{item_id}")
async def legacy_patch_buyer_project_line_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    await _owned_buyer_project(db, user, project_id)
    try:
        if "intent_id" in data and "procurement_request_id" not in data:
            data["procurement_request_id"] = data["intent_id"]
        if "price_tiers_jsonb" in data and "price_tiers_json" not in data:
            data["price_tiers_json"] = data["price_tiers_jsonb"]
        if "specs_jsonb" in data and "specs_json" not in data:
            data["specs_json"] = data["specs_jsonb"]
        row = await update_buyer_project_line_item(db, item_id, project_id, **data)
        await db.commit()
        await db.refresh(row)
        return _line_item_as_legacy(row)
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.delete("/buyer/projects/{project_id}/line-items/{item_id}", status_code=204)
async def legacy_delete_buyer_project_line_item(
    project_id: uuid.UUID, item_id: uuid.UUID, db: DB, user: CurrentUser
):
    await _owned_buyer_project(db, user, project_id)
    try:
        await update_buyer_project_line_item(db, item_id, project_id, status="REMOVED")
        await db.commit()
        return None
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/buyer/projects/{project_id}/freeze-form")
async def legacy_freeze_buyer_project_form(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    if project.status in {"DRAFT", "COLLECTING_INFO", "AI_ANALYZED"}:
        project.status = "READY_FOR_SOURCING"
    await db.commit()
    await db.refresh(project)
    return await _buyer_project_as_legacy(db, project, detail=True)


@router.post("/buyer/projects/{project_id}/publish")
async def legacy_publish_buyer_project(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_buyer_project(db, user, project_id)
    created_ids: list[uuid.UUID] = []
    skipped = 0
    for item in await list_buyer_project_line_items(db, project.id):
        if item.status != "CONFIRMED" or item.include_in_estimate is False:
            skipped += 1
            continue
        if item.procurement_request_id:
            skipped += 1
            continue
        workspace_id = await resolve_commerce_workspace(db, user=user, requested_workspace_id=None)
        req = await create_procurement_request(
            db,
            workspace_id=workspace_id,
            buyer_user_id=user.id,
            buyer_company_id=user.company_id,
            portal_key="cebu",
            title=item.name,
            description=item.description or project.description,
            category_schema_id=item.category_id,
            requirements_json={
                "qty": item.qty,
                "unit": item.unit,
                "currency": item.currency,
                "budget_max_minor": int(float(item.estimated_total_price or 0) * 100),
                "project_id": str(project.id),
                "project_line_item_id": str(item.id),
            },
            attrs_json={
                "source": "buyer_project",
                "quality_tier": item.quality_tier,
                "category_hint": item.category_hint,
            },
            status="draft",
        )
        item.procurement_request_id = req.id
        item.status = "SOURCING"
        created_ids.append(req.id)
    if created_ids:
        project.status = "SOURCING"
    await db.commit()
    await db.refresh(project)
    return {
        "project_id": project.id,
        "published_count": len(created_ids),
        "intents_created": created_ids,
        "skipped_count": skipped,
    }


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


@router.get("/supplier/catalog/items")
async def legacy_supplier_catalog_items(
    db: DB,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    status: str | None = None,
    market_mode: str | None = None,
    category_id: uuid.UUID | None = None,
):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    stmt = select(SupplierListing).where(SupplierListing.company_id == company_id)
    if keyword:
        stmt = stmt.where(SupplierListing.title.ilike(f"%{keyword.strip()}%"))
    if category_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_id)
    if status:
        stmt = stmt.where(SupplierListing.status == _catalog_status_to_core(status))
    else:
        stmt = stmt.where(SupplierListing.status != "archived")
    rows = list((await db.execute(stmt.order_by(SupplierListing.created_at.desc()))).scalars())
    if market_mode:
        rows = [
            row
            for row in rows
            if (row.attributes_json or {}).get("market_mode", "B2B").upper() == market_mode.upper()
        ]
    total = len(rows)
    offset = (page - 1) * page_size
    page_rows = rows[offset : offset + page_size]
    company = await db.get(Company, company_id)
    return {
        "items": [_catalog_item_as_legacy(row, company_name=company.name if company else None) for row in page_rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": offset + page_size < total,
    }


@router.post("/supplier/catalog/items", status_code=201)
async def legacy_create_supplier_catalog_item(data: dict, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=data.get("company_id"))
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    title = str(data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="title is required")
    category_id = _uuid_or_none(data.get("category_schema_id") or data.get("category_id"))
    region_id = _uuid_or_none(data.get("region_id"))
    attrs = _catalog_attrs_from_payload(data)
    row = await create_listing(
        db,
        company_id=company_id,
        region_id=region_id,
        category_schema_id=category_id,
        title=title,
        attributes_json=attrs,
        price_minor=int(data.get("price_minor") or 0),
        currency=str(data.get("currency") or "PHP").upper(),
        status=_catalog_status_to_core(data.get("status")) or "active",
        legacy_catalog_item_id=data.get("legacy_catalog_item_id"),
    )
    await db.commit()
    await db.refresh(row)
    company = await db.get(Company, company_id)
    return _catalog_item_as_legacy(row, company_name=company.name if company else None)


@router.get("/supplier/catalog/items/{item_id}")
async def legacy_get_supplier_catalog_item(item_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await db.get(SupplierListing, item_id)
    if row is None or row.company_id != company_id or row.status == "archived":
        raise HTTPException(status_code=404, detail="Catalog item not found")
    company = await db.get(Company, company_id)
    return _catalog_item_as_legacy(row, company_name=company.name if company else None)


@router.patch("/supplier/catalog/items/{item_id}")
async def legacy_update_supplier_catalog_item(item_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=data.get("company_id"))
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await db.get(SupplierListing, item_id)
    if row is None or row.company_id != company_id or row.status == "archived":
        raise HTTPException(status_code=404, detail="Catalog item not found")
    if "title" in data and data.get("title"):
        row.title = str(data["title"]).strip()
    if "category_id" in data or "category_schema_id" in data:
        row.category_schema_id = _uuid_or_none(data.get("category_schema_id") or data.get("category_id"))
    if "region_id" in data:
        row.region_id = _uuid_or_none(data.get("region_id"))
    if "price_minor" in data:
        row.price_minor = int(data.get("price_minor") or 0)
    if "currency" in data and data.get("currency"):
        row.currency = str(data["currency"]).upper()
    if "status" in data:
        row.status = _catalog_status_to_core(data.get("status")) or row.status
    row.attributes_json = _catalog_attrs_from_payload(data, row.attributes_json)
    await db.commit()
    await db.refresh(row)
    company = await db.get(Company, company_id)
    return _catalog_item_as_legacy(row, company_name=company.name if company else None)


@router.delete("/supplier/catalog/items/{item_id}", status_code=204)
async def legacy_delete_supplier_catalog_item(item_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await db.get(SupplierListing, item_id)
    if row is None or row.company_id != company_id or row.status == "archived":
        raise HTTPException(status_code=404, detail="Catalog item not found")
    row.status = "archived"
    await db.commit()
    return None


async def _owned_ad_campaign(db: DB, user: User, campaign_id: uuid.UUID) -> AdCampaign:
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await db.get(AdCampaign, campaign_id)
    if row is None or row.company_id != company_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return row


@router.get("/merchant/ad-campaigns")
async def legacy_merchant_ad_campaigns(db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    rows = await list_ad_campaigns(db, company_id=company_id)
    return [_ad_campaign_as_legacy(row) for row in rows]


@router.post("/merchant/ad-campaigns", status_code=201)
async def legacy_create_merchant_ad_campaign(data: dict, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    listing_id = _uuid_or_none(data.get("listing_id") or data.get("catalog_item_id"))
    if listing_id:
        listing = await db.get(SupplierListing, listing_id)
        if listing is None or listing.company_id != company_id or listing.status == "archived":
            raise HTTPException(status_code=403, detail="Cannot advertise another supplier catalog item")
    title = str(data.get("title") or data.get("name") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="title is required")
    campaign = await create_ad_campaign(
        db,
        company_id=company_id,
        listing_id=listing_id,
        title=title,
        placement=data.get("placement") or "FEED_TOP",
        target_category_id=_uuid_or_none(data.get("target_category_id")),
        target_keywords=data.get("target_keywords"),
        target_countries=data.get("target_countries"),
        budget_minor=int(data.get("budget_minor") or 0),
        bid_per_click_minor=int(data.get("bid_per_click_minor") or 0),
        currency=str(data.get("currency") or "USD").upper(),
        starts_at=data.get("starts_at"),
        ends_at=data.get("ends_at"),
    )
    await db.commit()
    await db.refresh(campaign)
    return _ad_campaign_as_legacy(campaign)


@router.post("/merchant/ad-campaigns/{campaign_id}/submit")
async def legacy_submit_merchant_ad_campaign(campaign_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await _owned_ad_campaign(db, user, campaign_id)
    if row.status not in ("DRAFT", "PAUSED", "REJECTED"):
        raise HTTPException(status_code=409, detail=f"Cannot submit campaign in {row.status}")
    try:
        updated = await update_ad_campaign_status(
            db,
            campaign_id,
            new_status="PENDING_REVIEW",
            company_id=row.company_id,
        )
        await db.commit()
        await db.refresh(updated)
        return _ad_campaign_as_legacy(updated)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/merchant/ad-campaigns/{campaign_id}/pause")
async def legacy_pause_merchant_ad_campaign(campaign_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await _owned_ad_campaign(db, user, campaign_id)
    if row.status not in ("ACTIVE", "PENDING_REVIEW", "DRAFT"):
        raise HTTPException(status_code=409, detail=f"Cannot pause campaign in {row.status}")
    try:
        updated = await update_ad_campaign_status(
            db,
            campaign_id,
            new_status="PAUSED",
            company_id=row.company_id,
        )
        await db.commit()
        await db.refresh(updated)
        return _ad_campaign_as_legacy(updated)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/admin/ad-campaigns")
async def legacy_admin_ad_campaigns(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    rows = await list_ad_campaigns(db, status=_ad_status_to_core(status) if status else None)
    return [_ad_campaign_as_legacy(row) for row in rows]


@router.post("/admin/ad-campaigns/{campaign_id}/approve")
async def legacy_admin_approve_ad_campaign(campaign_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    try:
        row = await update_ad_campaign_status(db, campaign_id, new_status="ACTIVE")
        await db.commit()
        await db.refresh(row)
        return _ad_campaign_as_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/admin/ad-campaigns/{campaign_id}/reject")
async def legacy_admin_reject_ad_campaign(campaign_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    reason = data.get("reason") or data.get("rejection_reason") or "Rejected by admin"
    try:
        row = await update_ad_campaign_status(
            db,
            campaign_id,
            new_status="REJECTED",
            rejection_reason=reason,
        )
        await db.commit()
        await db.refresh(row)
        return _ad_campaign_as_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/admin/ad-campaigns/{campaign_id}/pause")
async def legacy_admin_pause_ad_campaign(campaign_id: uuid.UUID, db: DB, user: CurrentUser, data: dict | None = None):
    _require_legacy_admin(user)
    try:
        row = await update_ad_campaign_status(db, campaign_id, new_status="PAUSED")
        await db.commit()
        await db.refresh(row)
        return _ad_campaign_as_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


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
    row, _party = await _require_legacy_order_party(db, user, order_id)
    return await _order_as_legacy(db, row)


@router.post("/orders/{order_id}/pay-from-wallet")
async def legacy_pay_order_from_wallet(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"buyer"})
    if row.status in ("completed", "cancelled", "disputed"):
        raise HTTPException(status_code=409, detail="Order cannot be paid in current status")
    if row.total_minor <= 0:
        raise HTTPException(status_code=409, detail="Order amount must be greater than zero")

    try:
        existing = await _order_escrow(db, row)
        if existing is not None:
            if existing.status in ("AUTH_HELD", "CAPTURED", "RELEASED"):
                return await _order_as_legacy(db, row)
            raise HTTPException(status_code=409, detail=f"Escrow is already in {existing.status}")

        wallet = await get_or_create_wallet(db, user.id, row.currency)
        if wallet.available_balance_minor < row.total_minor:
            raise HTTPException(status_code=409, detail="Insufficient wallet balance")
        wallet.available_balance_minor -= row.total_minor

        escrow = await create_escrow(
            db,
            order_id=row.id,
            auth_amount_minor=row.total_minor,
            currency=row.currency,
            provider="AINERWISE_WALLET",
        )
        escrow.status = "AUTH_HELD"
        await db.flush()
        escrow = await capture_escrow(db, escrow.id, row.total_minor)
        row.status = "confirmed"
        db.add(
            _wallet_transaction(
                wallet_id=wallet.id,
                owner_user_id=user.id,
                tx_type="ESCROW_CAPTURED_FROM_WALLET",
                amount_delta_minor=-row.total_minor,
                currency=row.currency,
                available_after=wallet.available_balance_minor,
                locked_after=wallet.locked_balance_minor,
                reference_type="escrow_transaction",
                reference_id=escrow.id,
                note=f"Wallet payment captured for order {row.id}",
            )
        )
        await db.commit()
        await db.refresh(row)
        return await _order_as_legacy(db, row)
    except HTTPException:
        await db.rollback()
        raise
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/accept")
async def legacy_accept_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"admin", "buyer"})
    try:
        updated = await complete_order(db, order_id=order_id)
        escrow = await _order_escrow(db, updated)
        if escrow is not None and escrow.status in ("AUTH_HELD", "CAPTURED"):
            escrow = await release_escrow(db, escrow.id)
            await _credit_supplier_wallet_from_escrow(db, order=updated, escrow=escrow)
        await db.commit()
        await db.refresh(updated)
        return await _order_as_legacy(db, updated)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/orders/{order_id}/delivery")
async def legacy_order_deliveries(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id)
    deliveries = await list_deliveries(db, row)
    return [_delivery_as_legacy(delivery) for delivery in deliveries]


@router.post("/orders/{order_id}/delivery", status_code=201)
async def legacy_create_delivery(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"admin", "supplier"})
    payload = OrderDeliveryCreate(
        carrier=data.get("carrier"),
        tracking_number=data.get("tracking_number"),
        ship_from_json=data.get("ship_from_json"),
        ship_to_json=data.get("ship_to_json"),
        estimated_at=data.get("estimated_at"),
    )
    proof_json = None
    if data.get("proofs") or data.get("notes"):
        proof_json = {"proofs": data.get("proofs") or [], "notes": data.get("notes")}
    try:
        deliveries = await list_deliveries(db, row)
        if deliveries:
            delivery = deliveries[-1]
            update_values = payload.model_dump()
            for key, value in update_values.items():
                if value is not None:
                    setattr(delivery, key, value)
            if proof_json:
                delivery.proof_json = proof_json
            await db.flush()
        else:
            delivery = await create_delivery(db, order_id, **payload.model_dump())
            if proof_json:
                delivery.proof_json = proof_json
                await db.flush()
        delivery = await _advance_delivery_to_legacy_status(
            db,
            delivery,
            data.get("status"),
            proof_json=proof_json,
        )
        await db.commit()
        await db.refresh(delivery)
        return _delivery_as_legacy(delivery, actor_id=user.id)
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


@router.post("/orders/{order_id}/reviews/seller", status_code=201)
async def legacy_review_seller(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"admin", "buyer"})
    rating = _rating_average(
        data.get("overall_rating"),
        data.get("product_quality_rating"),
        data.get("logistics_rating"),
        data.get("communication_rating"),
    )
    try:
        review = await submit_transaction_review(
            db,
            order_id=order_id,
            user=user,
            rating=rating,
            comment=data.get("comment"),
        )
        await db.refresh(review)
        delivery_json = dict(row.delivery_json or {})
        reviews = dict(delivery_json.get("seller_review_details") or {})
        reviews[str(review.id)] = {
            "id": str(review.id),
            "reviewer_id": str(user.id),
            "transaction_channel": data.get("transaction_channel") or "ONLINE",
            "overall_rating": rating,
            "product_quality_rating": data.get("product_quality_rating"),
            "logistics_rating": data.get("logistics_rating"),
            "communication_rating": data.get("communication_rating"),
            "comment": data.get("comment"),
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
        delivery_json["seller_review_details"] = reviews
        row.delivery_json = delivery_json
        await db.commit()
        await db.refresh(review)
        return {
            "id": review.id,
            "order_id": review.commerce_order_id,
            "reviewer_id": review.reviewer_user_id,
            "supplier_company_id": review.supplier_company_id,
            "overall_rating": review.rating,
            "product_quality_rating": data.get("product_quality_rating"),
            "logistics_rating": data.get("logistics_rating"),
            "communication_rating": data.get("communication_rating"),
            "transaction_channel": data.get("transaction_channel") or "ONLINE",
            "comment": review.comment,
            "status": review.status,
            "created_at": review.created_at,
        }
    except CommerceTrustError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/reviews/buyer", status_code=201)
async def legacy_review_buyer(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"admin", "supplier"})
    if row.status != "completed":
        raise HTTPException(status_code=409, detail="Order must be completed before review")
    delivery_json = dict(row.delivery_json or {})
    reviews = dict(delivery_json.get("buyer_review_details") or {})
    for item in reviews.values():
        if item.get("reviewer_id") == str(user.id):
            raise HTTPException(status_code=409, detail="review already submitted")
    review_id = str(uuid.uuid4())
    rating = _rating_average(data.get("buyer_rating"), data.get("communication_rating"))
    review = {
        "id": review_id,
        "order_id": str(order_id),
        "reviewer_id": str(user.id),
        "buyer_company_id": str(row.buyer_company_id) if row.buyer_company_id else None,
        "transaction_channel": data.get("transaction_channel") or "ONLINE",
        "overall_rating": rating,
        "buyer_rating": data.get("buyer_rating"),
        "communication_rating": data.get("communication_rating"),
        "comment": data.get("comment"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reviews[review_id] = review
    delivery_json["buyer_review_details"] = reviews
    row.delivery_json = delivery_json
    await db.commit()
    return review


@router.get("/reviews/company/me")
async def legacy_my_company_reviews(db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=None)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    rows = list(
        (
            await db.execute(
                select(TransactionReview)
                .where(
                    TransactionReview.supplier_company_id == company_id,
                    TransactionReview.status == "published",
                )
                .order_by(TransactionReview.created_at.desc())
                .limit(100)
            )
        ).scalars()
    )
    items = []
    product_ratings: list[int] = []
    logistics_ratings: list[int] = []
    communication_ratings: list[int] = []
    online_reviews = 0
    offline_reviews = 0
    for review in rows:
        order = await db.get(CommerceOrder, review.commerce_order_id)
        details = {}
        if order is not None:
            details = (order.delivery_json or {}).get("seller_review_details", {}).get(str(review.id), {})
        channel = details.get("transaction_channel") or "ONLINE"
        if channel == "OFFLINE":
            offline_reviews += 1
        else:
            online_reviews += 1
        product = details.get("product_quality_rating")
        logistics = details.get("logistics_rating")
        communication = details.get("communication_rating")
        for value, bucket in (
            (product, product_ratings),
            (logistics, logistics_ratings),
            (communication, communication_ratings),
        ):
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            if 1 <= number <= 5:
                bucket.append(number)
        items.append(
            {
                "id": review.id,
                "order_id": review.commerce_order_id,
                "reviewer_id": review.reviewer_user_id,
                "overall_rating": review.rating,
                "product_quality_rating": product,
                "logistics_rating": logistics,
                "communication_rating": communication,
                "transaction_channel": channel,
                "comment": review.comment,
                "created_at": review.created_at,
            }
        )

    def avg(values: list[int]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    return {
        "total_reviews": len(items),
        "average_overall_rating": round(sum(item["overall_rating"] for item in items) / len(items), 2)
        if items
        else 0,
        "average_product_quality_rating": avg(product_ratings),
        "average_logistics_rating": avg(logistics_ratings),
        "average_communication_rating": avg(communication_ratings),
        "online_reviews": online_reviews,
        "offline_reviews": offline_reviews,
        "reviews": items,
    }


@router.get("/threads/order/{order_id}/messages")
async def legacy_order_thread_messages(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order, _party = await _require_legacy_order_party(db, user, order_id)
    try:
        thread = await get_or_create_thread_for_order(db, order)
        await db.commit()
        await db.refresh(thread)
    except CommerceMessagingError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None
    rows = await list_thread_messages(db, thread)
    return [_message_as_legacy(row) for row in rows]


@router.post("/threads/order/{order_id}/messages", status_code=201)
async def legacy_post_order_thread_message(order_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    order, _party = await _require_legacy_order_party(db, user, order_id)
    body = str(data.get("body") or data.get("message") or "").strip()
    if not body:
        raise HTTPException(status_code=422, detail="body is required")
    raw_attachments = data.get("attachments_json") or data.get("attachments")
    if isinstance(raw_attachments, dict):
        attachments_json = raw_attachments
    elif isinstance(raw_attachments, list):
        attachments_json = {"attachments": raw_attachments}
    else:
        attachments_json = None
    try:
        thread = await get_or_create_thread_for_order(db, order)
        message = await post_thread_message(
            db,
            thread_id=thread.id,
            user=user,
            body=body,
            attachments_json=attachments_json,
        )
        await db.commit()
        await db.refresh(message)
        return _message_as_legacy(message)
    except CommerceMessagingAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CommerceMessagingError as exc:
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

"""P3-06: Legacy Cebu API path aliases -> Core commerce services.

Frontends can point `NUXT_PUBLIC_API_BASE` at `/api/v1/cebu-compat` for a
drop-in migration window. New work should call `/api/v1/commerce/*` directly.
"""
import io
import secrets
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DB
from app.core.permissions import STAFF_ROLES
from app.core.security import hash_password, verify_password
from app.api.v1.endpoints.files import BUCKET_NAME, get_minio_client
from app.core.object_storage import new_user_upload_key
from app.models.admin_config import NotificationTemplate, PlatformSetting
from app.models.audit import AuditLog
from app.models.backup import BackupJob, BackupSchedule
from app.models.commerce import (
    CommerceMessage,
    CommerceOrder,
    CommerceThread,
    OrderDispute,
    OrderDelivery,
    ProcurementRequest,
    RiskFlag,
    SupplierListing,
    SupplierOffer,
    TransactionReview,
    TrustProfile,
    TrustScoreEvent,
    TradeCategorySchema,
)
from app.models.notification import (
    NotificationPreference,
    PortalNotification,
    apply_notification_preference_defaults,
)
from app.models.region import Region
from app.models.settings import IntegrationSetting
from app.models.user import Company, User
from app.modules.cebu_trade.models import (
    AdCampaign,
    Address,
    EscrowTransaction,
    OrderShipping,
    PaymentEvent,
    Payout,
    RegionPaymentConfig,
    SettlementEvent,
    ShippingRate,
    ShippingRoute,
    WalletDeposit,
    WalletTransaction,
)
from app.modules.cebu_trade.payment_policy import fallback_payment_policy, normalize_country_code
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
    refund_escrow,
    reject_deposit,
    release_escrow,
    update_ad_campaign_status,
    verify_deposit,
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
from app.modules.kyc.models import CompanyDocument, KYCAnalysisResult, VerificationReview
from app.modules.kyc.schemas import CompanyDocumentCreate, CompanyDocumentRead, VerificationReviewRead
from app.modules.kyc.service import (
    KYCError,
    decide_verification,
    list_documents as list_kyc_documents,
    list_verification_queue,
    submit_for_verification,
    upload_document as upload_kyc_document,
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
    resolve_dispute as resolve_commerce_dispute,
    submit_offer,
)
from app.services.commerce_trust import CommerceTrustError, get_or_create_trust_profile, submit_transaction_review
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
from app.services.audit import append_audit_event
from app.services.backup_service import create_backup_archive, next_run_at_for_schedule
from app.services.demo_mode import is_demo_mode_enabled, set_demo_mode_enabled
from app.services.integrations import get_config as get_integration_config
from app.services.integrations import upsert_config as upsert_integration_config
from app.services.portal_access import suspend_user_portal_access, sync_role_portal_access

router = APIRouter(prefix="/cebu-compat", tags=["cebu-legacy-compat"])


class LegacyTelegramUpdate(BaseModel):
    telegram_chat_id: str | None = None


class LegacyNotificationPreferencesUpdate(BaseModel):
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    viber_enabled: bool | None = None
    telegram_chat_id: str | None = None
    email: str | None = None
    whatsapp_number: str | None = None
    viber_number: str | None = None
    alerts_enabled: bool | None = None
    reports_enabled: bool | None = None
    maintenance_enabled: bool | None = None
    renewal_enabled: bool | None = None


class LegacyWalletDepositCreate(BaseModel):
    amount_minor: int
    currency: str = "EUR"
    network: str = "LOCAL_BANK"
    provider: str = "MANUAL_BANK"
    payment_method: str = "BANK_TRANSFER"
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
    currency: str = "EUR"
    quality_tier: str = "MID_RANGE"
    selected_tier: str = "MID_RANGE"
    notes: str | None = None


class LegacyProjectReportChatRequest(BaseModel):
    message: str


@router.get("/system-mode")
async def legacy_system_mode(db: DB):
    from app.api.v1.endpoints.localization import _localization_payload

    market_cfg = await get_integration_config(db, "market")
    localization = await _localization_payload(db)
    return {
        "demo_mode": await is_demo_mode_enabled(db),
        "registration_enabled": True,
        "app_name": "AinerWise Procurement",
        "intent_max_attachments": 10,
        "default_locale": localization.get("default_locale_prefix", "en"),
        "locales": localization.get("supported_locales", []),
        "regions": localization.get("supported_regions", []),
        "direct_payments_only": not market_cfg.get("wallet_payments_enabled", False),
    }


def _payment_region_config_as_legacy(row: RegionPaymentConfig | None, country: str) -> dict:
    normalized = normalize_country_code(country)
    fallback = fallback_payment_policy(normalized)
    if row is None:
        return {
            "country_code": normalized,
            **fallback,
            "is_active": True,
            "source": "fallback",
        }
    return {
        "id": row.id,
        "country_code": row.country_code,
        "country_name": row.country_name,
        "local_currency": row.local_currency,
        "local_currency_alias": fallback.get("local_currency_alias"),
        "default_settlement_currency": row.default_settlement_currency,
        "default_transaction_mode": row.default_transaction_mode,
        "enabled_currencies": row.enabled_currencies or [row.local_currency],
        "settlement_currencies": fallback.get("settlement_currencies") or row.enabled_currencies or [row.default_settlement_currency],
        "enabled_payment_methods": row.enabled_payment_methods or ["WALLET"],
        "cross_border_currencies": row.cross_border_currencies or [],
        "force_usd_bridge": row.force_usd_bridge,
        "allow_supplier_payout_currency": row.allow_supplier_payout_currency,
        "reference_rates": fallback.get("reference_rates", {}),
        "rate_source": fallback.get("rate_source", "REQUIRES_FX_QUOTE"),
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
            "expired": "EXPIRED",
            "closed": "CLOSED",
            "cancelled": "CANCELED",
        },
        "offer": {
            "draft": "DRAFT",
            "submitted": "SUBMITTED",
            "withdrawn": "WITHDRAWN",
            "awarded": "AWARDED",
            "expired": "EXPIRED",
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
    if value == "project_manager":
        return "OPS_MANAGER"
    if value == "sales_manager":
        return "SUPPORT_AGENT"
    if value == "marketing_operator":
        return "ADMIN"
    return (role or "").upper()


def _user_as_legacy(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "role": _legacy_role(user.role),
        "language": user.language,
        "country": user.country,
        "company_id": user.company_id,
        "is_active": user.is_active,
        "status": "ACTIVE" if user.is_active else "INACTIVE",
        "two_fa_enabled": False,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _require_legacy_admin(user: User) -> None:
    if user.role not in ("admin", "super_admin", "finance"):
        raise HTTPException(status_code=403, detail="Admin privileges required")


_LEGACY_STAFF_ROLE_TO_CORE = {
    "ADMIN": "admin",
    "SUPER_ADMIN": "super_admin",
    "OPS_MANAGER": "project_manager",
    "PROJECT_MANAGER": "project_manager",
    "SALES_MANAGER": "sales_manager",
    "SUPPORT_AGENT": "sales_manager",
    "FINANCE_OFFICER": "finance",
    "RISK_ANALYST": "admin",
    "DISPUTE_AGENT": "admin",
    "VERIFICATION_OFFICER": "admin",
    "AUDITOR": "admin",
    "MARKETING_OPERATOR": "marketing_operator",
}


def _core_staff_role(role: str | None) -> str:
    requested = (role or "").strip()
    requested_upper = requested.upper()
    core_role = _LEGACY_STAFF_ROLE_TO_CORE.get(requested_upper, requested.lower())
    allowed_roles = {item.value for item in STAFF_ROLES}
    if core_role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Role must be an internal staff role")
    return core_role


def _legacy_admin_status(value: str | None) -> str:
    normalized = (value or "").strip().upper()
    if normalized in {"ACTIVE", "ENABLED", "TRUE", "1"}:
        return "ACTIVE"
    if normalized in {"SUSPENDED", "INACTIVE", "DISABLED", "FALSE", "0"}:
        return "SUSPENDED"
    raise HTTPException(status_code=422, detail="Invalid status")


def _legacy_order_status_to_core(status: str | None) -> str:
    normalized = (status or "").strip().upper()
    mapping = {
        "CREATED": "pending",
        "AWAITING_PAYMENT": "confirmed",
        "PAID_IN_ESCROW": "confirmed",
        "IN_PROGRESS": "in_delivery",
        "DELIVERED": "in_delivery",
        "ACCEPTED": "completed",
        "PAYOUT_RELEASED": "completed",
        "DISPUTED": "disputed",
        "CANCELED": "cancelled",
        "CANCELLED": "cancelled",
        "REFUNDED": "cancelled",
    }
    if normalized not in mapping:
        raise HTTPException(status_code=422, detail="Invalid order status")
    return mapping[normalized]


def _legacy_verification_level(value: str | None, *, strict: bool = False) -> str:
    normalized = (value or "").strip().upper()
    if normalized in {"NONE", "BASIC", "BUSINESS", "PREMIUM"}:
        return normalized
    if normalized in {"PENDING", "SUBMITTED", "NEEDS_INFO"}:
        return "BASIC"
    if normalized in {"APPROVED", "VERIFIED"}:
        return "BUSINESS"
    if normalized in {"REJECTED", "DENIED"}:
        return "NONE"
    if strict:
        raise HTTPException(status_code=422, detail="Invalid verification level")
    return "BASIC"


def _verification_level_to_core_status(level: str, current: str | None = None) -> str:
    current_value = (current or "").strip().lower()
    if level == "NONE":
        return "rejected"
    if level == "BASIC":
        return "pending"
    if level in {"BUSINESS", "PREMIUM"}:
        if current_value in {"approved", "verified"}:
            return current_value
        return "approved"
    return current_value or "pending"


async def _append_legacy_admin_audit(
    db: DB,
    user: User,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    before: object | None,
    after: object | None,
    reason: str | None = None,
) -> None:
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key="procurement_admin",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before={"value": before},
        after={"value": after},
        reason=reason,
        source="cebu.compat.admin",
    )


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
    verification_level = contact_info.get("verification_level") or _legacy_verification_level(row.verification_status)
    operational_status = str(contact_info.get("operational_status") or "ACTIVE").upper()
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
        "verification_level": verification_level,
        "operational_status": operational_status,
        "status": operational_status,
        "contact_info": contact_info,
        "logo_url": row.logo_url,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _company_profile_as_legacy(row: Company, user: User | None = None) -> dict:
    contact_info = row.contact_info or {}
    return {
        "id": row.id,
        "company_id": row.id,
        "company_name": row.name,
        "name": row.name,
        "registration_number": contact_info.get("registration_number") or contact_info.get("tax_id"),
        "tax_id": contact_info.get("tax_id") or contact_info.get("registration_number"),
        "industry": contact_info.get("industry"),
        "company_size": contact_info.get("company_size") or "1-10",
        "website": row.website,
        "bio": row.description,
        "description": row.description,
        "address_line1": contact_info.get("address_line1") or row.address,
        "address": row.address,
        "city": row.city,
        "country": row.country,
        "phone": contact_info.get("phone") or (user.phone if user else None),
        "email": contact_info.get("email") or (user.email if user else None),
        "account_type": contact_info.get("account_type") or "BUSINESS",
        "company_type": row.type,
        "kyb_status": row.verification_status.upper(),
        "verification_status": row.verification_status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _apply_company_payload(company: Company, data: dict, user: User | None = None) -> None:
    contact_info = dict(company.contact_info or {})
    name = data.get("name") or data.get("company_name") or data.get("companyName")
    if name:
        company.name = str(name)
    if data.get("type"):
        company.type = str(data.get("type")).lower()
    if data.get("company_type"):
        company.type = str(data.get("company_type")).lower()
    for field in ("country", "city", "address", "website", "description"):
        if field in data:
            setattr(company, field, data.get(field))
    if "bio" in data:
        company.description = data.get("bio")
    if "address_line1" in data:
        company.address = data.get("address_line1")
    for field in (
        "tax_id",
        "registration_number",
        "industry",
        "company_size",
        "phone",
        "email",
        "category",
        "account_type",
        "address_line1",
    ):
        if field in data:
            contact_info[field] = data.get(field)
    if user is not None:
        contact_info.setdefault("email", user.email)
        if user.phone:
            contact_info.setdefault("phone", user.phone)
    company.contact_info = contact_info


async def _ensure_user_company(
    db: DB,
    user: User,
    data: dict | None = None,
    *,
    default_type: str = "buyer",
) -> Company:
    payload = data or {}
    company = await db.get(Company, user.company_id) if user.company_id else None
    if company is None:
        company = Company(
            name=(
                payload.get("name")
                or payload.get("company_name")
                or payload.get("companyName")
                or f"{user.full_name or user.email} Company"
            ),
            type=str(payload.get("type") or payload.get("company_type") or default_type).lower(),
            country=payload.get("country") or user.country,
            city=payload.get("city"),
            address=payload.get("address") or payload.get("address_line1"),
            website=payload.get("website"),
            description=payload.get("description") or payload.get("bio"),
            contact_info={"email": user.email, "phone": user.phone} if (user.email or user.phone) else {},
        )
        db.add(company)
        await db.flush()
        user.company_id = company.id
    _apply_company_payload(company, payload, user)
    await sync_role_portal_access(db, user_id=user.id, role=user.role, company_id=company.id)
    await db.flush()
    return company


def _address_as_legacy(row: Address) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "company_id": row.company_id,
        "address_type": row.address_type,
        "label": row.label,
        "contact_name": row.contact_name,
        "contact_phone": row.contact_phone,
        "country_code": row.country_code,
        "country_name": row.country_name,
        "state_province": row.state_province,
        "city": row.city,
        "district": row.district,
        "postal_code": row.postal_code,
        "address_line1": row.address_line1,
        "address_line2": row.address_line2,
        "lat": row.lat,
        "lng": row.lng,
        "is_default": row.is_default,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def _unset_address_defaults(db: DB, user_id: uuid.UUID, address_type: str) -> None:
    rows = list(
        (
            await db.execute(
                select(Address).where(
                    Address.user_id == user_id,
                    Address.address_type == address_type,
                    Address.status == "ACTIVE",
                    Address.is_default.is_(True),
                )
            )
        ).scalars()
    )
    for row in rows:
        row.is_default = False


def _address_payload(data: dict, user: User) -> dict:
    country_code = str(data.get("country_code") or data.get("country") or user.country or "PH").upper()
    if len(country_code) > 5:
        country_code = "PH" if "phil" in country_code.lower() else country_code[:5]
    return {
        "address_type": str(data.get("address_type") or "DELIVERY_TO").upper(),
        "label": data.get("label") or data.get("name") or "Default Address",
        "contact_name": data.get("contact_name") or user.full_name or user.email,
        "contact_phone": data.get("contact_phone") or data.get("phone") or user.phone or "N/A",
        "country_code": country_code,
        "country_name": data.get("country_name") or data.get("country") or user.country or "Philippines",
        "state_province": data.get("state_province") or data.get("province") or data.get("state"),
        "city": data.get("city") or "Cebu",
        "district": data.get("district"),
        "postal_code": data.get("postal_code") or data.get("zip"),
        "address_line1": data.get("address_line1") or data.get("address") or "Address pending",
        "address_line2": data.get("address_line2"),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "is_default": bool(data.get("is_default")),
    }


def _dispute_evidence(row: OrderDispute) -> list:
    data = row.resolution_json or {}
    evidence = data.get("evidence_json") or data.get("evidence") or []
    return evidence if isinstance(evidence, list) else []


def _dispute_status_as_legacy(status: str | None) -> str:
    maps = {
        "open": "OPEN",
        "under_review": "UNDER_REVIEW",
        "resolved_buyer": "RESOLVED",
        "resolved_supplier": "RESOLVED",
        "closed": "DISMISSED",
        "withdrawn": "DISMISSED",
    }
    return maps.get((status or "").lower(), (status or "").upper())


def _dispute_status_to_core(status: str | None) -> set[str] | None:
    if not status:
        return None
    maps = {
        "OPEN": {"open"},
        "OPENED": {"open"},
        "UNDER_REVIEW": {"under_review"},
        "IN_REVIEW": {"under_review"},
        "RESOLVED": {"resolved_buyer", "resolved_supplier"},
        "RESOLVED_REFUND": {"resolved_buyer"},
        "RESOLVED_RELEASE": {"resolved_supplier"},
        "DISMISSED": {"closed", "withdrawn"},
        "CLOSED": {"closed"},
    }
    return maps.get(str(status).upper(), {str(status).lower()})


def _dispute_as_legacy(row: OrderDispute) -> dict:
    data = row.resolution_json or {}
    return {
        "id": row.id,
        "order_id": row.commerce_order_id,
        "commerce_order_id": row.commerce_order_id,
        "opened_by_user_id": row.opened_by_user_id,
        "filed_by_role": row.opened_by_role.upper(),
        "opened_by_role": row.opened_by_role.upper(),
        "reason": row.reason_code,
        "reason_code": row.reason_code,
        "description": row.description,
        "evidence_json": _dispute_evidence(row),
        "admin_notes": data.get("admin_notes"),
        "status": _dispute_status_as_legacy(row.status),
        "core_status": row.status,
        "resolution": data.get("resolution") or data.get("admin_reason"),
        "refund_amount_minor": data.get("refund_amount_minor"),
        "resolved_at": row.resolved_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _risk_status_to_core(status: str | None) -> str:
    value = (status or "OPEN").upper()
    if value in {"OPEN", "IN_REVIEW"}:
        return "open"
    if value in {"MITIGATED", "ACTION_TAKEN", "CLOSED", "RESOLVED"}:
        return "resolved"
    if value in {"FALSE_POSITIVE", "DISMISSED"}:
        return "dismissed"
    return value.lower()


def _risk_status_as_legacy(row: RiskFlag) -> str:
    details = row.details_json or {}
    legacy_status = details.get("legacy_status")
    if legacy_status:
        return str(legacy_status).upper()
    maps = {"open": "OPEN", "resolved": "MITIGATED", "dismissed": "FALSE_POSITIVE"}
    return maps.get((row.status or "").lower(), (row.status or "").upper())


def _risk_flag_as_legacy(row: RiskFlag) -> dict:
    details = row.details_json or {}
    admin_actions = details.get("admin_actions") or []
    last_action = admin_actions[-1] if admin_actions else None
    return {
        "id": row.id,
        "entity_type": row.subject_type.upper(),
        "entity_id": row.subject_id,
        "subject_type": row.subject_type,
        "subject_id": row.subject_id,
        "company_id": row.company_id,
        "risk_type": row.reason_code.upper(),
        "reason_code": row.reason_code,
        "risk_level": row.severity.upper(),
        "severity": row.severity,
        "description": details.get("description"),
        "details_json": details,
        "status": _risk_status_as_legacy(row),
        "core_status": row.status,
        "action_taken": last_action.get("action_taken") if isinstance(last_action, dict) else None,
        "last_action": last_action,
        "source_event": row.source_event,
        "resolved_at": row.resolved_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _kyc_doc_as_legacy(row: CompanyDocument, latest_analysis: KYCAnalysisResult | None = None) -> dict:
    data = {
        "id": row.id,
        "company_id": row.company_id,
        "doc_type": row.doc_type,
        "file_url": row.file_url,
        "original_filename": row.original_filename,
        "status": row.status,
        "reviewer_note": row.reviewer_note,
        "reviewed_by": row.reviewed_by,
        "reviewed_at": row.reviewed_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
    if latest_analysis is not None:
        data["latest_analysis"] = {
            "id": latest_analysis.id,
            "authenticity": latest_analysis.authenticity,
            "confidence": latest_analysis.confidence,
            "risk_score": latest_analysis.overall_risk_score,
            "overall_risk_score": latest_analysis.overall_risk_score,
            "recommended_action": latest_analysis.recommended_action,
            "tamper_suspected": latest_analysis.tamper_suspected,
            "photoshop_suspected": latest_analysis.photoshop_suspected,
            "text_photo_consistency": latest_analysis.text_photo_consistency,
            "created_at": latest_analysis.created_at,
        }
    return data


def _verification_review_as_legacy(row: VerificationReview) -> dict:
    status = row.status
    status_map = {
        "APPROVED_BASIC": "APPROVED",
        "APPROVED_BUSINESS": "APPROVED",
        "NEEDS_MORE_INFO": "NEEDS_INFO",
    }
    return {
        "id": row.id,
        "company_id": row.company_id,
        "status": status_map.get(status, status),
        "core_status": row.status,
        "decision": row.decision,
        "decision_reason": row.decision_reason,
        "user_facing_note": row.user_facing_note,
        "decided_at": row.decided_at,
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
        "listing_origin",
        "item_condition",
        "warranty_left_months",
        "warranty_note",
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
        "listing_origin": attrs.get("listing_origin") or "new",
        "item_condition": attrs.get("item_condition") or "new",
        "warranty_left_months": attrs.get("warranty_left_months"),
        "warranty_note": attrs.get("warranty_note"),
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


def _intent_as_legacy(row: ProcurementRequest, offer_count: int | None = None) -> dict:
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
        "currency": str(requirements.get("currency") or attrs.get("currency") or "EUR"),
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
        "offer_count": offer_count,
    }


async def _intent_as_legacy_with_offer_count(db: DB, row: ProcurementRequest) -> dict:
    count = (
        await db.execute(
            select(func.count())
            .select_from(SupplierOffer)
            .where(SupplierOffer.procurement_request_id == row.id)
        )
    ).scalar() or 0
    return _intent_as_legacy(row, offer_count=int(count))


def _intent_status_to_core_filter(status: str | None) -> set[str] | None:
    if not status:
        return None
    value = status.upper()
    maps = {
        "DRAFT": {"draft"},
        "ACTIVE": {"published", "matching", "offer_received"},
        "PUBLISHED": {"published"},
        "MATCHING": {"matching"},
        "OFFER_RECEIVED": {"offer_received"},
        "AWARDED": {"awarded"},
        "EXPIRED": {"expired"},
        "CLOSED": {"closed"},
        "CANCELED": {"cancelled"},
        "CANCELLED": {"cancelled"},
    }
    return maps.get(value, {status.lower()})


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


def _offer_status_to_core_filter(status: str | None) -> set[str] | None:
    if not status:
        return None
    value = status.upper()
    maps = {
        "DRAFT": {"draft"},
        "SUBMITTED": {"submitted"},
        "WITHDRAWN": {"withdrawn"},
        "AWARDED": {"awarded"},
        "EXPIRED": {"expired"},
        "REJECTED": {"rejected"},
    }
    return maps.get(value, {status.lower()})


async def _legacy_offer_visible_to_user(db: DB, row: SupplierOffer, user: User) -> None:
    if user.role in ("admin", "super_admin", "finance"):
        return
    if user.company_id and row.supplier_company_id == user.company_id:
        return
    request = await db.get(ProcurementRequest, row.procurement_request_id)
    if request and (
        request.buyer_user_id == user.id
        or (user.company_id and request.buyer_company_id == user.company_id)
    ):
        return
    raise HTTPException(status_code=403, detail="Not allowed to view this offer")


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


def _admin_escrow_as_legacy(row: EscrowTransaction | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "order_id": row.order_id,
        "provider": row.provider,
        "provider_reference": row.provider_reference,
        "auth_amount_minor": row.auth_amount_minor,
        "captured_amount_minor": row.captured_amount_minor,
        "released_amount_minor": row.released_amount_minor,
        "refunded_amount_minor": row.refunded_amount_minor,
        "currency": row.currency,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _wallet_deposit_as_admin_legacy(row: WalletDeposit) -> dict:
    return {
        "id": row.id,
        "wallet_id": row.wallet_id,
        "owner_user_id": row.owner_user_id,
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "network": row.network,
        "provider": row.provider,
        "payment_method": row.payment_method,
        "source_currency": row.source_currency,
        "target_currency": row.target_currency,
        "deposit_address": row.deposit_address,
        "tx_hash": row.tx_hash,
        "confirmations": row.confirmations,
        "status": row.status,
        "submitter_note": row.submitter_note,
        "admin_note": row.admin_note,
        "verified_by": row.verified_by,
        "verified_at": row.verified_at,
        "rejected_by": row.rejected_by,
        "rejected_at": row.rejected_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _payout_as_admin_legacy(row: Payout) -> dict:
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "company_id": row.company_id,
        "supplier_id": row.company_id,
        "order_id": row.order_id,
        "escrow_id": row.escrow_id,
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "provider": row.provider,
        "method": row.provider,
        "destination": row.destination,
        "status": row.status,
        "risk_hold": row.risk_hold,
        "provider_reference": row.provider_reference,
        "failure_reason": row.failure_reason,
        "scheduled_at": row.scheduled_at,
        "paid_at": row.paid_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _payment_event_as_admin_legacy(row: PaymentEvent) -> dict:
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "provider": row.provider,
        "provider_event_id": row.provider_event_id,
        "event_type": row.event_type,
        "order_id": row.order_id,
        "escrow_id": row.escrow_id,
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "status": row.status,
        "error_message": row.error_message,
        "raw_payload": row.raw_payload,
        "received_at": row.received_at,
        "processed_at": row.processed_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _settlement_event_as_admin_legacy(row: SettlementEvent) -> dict:
    return {
        "id": row.id,
        "payment_intent_id": row.payment_intent_id,
        "provider": row.provider,
        "provider_reference": row.provider_reference,
        "gross_amount_minor": row.gross_amount_minor,
        "fee_amount_minor": row.fee_amount_minor,
        "net_amount_minor": row.net_amount_minor,
        "currency": row.currency,
        "status": row.status,
        "raw_payload": row.raw_payload,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _shipping_route_as_admin_legacy(row: ShippingRoute) -> dict:
    return {
        "id": row.id,
        "origin_country": row.origin_country,
        "origin_region": row.origin_region,
        "dest_country": row.dest_country,
        "dest_region": row.dest_region,
        "shipping_method": row.shipping_method,
        "description": row.description,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _shipping_rate_as_admin_legacy(row: ShippingRate) -> dict:
    return {
        "id": row.id,
        "route_id": row.route_id,
        "weight_min_kg": row.weight_min_kg,
        "weight_max_kg": row.weight_max_kg,
        "price_per_kg_minor": row.price_per_kg_minor,
        "currency": row.currency,
        "min_charge_minor": row.min_charge_minor,
        "volume_factor": row.volume_factor,
        "estimated_days_min": row.estimated_days_min,
        "estimated_days_max": row.estimated_days_max,
        "surcharges_json": row.surcharges_json,
        "valid_from": row.valid_from,
        "valid_until": row.valid_until,
        "notes": row.notes,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _normalize_country_code(value: object | None, fallback: str = "PH") -> str:
    raw = str(value or fallback).strip()
    if not raw:
        return fallback
    upper = raw.upper()
    aliases = {
        "PHILIPPINES": "PH",
        "THE PHILIPPINES": "PH",
        "CEBU": "PH",
        "UNITED STATES": "US",
        "USA": "US",
        "UNITED ARAB EMIRATES": "AE",
        "UAE": "AE",
    }
    return aliases.get(upper, upper[:5])


def _shipping_estimate_as_legacy(route: ShippingRoute, rate: ShippingRate, weight_kg: float) -> dict:
    base_cost = max(int(weight_kg * float(rate.price_per_kg_minor or 0)), int(rate.min_charge_minor or 0))
    surcharges_minor = 0
    if isinstance(rate.surcharges_json, dict):
        for value in rate.surcharges_json.values():
            if isinstance(value, (int, float)):
                surcharges_minor += int(value)
            elif isinstance(value, dict) and isinstance(value.get("amount_minor"), (int, float)):
                surcharges_minor += int(value["amount_minor"])
    total_shipping_minor = base_cost + surcharges_minor
    return {
        "route_id": route.id,
        "rate_id": rate.id,
        "shipping_method": route.shipping_method,
        "origin_country": route.origin_country,
        "origin_region": route.origin_region,
        "dest_country": route.dest_country,
        "dest_region": route.dest_region,
        "weight_kg": weight_kg,
        "cost_minor": base_cost,
        "surcharges_minor": surcharges_minor,
        "total_shipping_minor": total_shipping_minor,
        "currency": rate.currency,
        "estimated_days_min": rate.estimated_days_min,
        "estimated_days_max": rate.estimated_days_max,
    }


def _trust_tier(score: int) -> str:
    if score >= 90:
        return "DIAMOND"
    if score >= 75:
        return "PLATINUM"
    if score >= 60:
        return "GOLD"
    if score >= 40:
        return "SILVER"
    return "BRONZE"


def _trust_profile_as_admin_legacy(row: TrustProfile, company: Company | None = None) -> dict:
    metrics = row.metrics_json or {}
    completion = 50
    if company is not None:
        fields = [company.name, company.country, company.city, company.address, company.description, company.website]
        completion = min(100, 20 + sum(1 for value in fields if value) * 12)
        if company.verification_status.lower() == "approved":
            completion = 100
    dispute_rate = 0
    if row.completed_orders:
        dispute_rate = round(row.dispute_count * 100 / row.completed_orders, 2)
    return {
        "id": row.id,
        "entity_id": row.company_id,
        "entity_type": "SUPPLIER",
        "company_id": row.company_id,
        "company_name": company.name if company else None,
        "portal_key": row.portal_key,
        "trust_score": row.trust_score,
        "trust_tier": _trust_tier(row.trust_score),
        "profile_completion_rate": metrics.get("profile_completion_rate", completion),
        "deal_completion_rate": metrics.get("deal_completion_rate", 100 if row.completed_orders else 0),
        "successful_deals_count": row.completed_orders,
        "canceled_deals_count": metrics.get("canceled_deals_count", 0),
        "deposit_amount_minor": metrics.get("deposit_amount_minor", 0),
        "deposit_currency": metrics.get("deposit_currency", "EUR"),
        "dispute_rate": metrics.get("dispute_rate", dispute_rate),
        "refund_rate": metrics.get("refund_rate", 0),
        "completed_orders": row.completed_orders,
        "dispute_count": row.dispute_count,
        "review_count": row.review_count,
        "avg_rating": row.avg_rating,
        "status": metrics.get("status", "ACTIVE"),
        "metrics_json": metrics,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _region_extra(row: Region) -> dict:
    payload = row.tax_rules_json if isinstance(row.tax_rules_json, dict) else {}
    return payload.get("procurement_admin", {}) if isinstance(payload.get("procurement_admin"), dict) else {}


def _region_as_admin_legacy(row: Region) -> dict:
    extra = _region_extra(row)
    return {
        "id": row.id,
        "name": row.name,
        "slug": extra.get("slug") or row.code.lower(),
        "region_type": extra.get("region_type") or "COUNTRY",
        "country": extra.get("country") or row.name,
        "city": extra.get("city"),
        "center_lat": extra.get("center_lat"),
        "center_lng": extra.get("center_lng"),
        "default_radius_km": extra.get("default_radius_km") or 15,
        "status": "ACTIVE" if row.is_active else "DISABLED",
        "notes": extra.get("notes"),
        "code": row.code,
        "currency_code": row.currency_code,
        "language_codes_json": row.language_codes_json or [],
        "timezone": row.timezone,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _backup_config_from_rows(schedules: list[BackupSchedule], jobs: list[BackupJob]) -> dict:
    enabled = any(row.enabled for row in schedules) if schedules else True
    primary = schedules[0] if schedules else None
    latest_job = jobs[0] if jobs else None
    latest_success = next((row for row in jobs if row.status == "SUCCESS"), None)
    return {
        "enabled": enabled,
        "backup_storage_path": "/var/backups/ainerwise-procurement",
        "backup_retention_days": primary.retention_days if primary else 30,
        "backup_retention_count": primary.retention_count if primary else 10,
        "default_frequency": primary.frequency if primary else "WEEKLY",
        "total_schedules": len(schedules),
        "total_jobs": len(jobs),
        "successful_jobs": sum(1 for row in jobs if row.status == "SUCCESS"),
        "failed_jobs": sum(1 for row in jobs if row.status == "FAILED"),
        "last_run_at": latest_job.started_at if latest_job else None,
        "last_success_at": latest_success.finished_at if latest_success else None,
        "next_run_at": min((row.next_run_at for row in schedules if row.enabled and row.next_run_at), default=None),
    }


def _platform_setting_value(row: PlatformSetting) -> object | None:
    payload = row.value_json or {}
    if isinstance(payload, dict) and "value" in payload:
        return payload.get("value")
    return payload


def _platform_setting_as_admin_legacy(row: PlatformSetting) -> dict:
    value = _platform_setting_value(row)
    return {
        "id": row.id,
        "key": row.key,
        "value": value,
        "value_json": row.value_json,
        "description": row.description,
        "updated_by": row.updated_by,
        "updated_at": row.updated_at,
    }


MARKET_LOCALE_OPTIONS = [
    {"code": "EN", "locale": "en", "uri_prefix": "en", "label": "English"},
    {"code": "ZH", "locale": "zh", "uri_prefix": "cn", "label": "中文"},
    {"code": "SR", "locale": "sr", "uri_prefix": "rs", "label": "Srpski"},
    {"code": "BS", "locale": "bs", "uri_prefix": "ba", "label": "Bosanski"},
    {"code": "PL", "locale": "pl", "uri_prefix": "pl", "label": "Polski"},
    {"code": "DE", "locale": "de", "uri_prefix": "de", "label": "Deutsch"},
    {"code": "RO", "locale": "ro", "uri_prefix": "ro", "label": "Romana"},
]

MARKET_LOCALIZATION_SETTING_DEFAULTS = {
    "market_enabled_locale_prefixes": {
        "value": "en,cn,rs",
        "description": "Enabled AISLOS Market URI language prefixes. Example: /cn, /rs.",
    },
    "market_default_locale_prefix": {
        "value": "en",
        "description": "Default AISLOS Market URI language prefix.",
    },
    "market_enabled_region_codes": {
        "value": "RS,CN,PH",
        "description": "Enabled AISLOS Market region codes. Keep this aligned with Admin -> Regions.",
    },
}


def _setting_value_text(row: PlatformSetting | None, default: str = "") -> str:
    if row is None:
        return default
    value = _platform_setting_value(row)
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value)
    if value is None:
        return default
    return str(value)


def _split_csv(value: object | None) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        raw_items = value
    else:
        raw_items = str(value or "").split(",")
    seen: set[str] = set()
    items: list[str] = []
    for item in raw_items:
        normalized = str(item or "").strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(normalized)
    return items


def _default_ranking_profiles() -> list[dict]:
    return [
        {
            "id": "default",
            "name": "Balanced",
            "description": "Balanced supplier ranking for most procurement requests.",
            "is_default": True,
            "weights": {
                "category_match": 0.30,
                "trust": 0.25,
                "distance": 0.15,
                "deal_rate": 0.15,
                "stock": 0.15,
            },
        },
        {
            "id": "cost",
            "name": "Cost Sensitive",
            "description": "Prioritize available stock and deal conversion for price-sensitive sourcing.",
            "is_default": False,
            "weights": {
                "category_match": 0.25,
                "trust": 0.15,
                "distance": 0.10,
                "deal_rate": 0.25,
                "stock": 0.25,
            },
        },
        {
            "id": "trust",
            "name": "Trust First",
            "description": "Prefer verified and historically reliable suppliers.",
            "is_default": False,
            "weights": {
                "category_match": 0.25,
                "trust": 0.45,
                "distance": 0.10,
                "deal_rate": 0.15,
                "stock": 0.05,
            },
        },
        {
            "id": "distance",
            "name": "Nearby Delivery",
            "description": "Favor nearby suppliers for urgent local delivery.",
            "is_default": False,
            "weights": {
                "category_match": 0.25,
                "trust": 0.20,
                "distance": 0.35,
                "deal_rate": 0.10,
                "stock": 0.10,
            },
        },
        {
            "id": "delivery",
            "name": "Delivery Confidence",
            "description": "Prefer suppliers with stock and delivery readiness.",
            "is_default": False,
            "weights": {
                "category_match": 0.25,
                "trust": 0.20,
                "distance": 0.15,
                "deal_rate": 0.15,
                "stock": 0.25,
            },
        },
    ]


def _ranking_profile_as_legacy(profile: dict) -> dict:
    weights = profile.get("weights") or {}
    normalized_weights = {str(key): float(value or 0) for key, value in weights.items()}
    return {
        "id": str(profile.get("id")),
        "name": profile.get("name") or str(profile.get("id")).title(),
        "description": profile.get("description"),
        "is_default": bool(profile.get("is_default")),
        "weights": normalized_weights,
        "total_weight": round(sum(normalized_weights.values()), 4),
        "updated_at": profile.get("updated_at"),
    }


async def _ranking_profiles_setting(db: DB) -> PlatformSetting:
    row = (
        await db.execute(
            select(PlatformSetting).where(
                PlatformSetting.portal_key == "admin_cebu",
                PlatformSetting.key == "ranking_profiles_json",
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = PlatformSetting(
            portal_key="admin_cebu",
            key="ranking_profiles_json",
            value_json={"value": _default_ranking_profiles()},
            description="AISLOS Market supplier ranking profile weights.",
        )
        db.add(row)
        await db.flush()
    return row


async def _load_ranking_profiles(db: DB) -> list[dict]:
    row = await _ranking_profiles_setting(db)
    value = _platform_setting_value(row)
    profiles = value if isinstance(value, list) else _default_ranking_profiles()
    return [_ranking_profile_as_legacy(profile) for profile in profiles if isinstance(profile, dict)]


async def _save_ranking_profiles(db: DB, profiles: list[dict]) -> PlatformSetting:
    row = await _ranking_profiles_setting(db)
    row.value_json = {"value": profiles}
    await db.flush()
    return row


async def _ensure_legacy_admin_default_settings(db: DB) -> list[PlatformSetting]:
    defaults = {
        "DEMO_MODE": {
            "value": "true" if await is_demo_mode_enabled(db) else "false",
            "description": "Show demo procurement credentials and allow demo buyer/supplier login.",
        },
        "ai_enabled": {"value": "true", "description": "Enable AI helpers in Procurement Admin."},
        "ai_provider": {"value": "openai", "description": "Default AI provider name for the Admin bridge."},
        "ai_model": {"value": "gpt-4o-mini", "description": "Default AI model for compatibility smoke checks."},
        "ai_providers_json": {"value": "[]", "description": "Saved AI provider presets for the copied Admin UI."},
    }
    defaults.update(MARKET_LOCALIZATION_SETTING_DEFAULTS)
    existing_rows = list(
        (
            await db.execute(
                select(PlatformSetting).where(
                    PlatformSetting.portal_key == "admin_cebu",
                    PlatformSetting.key.in_(defaults.keys()),
                )
            )
        ).scalars()
    )
    existing = {row.key: row for row in existing_rows}
    created: list[PlatformSetting] = []
    for key, payload in defaults.items():
        if key in existing:
            continue
        row = PlatformSetting(
            portal_key="admin_cebu",
            key=key,
            value_json={"value": payload["value"]},
            description=payload["description"],
        )
        db.add(row)
        created.append(row)
    if created:
        await db.flush()
    return list(existing.values()) + created


def _audit_risk_level(row: AuditLog) -> str:
    text = " ".join(
        str(value or "").lower()
        for value in (row.action, row.entity_type, row.reason, row.source)
    )
    if any(marker in text for marker in ("critical", "failed", "refund", "delete", "reject")):
        return "HIGH"
    if any(marker in text for marker in ("risk", "dispute", "suspend", "forbidden")):
        return "MEDIUM"
    return "LOW"


def _audit_log_as_admin_legacy(row: AuditLog, actor: User | None = None) -> dict:
    return {
        "id": row.id,
        "actor_type": row.actor_type,
        "actor_user_id": row.actor_user_id,
        "actor_role": _legacy_role(actor.role) if actor else None,
        "agent_slug": row.agent_slug,
        "portal_key": row.portal_key,
        "action": row.action,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "before": row.before_json,
        "after": row.after_json,
        "reason": row.reason,
        "source": row.source,
        "risk_level": _audit_risk_level(row),
        "correlation_id": row.correlation_id,
        "ip": row.ip,
        "user_agent": row.user_agent,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _notification_template_as_admin_legacy(row: NotificationTemplate) -> dict:
    return {
        "id": row.id,
        "portal_key": row.portal_key,
        "template_key": row.template_key,
        "channel": row.channel,
        "language": row.language,
        "subject": row.subject,
        "body": row.body,
        "variables_hint": row.variables_hint,
        "active": row.active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _portal_notification_as_admin_legacy(row: PortalNotification) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "portal_key": row.portal_key,
        "domain": row.domain,
        "event_type": row.event_type,
        "title": row.title,
        "body": row.body,
        "link_path": row.link_path,
        "aggregate_type": row.aggregate_type,
        "aggregate_id": row.aggregate_id,
        "status": row.status,
        "read_at": row.read_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _backup_schedule_as_admin_legacy(row: BackupSchedule) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "frequency": row.frequency,
        "cron_expr": row.cron_expr,
        "day_of_week": row.day_of_week,
        "day_of_month": row.day_of_month,
        "hour": row.hour,
        "minute": row.minute,
        "enabled": row.enabled,
        "retention_count": row.retention_count,
        "retention_days": row.retention_days,
        "last_run_at": row.last_run_at,
        "next_run_at": row.next_run_at,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _backup_job_as_admin_legacy(row: BackupJob) -> dict:
    return {
        "id": row.id,
        "schedule_id": row.schedule_id,
        "status": row.status,
        "archive_size_bytes": row.archive_size_bytes,
        "archive_path": row.archive_path,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "error_message": row.error_message,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def _get_integration_setting(db: DB, category: str) -> IntegrationSetting | None:
    return (
        await db.execute(select(IntegrationSetting).where(IntegrationSetting.category == category))
    ).scalar_one_or_none()


async def _upsert_integration_setting(
    db: DB,
    category: str,
    *,
    enabled: bool,
    config: dict,
) -> IntegrationSetting:
    row = await _get_integration_setting(db, category)
    if row is None:
        row = IntegrationSetting(category=category, is_enabled=enabled, config_json=config)
        db.add(row)
    else:
        row.is_enabled = enabled
        row.config_json = config
    await db.flush()
    return row


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "configured"
    return f"{value[:4]}...{value[-4:]}"


def _kyc_analysis_as_legacy(row: KYCAnalysisResult) -> dict:
    return {
        "id": row.id,
        "document_id": row.document_id,
        "company_id": row.company_id,
        "ai_provider": row.ai_provider,
        "ai_model": row.ai_model,
        "authenticity": row.authenticity,
        "confidence": row.confidence,
        "overall_risk_score": row.overall_risk_score,
        "recommended_action": row.recommended_action,
        "tamper_suspected": row.tamper_suspected,
        "photoshop_suspected": row.photoshop_suspected,
        "text_photo_consistency": row.text_photo_consistency,
        "extracted_fields": row.extracted_fields,
        "detected_issues": row.detected_issues,
        "concerns": row.concerns,
        "raw_result_json": row.raw_result_json,
        "created_at": row.created_at,
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
    await db.refresh(row)
    request = await db.get(ProcurementRequest, row.procurement_request_id)
    escrow = await _order_escrow(db, row)
    await db.refresh(row)
    latest_delivery = await _order_latest_delivery(db, row)
    await db.refresh(row)
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


async def _ensure_admin_order_delivery_marker(
    db: DB,
    row: CommerceOrder,
    legacy_status: str,
    user: User,
) -> None:
    normalized = legacy_status.upper()
    if normalized not in {"DELIVERED", "ACCEPTED", "PAYOUT_RELEASED"}:
        return
    latest_delivery = await _order_latest_delivery(db, row)
    if latest_delivery is None:
        latest_delivery = OrderDelivery(
            workspace_id=row.workspace_id,
            commerce_order_id=row.id,
            status="scheduled",
            proof_json={
                "notes": "Created by Procurement Admin compatibility status update",
                "actor_id": str(user.id),
            },
        )
        db.add(latest_delivery)
        await db.flush()
    now = datetime.now(timezone.utc)
    if normalized == "DELIVERED":
        latest_delivery.status = "delivered"
        latest_delivery.delivered_at = latest_delivery.delivered_at or now
    else:
        latest_delivery.status = "accepted"
        latest_delivery.delivered_at = latest_delivery.delivered_at or now
        latest_delivery.accepted_at = latest_delivery.accepted_at or now


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


_COUNTRY_ALIASES = {
    "RS": {"RS", "SRB", "SERBIA", "SRBIJA"},
    "PL": {"PL", "POL", "POLAND", "POLSKA"},
    "PH": {"PH", "PHL", "PHILIPPINES"},
    "BA": {"BA", "BIH", "BOSNIA", "BOSNIA AND HERZEGOVINA"},
    "RO": {"RO", "ROU", "ROMANIA"},
}


def _country_alias_values(value: str | None) -> list[str]:
    normalized = str(value or "").strip().upper()
    if not normalized:
        return []
    for code, aliases in _COUNTRY_ALIASES.items():
        if normalized == code or normalized in aliases:
            return sorted(aliases | {code})
    return [normalized]


def _wallet_instruction_address(data: LegacyWalletDepositCreate, user: CurrentUser) -> str:
    provided = (data.deposit_address or "").strip()
    if provided:
        return provided
    currency = (data.currency or "EUR").upper()
    network = (data.network or "LOCAL_BANK").upper()
    method = (data.payment_method or "BANK_TRANSFER").upper()
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
                    currency=project.currency or "EUR",
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
        "currency": project.currency or "EUR",
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


@router.get("/companies/my")
async def legacy_get_my_company_alias(db: DB, user: CurrentUser):
    return await legacy_get_my_company(db, user)


@router.post("/companies", status_code=201)
async def legacy_create_my_company(data: dict, db: DB, user: CurrentUser):
    company = await _ensure_user_company(db, user, data, default_type="vendor" if user.role == "vendor" else "buyer")
    await db.commit()
    await db.refresh(company)
    await db.refresh(user)
    return _company_as_legacy(company)


@router.patch("/companies/me")
async def legacy_update_my_company(data: dict, db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=404, detail="Company not found")
    company = await db.get(Company, user.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    _apply_company_payload(company, data, user)
    await sync_role_portal_access(db, user_id=user.id, role=user.role, company_id=company.id)
    await db.commit()
    await db.refresh(company)
    return _company_as_legacy(company)


@router.get("/companies/me/documents")
async def legacy_get_my_company_documents(db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Company required")
    rows = await list_kyc_documents(db, user.company_id)
    return [_kyc_doc_as_legacy(row) for row in rows]


@router.post("/companies/me/documents", status_code=201)
async def legacy_create_my_company_document(data: CompanyDocumentCreate, db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Company required")
    row = await upload_kyc_document(
        db,
        company_id=user.company_id,
        doc_type=data.doc_type,
        file_url=data.file_url,
        original_filename=data.original_filename,
    )
    await db.commit()
    await db.refresh(row)
    return _kyc_doc_as_legacy(row)


@router.get("/companies/me/verification/status")
async def legacy_get_my_company_verification_status(db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Company required")
    row = (
        await db.execute(
            select(VerificationReview)
            .where(VerificationReview.company_id == user.company_id)
            .order_by(VerificationReview.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return {
            "company_id": user.company_id,
            "status": "NOT_STARTED",
            "core_status": "NOT_STARTED",
            "created_at": None,
        }
    return _verification_review_as_legacy(row)


@router.post("/companies/me/verification/submit", status_code=201)
async def legacy_submit_my_company_verification(db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Company required")
    docs = await list_kyc_documents(db, user.company_id)
    if not docs:
        raise HTTPException(status_code=400, detail="Upload at least one KYB document before submitting")
    try:
        row = await submit_for_verification(db, user.company_id)
        company = await db.get(Company, user.company_id)
        if company is not None and company.verification_status == "verified":
            company.verification_status = "pending"
        await db.commit()
        await db.refresh(row)
        return _verification_review_as_legacy(row)
    except KYCError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/uploads", status_code=201)
async def legacy_upload_file(db: DB, user: CurrentUser, file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="File is empty")
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is too large")
    object_name = new_user_upload_key(user.id, file.filename or "upload")
    client = get_minio_client()
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
    client.put_object(
        BUCKET_NAME,
        object_name,
        io.BytesIO(content),
        len(content),
        content_type=file.content_type or "application/octet-stream",
    )
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key="procurement",
        action="procurement.upload.create",
        entity_type="object_storage",
        entity_id=None,
        before=None,
        after={"bucket": BUCKET_NAME, "object_name": object_name, "filename": file.filename},
        reason="Legacy Procurement upload compatibility",
        source="cebu.compat.upload",
    )
    await db.commit()
    return {
        "url": f"minio://{BUCKET_NAME}/{object_name}",
        "object_name": object_name,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
    }


@router.get("/buyer/company-profile")
async def legacy_get_buyer_company_profile(db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(status_code=404, detail="Company profile not found")
    company = await db.get(Company, user.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return _company_profile_as_legacy(company, user)


@router.patch("/buyer/company-profile")
async def legacy_update_buyer_company_profile(data: dict, db: DB, user: CurrentUser):
    company = await _ensure_user_company(db, user, data, default_type="buyer")
    await db.commit()
    await db.refresh(company)
    await db.refresh(user)
    return _company_profile_as_legacy(company, user)


def _team_member_as_legacy(member: User, owner_id: uuid.UUID) -> dict:
    return {
        "id": member.id,
        "email": member.email,
        "display_name": member.full_name or member.email,
        "role": "OWNER" if member.id == owner_id else "MEMBER",
        "core_role": member.role,
        "status": "ACTIVE" if member.is_active else "INACTIVE",
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }


@router.get("/buyer/team/members")
async def legacy_buyer_team_members(db: DB, user: CurrentUser):
    if not user.company_id:
        return [_team_member_as_legacy(user, user.id)]
    rows = list(
        (
            await db.execute(
                select(User)
                .where(User.company_id == user.company_id)
                .order_by(User.created_at.asc())
            )
        ).scalars()
    )
    return [_team_member_as_legacy(row, user.id) for row in rows]


@router.post("/buyer/team/invite", status_code=201)
async def legacy_buyer_team_invite(data: dict, db: DB, user: CurrentUser):
    email = str(data.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="email is required")
    company = await _ensure_user_company(db, user, {}, default_type="buyer")
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        if existing.company_id != company.id:
            raise HTTPException(status_code=409, detail="This user belongs to another company")
        return _team_member_as_legacy(existing, user.id)
    member = User(
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        full_name=data.get("display_name") or data.get("name") or email.split("@")[0],
        role="buyer",
        language=user.language,
        country=user.country,
        company_id=company.id,
        is_active=True,
    )
    db.add(member)
    await db.flush()
    await sync_role_portal_access(db, user_id=member.id, role=member.role, company_id=company.id)
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key="procurement",
        action="buyer.team.invite",
        entity_type="user",
        entity_id=member.id,
        before=None,
        after={"email": member.email, "company_id": str(company.id), "role": data.get("role") or "MEMBER"},
        reason="Legacy buyer team invite compatibility",
        source="cebu.compat.team",
    )
    await db.commit()
    await db.refresh(member)
    return _team_member_as_legacy(member, user.id)


@router.delete("/buyer/team/members/{member_id}", status_code=204)
async def legacy_buyer_team_remove_member(member_id: uuid.UUID, db: DB, user: CurrentUser):
    if member_id == user.id:
        raise HTTPException(status_code=409, detail="Cannot remove yourself")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Company required")
    member = await db.get(User, member_id)
    if member is None or member.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Team member not found")
    member.is_active = False
    await suspend_user_portal_access(db, user_id=member.id)
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key="procurement",
        action="buyer.team.remove",
        entity_type="user",
        entity_id=member.id,
        before={"is_active": True},
        after={"is_active": False},
        reason="Legacy buyer team remove compatibility",
        source="cebu.compat.team",
    )
    await db.commit()
    return None


@router.get("/trust/me")
async def legacy_trust_me(db: DB, user: CurrentUser):
    company = await db.get(Company, user.company_id) if user.company_id else None
    if company is None:
        return {
            "company_id": None,
            "trust_score": 50,
            "trust_tier": "SILVER",
            "profile_completion_rate": 20,
            "deal_completion_rate": 0,
            "successful_deals_count": 0,
            "dispute_rate": 0,
            "status": "INCOMPLETE",
        }
    try:
        row = await get_or_create_trust_profile(db, company_id=company.id, portal_key="cebu")
    except CommerceTrustError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(row)
    return _trust_profile_as_admin_legacy(row, company)


@router.get("/addresses")
async def legacy_list_addresses(db: DB, user: CurrentUser, address_type: str | None = None):
    stmt = (
        select(Address)
        .where(Address.user_id == user.id, Address.status == "ACTIVE")
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    if address_type:
        stmt = stmt.where(Address.address_type == address_type.upper())
    rows = list((await db.execute(stmt)).scalars())
    return [_address_as_legacy(row) for row in rows]


@router.post("/addresses", status_code=201)
async def legacy_create_address(data: dict, db: DB, user: CurrentUser):
    payload = _address_payload(data, user)
    if payload["is_default"]:
        await _unset_address_defaults(db, user.id, payload["address_type"])
    row = Address(user_id=user.id, company_id=user.company_id, status="ACTIVE", **payload)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _address_as_legacy(row)


@router.patch("/addresses/{address_id}")
async def legacy_update_address(address_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row = await db.get(Address, address_id)
    if row is None or row.user_id != user.id or row.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Address not found")
    payload = _address_payload({**_address_as_legacy(row), **data}, user)
    if payload["is_default"]:
        await _unset_address_defaults(db, user.id, row.address_type)
    for key, value in payload.items():
        setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _address_as_legacy(row)


@router.post("/addresses/{address_id}/set-default")
async def legacy_set_default_address(address_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(Address, address_id)
    if row is None or row.user_id != user.id or row.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Address not found")
    await _unset_address_defaults(db, user.id, row.address_type)
    row.is_default = True
    await db.commit()
    await db.refresh(row)
    return _address_as_legacy(row)


@router.delete("/addresses/{address_id}", status_code=204)
async def legacy_delete_address(address_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(Address, address_id)
    if row is None or row.user_id != user.id or row.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Address not found")
    row.status = "DELETED"
    await db.commit()
    return None


@router.patch("/users/me")
async def legacy_update_me(data: UserUpdate, db: DB, user: CurrentUser):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return _user_as_legacy(user)


@router.patch("/users/me/password")
async def legacy_change_my_password(data: dict, db: DB, user: CurrentUser):
    current_password = data.get("current_password") or data.get("old_password")
    new_password = data.get("new_password") or data.get("password")
    if not current_password or not new_password:
        raise HTTPException(status_code=422, detail="current_password and new_password are required")
    if len(str(new_password)) < 8:
        raise HTTPException(status_code=422, detail="New password must be at least 8 characters")
    if not verify_password(str(current_password), user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(str(new_password))
    await db.commit()
    return {"message": "Password changed successfully"}


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
        row = NotificationPreference(
            user_id=user.id,
            company_id=user.company_id,
            email=user.email,
            email_enabled=True,
            telegram_enabled=True,
        )
        db.add(row)
        await db.flush()
    else:
        apply_notification_preference_defaults(row, email=user.email)
    return row


def _notification_preference_as_legacy(row: NotificationPreference) -> dict:
    return {
        "telegram_enabled": row.telegram_enabled,
        "email_enabled": row.email_enabled,
        "whatsapp_enabled": row.whatsapp_enabled,
        "viber_enabled": row.viber_enabled,
        "telegram_chat_id": row.telegram_chat_id,
        "email": row.email,
        "whatsapp_number": row.whatsapp_number,
        "viber_number": row.viber_number,
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
    normalized = normalize_country_code(country)
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
    currency: str = Query(default="EUR"),
):
    normalized_currency = (currency or "EUR").upper()
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


async def _require_wallet_payments_enabled(db: DB) -> None:
    """AISLOS hard rule: records-first, no custody. Wallet top-up/pay stays 409
    unless an admin explicitly re-enables wallet_payments_enabled (legacy mode)."""
    market_cfg = await get_integration_config(db, "market")
    if not market_cfg.get("wallet_payments_enabled", False):
        raise HTTPException(
            status_code=409,
            detail=(
                "This platform runs in direct-payment mode and does not hold customer funds. "
                "Pay the supplier directly and record the payment on the order."
            ),
        )


@router.post("/wallets/deposits", status_code=201)
async def legacy_create_wallet_deposit(
    data: LegacyWalletDepositCreate,
    db: DB,
    user: CurrentUser,
):
    await _require_wallet_payments_enabled(db)
    if data.amount_minor <= 0:
        raise HTTPException(status_code=422, detail="amount_minor must be greater than 0")
    currency = (data.currency or "EUR").upper()
    wallet = await get_or_create_wallet(db, user.id, currency)
    fields = data.model_dump()
    fields["currency"] = currency
    fields["network"] = (fields.get("network") or "LOCAL_BANK").upper()
    fields["provider"] = fields.get("provider") or "MANUAL_BANK"
    fields["payment_method"] = fields.get("payment_method") or "BANK_TRANSFER"
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
    market_mode: str | None = None,
    origin_country: str | None = None,
    country: str | None = None,
    city: str | None = None,
    budget_min_minor: int | None = Query(default=None, ge=0),
    budget_max_minor: int | None = Query(default=None, ge=0),
    budget_currency: str | None = None,
    account_type: str | None = None,
    verified_only: bool = False,
    listing_origin: str | None = None,
    sort: str = Query(default="rank"),
):
    stmt = select(SupplierListing, Company.name.label("company_name")).join(
        Company,
        Company.id == SupplierListing.company_id,
        isouter=True,
    ).where(SupplierListing.status == "active")
    if category_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_id)
    if keyword:
        term = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                SupplierListing.title.ilike(term),
                SupplierListing.attributes_json["description"].astext.ilike(term),
                Company.name.ilike(term),
            )
        )
    normalized_mode = (market_mode or "").strip().upper()
    if normalized_mode in {"B2B", "B2C"}:
        mode_expr = func.upper(func.coalesce(SupplierListing.attributes_json["market_mode"].astext, "B2B"))
        stmt = stmt.where(mode_expr.in_([normalized_mode, "BOTH"]))
    elif normalized_mode == "BOTH":
        stmt = stmt.where(func.upper(SupplierListing.attributes_json["market_mode"].astext) == "BOTH")

    origin_aliases = _country_alias_values(origin_country)
    if origin_aliases:
        listing_origin = func.upper(func.coalesce(SupplierListing.attributes_json["origin_country"].astext, ""))
        stmt = stmt.where(listing_origin.in_(origin_aliases))

    country_aliases = _country_alias_values(country)
    if country_aliases:
        company_country = func.upper(func.coalesce(Company.country, ""))
        listing_origin = func.upper(func.coalesce(SupplierListing.attributes_json["origin_country"].astext, ""))
        stmt = stmt.where(
            or_(
                company_country.in_(country_aliases),
                listing_origin.in_(country_aliases),
                company_country == "",
                listing_origin == "",
            )
        )
    if city:
        company_city = func.coalesce(Company.city, "")
        stmt = stmt.where(or_(company_city == "", Company.city.ilike(f"%{city.strip()}%")))
    if budget_min_minor is not None:
        stmt = stmt.where(SupplierListing.price_minor >= budget_min_minor)
    if budget_max_minor is not None:
        stmt = stmt.where(SupplierListing.price_minor <= budget_max_minor)
    normalized_budget_currency = (budget_currency or "").strip().upper()[:3]
    if normalized_budget_currency and (budget_min_minor is not None or budget_max_minor is not None):
        stmt = stmt.where(func.upper(SupplierListing.currency) == normalized_budget_currency)
    normalized_account_type = (account_type or "").strip().upper()
    if normalized_account_type == "INDIVIDUAL":
        stmt = stmt.where(func.lower(Company.type).in_(["individual", "freelancer"]))
    elif normalized_account_type == "BUSINESS":
        stmt = stmt.where(or_(Company.type.is_(None), ~func.lower(Company.type).in_(["individual", "freelancer"])))
    if verified_only:
        stmt = stmt.where(func.lower(Company.verification_status) == "verified")
    normalized_listing_origin = (listing_origin or "").strip().lower()
    if normalized_listing_origin and normalized_listing_origin != "all":
        stmt = stmt.where(
            func.lower(func.coalesce(SupplierListing.attributes_json["listing_origin"].astext, "new"))
            == normalized_listing_origin
        )

    offset = (page - 1) * page_size
    # Official listings first (admin-curated via attributes_json.official),
    # then newest — ordering must happen before pagination.
    official_first = (SupplierListing.attributes_json["official"].astext == "true").desc().nullslast()
    sort_key = (sort or "rank").strip().lower()
    if sort_key == "price_asc":
        order_by = [official_first, SupplierListing.price_minor.asc().nullslast(), SupplierListing.created_at.desc()]
    elif sort_key == "price_desc":
        order_by = [official_first, SupplierListing.price_minor.desc().nullslast(), SupplierListing.created_at.desc()]
    elif sort_key == "newest":
        order_by = [SupplierListing.created_at.desc()]
    else:
        order_by = [official_first, SupplierListing.created_at.desc()]
    total = int(
        (
            await db.execute(
                select(func.count()).select_from(stmt.with_only_columns(SupplierListing.id).order_by(None).subquery())
            )
        ).scalar()
        or 0
    )
    rows = list((await db.execute(
        stmt.order_by(*order_by).offset(offset).limit(page_size)
    )).all())
    category_ids = {listing.category_schema_id for listing, _ in rows if listing.category_schema_id}
    category_names = {}
    if category_ids:
        category_rows = list(
            (
                await db.execute(select(TradeCategorySchema).where(TradeCategorySchema.id.in_(category_ids)))
            ).scalars()
        )
        category_names = {row.id: row.name for row in category_rows}
    items = []
    for listing, company_name in rows:
        # attributes_json is untrusted legacy data — some rows carry arrays.
        attrs = listing.attributes_json if isinstance(listing.attributes_json, dict) else {}
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
                "listing_origin": attrs.get("listing_origin") or "new",
                "item_condition": attrs.get("item_condition") or "new",
                "warranty_left_months": attrs.get("warranty_left_months"),
                "warranty_note": attrs.get("warranty_note"),
                "view_count": attrs.get("view_count") or 0,
                "order_count": attrs.get("order_count") or 0,
                "status": "ACTIVE",
                "category_id": listing.category_schema_id,
                "category_name": category_names.get(listing.category_schema_id),
                "company_id": listing.company_id,
                "company_name": company_name,
                "company_trust_score": None,
                "is_sponsored": False,
                "is_official": bool(attrs.get("official")),
                "created_at": listing.created_at,
            }
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (offset + len(items)) < total,
    }


@router.get("/marketplace/filters")
async def legacy_marketplace_filters(db: DB):
    categories = list(
        (
            await db.execute(
                select(TradeCategorySchema)
                .where(TradeCategorySchema.status == "active")
                .order_by(TradeCategorySchema.name.asc())
            )
        ).scalars()
    )
    count_rows = list(
        (
            await db.execute(
                select(SupplierListing.category_schema_id, func.count(SupplierListing.id))
                .where(SupplierListing.status == "active")
                .group_by(SupplierListing.category_schema_id)
            )
        ).all()
    )
    category_counts = {category_id: int(count or 0) for category_id, count in count_rows if category_id}

    country_rows = list(
        (
            await db.execute(
                select(SupplierListing.attributes_json, Company.country)
                .join(Company, Company.id == SupplierListing.company_id, isouter=True)
                .where(SupplierListing.status == "active")
            )
        ).all()
    )
    origin_countries: set[str] = set()
    for attrs, company_country in country_rows:
        if isinstance(attrs, dict) and attrs.get("origin_country"):
            origin_countries.add(str(attrs["origin_country"]).strip())
        if company_country:
            origin_countries.add(str(company_country).strip())

    category_payload = []
    for row in categories:
        payload = _category_as_legacy(row)
        payload["item_count"] = category_counts.get(row.id, 0)
        category_payload.append(payload)

    return {
        "categories": category_payload,
        "market_modes": ["B2B", "B2C", "BOTH"],
        "sort_options": ["newest", "price_asc", "price_desc"],
        "currencies": ["EUR", "RSD", "PLN", "PHP", "USD"],
        "origin_countries": sorted(country for country in origin_countries if country),
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
    attrs = listing.attributes_json if isinstance(listing.attributes_json, dict) else {}
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
        "is_official": bool(attrs.get("official")),
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
        currency=str(data.get("currency") or "EUR").upper(),
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


@router.get("/admin/dashboard")
async def legacy_admin_dashboard(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    users_total = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    buyers_total = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role.in_(("buyer", "customer_user")))
        )
    ).scalar() or 0
    suppliers_total = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role.in_(("vendor", "service_partner")))
        )
    ).scalar() or 0
    active_intents = (
        await db.execute(
            select(func.count())
            .select_from(ProcurementRequest)
            .where(ProcurementRequest.status.in_(("published", "matching", "offer_received")))
        )
    ).scalar() or 0
    open_disputes = (
        await db.execute(
            select(func.count())
            .select_from(OrderDispute)
            .where(OrderDispute.status.in_(("open", "under_review")))
        )
    ).scalar() or 0
    pending_company_verifications = (
        await db.execute(
            select(func.count())
            .select_from(Company)
            .where(Company.verification_status.in_(("pending", "submitted", "needs_info")))
        )
    ).scalar() or 0
    orders_in_escrow = (
        await db.execute(
            select(func.count())
            .select_from(EscrowTransaction)
            .where(EscrowTransaction.status == "CAPTURED")
        )
    ).scalar() or 0
    escrow_held_minor = (
        await db.execute(
            select(func.coalesce(func.sum(EscrowTransaction.captured_amount_minor), 0))
            .where(EscrowTransaction.status == "CAPTURED")
        )
    ).scalar() or 0
    open_risk_flags = (
        await db.execute(
            select(func.count())
            .select_from(RiskFlag)
            .where(RiskFlag.status == "open")
        )
    ).scalar() or 0
    return {
        "users_total": users_total,
        "buyers_total": buyers_total,
        "suppliers_total": suppliers_total,
        "active_intents": active_intents,
        "open_disputes": open_disputes,
        "pending_company_verifications": pending_company_verifications,
        "orders_in_escrow": orders_in_escrow,
        "open_risk_flags": open_risk_flags,
        "escrow_held_minor": escrow_held_minor,
    }


@router.get("/admin/users")
async def legacy_admin_users(
    db: DB,
    user: CurrentUser,
    role: str | None = None,
    active: bool | None = None,
    limit: int = Query(default=200, ge=1, le=500),
):
    _require_legacy_admin(user)
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if role:
        requested = role.strip().upper()
        if requested in _LEGACY_STAFF_ROLE_TO_CORE:
            stmt = stmt.where(User.role == _core_staff_role(requested))
        else:
            stmt = stmt.where(User.role == requested.lower())
    if active is not None:
        stmt = stmt.where(User.is_active.is_(active))
    rows = list((await db.execute(stmt)).scalars())
    return [_user_as_legacy(row) for row in rows]


@router.post("/admin/users/{target_user_id}/status")
async def legacy_admin_update_user_status(
    target_user_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    _require_legacy_admin(user)
    status = _legacy_admin_status(str(data.get("status") or ""))
    target = await db.get(User, target_user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id and status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Admin cannot deactivate own account")
    if target.role == "super_admin" and user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin accounts")
    before = target.is_active
    target.is_active = status == "ACTIVE"
    if target.is_active:
        await sync_role_portal_access(db, user_id=target.id, role=target.role, company_id=target.company_id)
    else:
        await suspend_user_portal_access(db, user_id=target.id)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.user_status_changed",
        entity_type="user",
        entity_id=target.id,
        before=before,
        after=target.is_active,
        reason=data.get("reason_text") or data.get("reason_code"),
    )
    await db.commit()
    await db.refresh(target)
    return _user_as_legacy(target)


@router.get("/admin/staff")
async def legacy_admin_staff(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    allowed_roles = {role.value for role in STAFF_ROLES}
    rows = list(
        (
            await db.execute(
                select(User)
                .where(User.role.in_(allowed_roles))
                .order_by(User.created_at.desc())
            )
        ).scalars()
    )
    return [_user_as_legacy(row) for row in rows]


@router.post("/admin/staff/invite", status_code=201)
async def legacy_admin_invite_staff(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    core_role = _core_staff_role(str(data.get("role") or "ADMIN"))
    if core_role == "super_admin" and user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can invite a super admin")
    email = str(data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Valid email is required")
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    password = str(data.get("password") or "")
    password_reset_required = False
    if len(password) < 8:
        password = secrets.token_urlsafe(18)
        password_reset_required = True
    row = User(
        email=email,
        full_name=data.get("full_name"),
        role=core_role,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(row)
    await db.flush()
    await sync_role_portal_access(db, user_id=row.id, role=row.role, company_id=None)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.staff_invited",
        entity_type="user",
        entity_id=row.id,
        before=None,
        after=row.role,
        reason="Procurement Admin staff invite",
    )
    await db.commit()
    await db.refresh(row)
    return {**_user_as_legacy(row), "password_reset_required": password_reset_required}


@router.put("/admin/staff/{staff_id}/role")
async def legacy_admin_update_staff_role(
    staff_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    _require_legacy_admin(user)
    core_role = _core_staff_role(str(data.get("role") or ""))
    target = await db.get(User, staff_id)
    allowed_roles = {role.value for role in STAFF_ROLES}
    if target is None or target.role not in allowed_roles:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if target.id == user.id:
        raise HTTPException(status_code=409, detail="Admin cannot change own role")
    if (target.role == "super_admin" or core_role == "super_admin") and user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin roles")
    before = target.role
    target.role = core_role
    await sync_role_portal_access(db, user_id=target.id, role=target.role, company_id=target.company_id)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.staff_role_changed",
        entity_type="user",
        entity_id=target.id,
        before=before,
        after=target.role,
        reason=data.get("reason"),
    )
    await db.commit()
    await db.refresh(target)
    return _user_as_legacy(target)


@router.get("/admin/companies")
async def legacy_admin_companies(
    db: DB,
    user: CurrentUser,
    type: str | None = None,
    verification_status: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
):
    _require_legacy_admin(user)
    stmt = select(Company).order_by(Company.created_at.desc()).limit(limit)
    if type:
        stmt = stmt.where(Company.type == type)
    if verification_status:
        stmt = stmt.where(Company.verification_status == verification_status)
    rows = list((await db.execute(stmt)).scalars())
    return [_company_as_legacy(row) for row in rows]


@router.get("/admin/marketplace/items")
async def legacy_admin_marketplace_items(
    db: DB,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    status: str | None = None,
    market_mode: str | None = None,
    category_id: uuid.UUID | None = None,
):
    _require_legacy_admin(user)
    stmt = select(SupplierListing, Company.name.label("company_name")).join(
        Company,
        Company.id == SupplierListing.company_id,
        isouter=True,
    )
    if keyword:
        stmt = stmt.where(SupplierListing.title.ilike(f"%{keyword.strip()}%"))
    if category_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_id)
    if status:
        stmt = stmt.where(SupplierListing.status == _catalog_status_to_core(status))
    else:
        stmt = stmt.where(SupplierListing.status != "archived")
    rows = list((await db.execute(stmt.order_by(SupplierListing.created_at.desc()))).all())
    if market_mode:
        rows = [
            (listing, company_name)
            for listing, company_name in rows
            if (listing.attributes_json or {}).get("market_mode", "B2B").upper() == market_mode.upper()
        ]
    category_ids = {listing.category_schema_id for listing, _ in rows if listing.category_schema_id}
    categories = {}
    if category_ids:
        category_rows = list(
            (
                await db.execute(
                    select(TradeCategorySchema).where(TradeCategorySchema.id.in_(category_ids))
                )
            ).scalars()
        )
        categories = {row.id: row.name for row in category_rows}
    total = len(rows)
    offset = (page - 1) * page_size
    items = []
    for listing, company_name in rows[offset : offset + page_size]:
        data = _catalog_item_as_legacy(listing, company_name=company_name)
        data["category_name"] = categories.get(listing.category_schema_id)
        items.append(data)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": offset + page_size < total,
    }


@router.patch("/admin/marketplace/items/{item_id}")
async def legacy_admin_update_marketplace_item(item_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(SupplierListing, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    before = row.status
    if "status" in data:
        row.status = _catalog_status_to_core(data.get("status")) or row.status
    row.attributes_json = _catalog_attrs_from_payload(data, row.attributes_json)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.marketplace_item_updated",
        entity_type="supplier_listing",
        entity_id=row.id,
        before=before,
        after=row.status,
        reason=data.get("reason"),
    )
    await db.commit()
    await db.refresh(row)
    company = await db.get(Company, row.company_id)
    return _catalog_item_as_legacy(row, company_name=company.name if company else None)


@router.patch("/admin/companies/{company_id}/verification")
async def legacy_admin_update_company_verification(
    company_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    level: str | None = None,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    data = data or {}
    legacy_level = _legacy_verification_level(
        level or data.get("level") or data.get("verification_status"),
        strict=True,
    )
    row = await db.get(Company, company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    before = row.verification_status
    contact = dict(row.contact_info or {})
    contact["verification_level"] = legacy_level
    row.contact_info = contact
    row.verification_status = _verification_level_to_core_status(legacy_level, row.verification_status)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.company_verification_changed",
        entity_type="company",
        entity_id=row.id,
        before=before,
        after=row.verification_status,
        reason=data.get("reason"),
    )
    await db.commit()
    await db.refresh(row)
    return _company_as_legacy(row)


@router.patch("/admin/companies/{company_id}/status")
async def legacy_admin_update_company_status(
    company_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    data = data or {}
    legacy_status = _legacy_admin_status(status or data.get("status") or "")
    row = await db.get(Company, company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    contact = dict(row.contact_info or {})
    before = contact.get("operational_status", "ACTIVE")
    contact["operational_status"] = legacy_status
    contact["operational_status_reason"] = data.get("reason") or data.get("reason_text")
    row.contact_info = contact
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.company_status_changed",
        entity_type="company",
        entity_id=row.id,
        before=before,
        after=legacy_status,
        reason=contact.get("operational_status_reason"),
    )
    await db.commit()
    await db.refresh(row)
    return _company_as_legacy(row)


@router.get("/admin/orders")
async def legacy_admin_orders(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
):
    _require_legacy_admin(user)
    stmt = select(CommerceOrder).order_by(CommerceOrder.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(CommerceOrder.status == _legacy_order_status_to_core(status))
    rows = list((await db.execute(stmt)).scalars())
    return [await _order_as_legacy(db, row) for row in rows]


@router.post("/admin/orders/{order_id}/status")
async def legacy_admin_update_order_status(
    order_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    _require_legacy_admin(user)
    legacy_status = str(data.get("status") or "").strip().upper()
    core_status = _legacy_order_status_to_core(legacy_status)
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    before = row.status
    row.status = core_status
    if core_status == "completed" and row.completed_at is None:
        row.completed_at = datetime.now(timezone.utc)
    await _ensure_admin_order_delivery_marker(db, row, legacy_status, user)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.order_status_changed",
        entity_type="commerce_order",
        entity_id=row.id,
        before=before,
        after=row.status,
        reason=data.get("reason"),
    )
    await db.commit()
    await db.refresh(row)
    return await _order_as_legacy(db, row)


@router.get("/localization/config")
async def market_localization_config(db: DB):
    from app.api.v1.endpoints.localization import _localization_payload

    return await _localization_payload(db)


@router.get("/admin/settings")
async def legacy_admin_settings(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    await _ensure_legacy_admin_default_settings(db)
    rows = list(
        (
            await db.execute(
                select(PlatformSetting)
                .where(PlatformSetting.portal_key == "admin_cebu")
                .order_by(PlatformSetting.key.asc())
            )
        ).scalars()
    )
    return [_platform_setting_as_admin_legacy(row) for row in rows]


@router.put("/admin/settings/{key}")
async def legacy_admin_upsert_setting(key: str, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    normalized_key = key.strip()
    if not normalized_key:
        raise HTTPException(status_code=422, detail="Setting key is required")
    row = (
        await db.execute(
            select(PlatformSetting).where(
                PlatformSetting.portal_key == "admin_cebu",
                PlatformSetting.key == normalized_key,
            )
        )
    ).scalar_one_or_none()
    before = row.value_json if row else None
    if row is None:
        row = PlatformSetting(portal_key="admin_cebu", key=normalized_key, value_json={})
        db.add(row)
    value = data.get("value")
    row.value_json = {"value": value}
    row.description = data.get("description", row.description)
    row.updated_by = user.id
    if normalized_key == "DEMO_MODE":
        await set_demo_mode_enabled(db, str(value).lower() in {"true", "1", "yes", "on"})
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.platform_setting_updated",
        entity_type="platform_setting",
        entity_id=row.id,
        before=before,
        after=row.value_json,
        reason=normalized_key,
    )
    await db.commit()
    await db.refresh(row)
    return _platform_setting_as_admin_legacy(row)


@router.get("/admin/audit-logs")
async def legacy_admin_audit_logs(
    db: DB,
    user: CurrentUser,
    action: str | None = None,
    risk_level: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    _require_legacy_admin(user)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    rows = list((await db.execute(stmt)).scalars())
    actor_ids = [row.actor_user_id for row in rows if row.actor_user_id]
    actors: dict[uuid.UUID, User] = {}
    if actor_ids:
        actor_rows = list((await db.execute(select(User).where(User.id.in_(actor_ids)))).scalars())
        actors = {actor.id: actor for actor in actor_rows}
    items = [_audit_log_as_admin_legacy(row, actors.get(row.actor_user_id)) for row in rows]
    if risk_level:
        items = [item for item in items if item["risk_level"] == risk_level.upper()]
    return items


@router.get("/admin/notification-templates")
async def legacy_admin_notification_templates(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list(
        (
            await db.execute(
                select(NotificationTemplate)
                .where(NotificationTemplate.portal_key == "admin_cebu")
                .order_by(NotificationTemplate.template_key.asc(), NotificationTemplate.channel.asc())
            )
        ).scalars()
    )
    return [_notification_template_as_admin_legacy(row) for row in rows]


@router.put("/admin/notification-templates/{template_key}")
async def legacy_admin_upsert_notification_template(
    template_key: str,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    _require_legacy_admin(user)
    channel = str(data.get("channel") or "").strip().upper()
    language = str(data.get("language") or "en").strip() or "en"
    stmt = select(NotificationTemplate).where(
        NotificationTemplate.portal_key == "admin_cebu",
        NotificationTemplate.template_key == template_key,
    )
    if channel:
        stmt = stmt.where(NotificationTemplate.channel == channel)
    row = (await db.execute(stmt.order_by(NotificationTemplate.channel.asc()))).scalars().first()
    before = None
    if row is None:
        row = NotificationTemplate(
            portal_key="admin_cebu",
            template_key=template_key,
            channel=channel or "EMAIL",
            language=language,
            body=str(data.get("body") or ""),
            active=bool(data.get("active", True)),
        )
        db.add(row)
    else:
        before = {
            "subject": row.subject,
            "body": row.body,
            "active": row.active,
            "channel": row.channel,
        }
    if "subject" in data:
        row.subject = data.get("subject")
    if "body" in data:
        row.body = str(data.get("body") or "")
    if "active" in data:
        row.active = bool(data.get("active"))
    if channel:
        row.channel = channel
    row.language = language
    await db.flush()
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.notification_template_updated",
        entity_type="notification_template",
        entity_id=row.id,
        before=before,
        after={"subject": row.subject, "active": row.active, "channel": row.channel},
        reason=template_key,
    )
    await db.commit()
    await db.refresh(row)
    return _notification_template_as_admin_legacy(row)


@router.get("/admin/notifications")
async def legacy_admin_notifications(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    _require_legacy_admin(user)
    stmt = select(PortalNotification).order_by(PortalNotification.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(PortalNotification.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return [_portal_notification_as_admin_legacy(row) for row in rows]


@router.post("/admin/notifications/test", status_code=201)
async def legacy_admin_test_notification(
    db: DB,
    user: CurrentUser,
    channel: str | None = None,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    payload = data or {}
    normalized_channel = str(channel or payload.get("channel") or "IN_APP").upper()
    row = PortalNotification(
        user_id=user.id,
        portal_key="admin_cebu",
        domain="commerce",
        event_type="cebu.admin.test",
        title=payload.get("title") or f"AISLOS Market {normalized_channel} test",
        body=payload.get("body") or "This is a real in-app test notification from Procurement Admin.",
        link_path="/notifications",
        status="unread",
    )
    db.add(row)
    await db.flush()
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.notification_tested",
        entity_type="portal_notification",
        entity_id=row.id,
        before=None,
        after=normalized_channel,
        reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return {
        "message": f"Test notification queued for {normalized_channel}",
        "notification": _portal_notification_as_admin_legacy(row),
    }


@router.get("/admin/backups/schedules")
async def legacy_admin_backup_schedules(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(BackupSchedule).order_by(BackupSchedule.created_at.desc()))).scalars())
    return [_backup_schedule_as_admin_legacy(row) for row in rows]


@router.post("/admin/backups/schedules", status_code=201)
async def legacy_admin_create_backup_schedule(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    frequency = str(data.get("frequency") or "WEEKLY").upper()
    if frequency not in {"WEEKLY", "MONTHLY", "CUSTOM"}:
        raise HTTPException(status_code=422, detail="Invalid backup frequency")
    row = BackupSchedule(
        name=data.get("name") or f"{frequency.title()} procurement backup",
        frequency=frequency,
        cron_expr=data.get("cron_expr"),
        day_of_week=data.get("day_of_week"),
        day_of_month=data.get("day_of_month"),
        hour=int(data.get("hour") if data.get("hour") is not None else 2),
        minute=int(data.get("minute") if data.get("minute") is not None else 0),
        enabled=bool(data.get("enabled", True)),
        retention_count=int(data.get("retention_count") if data.get("retention_count") is not None else 10),
        retention_days=int(data.get("retention_days") if data.get("retention_days") is not None else 30),
        created_by=user.id,
    )
    row.next_run_at = next_run_at_for_schedule(row)
    db.add(row)
    await db.flush()
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.backup_schedule_created",
        entity_type="backup_schedule",
        entity_id=row.id,
        before=None,
        after=row.frequency,
        reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_schedule_as_admin_legacy(row)


@router.patch("/admin/backups/schedules/{schedule_id}")
async def legacy_admin_update_backup_schedule(
    schedule_id: uuid.UUID,
    data: dict,
    db: DB,
    user: CurrentUser,
):
    _require_legacy_admin(user)
    row = await db.get(BackupSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Backup schedule not found")
    before = _backup_schedule_as_admin_legacy(row)
    for key in (
        "name",
        "frequency",
        "cron_expr",
        "day_of_week",
        "day_of_month",
        "hour",
        "minute",
        "enabled",
        "retention_count",
        "retention_days",
    ):
        if key not in data:
            continue
        value = data[key]
        if key == "frequency":
            value = str(value).upper()
            if value not in {"WEEKLY", "MONTHLY", "CUSTOM"}:
                raise HTTPException(status_code=422, detail="Invalid backup frequency")
        setattr(row, key, value)
    row.next_run_at = next_run_at_for_schedule(row)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.backup_schedule_updated",
        entity_type="backup_schedule",
        entity_id=row.id,
        before={"enabled": before["enabled"], "frequency": before["frequency"]},
        after={"enabled": row.enabled, "frequency": row.frequency},
        reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_schedule_as_admin_legacy(row)


@router.delete("/admin/backups/schedules/{schedule_id}", status_code=204)
async def legacy_admin_delete_backup_schedule(schedule_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(BackupSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Backup schedule not found")
    before = _backup_schedule_as_admin_legacy(row)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.backup_schedule_deleted",
        entity_type="backup_schedule",
        entity_id=row.id,
        before={"enabled": before["enabled"], "frequency": before["frequency"]},
        after=None,
        reason=row.name,
    )
    await db.delete(row)
    await db.commit()


@router.post("/admin/backups/manual")
async def legacy_admin_manual_backup(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await create_backup_archive(db, created_by=user.id)
    await _append_legacy_admin_audit(
        db,
        user,
        action="cebu.compat.admin.backup_executed",
        entity_type="backup_job",
        entity_id=row.id,
        before=None,
        after=row.status,
        reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_job_as_admin_legacy(row)


@router.get("/admin/backups/jobs")
async def legacy_admin_backup_jobs(
    db: DB,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=500),
):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(BackupJob).order_by(BackupJob.created_at.desc()).limit(limit))).scalars())
    return [_backup_job_as_admin_legacy(row) for row in rows]


@router.get("/admin/backups/jobs/{job_id}/download")
async def legacy_admin_download_backup(job_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(BackupJob, job_id)
    if row is None or not row.archive_path:
        raise HTTPException(status_code=404, detail="Backup archive not found")
    path = Path(row.archive_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Backup archive not found")
    return FileResponse(path, media_type="application/zip", filename=path.name)


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


@router.get("/admin/intents")
async def legacy_admin_intents(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    _require_legacy_admin(user)
    stmt = select(ProcurementRequest).order_by(ProcurementRequest.created_at.desc()).limit(limit).offset(offset)
    statuses = _intent_status_to_core_filter(status)
    if statuses:
        stmt = stmt.where(ProcurementRequest.status.in_(statuses))
    rows = list((await db.execute(stmt)).scalars())
    return [await _intent_as_legacy_with_offer_count(db, row) for row in rows]


@router.get("/admin/intents/{intent_id}")
async def legacy_admin_get_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(ProcurementRequest, intent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Intent not found")
    return await _intent_as_legacy_with_offer_count(db, row)


@router.post("/admin/intents/{intent_id}/moderate")
async def legacy_admin_moderate_intent(intent_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(ProcurementRequest, intent_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Intent not found")
    action = str(data.get("action") or "").lower()
    reason = data.get("reason")
    before = row.status
    attrs = dict(row.attrs_json or {})
    events = list(attrs.get("moderation_events") or [])
    events.append(
        {
            "action": action,
            "reason": reason,
            "actor_user_id": str(user.id),
            "at": datetime.now(timezone.utc).isoformat(),
            "before": before,
        }
    )
    attrs["moderation_events"] = events[-50:]
    if action == "cancel":
        row.status = "cancelled"
    elif action == "expire":
        row.status = "expired"
    elif action == "restore":
        row.status = "published"
        attrs["moderation_flagged"] = False
    elif action == "flag":
        attrs["moderation_flagged"] = True
    elif action == "close":
        row.status = "closed"
    else:
        raise HTTPException(status_code=422, detail="Unsupported moderation action")
    row.attrs_json = attrs
    await db.commit()
    await db.refresh(row)
    data_out = await _intent_as_legacy_with_offer_count(db, row)
    data_out["before_status"] = _legacy_status(before, kind="intent")
    data_out["moderation_flagged"] = attrs.get("moderation_flagged", False)
    return data_out


@router.get("/admin/offers")
async def legacy_admin_offers(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    limit: int = Query(default=100, le=500),
):
    _require_legacy_admin(user)
    stmt = select(SupplierOffer).order_by(SupplierOffer.created_at.desc()).limit(limit)
    statuses = _offer_status_to_core_filter(status)
    if statuses:
        stmt = stmt.where(SupplierOffer.status.in_(statuses))
    rows = list((await db.execute(stmt)).scalars())
    return [_offer_as_legacy(row) for row in rows]


@router.get("/admin/offers/{offer_id}")
async def legacy_admin_get_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(SupplierOffer, offer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return _offer_as_legacy(row)


@router.post("/admin/offers/{offer_id}/remove")
async def legacy_admin_remove_offer(offer_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(SupplierOffer, offer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if row.status == "awarded":
        raise HTTPException(status_code=409, detail="Awarded offers cannot be removed")
    terms = dict(row.terms_json or {})
    events = list(terms.get("moderation_events") or [])
    events.append(
        {
            "action": "remove",
            "reason": data.get("reason"),
            "actor_user_id": str(user.id),
            "at": datetime.now(timezone.utc).isoformat(),
            "before": row.status,
        }
    )
    terms["moderation_events"] = events[-50:]
    row.terms_json = terms
    row.status = "rejected"
    await db.commit()
    await db.refresh(row)
    return _offer_as_legacy(row)


@router.get("/admin/disputes")
async def legacy_admin_disputes(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(OrderDispute).order_by(OrderDispute.created_at.desc()).limit(200)
    statuses = _dispute_status_to_core(status)
    if statuses:
        stmt = stmt.where(OrderDispute.status.in_(statuses))
    rows = list((await db.execute(stmt)).scalars())
    return [_dispute_as_legacy(row) for row in rows]


@router.get("/admin/disputes/{dispute_id}")
async def legacy_admin_get_dispute(dispute_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(OrderDispute, dispute_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return _dispute_as_legacy(row)


@router.post("/admin/disputes/{dispute_id}/request-evidence")
async def legacy_admin_request_dispute_evidence(
    dispute_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    from_party: str | None = None,
):
    _require_legacy_admin(user)
    row = await db.get(OrderDispute, dispute_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    before = row.status
    row.status = "under_review"
    data = dict(row.resolution_json or {})
    requests = list(data.get("evidence_requests") or [])
    requests.append(
        {
            "from_party": (from_party or "UNKNOWN").upper(),
            "requested_by": str(user.id),
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    data["evidence_requests"] = requests[-50:]
    row.resolution_json = data
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "status": _dispute_status_as_legacy(row.status), "before": before}


@router.post("/admin/disputes/{dispute_id}/resolve")
async def legacy_admin_resolve_dispute(
    dispute_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    decision: str | None = None,
    resolution: str | None = None,
    refund_amount_minor: int | None = None,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    body = data or {}
    decision_value = str(decision or body.get("decision") or body.get("resolution_code") or "").upper()
    resolution_text = resolution or body.get("resolution") or body.get("reason")
    refund_minor = refund_amount_minor if refund_amount_minor is not None else body.get("refund_amount_minor")
    if decision_value in {"BUYER_FAVOR", "FULL_REFUND", "PARTIAL_REFUND", "RESOLVED_REFUND"}:
        core_resolution = "resolved_buyer"
    elif decision_value in {"SUPPLIER_FAVOR", "RELEASE_TO_SUPPLIER", "RESOLVED_RELEASE"}:
        core_resolution = "resolved_supplier"
    elif decision_value in {"DISMISSED", "CLOSED", "SPLIT"}:
        core_resolution = "closed"
    else:
        raise HTTPException(status_code=422, detail="Unsupported dispute decision")
    try:
        row = await resolve_commerce_dispute(
            db,
            dispute_id,
            resolution=core_resolution,
            resolution_json={
                **(body.get("resolution_json") or {}),
                "decision": decision_value,
                "resolution": resolution_text,
                "admin_reason": resolution_text,
                "refund_amount_minor": refund_minor,
                "resolved_by_user_id": str(user.id),
            },
        )
        await db.commit()
        await db.refresh(row)
        return _dispute_as_legacy(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/admin/risk-flags")
async def legacy_admin_risk_flags(
    db: DB,
    user: CurrentUser,
    status: str | None = None,
    entity_type: str | None = None,
):
    _require_legacy_admin(user)
    stmt = select(RiskFlag).order_by(RiskFlag.created_at.desc()).limit(200)
    if entity_type:
        stmt = stmt.where(RiskFlag.subject_type == entity_type.lower())
    if status:
        core_status = _risk_status_to_core(status)
        stmt = stmt.where(RiskFlag.status == core_status)
    rows = list((await db.execute(stmt)).scalars())
    if status and status.upper() in {"IN_REVIEW", "MITIGATED", "FALSE_POSITIVE", "ACTION_TAKEN", "CLOSED"}:
        rows = [row for row in rows if _risk_status_as_legacy(row) == status.upper()]
    return [_risk_flag_as_legacy(row) for row in rows]


@router.post("/admin/risk-flags", status_code=201)
async def legacy_admin_create_risk_flag(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    subject_id = _uuid_or_none(data.get("subject_id") or data.get("entity_id"))
    if subject_id is None:
        raise HTTPException(status_code=422, detail="entity_id is required")
    legacy_status = str(data.get("status") or "OPEN").upper()
    severity = str(data.get("severity") or data.get("risk_level") or "MEDIUM").lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid risk level")
    row = RiskFlag(
        subject_type=str(data.get("subject_type") or data.get("entity_type") or "USER").lower(),
        subject_id=subject_id,
        company_id=_uuid_or_none(data.get("company_id")),
        reason_code=str(data.get("reason_code") or data.get("risk_type") or "OTHER").lower(),
        severity=severity,
        status=_risk_status_to_core(legacy_status),
        source_event="cebu.admin.manual",
        details_json={
            "description": data.get("description"),
            "legacy_status": legacy_status,
            **(data.get("details_json") or {}),
        },
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _risk_flag_as_legacy(row)


@router.post("/admin/risk-flags/{flag_id}/action")
async def legacy_admin_risk_flag_action(flag_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(RiskFlag, flag_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found")
    legacy_status = str(data.get("status") or "IN_REVIEW").upper()
    row.status = _risk_status_to_core(legacy_status)
    details = dict(row.details_json or {})
    details["legacy_status"] = legacy_status
    actions = list(details.get("admin_actions") or [])
    actions.append(
        {
            "action_taken": data.get("action_taken"),
            "status": legacy_status,
            "actor_user_id": str(user.id),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    details["admin_actions"] = actions[-50:]
    row.details_json = details
    if row.status != "open":
        row.resolved_at = datetime.now(timezone.utc)
        row.resolved_by_user_id = user.id
    await db.commit()
    await db.refresh(row)
    return _risk_flag_as_legacy(row)


@router.get("/admin/verification/queue")
async def legacy_admin_verification_queue(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    mapped_status = {"APPROVED": "APPROVED_BUSINESS", "NEEDS_INFO": "NEEDS_MORE_INFO"}.get(
        (status or "").upper(),
        status,
    )
    rows = await list_verification_queue(db, status=mapped_status)
    return [_verification_review_as_legacy(row) for row in rows]


@router.get("/admin/verification/{company_id}/documents")
async def legacy_admin_company_documents(company_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = await list_kyc_documents(db, company_id)
    return [_kyc_doc_as_legacy(row) for row in rows]


@router.post("/admin/verification/{company_id}/decide")
async def legacy_admin_decide_verification(company_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    company = await db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    review = (
        await db.execute(
            select(VerificationReview)
            .where(VerificationReview.company_id == company_id)
            .order_by(VerificationReview.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if review is None:
        review = VerificationReview(company_id=company_id, status="SUBMITTED")
        db.add(review)
        await db.flush()
    if review.status not in {"SUBMITTED", "IN_REVIEW"}:
        review.status = "SUBMITTED"
        await db.flush()
    legacy_decision = str(data.get("decision") or "").upper()
    decision_map = {
        "APPROVED": "APPROVE_BUSINESS",
        "APPROVE": "APPROVE_BUSINESS",
        "APPROVE_BASIC": "APPROVE_BASIC",
        "APPROVE_BUSINESS": "APPROVE_BUSINESS",
        "REJECTED": "REJECT",
        "REJECT": "REJECT",
        "NEEDS_INFO": "REQUEST_MORE_INFO",
        "REQUEST_MORE_INFO": "REQUEST_MORE_INFO",
        "ESCALATE_TO_RISK": "ESCALATE_TO_RISK",
    }
    decision = decision_map.get(legacy_decision)
    if not decision:
        raise HTTPException(status_code=422, detail="Unsupported verification decision")
    try:
        updated = await decide_verification(
            db,
            review.id,
            user.id,
            decision,
            data.get("decision_reason"),
            data.get("internal_note"),
            data.get("user_facing_note"),
        )
        if decision in {"APPROVE_BASIC", "APPROVE_BUSINESS"}:
            company.verification_status = "verified"
        elif decision == "REJECT":
            company.verification_status = "rejected"
        elif decision == "REQUEST_MORE_INFO":
            company.verification_status = "needs_info"
        await db.commit()
        await db.refresh(updated)
        return _verification_review_as_legacy(updated)
    except KYCError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/admin/kyc-media/files")
async def legacy_admin_kyc_media_files(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(CompanyDocument).order_by(CompanyDocument.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(CompanyDocument.status == status)
    rows = list((await db.execute(stmt)).scalars())
    out = []
    for row in rows:
        latest = (
            await db.execute(
                select(KYCAnalysisResult)
                .where(KYCAnalysisResult.document_id == row.id)
                .order_by(KYCAnalysisResult.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        out.append(_kyc_doc_as_legacy(row, latest_analysis=latest))
    return out


@router.get("/admin/kyc-media/files/{document_id}")
async def legacy_admin_kyc_media_file(document_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(CompanyDocument, document_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    analyses = list(
        (
            await db.execute(
                select(KYCAnalysisResult)
                .where(KYCAnalysisResult.document_id == row.id)
                .order_by(KYCAnalysisResult.created_at.desc())
            )
        ).scalars()
    )
    data = _kyc_doc_as_legacy(row, latest_analysis=analyses[0] if analyses else None)
    data["analyses"] = [
        {
            "id": item.id,
            "authenticity": item.authenticity,
            "confidence": item.confidence,
            "overall_risk_score": item.overall_risk_score,
            "recommended_action": item.recommended_action,
            "tamper_suspected": item.tamper_suspected,
            "photoshop_suspected": item.photoshop_suspected,
            "text_photo_consistency": item.text_photo_consistency,
            "detected_issues": item.detected_issues,
            "concerns": item.concerns,
            "created_at": item.created_at,
        }
        for item in analyses
    ]
    return data


@router.post("/admin/kyc-media/files/{document_id}/flag-risk")
async def legacy_admin_flag_kyc_media(document_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    document = await db.get(CompanyDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    note = data.get("note") or data.get("reason") or "KYC media flagged by admin"
    severity = str(data.get("severity") or "high").lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid risk severity")
    document.status = "REJECTED"
    document.reviewer_note = note
    document.reviewed_by = user.id
    document.reviewed_at = datetime.now(timezone.utc)
    flag = RiskFlag(
        subject_type="company_document",
        subject_id=document.id,
        company_id=document.company_id,
        reason_code="kyc_media_risk",
        severity=severity,
        status="open",
        source_event="cebu.admin.kyc_media",
        details_json={"description": note, "legacy_status": "OPEN", "document_type": document.doc_type},
    )
    db.add(flag)
    await db.commit()
    await db.refresh(document)
    await db.refresh(flag)
    return {"document_id": document.id, "status": document.status, "risk_flag_id": flag.id}


@router.post("/shipping/estimate")
async def legacy_shipping_estimate(data: dict, db: DB, user: CurrentUser):
    origin_country = _normalize_country_code(data.get("origin_country"))
    dest_country = _normalize_country_code(data.get("dest_country"))
    try:
        weight_kg = float(data.get("weight_kg") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="weight_kg must be a positive number") from None
    if weight_kg <= 0:
        raise HTTPException(status_code=422, detail="weight_kg must be a positive number")

    shipping_method = data.get("shipping_method")
    today = date.today()
    stmt = (
        select(ShippingRoute, ShippingRate)
        .join(ShippingRate, ShippingRate.route_id == ShippingRoute.id)
        .where(
            ShippingRoute.origin_country == origin_country,
            ShippingRoute.dest_country == dest_country,
            ShippingRoute.status == "ACTIVE",
            ShippingRate.status == "ACTIVE",
            ShippingRate.weight_min_kg <= weight_kg,
            ShippingRate.weight_max_kg >= weight_kg,
            ShippingRate.valid_from <= today,
            or_(ShippingRate.valid_until.is_(None), ShippingRate.valid_until >= today),
        )
    )
    if shipping_method:
        stmt = stmt.where(ShippingRoute.shipping_method == str(shipping_method).upper())
    rows = (await db.execute(stmt)).all()
    estimates = sorted(
        [_shipping_estimate_as_legacy(route, rate, weight_kg) for route, rate in rows],
        key=lambda item: (item["total_shipping_minor"], item["estimated_days_max"]),
    )
    return {
        "estimates": estimates,
        "items": estimates,
        "total": len(estimates),
        "origin_country": origin_country,
        "dest_country": dest_country,
        "weight_kg": weight_kg,
    }


@router.get("/admin/shipping/routes")
async def legacy_admin_shipping_routes(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(ShippingRoute).order_by(ShippingRoute.created_at.desc()))).scalars())
    return [_shipping_route_as_admin_legacy(row) for row in rows]


@router.post("/admin/shipping/routes", status_code=201)
async def legacy_admin_create_shipping_route(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = ShippingRoute(
        origin_country=str(data.get("origin_country") or "").upper(),
        origin_region=data.get("origin_region"),
        dest_country=str(data.get("dest_country") or "").upper(),
        dest_region=data.get("dest_region"),
        shipping_method=str(data.get("shipping_method") or "LOCAL_DELIVERY").upper(),
        description=data.get("description"),
        status=str(data.get("status") or "ACTIVE").upper(),
    )
    if not row.origin_country or not row.dest_country:
        raise HTTPException(status_code=422, detail="origin_country and dest_country are required")
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _shipping_route_as_admin_legacy(row)


@router.patch("/admin/shipping/routes/{route_id}")
async def legacy_admin_update_shipping_route(route_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(ShippingRoute, route_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Shipping route not found")
    for key in ("origin_country", "origin_region", "dest_country", "dest_region", "shipping_method", "description", "status"):
        if key in data:
            value = data[key]
            if key in {"origin_country", "dest_country", "shipping_method", "status"} and value is not None:
                value = str(value).upper()
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _shipping_route_as_admin_legacy(row)


@router.get("/admin/shipping/rates")
async def legacy_admin_shipping_rates(db: DB, user: CurrentUser, route_id: uuid.UUID | None = None):
    _require_legacy_admin(user)
    stmt = select(ShippingRate).order_by(ShippingRate.created_at.desc())
    if route_id:
        stmt = stmt.where(ShippingRate.route_id == route_id)
    rows = list((await db.execute(stmt)).scalars())
    return [_shipping_rate_as_admin_legacy(row) for row in rows]


@router.post("/admin/shipping/rates", status_code=201)
async def legacy_admin_create_shipping_rate(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    route_id = _uuid_or_none(data.get("route_id"))
    if route_id is None or await db.get(ShippingRoute, route_id) is None:
        raise HTTPException(status_code=404, detail="Shipping route not found")
    row = ShippingRate(
        route_id=route_id,
        weight_min_kg=float(data.get("weight_min_kg") or 0),
        weight_max_kg=float(data.get("weight_max_kg") or 99999),
        price_per_kg_minor=int(data.get("price_per_kg_minor") or 0),
        currency=str(data.get("currency") or "USD").upper(),
        min_charge_minor=int(data.get("min_charge_minor") or 0),
        volume_factor=float(data.get("volume_factor") or 5000),
        estimated_days_min=int(data.get("estimated_days_min") or 1),
        estimated_days_max=int(data.get("estimated_days_max") or 7),
        surcharges_json=data.get("surcharges_json"),
        valid_from=data.get("valid_from") or date.today(),
        valid_until=data.get("valid_until"),
        notes=data.get("notes"),
        status=str(data.get("status") or "ACTIVE").upper(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _shipping_rate_as_admin_legacy(row)


@router.patch("/admin/shipping/rates/{rate_id}")
async def legacy_admin_update_shipping_rate(rate_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(ShippingRate, rate_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Shipping rate not found")
    for key in (
        "weight_min_kg",
        "weight_max_kg",
        "price_per_kg_minor",
        "currency",
        "min_charge_minor",
        "volume_factor",
        "estimated_days_min",
        "estimated_days_max",
        "surcharges_json",
        "valid_from",
        "valid_until",
        "notes",
        "status",
    ):
        if key in data:
            value = data[key]
            if key in {"currency", "status"} and value is not None:
                value = str(value).upper()
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _shipping_rate_as_admin_legacy(row)


@router.get("/admin/shipping/statistics")
async def legacy_admin_shipping_statistics(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    routes = list((await db.execute(select(ShippingRoute))).scalars())
    rates = list((await db.execute(select(ShippingRate))).scalars())
    shipments = list((await db.execute(select(OrderShipping))).scalars())
    active_routes = [row for row in routes if row.status == "ACTIVE"]
    active_rates = [row for row in rates if row.status == "ACTIVE"]
    by_method: dict[str, int] = {}
    for row in routes:
        by_method[row.shipping_method] = by_method.get(row.shipping_method, 0) + 1
    route_labels = {
        row.id: f"{row.origin_country}->{row.dest_country} · {row.shipping_method}"
        for row in routes
    }
    rate_avgs = [
        {
            "route_id": row.route_id,
            "route_label": route_labels.get(row.route_id, str(row.route_id)),
            "avg_price_per_kg_minor": row.price_per_kg_minor,
            "avg_eta_max_days": row.estimated_days_max,
        }
        for row in rates
    ]
    avg_price = int(sum(row.price_per_kg_minor for row in rates) / len(rates)) if rates else 0
    return {
        "total_routes": len(routes),
        "active_routes": len(active_routes),
        "inactive_routes": len(routes) - len(active_routes),
        "total_rates": len(rates),
        "active_rates": len(active_rates),
        "inactive_rates": len(rates) - len(active_rates),
        "pending_shipments": sum(1 for row in shipments if row.status == "PENDING"),
        "shipped_orders": sum(1 for row in shipments if row.status in {"SHIPPED", "IN_TRANSIT"}),
        "delivered_orders": sum(1 for row in shipments if row.status == "DELIVERED"),
        "avg_price_per_kg_minor": avg_price,
        "last_route_updated_at": max((row.updated_at for row in routes if row.updated_at), default=None),
        "last_rate_updated_at": max((row.updated_at for row in rates if row.updated_at), default=None),
        "routes_by_method": by_method,
        "top_expensive_routes": sorted(rate_avgs, key=lambda item: item["avg_price_per_kg_minor"], reverse=True)[:5],
        "top_cheapest_routes": sorted(rate_avgs, key=lambda item: item["avg_price_per_kg_minor"])[:5],
        "top_slowest_routes": sorted(rate_avgs, key=lambda item: item["avg_eta_max_days"], reverse=True)[:5],
    }


@router.get("/admin/market-settings")
async def legacy_admin_get_market_settings(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    return await get_integration_config(db, "market")


@router.put("/admin/market-settings")
async def legacy_admin_update_market_settings(data: dict, db: DB, user: CurrentUser):
    """Payment-mode gate only; locales/regions are managed via /localization/config."""
    _require_legacy_admin(user)
    payload = {k: v for k, v in (data or {}).items() if k == "wallet_payments_enabled"}
    if not payload:
        raise HTTPException(status_code=422, detail="No valid settings provided")
    payload["wallet_payments_enabled"] = bool(payload["wallet_payments_enabled"])
    await upsert_integration_config(db, "market", config=payload, is_enabled=True)
    return await get_integration_config(db, "market")


@router.get("/admin/escrow")
async def legacy_admin_escrow_transactions(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(EscrowTransaction).order_by(EscrowTransaction.created_at.desc()).limit(200))).scalars())
    return [_admin_escrow_as_legacy(row) for row in rows]


@router.post("/admin/escrow/{escrow_id}/release")
async def legacy_admin_release_escrow(
    escrow_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    try:
        row = await release_escrow(db, escrow_id, (data or {}).get("amount_minor"))
        await db.commit()
        await db.refresh(row)
        return _admin_escrow_as_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/admin/escrow/{escrow_id}/refund")
async def legacy_admin_refund_escrow(
    escrow_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    body = data or {}
    try:
        row = await refund_escrow(
            db,
            escrow_id,
            body.get("amount_minor"),
            body.get("reason") or body.get("reason_text") or body.get("reason_code"),
        )
        await db.commit()
        await db.refresh(row)
        return _admin_escrow_as_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/admin/deposits")
async def legacy_admin_deposits(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(WalletDeposit).order_by(WalletDeposit.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(WalletDeposit.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return [_wallet_deposit_as_admin_legacy(row) for row in rows]


@router.post("/admin/deposits/{deposit_id}/verify")
async def legacy_admin_verify_deposit(
    deposit_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    try:
        row = await verify_deposit(db, deposit_id, user.id, (data or {}).get("admin_note"))
        await db.commit()
        await db.refresh(row)
        return _wallet_deposit_as_admin_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/admin/deposits/{deposit_id}/reject")
async def legacy_admin_reject_deposit(
    deposit_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    data: dict | None = None,
):
    _require_legacy_admin(user)
    try:
        row = await reject_deposit(db, deposit_id, user.id, (data or {}).get("admin_note"))
        await db.commit()
        await db.refresh(row)
        return _wallet_deposit_as_admin_legacy(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/admin/payouts")
async def legacy_admin_payouts(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(Payout).order_by(Payout.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(Payout.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return [_payout_as_admin_legacy(row) for row in rows]


@router.get("/admin/payment-events")
async def legacy_admin_payment_events(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(PaymentEvent).order_by(PaymentEvent.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(PaymentEvent.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return [_payment_event_as_admin_legacy(row) for row in rows]


@router.get("/admin/settlement-events")
async def legacy_admin_settlement_events(db: DB, user: CurrentUser, status: str | None = None):
    _require_legacy_admin(user)
    stmt = select(SettlementEvent).order_by(SettlementEvent.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(SettlementEvent.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return [_settlement_event_as_admin_legacy(row) for row in rows]


@router.get("/admin/payment-region-configs")
async def legacy_admin_payment_region_configs(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(RegionPaymentConfig).order_by(RegionPaymentConfig.country_code.asc()))).scalars())
    if not rows:
        return [_payment_region_config_as_legacy(None, "PH")]
    return [_payment_region_config_as_legacy(row, row.country_code) for row in rows]


@router.patch("/admin/payment-region-configs/{config_id}")
async def legacy_admin_update_payment_region_config(config_id: str, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = None
    try:
        row = await db.get(RegionPaymentConfig, uuid.UUID(config_id))
    except ValueError:
        row = (
            await db.execute(
                select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == config_id.upper()[:2])
            )
        ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Payment region config not found")
    for key in (
        "country_name",
        "local_currency",
        "default_settlement_currency",
        "default_transaction_mode",
        "enabled_currencies",
        "enabled_payment_methods",
        "cross_border_currencies",
        "force_usd_bridge",
        "allow_supplier_payout_currency",
        "is_active",
    ):
        if key in data:
            value = data[key]
            if key in {"local_currency", "default_settlement_currency", "default_transaction_mode"} and value is not None:
                value = str(value).upper()
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return _payment_region_config_as_legacy(row, row.country_code)


@router.get("/admin/regions")
async def legacy_admin_regions(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(Region).order_by(Region.created_at.desc()))).scalars())
    return [_region_as_admin_legacy(row) for row in rows]


@router.post("/admin/regions", status_code=201)
async def legacy_admin_create_region(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    slug = str(data.get("slug") or data.get("code") or data.get("name") or "").strip().lower()
    code = (data.get("code") or slug[:10]).upper()
    if not code:
        raise HTTPException(status_code=422, detail="slug or code is required")
    existing = (await db.execute(select(Region).where(Region.code == code))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Region code already exists")
    extra = {
        "slug": slug,
        "region_type": data.get("region_type") or "CITY",
        "country": data.get("country"),
        "city": data.get("city"),
        "center_lat": data.get("center_lat"),
        "center_lng": data.get("center_lng"),
        "default_radius_km": data.get("default_radius_km") or 15,
        "notes": data.get("notes"),
    }
    row = Region(
        code=code,
        name=data.get("name") or code,
        currency_code=str(data.get("currency_code") or ("PHP" if str(data.get("country") or "").lower() == "philippines" else "EUR")).upper(),
        language_codes_json=data.get("language_codes_json") or ["en"],
        tax_rules_json={"procurement_admin": extra},
        timezone=data.get("timezone") or "Asia/Manila",
        is_active=str(data.get("status") or "ACTIVE").upper() == "ACTIVE",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _region_as_admin_legacy(row)


@router.patch("/admin/regions/{region_id}")
async def legacy_admin_update_region(region_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await db.get(Region, region_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Region not found")
    if "name" in data:
        row.name = data["name"]
    if "currency_code" in data:
        row.currency_code = str(data["currency_code"]).upper()
    if "timezone" in data:
        row.timezone = data["timezone"]
    if "language_codes_json" in data:
        row.language_codes_json = data["language_codes_json"] or []
    if "status" in data:
        row.is_active = str(data["status"]).upper() == "ACTIVE"
    extra = _region_extra(row)
    for key in ("slug", "region_type", "country", "city", "center_lat", "center_lng", "default_radius_km", "notes"):
        if key in data:
            extra[key] = data[key]
    base = dict(row.tax_rules_json or {})
    base["procurement_admin"] = extra
    row.tax_rules_json = base
    await db.commit()
    await db.refresh(row)
    return _region_as_admin_legacy(row)


@router.get("/maps/coverage/estimate")
async def legacy_maps_coverage_estimate(
    db: DB,
    user: CurrentUser,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
):
    regions = list((await db.execute(select(Region).where(Region.is_active.is_(True)))).scalars())
    companies = list((await db.execute(select(Company).where(Company.verification_status != "rejected"))).scalars())
    active_names = [_region_as_admin_legacy(row)["name"] for row in regions]
    return {
        "lat": lat,
        "lng": lng,
        "radius_km": radius_km or 15,
        "matching_companies": len(companies),
        "matching_branches": len(companies),
        "active_regions": active_names,
    }


@router.get("/maps/reverse-geocode")
async def legacy_maps_reverse_geocode(lat: float = Query(...), lng: float = Query(...)):
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise HTTPException(status_code=422, detail="Invalid coordinates")
    nearest = min(
        [
            ("Cebu City, Philippines", 10.3157, 123.8854),
            ("Mandaue City, Philippines", 10.3236, 123.9223),
            ("Lapu-Lapu City, Philippines", 10.3103, 123.9494),
            ("Manila, Philippines", 14.5995, 120.9842),
            ("Davao City, Philippines", 7.0707, 125.6087),
        ],
        key=lambda item: abs(item[1] - lat) + abs(item[2] - lng),
    )
    label = f"{nearest[0]} ({lat:.4f}, {lng:.4f})"
    return {
        "formatted_address": label,
        "address": label,
        "lat": lat,
        "lng": lng,
        "provider": "ainerwise-local",
    }


@router.get("/admin/trust/users")
async def legacy_admin_trust_users(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    rows = list((await db.execute(select(TrustProfile).order_by(TrustProfile.updated_at.desc()).limit(200))).scalars())
    company_ids = [row.company_id for row in rows]
    companies = {}
    if company_ids:
        company_rows = list((await db.execute(select(Company).where(Company.id.in_(company_ids)))).scalars())
        companies = {row.id: row for row in company_rows}
    return [_trust_profile_as_admin_legacy(row, companies.get(row.company_id)) for row in rows]


@router.get("/ranking/profiles")
async def legacy_ranking_profiles(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    profiles = await _load_ranking_profiles(db)
    await db.commit()
    return profiles


@router.get("/admin/ranking/summary")
async def legacy_admin_ranking_summary(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    profiles = await _load_ranking_profiles(db)
    await db.commit()
    return {profile["id"]: profile["weights"] for profile in profiles}


@router.patch("/ranking/profiles/{profile_id}")
async def legacy_update_ranking_profile(profile_id: str, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    weights = data.get("weights")
    if not isinstance(weights, dict):
        raise HTTPException(status_code=422, detail="weights object is required")
    profiles = await _load_ranking_profiles(db)
    found = None
    for profile in profiles:
        if profile["id"] == profile_id:
            found = profile
            break
    if found is None:
        raise HTTPException(status_code=404, detail="Ranking profile not found")
    before = dict(found.get("weights") or {})
    found["weights"] = {str(key): max(0, min(float(value or 0), 1)) for key, value in weights.items()}
    found["updated_at"] = datetime.now(timezone.utc).isoformat()
    await _save_ranking_profiles(db, profiles)
    await _append_legacy_admin_audit(
        db,
        user,
        action="admin.ranking_profile.update",
        entity_type="ranking_profile",
        entity_id=None,
        before=before,
        after=found["weights"],
        reason=f"Updated ranking profile {profile_id}",
    )
    await db.commit()
    return _ranking_profile_as_legacy(found)


@router.delete("/ranking/profiles/{profile_id}", status_code=204)
async def legacy_delete_ranking_profile(profile_id: str, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    protected = {"default", "cost", "trust", "distance", "delivery"}
    if profile_id in protected:
        raise HTTPException(status_code=409, detail="Built-in ranking profiles cannot be deleted")
    profiles = await _load_ranking_profiles(db)
    kept = [profile for profile in profiles if profile["id"] != profile_id]
    if len(kept) == len(profiles):
        raise HTTPException(status_code=404, detail="Ranking profile not found")
    await _save_ranking_profiles(db, kept)
    await _append_legacy_admin_audit(
        db,
        user,
        action="admin.ranking_profile.delete",
        entity_type="ranking_profile",
        entity_id=None,
        before={"id": profile_id},
        after=None,
        reason=f"Deleted ranking profile {profile_id}",
    )
    await db.commit()
    return None


@router.post("/admin/trust/users/{entity_id}/recalculate")
async def legacy_admin_recalculate_trust_user(entity_id: uuid.UUID, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    company = await db.get(Company, entity_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = await get_or_create_trust_profile(db, company_id=company.id, portal_key="cebu")
    before = profile.trust_score
    score = 50 + min(profile.completed_orders * 5, 30)
    if profile.avg_rating is not None:
        score += int(float(profile.avg_rating) * 8)
    score -= profile.dispute_count * 10
    profile.trust_score = max(0, min(100, score))
    db.add(
        TrustScoreEvent(
            trust_profile_id=profile.id,
            event_type="ADMIN_RECALCULATED",
            score_delta=profile.trust_score - before,
            before_score=before,
            after_score=profile.trust_score,
            reason="Admin recalculated from procurement trust console",
            related_entity_type="COMPANY",
            related_entity_id=company.id,
            created_by=user.id,
        )
    )
    await db.commit()
    await db.refresh(profile)
    return _trust_profile_as_admin_legacy(profile, company)


@router.post("/admin/trust/{entity_type}/{entity_id}/adjust")
async def legacy_admin_adjust_trust(entity_type: str, entity_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    if entity_type.upper() not in {"SUPPLIER", "COMPANY"}:
        raise HTTPException(status_code=422, detail="Only supplier/company trust adjustment is supported")
    company = await db.get(Company, entity_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = await get_or_create_trust_profile(db, company_id=company.id, portal_key="cebu")
    delta = int(data.get("score_delta") or data.get("delta") or 0)
    before = profile.trust_score
    profile.trust_score = max(0, min(100, profile.trust_score + delta))
    metrics = dict(profile.metrics_json or {})
    adjustments = list(metrics.get("admin_adjustments") or [])
    adjustments.append(
        {
            "delta": delta,
            "reason": data.get("reason"),
            "actor_user_id": str(user.id),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    metrics["admin_adjustments"] = adjustments[-50:]
    profile.metrics_json = metrics
    db.add(
        TrustScoreEvent(
            trust_profile_id=profile.id,
            event_type="ADMIN_ADJUSTED",
            score_delta=profile.trust_score - before,
            before_score=before,
            after_score=profile.trust_score,
            reason=data.get("reason") or "Manual admin trust adjustment",
            related_entity_type="COMPANY",
            related_entity_id=company.id,
            created_by=user.id,
        )
    )
    await db.commit()
    await db.refresh(profile)
    return _trust_profile_as_admin_legacy(profile, company)


@router.get("/admin/backups/config")
async def legacy_admin_backup_config(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    schedules = list((await db.execute(select(BackupSchedule).order_by(BackupSchedule.created_at.asc()))).scalars())
    jobs = list((await db.execute(select(BackupJob).order_by(BackupJob.created_at.desc()).limit(100))).scalars())
    return _backup_config_from_rows(schedules, jobs)


@router.put("/admin/backups/config")
async def legacy_admin_update_backup_config(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    schedules = list((await db.execute(select(BackupSchedule).order_by(BackupSchedule.created_at.asc()))).scalars())
    if not schedules:
        schedule = BackupSchedule(
            name="Default Procurement Backup",
            frequency=data.get("default_frequency") or "WEEKLY",
            hour=2,
            minute=0,
            enabled=bool(data.get("enabled", True)),
            retention_count=int(data.get("backup_retention_count") or 10),
            retention_days=int(data.get("backup_retention_days") or 30),
            created_by=user.id,
        )
        db.add(schedule)
        schedules = [schedule]
    else:
        for schedule in schedules:
            if "enabled" in data:
                schedule.enabled = bool(data["enabled"])
            if "backup_retention_count" in data:
                schedule.retention_count = int(data["backup_retention_count"] or schedule.retention_count)
            if "backup_retention_days" in data:
                schedule.retention_days = int(data["backup_retention_days"] or schedule.retention_days)
    await db.commit()
    jobs = list((await db.execute(select(BackupJob).order_by(BackupJob.created_at.desc()).limit(100))).scalars())
    return {
        **_backup_config_from_rows(schedules, jobs),
        "backup_storage_path": data.get("backup_storage_path") or "/var/backups/ainerwise-procurement",
    }


@router.get("/admin/maps/config")
async def legacy_admin_maps_config(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await _get_integration_setting(db, "maps")
    config = dict(row.config_json or {}) if row else {}
    return {
        "provider": config.get("provider") or "LOCAL",
        "google_maps_api_key_masked": config.get("google_maps_api_key_masked") or "",
        "google_maps_region": config.get("google_maps_region") or "PH",
        "google_maps_language": config.get("google_maps_language") or "en",
        "maps_cache_ttl_seconds": int(config.get("maps_cache_ttl_seconds") or 86400),
        "maps_enabled": row.is_enabled if row else True,
        "updated_at": row.updated_at if row else None,
    }


@router.put("/admin/maps/config")
async def legacy_admin_update_maps_config(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    current = await _get_integration_setting(db, "maps")
    config = dict(current.config_json or {}) if current else {}
    if data.get("google_maps_api_key"):
        config["google_maps_api_key_masked"] = _mask_secret(str(data.get("google_maps_api_key")))
    for key in ("provider", "google_maps_region", "google_maps_language", "maps_cache_ttl_seconds"):
        if key in data:
            config[key] = data[key]
    enabled = bool(data.get("maps_enabled", True))
    row = await _upsert_integration_setting(db, "maps", enabled=enabled, config=config)
    await db.commit()
    await db.refresh(row)
    return await legacy_admin_maps_config(db, user)


@router.post("/admin/maps/test-connection")
async def legacy_admin_test_maps_connection(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    provider = str(data.get("provider") or "LOCAL").upper()
    if provider == "GOOGLE" and not data.get("google_maps_api_key"):
        existing = await _get_integration_setting(db, "maps")
        existing_config = existing.config_json if existing else {}
        if not (existing_config or {}).get("google_maps_api_key_masked"):
            return {
                "ok": False,
                "provider": provider,
                "error": "Google Maps API key is not configured",
            }
    return {
        "ok": True,
        "provider": provider,
        "region": data.get("google_maps_region") or "PH",
        "language": data.get("google_maps_language") or "en",
        "message": "Maps configuration accepted by AinerWise Core compatibility bridge",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/admin/ai/config")
async def legacy_admin_ai_config(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    row = await _get_integration_setting(db, "ai")
    config = dict(row.config_json or {}) if row else {}
    return {
        "enabled": row.is_enabled if row else True,
        "provider": config.get("provider") or "openai",
        "model": config.get("model") or "gpt-4o-mini",
        "kyc_enabled": config.get("kyc_enabled", True),
        "fraud_enabled": config.get("fraud_enabled", True),
        "moderation_enabled": config.get("moderation_enabled", True),
        "project_estimation_enabled": config.get("project_estimation_enabled", True),
        "multimodal_enabled": config.get("multimodal_enabled", False),
        "confidence_threshold": float(config.get("confidence_threshold") or 0.6),
        "updated_at": row.updated_at if row else None,
    }


@router.post("/admin/ai/test")
async def legacy_admin_test_ai(db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    config = await legacy_admin_ai_config(db, user)
    return {
        "ok": True,
        "provider": config["provider"],
        "model": config["model"],
        "kyc_enabled": config["kyc_enabled"],
        "message": "AI configuration is reachable through the AinerWise Core compatibility bridge",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


async def _run_kyc_analysis(db: DB, document_id: uuid.UUID, user: User) -> KYCAnalysisResult:
    document = await db.get(CompanyDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    config = await legacy_admin_ai_config(db, user)
    doc_type = (document.doc_type or "").upper()
    concerns = []
    detected_issues = []
    confidence = 0.82
    risk_score = 20.0
    authenticity = "AUTHENTIC"
    recommended_action = "APPROVE"
    if document.status == "REJECTED":
        confidence = 0.64
        risk_score = 70.0
        authenticity = "SUSPICIOUS"
        recommended_action = "MANUAL_REVIEW"
        concerns.append("Document was previously rejected by admin workflow")
    if doc_type not in {"BUSINESS_LICENSE", "SEC_REGISTRATION", "DTI_REGISTRATION", "TAX_CERTIFICATE", "MAYOR_PERMIT"}:
        confidence = min(confidence, 0.72)
        risk_score = max(risk_score, 45.0)
        authenticity = "SUSPICIOUS"
        recommended_action = "MANUAL_REVIEW"
        detected_issues.append("Document type is not in the preferred business-verification set")
    row = KYCAnalysisResult(
        company_id=document.company_id,
        document_id=document.id,
        analyzed_by=user.id,
        ai_provider=config["provider"],
        ai_model=config["model"],
        authenticity=authenticity,
        confidence=confidence,
        overall_risk_score=risk_score,
        recommended_action=recommended_action,
        tamper_suspected=False,
        photoshop_suspected=False,
        text_photo_consistency=True,
        extracted_fields={
            "doc_type": document.doc_type,
            "original_filename": document.original_filename,
            "source": "ainerwise_core_rule_analysis",
        },
        detected_issues=detected_issues,
        concerns=concerns,
        raw_result_json={
            "mode": "compatibility_rule_analysis",
            "file_url": document.file_url,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(row)
    await db.flush()
    return row


@router.post("/admin/ai/analyze-kyc-document")
async def legacy_admin_analyze_kyc_document(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    document_id = _uuid_or_none(data.get("document_id"))
    if document_id is None:
        raise HTTPException(status_code=422, detail="document_id is required")
    row = await _run_kyc_analysis(db, document_id, user)
    await db.commit()
    await db.refresh(row)
    return {
        "ok": True,
        "document_id": row.document_id,
        "analysis": _kyc_analysis_as_legacy(row),
    }


@router.post("/admin/ai/batch-analyze-kyc")
async def legacy_admin_batch_analyze_kyc(data: dict, db: DB, user: CurrentUser):
    _require_legacy_admin(user)
    document_ids = data.get("document_ids") or []
    if not isinstance(document_ids, list):
        raise HTTPException(status_code=422, detail="document_ids must be a list")
    results = []
    for raw_id in document_ids[:50]:
        try:
            document_id = _uuid_or_none(raw_id)
            if document_id is None:
                raise HTTPException(status_code=422, detail="document_id is required")
            row = await _run_kyc_analysis(db, document_id, user)
            results.append({"ok": True, "document_id": row.document_id, "analysis": _kyc_analysis_as_legacy(row)})
        except HTTPException as exc:
            results.append({"ok": False, "document_id": raw_id, "error": exc.detail})
    await db.commit()
    return {"ok": True, "results": results}


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
    return _intent_as_legacy(row, offer_count=0)


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
    return [await _intent_as_legacy_with_offer_count(db, row) for row in rows]


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
    return [await _intent_as_legacy_with_offer_count(db, row) for row in rows]


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
    return await _intent_as_legacy_with_offer_count(db, row)


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
    return await _intent_as_legacy_with_offer_count(db, row)


@router.post("/intents/{intent_id}/cancel")
async def legacy_cancel_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await _owned_intent(db, user, intent_id)
    if row.status not in ("draft", "published", "matching", "offer_received"):
        raise HTTPException(status_code=409, detail="Cannot cancel intent in current status")
    row.status = "cancelled"
    await db.commit()
    await db.refresh(row)
    return await _intent_as_legacy_with_offer_count(db, row)


@router.post("/intents/{intent_id}/publish")
async def legacy_publish_intent(intent_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_intent(db, user, intent_id)
    try:
        row = await publish_request(db, intent_id)
        await db.commit()
        await db.refresh(row)
        payload = await _intent_as_legacy_with_offer_count(db, row)
        payload["legacy_status"] = payload["status"]
        payload["status"] = row.status
        return payload
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
        currency=data.get("currency") or "EUR",
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


@router.get("/offers/{offer_id}")
async def legacy_get_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(SupplierOffer, offer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    await _legacy_offer_visible_to_user(db, row, user)
    return _offer_as_legacy(row)


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


@router.post("/orders", status_code=201)
async def legacy_create_direct_order(data: dict, db: DB, user: CurrentUser):
    listing_id = _uuid_or_none(data.get("catalog_item_id") or data.get("supplier_listing_id") or data.get("item_id"))
    if listing_id is None:
        raise HTTPException(status_code=422, detail="catalog_item_id is required")
    listing = await db.get(SupplierListing, listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Catalog item not found")
    if user.company_id and listing.company_id == user.company_id:
        raise HTTPException(status_code=409, detail="Cannot buy your own listing")
    qty = max(1, int(data.get("qty") or data.get("quantity") or 1))
    unit_price = int(listing.price_minor or 0)
    if unit_price <= 0:
        raise HTTPException(status_code=409, detail="Catalog item is not directly orderable")
    buyer_company = await _ensure_user_company(db, user, {}, default_type="buyer")
    try:
        workspace_id = await resolve_commerce_workspace(
            db,
            user=user,
            requested_workspace_id=_uuid_or_none(data.get("workspace_id")),
        )
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    total = unit_price * qty
    attrs = listing.attributes_json or {}
    request = ProcurementRequest(
        workspace_id=workspace_id,
        buyer_company_id=buyer_company.id,
        buyer_user_id=user.id,
        portal_key="cebu",
        category_schema_id=listing.category_schema_id,
        region_id=listing.region_id,
        title=f"Buy Now: {listing.title}",
        description=data.get("notes") or attrs.get("description"),
        requirements_json={
            "source": "marketplace_buy_now",
            "catalog_item_id": str(listing.id),
            "qty": qty,
            "unit_price_minor": unit_price,
            "currency": listing.currency,
        },
        attrs_json={
            "direct_order": True,
            "delivery_address_id": data.get("delivery_address_id"),
            "delivery_city": data.get("delivery_city"),
        },
        status="awarded",
        published_at=datetime.now(timezone.utc),
    )
    db.add(request)
    await db.flush()
    offer = SupplierOffer(
        workspace_id=workspace_id,
        procurement_request_id=request.id,
        supplier_listing_id=listing.id,
        supplier_company_id=listing.company_id,
        price_minor=total,
        currency=listing.currency,
        status="awarded",
        terms_json={
            "source": "marketplace_buy_now",
            "qty": qty,
            "unit_price_minor": unit_price,
            "notes": data.get("notes"),
        },
    )
    db.add(offer)
    await db.flush()
    order = CommerceOrder(
        workspace_id=workspace_id,
        procurement_request_id=request.id,
        winning_offer_id=offer.id,
        buyer_company_id=buyer_company.id,
        supplier_company_id=listing.company_id,
        status="confirmed",
        total_minor=total,
        currency=listing.currency,
        delivery_json={
            "qty": qty,
            "delivery_address_id": data.get("delivery_address_id"),
            "delivery_city": data.get("delivery_city"),
            "notes": data.get("notes"),
            "status": "PENDING",
        },
    )
    db.add(order)
    await db.flush()
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        portal_key="procurement",
        action="commerce.order.direct_create",
        entity_type="commerce_order",
        entity_id=order.id,
        before=None,
        after={
            "catalog_item_id": str(listing.id),
            "buyer_company_id": str(buyer_company.id),
            "supplier_company_id": str(listing.company_id),
            "total_minor": total,
            "currency": listing.currency,
        },
        reason="Legacy Marketplace Buy Now compatibility",
        source="cebu.compat.orders",
    )
    await db.commit()
    await db.refresh(order)
    return await _order_as_legacy(db, order)


@router.get("/orders/my")
async def legacy_my_orders(db: DB, user: CurrentUser):
    rows = await list_orders_for_user(db, user)
    return [await _order_as_legacy(db, row) for row in rows]


@router.get("/orders/{order_id}")
async def legacy_get_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    row, _party = await _require_legacy_order_party(db, user, order_id)
    return await _order_as_legacy(db, row)


@router.post("/orders/{order_id}/record-payment")
async def legacy_record_order_payment(
    order_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    data: dict | None = None,
):
    """Records-first direct payment: the buyer paid the supplier outside the
    platform and logs the reference here. No funds move through AISLOS."""
    row, _party = await _require_legacy_order_party(db, user, order_id, allowed={"buyer", "admin"})
    if row.status in ("completed", "cancelled", "disputed"):
        raise HTTPException(status_code=409, detail="Order cannot record payment in current status")
    if row.total_minor <= 0:
        raise HTTPException(status_code=409, detail="Order amount must be greater than zero")

    payload = data or {}
    reference = str(payload.get("reference") or "").strip()[:255] or None
    note = str(payload.get("note") or "").strip()[:2000] or None

    try:
        existing = await _order_escrow(db, row)
        if existing is not None:
            if existing.status in ("AUTH_HELD", "CAPTURED", "RELEASED"):
                return await _order_as_legacy(db, row)
            raise HTTPException(status_code=409, detail=f"Payment record already in {existing.status}")

        record = await create_escrow(
            db,
            order_id=row.id,
            auth_amount_minor=row.total_minor,
            currency=row.currency,
            provider="DIRECT_RECORDED",
        )
        record.status = "AUTH_HELD"
        record.provider_reference = reference
        record.raw_event_json = {
            "mode": "DIRECT",
            "recorded_by": str(user.id),
            "note": note,
        }
        await db.flush()
        await capture_escrow(db, record.id, row.total_minor)
        row.status = "confirmed"
        await db.commit()
        await db.refresh(row)
        return await _order_as_legacy(db, row)
    except HTTPException:
        await db.rollback()
        raise
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/pay-from-wallet")
async def legacy_pay_order_from_wallet(order_id: uuid.UUID, db: DB, user: CurrentUser):
    await _require_wallet_payments_enabled(db)
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
            # DIRECT_RECORDED = buyer paid the supplier directly; the platform
            # never held these funds, so there is nothing to credit internally.
            if escrow.provider != "DIRECT_RECORDED":
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
        evidence = data.get("evidence_json") or data.get("evidence") or data.get("attachments") or []
        if evidence and not isinstance(evidence, list):
            evidence = [evidence]
        dispute.resolution_json = {
            **(dispute.resolution_json or {}),
            "evidence_json": evidence,
            "requested_resolution": data.get("requested_resolution") or data.get("resolution"),
            "refund_amount_minor": data.get("refund_amount_minor"),
        }
        await db.commit()
        await db.refresh(dispute)
        return _dispute_as_legacy(dispute)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/disputes/my")
async def legacy_my_disputes(db: DB, user: CurrentUser, status: str | None = None):
    stmt = (
        select(OrderDispute)
        .join(CommerceOrder, CommerceOrder.id == OrderDispute.commerce_order_id)
        .order_by(OrderDispute.created_at.desc())
        .limit(100)
    )
    if user.role not in ("admin", "super_admin"):
        if not user.company_id:
            return []
        stmt = stmt.where(
            or_(
                CommerceOrder.buyer_company_id == user.company_id,
                CommerceOrder.supplier_company_id == user.company_id,
            )
        )
    statuses = _dispute_status_to_core(status)
    if statuses:
        stmt = stmt.where(OrderDispute.status.in_(statuses))
    rows = list((await db.execute(stmt)).scalars())
    return [_dispute_as_legacy(row) for row in rows]


@router.get("/disputes/{dispute_id}")
async def legacy_get_dispute(dispute_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(OrderDispute, dispute_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    order = await db.get(CommerceOrder, row.commerce_order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role not in ("admin", "super_admin") and not await user_is_order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this dispute")
    return _dispute_as_legacy(row)


@router.post("/disputes/{dispute_id}/evidence")
async def legacy_add_dispute_evidence(dispute_id: uuid.UUID, data: dict, db: DB, user: CurrentUser):
    row = await db.get(OrderDispute, dispute_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    order = await db.get(CommerceOrder, row.commerce_order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if user.role not in ("admin", "super_admin") and not await user_is_order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this dispute")
    evidence = _dispute_evidence(row)
    incoming = data.get("evidence") or data.get("evidence_json") or data.get("attachments") or data
    if not isinstance(incoming, list):
        incoming = [incoming]
    stamped = []
    for item in incoming:
        if isinstance(item, dict):
            payload = dict(item)
        else:
            payload = {"description": str(item)}
        payload.setdefault("submitted_by_user_id", str(user.id))
        payload.setdefault("submitted_by_role", _legacy_role(user.role))
        payload.setdefault("submitted_at", datetime.now(timezone.utc).isoformat())
        stamped.append(payload)
    info = dict(row.resolution_json or {})
    info["evidence_json"] = evidence + stamped
    row.resolution_json = info
    await db.commit()
    await db.refresh(row)
    return _dispute_as_legacy(row)


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

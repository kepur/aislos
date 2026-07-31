"""Historical Cebu data importer.

The importer is deliberately separate from the real-time legacy bridge. It is
admin-triggered, dependency ordered, idempotent, and records every migrated
legacy object without persisting legacy credentials.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.commerce import (
    CommerceMessage,
    CommerceOrder,
    CommerceThread,
    OrderDelivery,
    OrderDispute,
    ProcurementRequest,
    RiskFlag,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
    TransactionReview,
    TrustProfile,
    TrustScoreEvent,
)
from app.models.admin_config import AdminNote, NotificationTemplate, PlatformSetting
from app.models.audit import AuditLog
from app.models.backup import BackupJob, BackupSchedule
from app.models.commerce_geo import CompanyBranch, ServiceArea
from app.models.region import Region
from app.models.notification import PortalNotification
from app.modules.buyer_project.models import (
    BuyerProject,
    ProjectAIRun,
    ProjectFile,
    ProjectLineItem,
    ProjectMessage,
    ProjectMetricTemplate,
    ProjectMetricValue,
    ProjectPriceSnapshot,
    ProjectReport,
    ProjectReportVersion,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportChangeLog,
)
from app.modules.cebu_trade.models import (
    AdCampaign,
    Address,
    CurrencyConfig,
    EscrowTransaction,
    FeeLineItem,
    FeeRule,
    FxQuote,
    OrderShipping,
    Payout,
    PaymentEvent,
    PaymentMethodConfig,
    PaymentQuote,
    ProviderPaymentIntent,
    RegionPaymentConfig,
    ShippingRate,
    ShippingRoute,
    SettlementAdjustment,
    SettlementEvent,
    Wallet,
    WalletDeposit,
    WalletTransaction,
)
from app.modules.kyc.models import CompanyDocument, KYCAnalysisResult, VerificationReview
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun
from app.models.user import Company, User
from app.services.audit import append_audit_event
from app.services.legacy_identity import upsert_identity_mapping
from app.services.portal_access import get_default_workspace, sync_role_portal_access

ENTITY_ORDER = (
    "companies",
    "users",
    "branches",
    "regions",
    "service_areas",
    "categories",
    "catalog_items",
    "buyer_projects",
    "project_files",
    "project_ai_runs",
    "project_messages",
    "project_metric_templates",
    "project_metric_values",
    "intents",
    "project_line_items",
    "project_price_snapshots",
    "project_reports",
    "project_report_versions",
    "project_report_columns",
    "project_report_rows",
    "project_report_change_logs",
    "offers",
    "orders",
    "transaction_reviews",
    "wallets",
    "wallet_transactions",
    "wallet_deposits",
    "addresses",
    "shipping_routes",
    "shipping_rates",
    "order_shipping",
    "deliveries",
    "ad_campaigns",
    "escrow_transactions",
    "payouts",
    "disputes",
    "trust_profiles",
    "trust_score_events",
    "company_documents",
    "kyc_analysis_results",
    "verification_reviews",
    "risk_flags",
    "payment_events",
    "region_payment_configs",
    "currency_configs",
    "payment_method_configs",
    "fee_rules",
    "fx_quotes",
    "payment_quotes",
    "payment_intents",
    "fee_line_items",
    "settlement_events",
    "settlement_adjustments",
    "notifications",
    "notification_templates",
    "messages",
    "admin_notes",
    "platform_settings",
    "audit_logs",
    "backup_schedules",
    "backup_jobs",
)
RESERVED_BUNDLE_KEYS = frozenset({"batch_key", "source_system", "portal_key"})
SENSITIVE_KEYS = frozenset(
    {"password", "password_hash", "totp_secret", "token", "secret", "access_token", "refresh_token"}
)

USER_ROLE_MAP = {
    "BUYER": "buyer",
    "SUPPLIER_ADMIN": "vendor",
    "SUPPLIER_AGENT": "vendor",
    "ADMIN": "admin",
    "SUPER_ADMIN": "super_admin",
    "OPS_MANAGER": "project_manager",
    "FINANCE_OFFICER": "finance",
    "SUPPORT_AGENT": "sales_manager",
    "VERIFICATION_OFFICER": "admin",
    "DISPUTE_AGENT": "admin",
    "RISK_ANALYST": "admin",
    "AUDITOR": "admin",
}
REQUEST_STATUS_MAP = {
    "DRAFT": "draft",
    "ACTIVE": "published",
    "AWARDED": "awarded",
    "EXPIRED": "closed",
    "CANCELED": "cancelled",
    "CANCELLED": "cancelled",
}
OFFER_STATUS_MAP = {
    "SUBMITTED": "submitted",
    "WITHDRAWN": "withdrawn",
    "EXPIRED": "rejected",
    "AWARDED": "awarded",
    "REJECTED": "rejected",
}
ORDER_STATUS_MAP = {
    "CREATED": "pending",
    "AWAITING_PAYMENT": "pending",
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


class LegacyMigrationError(ValueError):
    pass


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items() if key.lower() not in SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _hash(value: Any) -> str:
    encoded = json.dumps(_sanitize(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _legacy_id(payload: dict, entity_type: str, index: int) -> str:
    value = payload.get("id") or payload.get("legacy_id")
    if value:
        return str(value)
    return f"missing-{entity_type}-{index}-{_hash(payload)[:12]}"


def _enum(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(getattr(value, "value", value)).upper()


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _date(value: Any) -> date | None:
    parsed = _datetime(value)
    if parsed:
        return parsed.date()
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _slug(value: Any, fallback: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return (clean or fallback.lower())[:120]


def _run_dict(row: LegacyMigrationRun, *, reused: bool = False) -> dict:
    return {
        "id": row.id,
        "source_system": row.source_system,
        "portal_key": row.portal_key,
        "batch_key": row.batch_key,
        "checksum": row.checksum,
        "status": row.status,
        "total_records": row.total_records,
        "succeeded_records": row.succeeded_records,
        "failed_records": row.failed_records,
        "counts": row.counts_json or {},
        "error_summary": row.error_summary,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "created_at": row.created_at,
        "reused": reused,
    }


def migration_run_dict(row: LegacyMigrationRun, *, reused: bool = False) -> dict:
    return _run_dict(row, reused=reused)


def migration_record_dict(row: LegacyMigrationRecord) -> dict:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "source_system": row.source_system,
        "entity_type": row.entity_type,
        "legacy_id": row.legacy_id,
        "core_entity_type": row.core_entity_type,
        "core_entity_id": row.core_entity_id,
        "payload_hash": row.payload_hash,
        "operation": row.operation,
        "status": row.status,
        "error_message": row.error_message,
        "details": row.details_json or {},
        "updated_at": row.updated_at,
    }


def _entity_groups(bundle: dict) -> tuple[str, ...]:
    known = [key for key in ENTITY_ORDER if isinstance(bundle.get(key), list)]
    unknown = sorted(
        key
        for key, value in bundle.items()
        if key not in RESERVED_BUNDLE_KEYS and key not in ENTITY_ORDER and isinstance(value, list)
    )
    return tuple(known + unknown)


async def _record(
    db: AsyncSession,
    *,
    run: LegacyMigrationRun,
    entity_type: str,
    legacy_id: str,
    payload_hash: str,
    source_payload: dict,
) -> LegacyMigrationRecord:
    row = (
        await db.execute(
            select(LegacyMigrationRecord).where(
                LegacyMigrationRecord.source_system == run.source_system,
                LegacyMigrationRecord.entity_type == entity_type,
                LegacyMigrationRecord.legacy_id == legacy_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = LegacyMigrationRecord(
            run_id=run.id,
            source_system=run.source_system,
            entity_type=entity_type,
            legacy_id=legacy_id,
            payload_hash=payload_hash,
        )
        db.add(row)
    else:
        row.run_id = run.id
        row.payload_hash = payload_hash
        row.status = "PENDING"
        row.error_message = None
    row.source_payload_json = _sanitize(source_payload)
    await db.flush()
    return row


async def _mapped_id(
    db: AsyncSession, source_system: str, entity_type: str, legacy_id: Any
) -> uuid.UUID | None:
    if not legacy_id:
        return None
    return (
        await db.execute(
            select(LegacyMigrationRecord.core_entity_id).where(
                LegacyMigrationRecord.source_system == source_system,
                LegacyMigrationRecord.entity_type == entity_type,
                LegacyMigrationRecord.legacy_id == str(legacy_id),
                LegacyMigrationRecord.status == "SUCCESS",
            )
        )
    ).scalar_one_or_none()


async def _existing_core(db: AsyncSession, record: LegacyMigrationRecord, model):
    if not record.core_entity_id:
        return None
    return await db.get(model, record.core_entity_id)


def _preserve_timestamps(row: Any, payload: dict) -> None:
    created_at = _datetime(payload.get("created_at"))
    updated_at = _datetime(payload.get("updated_at"))
    if created_at:
        row.created_at = created_at
    if updated_at:
        row.updated_at = updated_at


async def _import_company(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    row = await _existing_core(db, record, Company)
    operation = "updated" if row else "created"
    if row is None:
        row = Company(name=str(payload.get("name") or "Legacy Cebu company"), type="supplier")
        db.add(row)
    verification = _enum(payload.get("verification_level"), "UNVERIFIED")
    status = _enum(payload.get("status"), "PENDING")
    row.name = str(payload.get("name") or row.name)
    row.type = str(payload.get("type") or "supplier").lower()
    row.country = payload.get("country")
    row.city = payload.get("city")
    row.address = payload.get("address")
    row.verification_status = (
        "verified" if verification in {"BASIC", "BUSINESS", "TRUSTED"} and status == "ACTIVE"
        else status.lower()
    )
    row.contact_info = {
        **(row.contact_info or {}),
        "legacy_owner_user_id": str(payload.get("owner_user_id") or "") or None,
        "legacy_tax_id": payload.get("tax_id"),
        "legacy_kyb_notes": payload.get("kyb_notes"),
        "legacy_verification_level": verification,
        "legacy_status": status,
    }
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_user(
    db: AsyncSession,
    payload: dict,
    record: LegacyMigrationRecord,
    *,
    source_system: str,
    portal_key: str,
):
    email = str(payload.get("email") or "").strip().lower()
    if not email:
        raise LegacyMigrationError("user email is required")
    row = await _existing_core(db, record, User)
    if row is None:
        row = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    operation = "updated" if row else "created"
    role = USER_ROLE_MAP.get(_enum(payload.get("role"), "BUYER"), "buyer")
    if row is None:
        row = User(email=email, password_hash=hash_password(secrets.token_urlsafe(48)), role=role)
        db.add(row)
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        company_record = (
            await db.execute(
                select(LegacyMigrationRecord).where(
                    LegacyMigrationRecord.source_system == source_system,
                    LegacyMigrationRecord.entity_type == "companies",
                    LegacyMigrationRecord.details_json["legacy_owner_user_id"].astext == record.legacy_id,
                )
            )
        ).scalar_one_or_none()
        company_id = company_record.core_entity_id if company_record else None
    row.email = email
    row.phone = payload.get("phone")
    row.full_name = payload.get("full_name")
    row.role = role
    row.language = str(payload.get("language") or "en")[:10]
    row.country = payload.get("country")
    row.company_id = company_id
    row.is_active = _enum(payload.get("status"), "ACTIVE") in {"ACTIVE", "PENDING"}
    row.last_login_at = _datetime(payload.get("last_login_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    await upsert_identity_mapping(
        db,
        portal_key=portal_key,
        legacy_system=source_system,
        legacy_user_id=record.legacy_id,
        legacy_company_id=str(payload.get("company_id") or "") or None,
        core_user_id=row.id,
        core_company_id=row.company_id,
        metadata_json={
            "legacy_role": _enum(payload.get("role"), "BUYER"),
            "legacy_status": _enum(payload.get("status"), "ACTIVE"),
            "password_reset_required": True,
        },
    )
    await sync_role_portal_access(
        db,
        user_id=row.id,
        role=row.role,
        company_id=row.company_id,
    )
    return row, operation


async def _import_category(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    slug = _slug(payload.get("slug") or payload.get("name"), f"legacy-{record.legacy_id}")
    row = await _existing_core(db, record, TradeCategorySchema)
    if row is None:
        row = (
            await db.execute(select(TradeCategorySchema).where(TradeCategorySchema.slug == slug))
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = TradeCategorySchema(slug=slug, name=str(payload.get("name") or slug), schema_json={})
        db.add(row)
    row.slug = slug
    row.name = str(payload.get("name") or row.name)
    row.schema_json = {
        **(payload.get("schema_json") or {}),
        "_legacy": _sanitize(
            {
                "parent_id": payload.get("parent_id"),
                "name_zh": payload.get("name_zh"),
                "name_tl": payload.get("name_tl"),
                "level": payload.get("level"),
                "icon": payload.get("icon"),
                "description": payload.get("description"),
                "sort_order": payload.get("sort_order"),
                "typical_weight_kg": payload.get("typical_weight_kg"),
                "customs_hs_code": payload.get("customs_hs_code"),
            }
        ),
    }
    row.status = "active" if _enum(payload.get("status"), "ACTIVE") == "ACTIVE" else "inactive"
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_region(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    row = await _existing_core(db, record, Region)
    operation = "updated" if row else "created"
    if row is None:
        code = f"LEG{_hash(record.legacy_id)[:7].upper()}"
        row = Region(code=code, name=str(payload.get("name") or "Legacy Cebu region"))
        db.add(row)
    row.name = str(payload.get("name") or row.name)
    row.currency_code = str(payload.get("currency_code") or "PHP")[:10].upper()
    row.language_codes_json = payload.get("language_codes") or ["en"]
    row.tax_rules_json = {
        **(row.tax_rules_json or {}),
        "_legacy_geography": _sanitize(payload),
    }
    row.timezone = payload.get("timezone") or "Asia/Manila"
    row.is_active = _enum(payload.get("status"), "ACTIVE") == "ACTIVE"
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_branch(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        raise LegacyMigrationError("branch company is not migrated")
    row = await _existing_core(db, record, CompanyBranch)
    operation = "updated" if row else "created"
    if row is None:
        row = CompanyBranch(
            company_id=company_id,
            name=str(payload.get("name") or "Legacy branch"),
            country=str(payload.get("country") or "Philippines"),
            city=str(payload.get("city") or "Unknown"),
        )
        db.add(row)
    row.company_id = company_id
    row.name = str(payload.get("name") or row.name)
    row.country = str(payload.get("country") or row.country)
    row.city = str(payload.get("city") or row.city)
    row.address = payload.get("address")
    row.lat = payload.get("lat")
    row.lng = payload.get("lng")
    row.radius_km = int(payload.get("radius_km") or 30)
    row.delivery_methods_json = payload.get("delivery_methods") or payload.get("delivery_methods_json")
    row.status = _enum(payload.get("status"), "ACTIVE")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_service_area(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    region_id = await _mapped_id(db, source_system, "regions", payload.get("region_id"))
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    row = await _existing_core(db, record, ServiceArea)
    operation = "updated" if row else "created"
    if row is None:
        row = ServiceArea(name=str(payload.get("name") or "Legacy service area"))
        db.add(row)
    row.name = str(payload.get("name") or row.name)
    row.region_id = region_id
    row.company_id = company_id
    row.coverage_type = _enum(payload.get("coverage_type"), "RADIUS")
    row.center_lat = payload.get("center_lat")
    row.center_lng = payload.get("center_lng")
    row.radius_km = int(payload["radius_km"]) if payload.get("radius_km") is not None else None
    row.polygon_json = payload.get("polygon_json")
    row.status = _enum(payload.get("status"), "ACTIVE")
    row.notes = payload.get("notes")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_buyer_project(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    buyer_id = await _mapped_id(db, source_system, "users", payload.get("buyer_id"))
    if buyer_id is None:
        raise LegacyMigrationError("buyer project owner is not migrated")
    row = await _existing_core(db, record, BuyerProject)
    operation = "updated" if row else "created"
    if row is None:
        row = BuyerProject(buyer_id=buyer_id, title=str(payload.get("title") or "Legacy Cebu project"))
        db.add(row)
    row.buyer_id = buyer_id
    row.title = str(payload.get("title") or row.title)
    for key in ("project_type", "status", "country", "city", "area_unit", "currency", "quality_preference", "description", "ai_summary"):
        if payload.get(key) is not None:
            setattr(row, key, str(payload[key]))
    for key in ("lat", "lng", "area_value"):
        if payload.get(key) is not None:
            setattr(row, key, float(payload[key]))
    for key in ("budget_min", "budget_max"):
        if payload.get(key) is not None:
            setattr(row, key, int(payload[key]))
    row.scale_json = payload.get("scale_jsonb") or payload.get("scale_json")
    row.missing_questions_json = payload.get("missing_questions_jsonb") or payload.get("missing_questions_json")
    row.assumptions_json = payload.get("assumptions_jsonb") or payload.get("assumptions_json")
    row.risk_notes_json = payload.get("risk_notes_jsonb") or payload.get("risk_notes_json")
    row.acceptance_criteria_json = (
        payload.get("acceptance_criteria_jsonb") or payload.get("acceptance_criteria_json")
    )
    row.estimated_budget_json = payload.get("estimated_budget_jsonb") or payload.get("estimated_budget_json")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_file(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project file project is not migrated")
    row = await _existing_core(db, record, ProjectFile)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectFile(
            project_id=project_id,
            url=str(payload.get("url") or "legacy://missing"),
            file_name=str(payload.get("file_name") or "legacy-file"),
            content_type=str(payload.get("content_type") or "application/octet-stream"),
        )
        db.add(row)
    row.project_id = project_id
    for key, default in (
        ("url", "legacy://missing"),
        ("file_name", "legacy-file"),
        ("content_type", "application/octet-stream"),
        ("status", "UPLOADED"),
    ):
        setattr(row, key, str(payload.get(key) or default))
    row.file_size = int(payload.get("file_size") or 0)
    row.extracted_text = payload.get("extracted_text")
    row.vision_summary = payload.get("vision_summary")
    row.error_message = payload.get("error_message")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_ai_run(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project AI run project is not migrated")
    row = await _existing_core(db, record, ProjectAIRun)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectAIRun(project_id=project_id)
        db.add(row)
    row.project_id = project_id
    for key in ("provider", "model", "prompt_version", "raw_output", "error_message"):
        setattr(row, key, payload.get(key))
    row.status = _enum(payload.get("status"), "PENDING")
    row.input_snapshot_json = payload.get("input_snapshot_jsonb") or payload.get("input_snapshot_json")
    row.structured_output_json = payload.get("structured_output_jsonb") or payload.get("structured_output_json")
    row.token_usage_json = payload.get("token_usage_jsonb") or payload.get("token_usage_json")
    row.estimated_cost = payload.get("estimated_cost")
    row.started_at = _datetime(payload.get("started_at"))
    row.finished_at = _datetime(payload.get("finished_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_line_item(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project line item project is not migrated")
    row = await _existing_core(db, record, ProjectLineItem)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectLineItem(project_id=project_id, name=str(payload.get("name") or "Legacy line item"))
        db.add(row)
    row.project_id = project_id
    row.ai_run_id = await _mapped_id(db, source_system, "project_ai_runs", payload.get("ai_run_id"))
    row.category_id = await _mapped_id(db, source_system, "categories", payload.get("category_id"))
    row.procurement_request_id = await _mapped_id(db, source_system, "intents", payload.get("intent_id") or payload.get("procurement_request_id"))
    row.name = str(payload.get("name") or row.name)
    row.description = payload.get("description")
    row.specs_json = payload.get("specs_jsonb") or payload.get("specs_json")
    row.qty = float(payload.get("qty") or 1)
    row.unit = str(payload.get("unit") or "pcs")
    row.quality_tier = _enum(payload.get("quality_tier"), "MID_RANGE")
    row.estimated_unit_price = payload.get("estimated_unit_price")
    row.estimated_total_price = payload.get("estimated_total_price")
    row.currency = str(payload.get("currency") or "PHP")
    row.confidence = payload.get("confidence")
    row.sourcing_notes = payload.get("sourcing_notes")
    row.price_tiers_json = payload.get("price_tiers_jsonb") or payload.get("price_tiers_json")
    row.category_hint = payload.get("category_hint")
    row.include_in_estimate = bool(payload.get("include_in_estimate", True))
    row.source = _enum(payload.get("source"), "AI")
    row.status = _enum(payload.get("status"), "DRAFT")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_message(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project message project is not migrated")
    row = await _existing_core(db, record, ProjectMessage)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectMessage(project_id=project_id, content=str(payload.get("content") or ""))
        db.add(row)
    row.project_id = project_id
    row.role = _enum(payload.get("role"), "USER")
    row.workflow_node = payload.get("workflow_node")
    row.content = str(payload.get("content") or "")
    row.file_ids_json = payload.get("file_ids_jsonb") or payload.get("file_ids_json")
    row.structured_delta_json = payload.get("structured_delta_jsonb") or payload.get("structured_delta_json")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_metric_template(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord
):
    project_type = _enum(payload.get("project_type"), "GENERAL")
    key = str(payload.get("key") or f"legacy-{record.legacy_id}").strip().lower()
    row = await _existing_core(db, record, ProjectMetricTemplate)
    if row is None:
        row = (
            await db.execute(
                select(ProjectMetricTemplate).where(
                    ProjectMetricTemplate.project_type == project_type,
                    ProjectMetricTemplate.key == key,
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectMetricTemplate(project_type=project_type, key=key, label=key)
        db.add(row)
    row.project_type = project_type
    row.key = key
    row.label = str(payload.get("label") or key)
    row.data_type = str(payload.get("data_type") or "text")
    row.unit_options_json = payload.get("unit_options_jsonb") or payload.get("unit_options_json")
    row.required = bool(payload.get("required", False))
    row.sort_order = int(payload.get("sort_order") or 0)
    row.prompt = payload.get("prompt")
    row.active = bool(payload.get("active", True))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_metric_value(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project metric value project is not migrated")
    row = await _existing_core(db, record, ProjectMetricValue)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectMetricValue(project_id=project_id, key=str(payload.get("key") or "legacy"))
        db.add(row)
    row.project_id = project_id
    row.template_id = await _mapped_id(
        db, source_system, "project_metric_templates", payload.get("template_id")
    )
    row.key = str(payload.get("key") or row.key)
    row.label = payload.get("label")
    row.value_json = payload.get("value_jsonb") or payload.get("value_json")
    row.source = _enum(payload.get("source"), "USER")
    row.confidence = payload.get("confidence")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_price_snapshot(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    line_item_id = await _mapped_id(
        db, source_system, "project_line_items", payload.get("line_item_id")
    )
    if project_id is None or line_item_id is None:
        raise LegacyMigrationError("project price snapshot project or line item is not migrated")
    row = await _existing_core(db, record, ProjectPriceSnapshot)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectPriceSnapshot(project_id=project_id, line_item_id=line_item_id)
        db.add(row)
    row.project_id = project_id
    row.line_item_id = line_item_id
    row.currency = str(payload.get("currency") or "PHP")
    row.sample_count = int(payload.get("sample_count") or 0)
    for key in (
        "min_unit_price", "avg_unit_price", "median_unit_price",
        "p20_unit_price", "p80_unit_price",
    ):
        setattr(row, key, payload.get(key))
    row.price_tiers_json = payload.get("price_tiers_jsonb") or payload.get("price_tiers_json")
    row.samples_json = payload.get("samples_jsonb") or payload.get("samples_json")
    row.source_summary = payload.get("source_summary")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_report(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if project_id is None:
        raise LegacyMigrationError("project report project is not migrated")
    row = await _existing_core(db, record, ProjectReport)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectReport(project_id=project_id)
        db.add(row)
    row.project_id = project_id
    row.current_version_id = await _mapped_id(
        db, source_system, "project_report_versions", payload.get("current_version_id")
    )
    row.frozen_version_id = await _mapped_id(
        db, source_system, "project_report_versions", payload.get("frozen_version_id")
    )
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_report_version(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    report_id = await _mapped_id(db, source_system, "project_reports", payload.get("report_id"))
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if report_id is None or project_id is None:
        raise LegacyMigrationError("project report version report or project is not migrated")
    row = await _existing_core(db, record, ProjectReportVersion)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectReportVersion(report_id=report_id, project_id=project_id)
        db.add(row)
    row.report_id = report_id
    row.project_id = project_id
    row.version_number = int(payload.get("version_number") or 1)
    row.status = _enum(payload.get("status"), "DRAFT")
    row.source = str(payload.get("source") or "SYSTEM")
    row.title = payload.get("title")
    row.summary_json = payload.get("summary_jsonb") or payload.get("summary_json")
    row.totals_json = payload.get("totals_jsonb") or payload.get("totals_json")
    row.created_by = await _mapped_id(db, source_system, "users", payload.get("created_by"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_report_column(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    version_id = await _mapped_id(
        db, source_system, "project_report_versions", payload.get("report_version_id")
    )
    if version_id is None:
        raise LegacyMigrationError("project report column version is not migrated")
    row = await _existing_core(db, record, ProjectReportColumn)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectReportColumn(
            report_version_id=version_id,
            key=str(payload.get("key") or "legacy"),
            label=str(payload.get("label") or payload.get("key") or "Legacy"),
        )
        db.add(row)
    row.report_version_id = version_id
    row.key = str(payload.get("key") or row.key)
    row.label = str(payload.get("label") or row.label)
    row.data_type = str(payload.get("data_type") or "text")
    row.sort_order = int(payload.get("sort_order") or 0)
    row.editable = bool(payload.get("editable", True))
    row.system = bool(payload.get("system", False))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_report_row(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    version_id = await _mapped_id(
        db, source_system, "project_report_versions", payload.get("report_version_id")
    )
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    if version_id is None or project_id is None:
        raise LegacyMigrationError("project report row version or project is not migrated")
    row = await _existing_core(db, record, ProjectReportRow)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectReportRow(
            report_version_id=version_id,
            project_id=project_id,
            name=str(payload.get("name") or "Legacy report row"),
        )
        db.add(row)
    row.report_version_id = version_id
    row.project_id = project_id
    row.line_item_id = await _mapped_id(
        db, source_system, "project_line_items", payload.get("line_item_id")
    )
    row.category_id = await _mapped_id(db, source_system, "categories", payload.get("category_id"))
    row.name = str(payload.get("name") or row.name)
    row.description = payload.get("description")
    row.specs_json = payload.get("specs_jsonb") or payload.get("specs_json")
    row.qty = float(payload.get("qty") or 1)
    row.unit = str(payload.get("unit") or "pcs")
    row.currency = str(payload.get("currency") or "PHP")
    row.quality_tier = _enum(payload.get("quality_tier"), "MID_RANGE")
    row.selected_tier = _enum(payload.get("selected_tier"), "MID_RANGE")
    row.include_in_total = bool(payload.get("include_in_total", True))
    row.selected_for_purchase = bool(payload.get("selected_for_purchase", True))
    row.price_tiers_json = payload.get("price_tiers_jsonb") or payload.get("price_tiers_json")
    row.custom_values_json = payload.get("custom_values_jsonb") or payload.get("custom_values_json")
    row.match_status = _enum(payload.get("match_status"), "UNMATCHED")
    row.samples_json = payload.get("samples_jsonb") or payload.get("samples_json")
    row.price_source = _enum(payload.get("price_source"), "AI_ESTIMATE")
    row.notes = payload.get("notes")
    row.sort_order = int(payload.get("sort_order") or 0)
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_project_report_change_log(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    project_id = await _mapped_id(db, source_system, "buyer_projects", payload.get("project_id"))
    report_id = await _mapped_id(db, source_system, "project_reports", payload.get("report_id"))
    if project_id is None or report_id is None:
        raise LegacyMigrationError("project report change project or report is not migrated")
    row = await _existing_core(db, record, ProjectReportChangeLog)
    operation = "updated" if row else "created"
    if row is None:
        row = ProjectReportChangeLog(project_id=project_id, report_id=report_id)
        db.add(row)
    row.project_id = project_id
    row.report_id = report_id
    row.version_id = await _mapped_id(
        db, source_system, "project_report_versions", payload.get("version_id")
    )
    row.actor_id = await _mapped_id(db, source_system, "users", payload.get("actor_id"))
    row.change_type = _enum(payload.get("change_type"), "MANUAL_EDIT")
    row.status = _enum(payload.get("status"), "PENDING")
    row.user_message = payload.get("user_message")
    row.patch_json = payload.get("patch_jsonb") or payload.get("patch_json")
    row.before_json = payload.get("before_jsonb") or payload.get("before_json")
    row.after_json = payload.get("after_jsonb") or payload.get("after_json")
    row.error_message = payload.get("error_message")
    row.applied_at = _datetime(payload.get("applied_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_listing(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        raise LegacyMigrationError("listing company is not migrated")
    category_id = await _mapped_id(db, source_system, "categories", payload.get("category_id"))
    row = await _existing_core(db, record, SupplierListing)
    if row is None:
        row = (
            await db.execute(
                select(SupplierListing).where(
                    SupplierListing.legacy_catalog_item_id == record.legacy_id
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = SupplierListing(company_id=company_id, title=str(payload.get("title") or "Legacy item"))
        db.add(row)
    row.company_id = company_id
    row.category_schema_id = category_id
    row.title = str(payload.get("title") or row.title)
    row.attributes_json = {
        **(payload.get("attrs_jsonb") or payload.get("attributes_json") or {}),
        "_legacy": _sanitize(
            {
                "description": payload.get("description"),
                "branch_id": payload.get("branch_id"),
                "stock_qty": payload.get("stock_qty"),
                "unit": payload.get("unit"),
                "images": payload.get("images"),
                "tags": payload.get("tags"),
                "market_mode": payload.get("market_mode"),
                "min_order_qty": payload.get("min_order_qty"),
                "weight_kg": payload.get("weight_kg"),
                "origin_country": payload.get("origin_country"),
                "view_count": payload.get("view_count"),
                "order_count": payload.get("order_count"),
            }
        ),
    }
    row.price_minor = payload.get("price_minor")
    row.currency = str(payload.get("currency") or "PHP")[:3].upper()
    legacy_status = _enum(payload.get("status"), "DRAFT")
    row.status = "active" if legacy_status == "ACTIVE" else "draft" if legacy_status == "DRAFT" else "inactive"
    row.legacy_catalog_item_id = record.legacy_id
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_request(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str, portal_key: str
):
    buyer_user_id = await _mapped_id(db, source_system, "users", payload.get("buyer_id"))
    if buyer_user_id is None:
        raise LegacyMigrationError("intent buyer is not migrated")
    buyer = await db.get(User, buyer_user_id)
    category_id = await _mapped_id(db, source_system, "categories", payload.get("category_id"))
    row = await _existing_core(db, record, ProcurementRequest)
    if row is None:
        row = (
            await db.execute(
                select(ProcurementRequest).where(ProcurementRequest.legacy_request_id == record.legacy_id)
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = ProcurementRequest(title=str(payload.get("title") or "Legacy Cebu intent"))
        db.add(row)
    if row.workspace_id is None:
        workspace = await get_default_workspace(db)
        row.workspace_id = workspace.id if workspace else None
    row.buyer_user_id = buyer_user_id
    row.buyer_company_id = buyer.company_id if buyer else None
    row.portal_key = portal_key
    row.category_schema_id = category_id
    row.title = str(payload.get("title") or row.title)
    row.description = payload.get("notes")
    row.requirements_json = _sanitize(
        {
            "qty": payload.get("qty"),
            "unit": payload.get("unit"),
            "budget_min_minor": payload.get("budget_min_minor"),
            "budget_max_minor": payload.get("budget_max_minor"),
            "currency": payload.get("currency"),
            "country": payload.get("country"),
            "city": payload.get("city"),
            "lat": payload.get("lat"),
            "lng": payload.get("lng"),
            "radius_km": payload.get("radius_km"),
            "delivery_window_start": payload.get("delivery_window_start"),
            "delivery_window_end": payload.get("delivery_window_end"),
            "attachments": payload.get("attachments"),
            "expires_at": payload.get("expires_at"),
            "legacy_project_id": payload.get("project_id"),
            "legacy_project_line_item_id": payload.get("project_line_item_id"),
        }
    )
    row.attrs_json = payload.get("attrs_jsonb") or payload.get("attrs_json") or {}
    row.status = REQUEST_STATUS_MAP.get(_enum(payload.get("status"), "ACTIVE"), "draft")
    row.published_at = row.created_at if row.status in {"published", "matching", "offer_received", "awarded"} else None
    row.legacy_request_id = record.legacy_id
    _preserve_timestamps(row, payload)
    await db.flush()
    if row.published_at is None and row.status in {"published", "matching", "offer_received", "awarded"}:
        row.published_at = row.created_at
    return row, operation


async def _import_offer(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    request_id = await _mapped_id(db, source_system, "intents", payload.get("intent_id"))
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if request_id is None or company_id is None:
        raise LegacyMigrationError("offer intent or supplier company is not migrated")
    request = await db.get(ProcurementRequest, request_id)
    if request is None or request.workspace_id is None:
        raise LegacyMigrationError("offer intent has no Workspace")
    listing_id = await _mapped_id(db, source_system, "catalog_items", payload.get("catalog_item_id"))
    row = await _existing_core(db, record, SupplierOffer)
    if row is None:
        row = (
            await db.execute(select(SupplierOffer).where(SupplierOffer.legacy_offer_id == record.legacy_id))
        ).scalar_one_or_none()
    if row is None:
        row = (
            await db.execute(
                select(SupplierOffer).where(
                    SupplierOffer.procurement_request_id == request_id,
                    SupplierOffer.supplier_company_id == company_id,
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = SupplierOffer(
            workspace_id=request.workspace_id,
            procurement_request_id=request_id,
            supplier_company_id=company_id,
            price_minor=0,
        )
        db.add(row)
    row.procurement_request_id = request_id
    row.workspace_id = request.workspace_id
    row.supplier_company_id = company_id
    row.supplier_listing_id = listing_id
    row.price_minor = int(payload.get("total_price_minor") or payload.get("price_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP")[:3].upper()
    row.terms_json = _sanitize(
        {
            "unit_price_minor": payload.get("unit_price_minor"),
            "qty_available": payload.get("qty_available"),
            "delivery_fee_minor": payload.get("delivery_fee_minor"),
            "eta_date": payload.get("eta_date"),
            "warranty": payload.get("warranty"),
            "tier": payload.get("tier"),
            "stock_confidence": payload.get("stock_confidence"),
            "message": payload.get("message"),
            "expires_at": payload.get("expires_at"),
            "legacy_supplier_user_id": payload.get("supplier_user_id"),
            "legacy_branch_id": payload.get("branch_id"),
        }
    )
    row.status = OFFER_STATUS_MAP.get(_enum(payload.get("status"), "SUBMITTED"), "submitted")
    row.legacy_offer_id = record.legacy_id
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_order(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    request_id = await _mapped_id(db, source_system, "intents", payload.get("intent_id"))
    offer_id = await _mapped_id(db, source_system, "offers", payload.get("offer_id"))
    buyer_user_id = await _mapped_id(db, source_system, "users", payload.get("buyer_id"))
    supplier_company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if request_id is None:
        raise LegacyMigrationError("order intent is not migrated")
    buyer = await db.get(User, buyer_user_id) if buyer_user_id else None
    row = await _existing_core(db, record, CommerceOrder)
    if row is None:
        row = (
            await db.execute(select(CommerceOrder).where(CommerceOrder.legacy_order_id == record.legacy_id))
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = CommerceOrder(procurement_request_id=request_id, total_minor=0)
        db.add(row)
    request = await db.get(ProcurementRequest, request_id)
    row.workspace_id = request.workspace_id if request else row.workspace_id
    if row.workspace_id is None:
        workspace = await get_default_workspace(db)
        row.workspace_id = workspace.id if workspace else None
    row.procurement_request_id = request_id
    row.winning_offer_id = offer_id
    row.buyer_company_id = buyer.company_id if buyer else None
    row.supplier_company_id = supplier_company_id
    row.status = ORDER_STATUS_MAP.get(_enum(payload.get("status"), "CREATED"), "pending")
    row.total_minor = int(payload.get("total_amount_minor") or payload.get("total_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP")[:3].upper()
    row.delivery_json = _sanitize(
        {
            "legacy_branch_id": payload.get("branch_id"),
            "legacy_buyer_id": payload.get("buyer_id"),
            "legacy_status": _enum(payload.get("status"), "CREATED"),
        }
    )
    row.legacy_order_id = record.legacy_id
    if row.status == "completed":
        row.completed_at = _datetime(payload.get("updated_at")) or datetime.now(timezone.utc)
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _legacy_order_workspace(db: AsyncSession, order_id: uuid.UUID) -> uuid.UUID:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise LegacyMigrationError("order is not migrated")
    if order.workspace_id is None and order.procurement_request_id is not None:
        request = await db.get(ProcurementRequest, order.procurement_request_id)
        if request is not None and request.workspace_id is not None:
            order.workspace_id = request.workspace_id
            await db.flush()
    if order.workspace_id is None:
        workspace = await get_default_workspace(db)
        if workspace is not None:
            order.workspace_id = workspace.id
            await db.flush()
    if order.workspace_id is None:
        raise LegacyMigrationError("order has no Workspace")
    return order.workspace_id


async def _import_transaction_review(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    reviewer_id = await _mapped_id(db, source_system, "users", payload.get("reviewer_id"))
    if order_id is None or reviewer_id is None:
        raise LegacyMigrationError("transaction review order or reviewer is not migrated")
    order = await db.get(CommerceOrder, order_id)
    if order is None or order.workspace_id is None:
        raise LegacyMigrationError("transaction review order has no Workspace")
    supplier_company_id = await _mapped_id(
        db, source_system, "companies", payload.get("reviewee_company_id")
    )
    row = await _existing_core(db, record, TransactionReview)
    operation = "updated" if row else "created"
    if row is None:
        row = (
            await db.execute(
                select(TransactionReview).where(
                    TransactionReview.commerce_order_id == order_id,
                    TransactionReview.reviewer_user_id == reviewer_id,
                )
            )
        ).scalar_one_or_none()
        operation = "updated" if row else "created"
    if row is None:
        row = TransactionReview(
            workspace_id=order.workspace_id,
            commerce_order_id=order_id,
            reviewer_user_id=reviewer_id,
            rating=1,
        )
        db.add(row)
    row.commerce_order_id = order_id
    row.workspace_id = order.workspace_id
    row.reviewer_user_id = reviewer_id
    row.supplier_company_id = supplier_company_id or (order.supplier_company_id if order else None)
    row.rating = max(1, min(5, int(payload.get("overall_rating") or 1)))
    row.comment = payload.get("comment")
    row.status = "published"
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_wallet(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    owner_id = await _mapped_id(db, source_system, "users", payload.get("owner_user_id"))
    if owner_id is None:
        raise LegacyMigrationError("wallet owner is not migrated")
    row = await _existing_core(db, record, Wallet)
    operation = "updated" if row else "created"
    if row is None:
        row = Wallet(owner_user_id=owner_id, currency=str(payload.get("currency") or "USDT"))
        db.add(row)
    row.owner_user_id = owner_id
    row.currency = str(payload.get("currency") or "USDT")
    row.available_balance_minor = int(payload.get("available_balance_minor") or 0)
    row.locked_balance_minor = int(payload.get("locked_balance_minor") or 0)
    row.total_deposited_minor = int(payload.get("total_deposited_minor") or 0)
    row.status = _enum(payload.get("status"), "ACTIVE")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_wallet_transaction(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    wallet_id = await _mapped_id(db, source_system, "wallets", payload.get("wallet_id"))
    owner_id = await _mapped_id(db, source_system, "users", payload.get("owner_user_id"))
    if wallet_id is None or owner_id is None:
        raise LegacyMigrationError("wallet transaction wallet or owner is not migrated")
    row = await _existing_core(db, record, WalletTransaction)
    operation = "updated" if row else "created"
    if row is None:
        row = WalletTransaction(wallet_id=wallet_id, owner_user_id=owner_id, tx_type="ADMIN_ADJUSTMENT")
        db.add(row)
    row.wallet_id = wallet_id
    row.owner_user_id = owner_id
    row.tx_type = _enum(payload.get("tx_type"), "ADMIN_ADJUSTMENT")
    row.amount_delta_minor = int(payload.get("amount_delta_minor") or 0)
    row.available_balance_after_minor = int(payload.get("available_balance_after_minor") or 0)
    row.locked_balance_after_minor = int(payload.get("locked_balance_after_minor") or 0)
    row.currency = str(payload.get("currency") or "USDT")
    row.reference_type = payload.get("reference_type")
    row.note = payload.get("note")
    row.metadata_json = _sanitize({
        **(payload.get("metadata_json") or {}),
        "legacy_reference_id": str(payload.get("reference_id") or "") or None,
    })
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_wallet_deposit(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    wallet_id = await _mapped_id(db, source_system, "wallets", payload.get("wallet_id"))
    owner_id = await _mapped_id(db, source_system, "users", payload.get("owner_user_id"))
    if wallet_id is None or owner_id is None:
        raise LegacyMigrationError("wallet deposit wallet or owner is not migrated")
    row = await _existing_core(db, record, WalletDeposit)
    operation = "updated" if row else "created"
    if row is None:
        row = WalletDeposit(wallet_id=wallet_id, owner_user_id=owner_id, amount_minor=0, deposit_address="legacy")
        db.add(row)
    row.wallet_id = wallet_id
    row.owner_user_id = owner_id
    for key, default in (
        ("amount_minor", 0), ("confirmations", 0),
    ):
        setattr(row, key, int(payload.get(key) or default))
    for key, default in (
        ("currency", "USDT"), ("network", "TRC20"), ("provider", "MANUAL_BANK"),
        ("payment_method", "PHP_MANUAL_BANK"), ("deposit_address", "legacy"),
    ):
        setattr(row, key, str(payload.get(key) or default))
    for key in ("source_currency", "target_currency", "tx_hash", "submitter_note", "admin_note"):
        setattr(row, key, payload.get(key))
    row.status = _enum(payload.get("status"), "PENDING_TX")
    row.verified_by = await _mapped_id(db, source_system, "users", payload.get("verified_by"))
    row.rejected_by = await _mapped_id(db, source_system, "users", payload.get("rejected_by"))
    row.verified_at = _datetime(payload.get("verified_at"))
    row.rejected_at = _datetime(payload.get("rejected_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_address(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    user_id = await _mapped_id(db, source_system, "users", payload.get("user_id"))
    if user_id is None:
        raise LegacyMigrationError("address user is not migrated")
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    row = await _existing_core(db, record, Address)
    operation = "updated" if row else "created"
    if row is None:
        row = Address(
            user_id=user_id, address_type="DELIVERY_TO", label="Legacy address",
            contact_name="Legacy contact", contact_phone="-", country_code="PH",
            country_name="Philippines", city="-", address_line1="-",
        )
        db.add(row)
    row.user_id = user_id
    row.company_id = company_id
    for key, default in (
        ("address_type", "DELIVERY_TO"), ("label", "Legacy address"),
        ("contact_name", "Legacy contact"), ("contact_phone", "-"),
        ("country_code", "PH"), ("country_name", "Philippines"), ("city", "-"),
        ("address_line1", "-"), ("status", "ACTIVE"),
    ):
        setattr(row, key, str(payload.get(key) or default))
    for key in ("state_province", "district", "postal_code", "address_line2", "lat", "lng"):
        setattr(row, key, payload.get(key))
    row.is_default = bool(payload.get("is_default", False))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_shipping_route(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    row = await _existing_core(db, record, ShippingRoute)
    operation = "updated" if row else "created"
    if row is None:
        row = ShippingRoute(origin_country="PH", dest_country="PH", shipping_method="LOCAL_DELIVERY")
        db.add(row)
    for key, default in (("origin_country", "PH"), ("dest_country", "PH"), ("shipping_method", "LOCAL_DELIVERY"), ("status", "ACTIVE")):
        setattr(row, key, str(payload.get(key) or default))
    for key in ("origin_region", "dest_region", "description"):
        setattr(row, key, payload.get(key))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_shipping_rate(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    route_id = await _mapped_id(db, source_system, "shipping_routes", payload.get("route_id"))
    if route_id is None:
        raise LegacyMigrationError("shipping rate route is not migrated")
    row = await _existing_core(db, record, ShippingRate)
    operation = "updated" if row else "created"
    if row is None:
        row = ShippingRate(route_id=route_id, price_per_kg_minor=0, valid_from=date.today())
        db.add(row)
    row.route_id = route_id
    for key, default in (("weight_min_kg", 0), ("weight_max_kg", 99999), ("volume_factor", 5000)):
        setattr(row, key, float(payload.get(key) if payload.get(key) is not None else default))
    for key, default in (("price_per_kg_minor", 0), ("min_charge_minor", 0), ("estimated_days_min", 1), ("estimated_days_max", 7)):
        setattr(row, key, int(payload.get(key) or default))
    row.currency = str(payload.get("currency") or "USD")
    row.surcharges_json = payload.get("surcharges_json")
    row.valid_from = _date(payload.get("valid_from")) or date.today()
    row.valid_until = _date(payload.get("valid_until"))
    row.notes = payload.get("notes")
    row.status = _enum(payload.get("status"), "ACTIVE")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_order_shipping(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    if order_id is None:
        raise LegacyMigrationError("order shipping order is not migrated")
    workspace_id = await _legacy_order_workspace(db, order_id)
    row = await _existing_core(db, record, OrderShipping)
    if row is None:
        row = (await db.execute(select(OrderShipping).where(OrderShipping.order_id == order_id))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = OrderShipping(workspace_id=workspace_id, order_id=order_id, shipping_method="LOCAL_DELIVERY")
        db.add(row)
    row.order_id = order_id
    row.workspace_id = workspace_id
    row.shipping_method = _enum(payload.get("shipping_method"), "LOCAL_DELIVERY")
    row.origin_address_id = await _mapped_id(db, source_system, "addresses", payload.get("origin_address_id"))
    row.dest_address_id = await _mapped_id(db, source_system, "addresses", payload.get("dest_address_id"))
    for key in ("chargeable_weight_kg", "shipping_cost_minor", "estimated_days_min", "estimated_days_max", "tracking_number", "carrier_name"):
        if key in payload:
            setattr(row, key, payload.get(key))
    row.currency = str(payload.get("currency") or "USD")
    row.shipped_at = _datetime(payload.get("shipped_at"))
    row.delivered_at = _datetime(payload.get("delivered_at"))
    row.status = _enum(payload.get("status"), "PENDING")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_delivery(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    if order_id is None:
        raise LegacyMigrationError("delivery order is not migrated")
    order = await db.get(CommerceOrder, order_id)
    if order is None or order.workspace_id is None:
        raise LegacyMigrationError("delivery order has no Workspace")
    status_map = {"PENDING": "scheduled", "READY_FOR_PICKUP": "scheduled", "DISPATCHED": "shipped", "DELIVERED": "delivered", "ACCEPTED": "accepted", "FAILED": "failed"}
    row = await _existing_core(db, record, OrderDelivery)
    operation = "updated" if row else "created"
    if row is None:
        row = OrderDelivery(workspace_id=order.workspace_id, commerce_order_id=order_id)
        db.add(row)
    row.commerce_order_id = order_id
    row.workspace_id = order.workspace_id
    row.carrier = payload.get("carrier")
    row.tracking_number = payload.get("tracking_number")
    row.status = status_map.get(_enum(payload.get("status"), "PENDING"), "scheduled")
    row.proof_json = _sanitize({"proofs": payload.get("proofs"), "notes": payload.get("notes"), "legacy_actor_id": payload.get("actor_id")})
    row.legacy_delivery_id = record.legacy_id
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_ad_campaign(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        raise LegacyMigrationError("ad campaign company is not migrated")
    row = await _existing_core(db, record, AdCampaign)
    operation = "updated" if row else "created"
    if row is None:
        row = AdCampaign(company_id=company_id, title="Legacy campaign", placement="FEED_TOP", budget_minor=0, bid_per_click_minor=0)
        db.add(row)
    row.company_id = company_id
    row.listing_id = await _mapped_id(db, source_system, "catalog_items", payload.get("catalog_item_id") or payload.get("listing_id"))
    row.title = str(payload.get("title") or "Legacy campaign")
    row.placement = _enum(payload.get("placement"), "FEED_TOP")
    row.target_category_id = await _mapped_id(db, source_system, "categories", payload.get("target_category_id"))
    for key in ("target_keywords", "target_countries", "rejection_reason"):
        setattr(row, key, payload.get(key))
    for key in ("budget_minor", "spent_minor", "bid_per_click_minor", "impressions", "clicks", "conversions"):
        setattr(row, key, int(payload.get(key) or 0))
    row.currency = str(payload.get("currency") or "USD")
    row.status = _enum(payload.get("status"), "DRAFT")
    row.starts_at = _datetime(payload.get("starts_at"))
    row.ends_at = _datetime(payload.get("ends_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_escrow(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    if order_id is None:
        raise LegacyMigrationError("escrow order is not migrated")
    workspace_id = await _legacy_order_workspace(db, order_id)
    row = await _existing_core(db, record, EscrowTransaction)
    if row is None:
        row = (await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == order_id))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = EscrowTransaction(workspace_id=workspace_id, order_id=order_id, auth_amount_minor=0)
        db.add(row)
    row.order_id = order_id
    row.workspace_id = workspace_id
    row.provider = _enum(payload.get("provider"), "SIMULATED")
    row.provider_reference = payload.get("provider_reference")
    for key in ("auth_amount_minor", "captured_amount_minor", "released_amount_minor", "refunded_amount_minor"):
        setattr(row, key, int(payload.get(key) or 0))
    row.currency = str(payload.get("currency") or "PHP")
    row.status = _enum(payload.get("status"), "AUTH_PENDING")
    row.raw_event_json = _sanitize(payload.get("raw_event_json") or {})
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_payout(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    if company_id is None or order_id is None:
        raise LegacyMigrationError("payout company or order is not migrated")
    workspace_id = await _legacy_order_workspace(db, order_id)
    row = await _existing_core(db, record, Payout)
    operation = "updated" if row else "created"
    if row is None:
        row = Payout(workspace_id=workspace_id, company_id=company_id, order_id=order_id, amount_minor=0)
        db.add(row)
    row.company_id = company_id
    row.order_id = order_id
    row.workspace_id = workspace_id
    row.escrow_id = await _mapped_id(db, source_system, "escrow_transactions", payload.get("escrow_id"))
    if row.escrow_id is not None:
        escrow = await db.get(EscrowTransaction, row.escrow_id)
        if escrow is not None and escrow.workspace_id != workspace_id:
            raise LegacyMigrationError("payout escrow and order use different Workspaces")
    row.amount_minor = int(payload.get("amount_minor") or 0)
    for key, default in (("currency", "PHP"), ("provider", "SIMULATED"), ("status", "PENDING")):
        setattr(row, key, str(payload.get(key) or default))
    for key in ("destination", "provider_reference", "failure_reason"):
        setattr(row, key, payload.get(key))
    row.risk_hold = bool(payload.get("risk_hold", False))
    row.scheduled_at = _datetime(payload.get("scheduled_at"))
    row.paid_at = _datetime(payload.get("paid_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_dispute(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    if order_id is None:
        raise LegacyMigrationError("dispute order is not migrated")
    order = await db.get(CommerceOrder, order_id)
    if order is None or order.workspace_id is None:
        raise LegacyMigrationError("dispute order has no Workspace")
    opened_by = await _mapped_id(db, source_system, "users", payload.get("opened_by_user_id"))
    status_map = {"OPENED": "open", "WAITING_BUYER_EVIDENCE": "under_review", "WAITING_SUPPLIER_EVIDENCE": "under_review", "UNDER_REVIEW": "under_review", "RESOLVED_REFUND": "resolved_buyer", "RESOLVED_RELEASE": "resolved_supplier", "RESOLVED_PARTIAL_REFUND": "resolved_buyer", "ESCALATED": "under_review", "CANCELED": "closed"}
    row = await _existing_core(db, record, OrderDispute)
    if row is None:
        row = (await db.execute(select(OrderDispute).where(OrderDispute.legacy_dispute_id == record.legacy_id))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = OrderDispute(
            workspace_id=order.workspace_id,
            commerce_order_id=order_id,
            opened_by_role="buyer",
            reason_code="legacy",
        )
        db.add(row)
    row.commerce_order_id = order_id
    row.workspace_id = order.workspace_id
    row.opened_by_user_id = opened_by
    row.opened_by_role = str(payload.get("opened_by_role") or "buyer").lower()
    row.reason_code = str(payload.get("reason_code") or "legacy")
    row.description = payload.get("reason") or payload.get("description")
    row.status = status_map.get(_enum(payload.get("status"), "OPENED"), "open")
    row.resolution_json = _sanitize({"evidence": payload.get("evidence_json"), "admin_notes": payload.get("admin_notes"), "resolution": payload.get("resolution"), "refund_amount_minor": payload.get("refund_amount_minor")})
    row.legacy_dispute_id = record.legacy_id
    if row.status.startswith("resolved_") or row.status == "closed":
        row.resolved_at = _datetime(payload.get("updated_at")) or datetime.now(timezone.utc)
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_trust_profile(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str, portal_key: str):
    entity_type = _enum(payload.get("entity_type"), "COMPANY")
    if entity_type == "COMPANY":
        company_id = await _mapped_id(db, source_system, "companies", payload.get("entity_id") or payload.get("company_id"))
    else:
        user_id = await _mapped_id(db, source_system, "users", payload.get("entity_id"))
        user = await db.get(User, user_id) if user_id else None
        company_id = user.company_id if user else None
    if company_id is None:
        raise LegacyMigrationError("trust profile company is not migrated")
    row = await _existing_core(db, record, TrustProfile)
    if row is None:
        row = (await db.execute(select(TrustProfile).where(TrustProfile.company_id == company_id, TrustProfile.portal_key == portal_key))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = TrustProfile(company_id=company_id, portal_key=portal_key)
        db.add(row)
    row.company_id = company_id
    row.portal_key = portal_key
    row.completed_orders = int(payload.get("successful_deals_count") or payload.get("completed_orders") or 0)
    row.dispute_count = int(payload.get("dispute_count") or 0)
    row.trust_score = max(0, min(100, int(payload.get("trust_score") or 0)))
    row.metrics_json = _sanitize(payload)
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_trust_score_event(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    profile_id = await _mapped_id(
        db, source_system, "trust_profiles", payload.get("trust_profile_id")
    )
    if profile_id is None:
        raise LegacyMigrationError("trust score event profile is not migrated")
    row = await _existing_core(db, record, TrustScoreEvent)
    operation = "updated" if row else "created"
    if row is None:
        row = TrustScoreEvent(trust_profile_id=profile_id, event_type="RECALCULATED")
        db.add(row)
    row.trust_profile_id = profile_id
    row.event_type = _enum(payload.get("event_type"), "RECALCULATED")
    row.score_delta = int(payload.get("score_delta") or 0)
    row.before_score = int(payload.get("before_score") or 0)
    row.after_score = int(payload.get("after_score") or 0)
    row.reason = payload.get("reason")
    row.related_entity_type = _enum(payload.get("related_entity_type")) or None
    related_groups = {
        "USER": "users",
        "COMPANY": "companies",
        "ORDER": "orders",
        "OFFER": "offers",
        "INTENT": "intents",
    }
    related_group = related_groups.get(row.related_entity_type or "")
    row.related_entity_id = (
        await _mapped_id(db, source_system, related_group, payload.get("related_entity_id"))
        if related_group else None
    )
    row.created_by = await _mapped_id(db, source_system, "users", payload.get("created_by"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_audit_log(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    row = await _existing_core(db, record, AuditLog)
    operation = "updated" if row else "created"
    if row is None:
        row = AuditLog(
            action=str(payload.get("action") or "legacy.cebu.unknown"),
            entity_type=str(payload.get("entity_type") or "legacy_object"),
        )
        db.add(row)
    row.actor_type = "user"
    row.actor_user_id = await _mapped_id(db, source_system, "users", payload.get("actor_id"))
    row.portal_key = "admin_cebu"
    row.action = str(payload.get("action") or "legacy.cebu.unknown")[:100]
    row.entity_type = str(payload.get("entity_type") or "legacy_object")[:50]
    try:
        row.entity_id = uuid.UUID(str(payload.get("entity_id"))) if payload.get("entity_id") else None
    except ValueError:
        row.entity_id = None
    row.before_json = payload.get("before_json") or {}
    row.after_json = {
        **(payload.get("after_json") or {}),
        "_legacy": {
            "actor_role": payload.get("actor_role"),
            "risk_level": _enum(payload.get("risk_level"), "LOW"),
            "legacy_entity_id": str(payload.get("entity_id") or "") or None,
        },
    }
    row.reason = payload.get("reason")
    row.source = "legacy.cebu.audit"
    row.ip = payload.get("ip_address")
    row.user_agent = payload.get("user_agent")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_backup_schedule(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    row = await _existing_core(db, record, BackupSchedule)
    operation = "updated" if row else "created"
    if row is None:
        row = BackupSchedule(name=str(payload.get("name") or "Legacy Cebu backup"))
        db.add(row)
    row.name = str(payload.get("name") or row.name)
    row.frequency = _enum(payload.get("frequency"), "MONTHLY")
    row.cron_expr = payload.get("cron_expr")
    row.day_of_week = int(payload["day_of_week"]) if payload.get("day_of_week") is not None else None
    row.day_of_month = int(payload["day_of_month"]) if payload.get("day_of_month") is not None else None
    row.hour = int(payload["hour"]) if payload.get("hour") is not None else 2
    row.minute = int(payload["minute"]) if payload.get("minute") is not None else 0
    row.enabled = bool(payload.get("enabled", True))
    row.retention_count = int(payload.get("retention_count") or 8)
    row.retention_days = int(payload.get("retention_days") or 120)
    row.last_run_at = _datetime(payload.get("last_run_at"))
    row.next_run_at = _datetime(payload.get("next_run_at"))
    row.created_by = await _mapped_id(db, source_system, "users", payload.get("created_by"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_backup_job(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    row = await _existing_core(db, record, BackupJob)
    operation = "updated" if row else "created"
    if row is None:
        row = BackupJob()
        db.add(row)
    row.schedule_id = await _mapped_id(
        db, source_system, "backup_schedules", payload.get("schedule_id")
    )
    row.status = _enum(payload.get("status"), "PENDING")
    row.archive_path = payload.get("archive_path")
    row.archive_size_bytes = (
        int(payload["archive_size_bytes"]) if payload.get("archive_size_bytes") is not None else None
    )
    row.started_at = _datetime(payload.get("started_at"))
    row.finished_at = _datetime(payload.get("finished_at"))
    row.error_message = payload.get("error_message")
    row.created_by = await _mapped_id(db, source_system, "users", payload.get("created_by"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_company_document(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        raise LegacyMigrationError("company document company is not migrated")
    row = await _existing_core(db, record, CompanyDocument)
    operation = "updated" if row else "created"
    if row is None:
        row = CompanyDocument(company_id=company_id, doc_type="OTHER", file_url="legacy://missing")
        db.add(row)
    row.company_id = company_id
    row.doc_type = _enum(payload.get("doc_type"), "OTHER")
    row.file_url = str(payload.get("file_url") or "legacy://missing")
    row.original_filename = payload.get("original_filename")
    row.status = _enum(payload.get("status"), "PENDING")
    row.reviewer_note = payload.get("reviewer_note")
    row.reviewed_by = await _mapped_id(db, source_system, "users", payload.get("reviewed_by"))
    row.reviewed_at = _datetime(payload.get("reviewed_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_kyc_analysis(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    document_id = await _mapped_id(db, source_system, "company_documents", payload.get("document_id"))
    if company_id is None or document_id is None:
        raise LegacyMigrationError("KYC analysis company or document is not migrated")
    row = await _existing_core(db, record, KYCAnalysisResult)
    operation = "updated" if row else "created"
    if row is None:
        row = KYCAnalysisResult(company_id=company_id, document_id=document_id)
        db.add(row)
    row.company_id = company_id
    row.document_id = document_id
    row.analyzed_by = await _mapped_id(db, source_system, "users", payload.get("analyzed_by"))
    row.ai_provider = str(payload.get("ai_provider") or "openai")
    row.ai_model = str(payload.get("ai_model") or "gpt-4o-mini")
    row.authenticity = _enum(payload.get("authenticity"), "SUSPICIOUS")
    row.confidence = float(payload.get("confidence") or 0)
    row.overall_risk_score = float(payload.get("overall_risk_score") or 0)
    row.recommended_action = _enum(payload.get("recommended_action"), "MANUAL_REVIEW")
    row.tamper_suspected = bool(payload.get("tamper_suspected", False))
    row.photoshop_suspected = bool(payload.get("photoshop_suspected", False))
    row.text_photo_consistency = bool(payload.get("text_photo_consistency", False))
    row.extracted_fields = payload.get("extracted_fields")
    row.detected_issues = payload.get("detected_issues")
    row.concerns = payload.get("concerns")
    row.raw_result_json = _sanitize(payload.get("raw_result_json") or {})
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_verification_review(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    company_id = await _mapped_id(db, source_system, "companies", payload.get("company_id"))
    if company_id is None:
        raise LegacyMigrationError("verification review company is not migrated")
    row = await _existing_core(db, record, VerificationReview)
    operation = "updated" if row else "created"
    if row is None:
        row = VerificationReview(company_id=company_id)
        db.add(row)
    row.company_id = company_id
    row.status = _enum(payload.get("status"), "SUBMITTED")
    row.assigned_reviewer_id = await _mapped_id(db, source_system, "users", payload.get("assigned_reviewer_id"))
    row.decision = _enum(payload.get("decision")) or None
    for key in ("decision_reason", "internal_note", "user_facing_note"):
        setattr(row, key, payload.get(key))
    row.decided_at = _datetime(payload.get("decided_at"))
    row.decided_by = await _mapped_id(db, source_system, "users", payload.get("decided_by"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_risk_flag(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    entity_type = _enum(payload.get("entity_type"), "OTHER")
    source_group = {
        "USER": "users",
        "COMPANY": "companies",
        "CATALOG_ITEM": "catalog_items",
        "INTENT": "intents",
        "OFFER": "offers",
        "ORDER": "orders",
        "DOCUMENT": "company_documents",
        "KYC_ANALYSIS": "kyc_analysis_results",
    }.get(entity_type)
    subject_id = await _mapped_id(db, source_system, source_group, payload.get("entity_id")) if source_group else None
    if subject_id is None:
        try:
            subject_id = uuid.UUID(str(payload.get("entity_id")))
        except (TypeError, ValueError):
            raise LegacyMigrationError("risk flag subject is not migrated")
    row = await _existing_core(db, record, RiskFlag)
    operation = "updated" if row else "created"
    if row is None:
        row = RiskFlag(subject_type=entity_type.lower(), subject_id=subject_id, reason_code="OTHER")
        db.add(row)
    row.subject_type = entity_type.lower()
    row.subject_id = subject_id
    if entity_type == "COMPANY":
        row.company_id = subject_id
    row.reason_code = _enum(payload.get("risk_type"), "OTHER")
    row.severity = str(payload.get("risk_level") or "MEDIUM").lower()
    legacy_status = _enum(payload.get("status"), "OPEN")
    row.status = (
        "dismissed" if legacy_status == "FALSE_POSITIVE"
        else "resolved" if legacy_status in {"MITIGATED", "ACTION_TAKEN", "CLOSED"}
        else "open"
    )
    row.source_event = "legacy.cebu.risk_flag"
    row.details_json = _sanitize(
        {
            "description": payload.get("description"),
            "action_taken": payload.get("action_taken"),
            "legacy_status": legacy_status,
            "legacy_assigned_analyst_id": payload.get("assigned_analyst_id"),
        }
    )
    row.resolved_by_user_id = await _mapped_id(db, source_system, "users", payload.get("resolved_by"))
    row.resolved_at = _datetime(payload.get("resolved_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_region_payment_config(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    country_code = str(payload.get("country_code") or "PH").upper()[:2]
    row = await _existing_core(db, record, RegionPaymentConfig)
    if row is None:
        row = (await db.execute(select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == country_code))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = RegionPaymentConfig(country_code=country_code, country_name=country_code, local_currency="PHP", default_settlement_currency="PHP")
        db.add(row)
    row.country_code = country_code
    row.country_name = str(payload.get("country_name") or row.country_name)
    row.local_currency = str(payload.get("local_currency") or row.local_currency).upper()
    row.default_settlement_currency = str(payload.get("default_settlement_currency") or row.default_settlement_currency).upper()
    row.default_transaction_mode = _enum(payload.get("default_transaction_mode"), "LOCAL_ONLY")
    row.enabled_currencies = payload.get("enabled_currencies") or []
    row.enabled_payment_methods = payload.get("enabled_payment_methods") or []
    row.cross_border_currencies = payload.get("cross_border_currencies") or []
    row.force_usd_bridge = bool(payload.get("force_usd_bridge", False))
    row.allow_supplier_payout_currency = bool(payload.get("allow_supplier_payout_currency", False))
    row.is_active = bool(payload.get("is_active", True))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_currency_config(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    code = str(payload.get("code") or "PHP").upper()[:10]
    row = await _existing_core(db, record, CurrencyConfig)
    if row is None:
        row = (await db.execute(select(CurrencyConfig).where(CurrencyConfig.code == code))).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = CurrencyConfig(code=code, name=code)
        db.add(row)
    row.code = code
    row.name = str(payload.get("name") or code)
    row.minor_unit = int(payload.get("minor_unit") or 2)
    row.is_fiat = bool(payload.get("is_fiat", True))
    row.is_enabled = bool(payload.get("is_enabled", True))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_payment_method_config(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    country = str(payload.get("country_code") or "PH").upper()[:2]
    method = str(payload.get("method_code") or "MANUAL_BANK").upper()
    currency = str(payload.get("currency") or "PHP").upper()
    row = await _existing_core(db, record, PaymentMethodConfig)
    if row is None:
        row = (
            await db.execute(
                select(PaymentMethodConfig).where(
                    PaymentMethodConfig.country_code == country,
                    PaymentMethodConfig.method_code == method,
                    PaymentMethodConfig.currency == currency,
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = PaymentMethodConfig(country_code=country, method_code=method, currency=currency)
        db.add(row)
    row.country_code = country
    row.method_code = method
    row.provider = str(payload.get("provider") or "SIMULATED")
    row.currency = currency
    row.is_enabled = bool(payload.get("is_enabled", True))
    row.config_json = payload.get("config_json") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_fee_rule(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    row = await _existing_core(db, record, FeeRule)
    operation = "updated" if row else "created"
    if row is None:
        row = FeeRule(name=str(payload.get("name") or "Legacy fee"), fee_type=_enum(payload.get("fee_type"), "PROVIDER_FEE"))
        db.add(row)
    row.name = str(payload.get("name") or row.name)
    row.country_code = payload.get("country_code")
    row.payment_method = payload.get("payment_method")
    row.fee_type = _enum(payload.get("fee_type"), "PROVIDER_FEE")
    row.currency = str(payload.get("currency") or "PHP").upper()
    for key in ("fixed_fee_minor", "variable_bps", "min_fee_minor"):
        setattr(row, key, int(payload.get(key) or 0))
    row.max_fee_minor = int(payload["max_fee_minor"]) if payload.get("max_fee_minor") is not None else None
    row.is_enabled = bool(payload.get("is_enabled", True))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_fx_quote(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    row = await _existing_core(db, record, FxQuote)
    operation = "updated" if row else "created"
    if row is None:
        row = FxQuote(source_currency="PHP", target_currency="USD", rate=1, expires_at=_datetime(payload.get("expires_at")) or datetime.now(timezone.utc))
        db.add(row)
    row.source_currency = str(payload.get("source_currency") or "PHP").upper()
    row.target_currency = str(payload.get("target_currency") or "USD").upper()
    row.rate = payload.get("rate") or 1
    row.rate_source = str(payload.get("rate_source") or "SIMULATED_RATE_TABLE")
    row.provider_quote_id = payload.get("provider_quote_id")
    row.expires_at = _datetime(payload.get("expires_at")) or datetime.now(timezone.utc)
    row.raw_payload = payload.get("raw_payload") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_payment_quote(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    row = await _existing_core(db, record, PaymentQuote)
    operation = "updated" if row else "created"
    if row is None:
        row = PaymentQuote(
            buyer_country="PH", supplier_country="PH", mode="LOCAL_ONLY", payment_method="MANUAL_BANK",
            order_currency="PHP", payer_currency="PHP", settlement_currency="PHP",
            amount_minor=0, payer_total_minor=0, escrow_amount_minor=0, supplier_estimated_net_minor=0,
            expires_at=_datetime(payload.get("expires_at")) or datetime.now(timezone.utc),
        )
        db.add(row)
    for key, default in (
        ("buyer_country", "PH"), ("supplier_country", "PH"), ("payment_method", "MANUAL_BANK"),
        ("order_currency", "PHP"), ("payer_currency", "PHP"), ("settlement_currency", "PHP"),
    ):
        setattr(row, key, str(payload.get(key) or default).upper())
    row.mode = _enum(payload.get("mode"), "LOCAL_ONLY")
    for key in ("amount_minor", "payer_total_minor", "escrow_amount_minor", "supplier_estimated_net_minor", "platform_revenue_minor"):
        setattr(row, key, int(payload.get(key) or 0))
    row.rate = payload.get("rate")
    row.rate_source = payload.get("rate_source")
    row.fx_quote_id = await _mapped_id(db, source_system, "fx_quotes", payload.get("fx_quote_id"))
    row.expires_at = _datetime(payload.get("expires_at")) or datetime.now(timezone.utc)
    row.status = _enum(payload.get("status"), "ACTIVE")
    row.metadata_json = payload.get("metadata_json") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_provider_payment_intent(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    row = await _existing_core(db, record, ProviderPaymentIntent)
    operation = "updated" if row else "created"
    if row is None:
        row = ProviderPaymentIntent(payment_method="MANUAL_BANK", amount_minor=0, currency="PHP")
        db.add(row)
    row.quote_id = await _mapped_id(db, source_system, "payment_quotes", payload.get("quote_id"))
    row.order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    row.workspace_id = await _legacy_order_workspace(db, row.order_id) if row.order_id is not None else None
    row.provider = str(payload.get("provider") or "SIMULATED")
    row.provider_reference = payload.get("provider_reference")
    row.payment_method = str(payload.get("payment_method") or "MANUAL_BANK")
    row.amount_minor = int(payload.get("amount_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP").upper()
    row.status = _enum(payload.get("status"), "CREATED")
    row.raw_payload = payload.get("raw_payload") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_fee_line_item(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    row = await _existing_core(db, record, FeeLineItem)
    operation = "updated" if row else "created"
    if row is None:
        row = FeeLineItem(fee_type="PROVIDER_FEE", label="Legacy fee", amount_minor=0, currency="PHP")
        db.add(row)
    row.quote_id = await _mapped_id(db, source_system, "payment_quotes", payload.get("quote_id"))
    row.payment_intent_id = await _mapped_id(db, source_system, "payment_intents", payload.get("payment_intent_id"))
    row.fee_type = _enum(payload.get("fee_type"), "PROVIDER_FEE")
    row.label = str(payload.get("label") or "Legacy fee")
    row.amount_minor = int(payload.get("amount_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP").upper()
    row.refundable = bool(payload.get("refundable", False))
    row.metadata_json = payload.get("metadata_json") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_settlement_event(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    row = await _existing_core(db, record, SettlementEvent)
    operation = "updated" if row else "created"
    if row is None:
        row = SettlementEvent(provider="SIMULATED", gross_amount_minor=0, net_amount_minor=0, currency="PHP")
        db.add(row)
    row.payment_intent_id = await _mapped_id(db, source_system, "payment_intents", payload.get("payment_intent_id"))
    row.provider = str(payload.get("provider") or "SIMULATED")
    row.provider_reference = payload.get("provider_reference")
    row.gross_amount_minor = int(payload.get("gross_amount_minor") or 0)
    row.fee_amount_minor = int(payload.get("fee_amount_minor") or 0)
    row.net_amount_minor = int(payload.get("net_amount_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP").upper()
    row.status = _enum(payload.get("status"), "RECEIVED")
    row.raw_payload = payload.get("raw_payload") or {}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_settlement_adjustment(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    event_id = await _mapped_id(db, source_system, "settlement_events", payload.get("settlement_event_id"))
    if event_id is None:
        raise LegacyMigrationError("settlement adjustment event is not migrated")
    row = await _existing_core(db, record, SettlementAdjustment)
    operation = "updated" if row else "created"
    if row is None:
        row = SettlementAdjustment(settlement_event_id=event_id, adjustment_type="LEGACY", amount_minor=0, currency="PHP")
        db.add(row)
    row.settlement_event_id = event_id
    row.adjustment_type = str(payload.get("adjustment_type") or "LEGACY")
    row.amount_minor = int(payload.get("amount_minor") or 0)
    row.currency = str(payload.get("currency") or "PHP").upper()
    row.reason = payload.get("reason")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_payment_event(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str):
    row = await _existing_core(db, record, PaymentEvent)
    operation = "updated" if row else "created"
    if row is None:
        row = PaymentEvent(provider="LEGACY", event_type="LEGACY_EVENT")
        db.add(row)
    row.provider = str(payload.get("provider") or "LEGACY")
    row.provider_event_id = payload.get("provider_event_id")
    row.event_type = str(payload.get("event_type") or "LEGACY_EVENT")
    row.order_id = await _mapped_id(db, source_system, "orders", payload.get("order_id"))
    row.escrow_id = await _mapped_id(db, source_system, "escrow_transactions", payload.get("escrow_id"))
    workspace_id = await _legacy_order_workspace(db, row.order_id) if row.order_id is not None else None
    if row.escrow_id is not None:
        escrow = await db.get(EscrowTransaction, row.escrow_id)
        if escrow is not None:
            if workspace_id is not None and escrow.workspace_id is not None and escrow.workspace_id != workspace_id:
                raise LegacyMigrationError("payment event escrow and order use different Workspaces")
            workspace_id = workspace_id or escrow.workspace_id
    row.workspace_id = workspace_id
    row.amount_minor = int(payload["amount_minor"]) if payload.get("amount_minor") is not None else None
    row.currency = payload.get("currency")
    row.status = str(payload.get("status") or "RECEIVED")
    row.error_message = payload.get("error_message")
    row.raw_payload = payload.get("raw_payload") or {}
    row.received_at = _datetime(payload.get("received_at"))
    row.processed_at = _datetime(payload.get("processed_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_notification(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str, portal_key: str):
    user_id = await _mapped_id(db, source_system, "users", payload.get("user_id"))
    if user_id is None:
        raise LegacyMigrationError("notification user is not migrated")
    row = await _existing_core(db, record, PortalNotification)
    operation = "updated" if row else "created"
    if row is None:
        row = PortalNotification(user_id=user_id, event_type="legacy.notification", title="Legacy notification")
        db.add(row)
    row.user_id = user_id
    row.portal_key = portal_key
    row.domain = "commerce"
    row.event_type = str(payload.get("notification_type") or "legacy.notification")
    row.title = str(payload.get("subject") or payload.get("notification_type") or "Legacy notification")[:255]
    row.body = payload.get("body")
    row.status = "read" if _enum(payload.get("status"), "PENDING") == "READ" else "unread"
    row.read_at = _datetime(payload.get("read_at"))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_admin_note(
    db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str
):
    author_id = await _mapped_id(db, source_system, "users", payload.get("author_id"))
    if author_id is None:
        raise LegacyMigrationError("admin note author is not migrated")
    entity_type = _enum(payload.get("entity_type"), "OTHER")
    source_group = {
        "USER": "users", "COMPANY": "companies", "INTENT": "intents",
        "OFFER": "offers", "ORDER": "orders", "DISPUTE": "disputes",
        "RISKFLAG": "risk_flags", "RISK_FLAG": "risk_flags",
    }.get(entity_type)
    entity_id = await _mapped_id(db, source_system, source_group, payload.get("entity_id")) if source_group else None
    if entity_id is None:
        try:
            entity_id = uuid.UUID(str(payload.get("entity_id")))
        except (TypeError, ValueError):
            raise LegacyMigrationError("admin note entity is not migrated")
    row = await _existing_core(db, record, AdminNote)
    operation = "updated" if row else "created"
    if row is None:
        row = AdminNote(
            portal_key="admin_cebu",
            entity_type=entity_type.lower(),
            entity_id=entity_id,
            author_id=author_id,
            note=str(payload.get("note") or ""),
        )
        db.add(row)
    row.portal_key = "admin_cebu"
    row.entity_type = entity_type.lower()
    row.entity_id = entity_id
    row.author_id = author_id
    row.visibility = str(payload.get("visibility") or "INTERNAL_ONLY").lower()
    row.note = str(payload.get("note") or "")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_notification_template(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    template_key = str(payload.get("template_key") or f"legacy-{record.legacy_id}")
    channel = str(payload.get("channel") or "IN_APP")
    language = str(payload.get("language") or "en")
    row = await _existing_core(db, record, NotificationTemplate)
    if row is None:
        row = (
            await db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.portal_key == "admin_cebu",
                    NotificationTemplate.template_key == template_key,
                    NotificationTemplate.channel == channel,
                    NotificationTemplate.language == language,
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = NotificationTemplate(
            portal_key="admin_cebu",
            template_key=template_key,
            channel=channel,
            language=language,
            body=str(payload.get("body") or ""),
        )
        db.add(row)
    row.portal_key = "admin_cebu"
    row.template_key = template_key
    row.channel = channel
    row.language = language
    row.subject = payload.get("subject")
    row.body = str(payload.get("body") or "")
    row.variables_hint = payload.get("variables_hint")
    row.active = bool(payload.get("active", True))
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_platform_setting(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    key = str(payload.get("key") or f"legacy-{record.legacy_id}").lower()
    if any(part in key for part in ("password", "secret", "token", "api_key")):
        raise LegacyMigrationError("secret platform settings must be migrated through the integration secret store")
    row = await _existing_core(db, record, PlatformSetting)
    if row is None:
        row = (
            await db.execute(
                select(PlatformSetting).where(
                    PlatformSetting.portal_key == "admin_cebu",
                    PlatformSetting.key == key,
                )
            )
        ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = PlatformSetting(portal_key="admin_cebu", key=key, value_json={})
        db.add(row)
    row.portal_key = "admin_cebu"
    row.key = key
    value = payload.get("value_json")
    row.value_json = value if isinstance(value, dict) else {"legacy_value": payload.get("value")}
    row.description = payload.get("description")
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _import_message(db: AsyncSession, payload: dict, record: LegacyMigrationRecord, *, source_system: str, portal_key: str):
    sender_id = await _mapped_id(db, source_system, "users", payload.get("sender_id"))
    if sender_id is None:
        raise LegacyMigrationError("message sender is not migrated")
    thread_type = str(payload.get("thread_type") or "").lower()
    request_id = await _mapped_id(db, source_system, "intents", payload.get("thread_id")) if "intent" in thread_type else None
    order_id = await _mapped_id(db, source_system, "orders", payload.get("thread_id")) if "order" in thread_type else None
    if request_id is None and order_id is None:
        raise LegacyMigrationError("message thread is not migrated")
    q = select(CommerceThread)
    q = q.where(CommerceThread.commerce_order_id == order_id) if order_id else q.where(CommerceThread.procurement_request_id == request_id)
    thread = (await db.execute(q.limit(1))).scalar_one_or_none()
    if thread is None:
        request = await db.get(ProcurementRequest, request_id) if request_id else None
        order = await db.get(CommerceOrder, order_id) if order_id else None
        thread = CommerceThread(
            workspace_id=request.workspace_id if request else order.workspace_id if order else None,
            portal_key=portal_key,
            procurement_request_id=request_id or (order.procurement_request_id if order else None),
            commerce_order_id=order_id,
            buyer_company_id=request.buyer_company_id if request else order.buyer_company_id if order else None,
            supplier_company_id=order.supplier_company_id if order else None,
            subject=request.title if request else f"Legacy order {payload.get('thread_id')}",
        )
        db.add(thread)
        await db.flush()
    sender = await db.get(User, sender_id)
    row = await _existing_core(db, record, CommerceMessage)
    operation = "updated" if row else "created"
    if row is None:
        row = CommerceMessage(
            workspace_id=thread.workspace_id,
            thread_id=thread.id,
            sender_role="buyer",
            body="Legacy message",
        )
        db.add(row)
    row.thread_id = thread.id
    row.workspace_id = thread.workspace_id
    row.sender_user_id = sender_id
    row.sender_role = "admin" if sender and sender.role in {"admin", "super_admin"} else "supplier" if sender and sender.role == "vendor" else "buyer"
    row.body = str(payload.get("body") or "")
    row.attachments_json = {"items": payload.get("attachments") or []}
    _preserve_timestamps(row, payload)
    await db.flush()
    return row, operation


async def _archive_only(db: AsyncSession, payload: dict, record: LegacyMigrationRecord):
    """Keep unsupported or future Cebu objects losslessly until a typed target exists."""
    await db.flush()
    return record, "archived"


async def _repair_project_report_version_links(db: AsyncSession, *, source_system: str) -> None:
    records = (
        await db.execute(
            select(LegacyMigrationRecord).where(
                LegacyMigrationRecord.source_system == source_system,
                LegacyMigrationRecord.entity_type == "project_reports",
                LegacyMigrationRecord.status == "SUCCESS",
            )
        )
    ).scalars()
    for record in records:
        if record.core_entity_id is None:
            continue
        report = await db.get(ProjectReport, record.core_entity_id)
        if report is None:
            continue
        payload = record.source_payload_json or {}
        report.current_version_id = await _mapped_id(
            db, source_system, "project_report_versions", payload.get("current_version_id")
        )
        report.frozen_version_id = await _mapped_id(
            db, source_system, "project_report_versions", payload.get("frozen_version_id")
        )
    await db.flush()


IMPORTERS = {
    "companies": _import_company,
    "users": _import_user,
    "branches": _import_branch,
    "regions": _import_region,
    "service_areas": _import_service_area,
    "categories": _import_category,
    "catalog_items": _import_listing,
    "buyer_projects": _import_buyer_project,
    "project_files": _import_project_file,
    "project_ai_runs": _import_project_ai_run,
    "project_line_items": _import_project_line_item,
    "project_messages": _import_project_message,
    "project_metric_templates": _import_project_metric_template,
    "project_metric_values": _import_project_metric_value,
    "project_price_snapshots": _import_project_price_snapshot,
    "project_reports": _import_project_report,
    "project_report_versions": _import_project_report_version,
    "project_report_columns": _import_project_report_column,
    "project_report_rows": _import_project_report_row,
    "project_report_change_logs": _import_project_report_change_log,
    "intents": _import_request,
    "offers": _import_offer,
    "orders": _import_order,
    "transaction_reviews": _import_transaction_review,
    "wallets": _import_wallet,
    "wallet_transactions": _import_wallet_transaction,
    "wallet_deposits": _import_wallet_deposit,
    "addresses": _import_address,
    "shipping_routes": _import_shipping_route,
    "shipping_rates": _import_shipping_rate,
    "order_shipping": _import_order_shipping,
    "deliveries": _import_delivery,
    "ad_campaigns": _import_ad_campaign,
    "escrow_transactions": _import_escrow,
    "payouts": _import_payout,
    "disputes": _import_dispute,
    "trust_profiles": _import_trust_profile,
    "trust_score_events": _import_trust_score_event,
    "company_documents": _import_company_document,
    "kyc_analysis_results": _import_kyc_analysis,
    "verification_reviews": _import_verification_review,
    "risk_flags": _import_risk_flag,
    "payment_events": _import_payment_event,
    "region_payment_configs": _import_region_payment_config,
    "currency_configs": _import_currency_config,
    "payment_method_configs": _import_payment_method_config,
    "fee_rules": _import_fee_rule,
    "fx_quotes": _import_fx_quote,
    "payment_quotes": _import_payment_quote,
    "fee_line_items": _import_fee_line_item,
    "payment_intents": _import_provider_payment_intent,
    "settlement_events": _import_settlement_event,
    "settlement_adjustments": _import_settlement_adjustment,
    "notifications": _import_notification,
    "notification_templates": _import_notification_template,
    "messages": _import_message,
    "admin_notes": _import_admin_note,
    "platform_settings": _import_platform_setting,
    "audit_logs": _import_audit_log,
    "backup_schedules": _import_backup_schedule,
    "backup_jobs": _import_backup_job,
}


async def import_cebu_bundle(
    db: AsyncSession,
    *,
    bundle: dict,
    actor_user_id: uuid.UUID,
) -> tuple[LegacyMigrationRun, bool]:
    source_system = str(bundle.get("source_system") or "cebu")[:50]
    portal_key = str(bundle.get("portal_key") or "cebu")[:64]
    batch_key = str(bundle.get("batch_key") or "").strip()
    if not batch_key:
        raise LegacyMigrationError("batch_key is required")
    entity_groups = _entity_groups(bundle)
    checksum = _hash({key: bundle.get(key, []) for key in entity_groups})
    existing = (
        await db.execute(
            select(LegacyMigrationRun).where(
                LegacyMigrationRun.source_system == source_system,
                LegacyMigrationRun.batch_key == batch_key,
            )
        )
    ).scalar_one_or_none()
    if existing and existing.checksum != checksum:
        raise LegacyMigrationError("batch_key already exists with a different payload")
    if existing and existing.status == "COMPLETED":
        return existing, True
    if existing and existing.status == "RUNNING":
        raise LegacyMigrationError("migration batch is already running")

    run = existing or LegacyMigrationRun(
        source_system=source_system,
        portal_key=portal_key,
        batch_key=batch_key[:160],
        checksum=checksum,
        created_by=actor_user_id,
    )
    if existing is None:
        db.add(run)
    run.status = "RUNNING"
    run.started_at = datetime.now(timezone.utc)
    run.finished_at = None
    run.error_summary = None
    run.total_records = sum(len(bundle.get(key) or []) for key in entity_groups)
    run.succeeded_records = 0
    run.failed_records = 0
    await db.flush()

    counts: dict[str, dict[str, int]] = {}
    failures: list[str] = []
    for entity_type in entity_groups:
        rows = bundle.get(entity_type) or []
        counts[entity_type] = {"total": len(rows), "succeeded": 0, "failed": 0}
        for index, raw_payload in enumerate(rows):
            payload = dict(raw_payload)
            legacy_id = _legacy_id(payload, entity_type, index)
            record = await _record(
                db,
                run=run,
                entity_type=entity_type,
                legacy_id=legacy_id,
                payload_hash=_hash(payload),
                source_payload=payload,
            )
            try:
                if legacy_id.startswith("missing-"):
                    raise LegacyMigrationError("legacy object id is required")
                async with db.begin_nested():
                    importer = IMPORTERS.get(entity_type, _archive_only)
                    kwargs: dict[str, Any] = {}
                    if entity_type in {
                        "users", "branches", "service_areas", "catalog_items", "buyer_projects", "project_files",
                        "project_ai_runs", "project_line_items", "project_messages",
                        "project_metric_values", "project_price_snapshots", "project_reports",
                        "project_report_versions", "project_report_columns", "project_report_rows",
                        "project_report_change_logs",
                        "intents", "offers", "orders", "transaction_reviews",
                        "wallets", "wallet_transactions", "wallet_deposits", "addresses",
                        "shipping_rates", "order_shipping", "deliveries", "ad_campaigns",
                        "escrow_transactions", "payouts", "disputes", "trust_profiles", "trust_score_events",
                        "company_documents", "kyc_analysis_results", "verification_reviews",
                        "risk_flags", "payment_events", "payment_quotes", "fee_line_items",
                        "payment_intents", "settlement_events", "settlement_adjustments",
                        "notifications", "messages", "admin_notes",
                        "audit_logs", "backup_schedules", "backup_jobs",
                    }:
                        kwargs["source_system"] = source_system
                    if entity_type in {"users", "intents", "trust_profiles", "notifications", "messages"}:
                        kwargs["portal_key"] = portal_key
                    core, operation = await importer(db, payload, record, **kwargs)
                    await db.flush()
                record.core_entity_type = core.__tablename__
                record.core_entity_id = core.id
                record.operation = operation
                record.status = "SUCCESS"
                record.error_message = None
                record.details_json = {
                    "password_reset_required": entity_type == "users",
                    "legacy_owner_user_id": (
                        str(payload.get("owner_user_id")) if entity_type == "companies" and payload.get("owner_user_id") else None
                    ),
                }
                counts[entity_type]["succeeded"] += 1
                run.succeeded_records += 1
            except Exception as exc:
                record.operation = "failed"
                record.status = "FAILED"
                record.error_message = str(exc)[:2000]
                record.details_json = {"dependency_error": isinstance(exc, LegacyMigrationError)}
                counts[entity_type]["failed"] += 1
                run.failed_records += 1
                failures.append(f"{entity_type}:{legacy_id}: {exc}")
            await db.flush()

    await _repair_project_report_version_links(db, source_system=source_system)
    run.counts_json = counts
    run.status = "COMPLETED" if run.failed_records == 0 else "PARTIAL"
    run.error_summary = "\n".join(failures[:30]) or None
    run.finished_at = datetime.now(timezone.utc)
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=actor_user_id,
        portal_key="admin_cebu",
        action="cebu.admin.legacy_migration_executed",
        entity_type="legacy_migration_run",
        entity_id=run.id,
        after={
            "batch_key": run.batch_key,
            "status": run.status,
            "total_records": run.total_records,
            "succeeded_records": run.succeeded_records,
            "failed_records": run.failed_records,
        },
        source="admin.cebu.migration",
    )
    await db.commit()
    await db.refresh(run)
    return run, False

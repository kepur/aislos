"""Cebu Admin compatibility workbench backed by unified Core models."""
from __future__ import annotations

import uuid
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, func, select

from app.api.deps import AdminUser, DB
from app.core.permissions import STAFF_ROLES
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.admin_config import AdminNote, NotificationTemplate, PlatformSetting
from app.models.backup import BackupJob, BackupSchedule
from app.models.commerce_geo import CompanyBranch, ServiceArea
from app.models.commerce import (
    CommerceOrder,
    CommercePaymentIntent,
    CommerceSettlement,
    OFFER_STATUSES,
    ORDER_STATUSES,
    PROCUREMENT_REQUEST_STATUSES,
    RISK_FLAG_STATUSES,
    OrderDispute,
    ProcurementRequest,
    RiskFlag,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
    TrustProfile,
    TrustScoreEvent,
)
from app.models.notification import PortalNotification
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun
from app.models.user import Company, User
from app.modules.cebu_trade.models import (
    AdCampaign,
    CurrencyConfig,
    EscrowTransaction,
    FeeLineItem,
    FeeRule,
    FxQuote,
    Payout,
    PaymentEvent,
    PaymentMethodConfig,
    PaymentQuote,
    ProviderPaymentIntent,
    RegionPaymentConfig,
    SettlementAdjustment,
    SettlementEvent,
    ShippingRate,
    ShippingRoute,
    WalletDeposit,
)
from app.modules.buyer_project.models import ProjectMetricTemplate
from app.modules.kyc.models import CompanyDocument, KYCAnalysisResult, VerificationReview
from app.schemas.audit import AuditLogRead
from app.schemas.commerce import (
    CommerceOrderRead,
    OrderDisputeRead,
    PaymentIntentRead,
    PortalNotificationRead,
    ProcurementRequestRead,
    RiskFlagRead,
    SupplierOfferRead,
)
from app.services.audit import append_audit_event
from app.services.backup_service import create_backup_archive, next_run_at_for_schedule
from app.services.legacy_migration import (
    LegacyMigrationError,
    import_cebu_bundle,
    migration_record_dict,
    migration_run_dict,
)
from app.services.legacy_cutover import build_legacy_cutover_readiness
from app.services.portal_access import suspend_user_portal_access, sync_role_portal_access
from app.modules.cebu_trade.access import cebu_trade_admin_workspace_ids

router = APIRouter(prefix="/admin/cebu", tags=["cebu-admin-workbench"])


class StatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class VerificationUpdate(BaseModel):
    verification_status: str
    reason: str | None = None


class StaffInviteInput(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    role: str


class StaffRoleUpdateInput(BaseModel):
    role: str
    reason: str = Field(min_length=3, max_length=500)


class CompanyStatusUpdate(BaseModel):
    status: str
    reason: str = Field(min_length=3, max_length=500)


class OrderHoldInput(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class RiskFlagCreateInput(BaseModel):
    subject_type: str = Field(min_length=1, max_length=64)
    subject_id: uuid.UUID
    company_id: uuid.UUID | None = None
    reason_code: str = Field(min_length=1, max_length=64)
    severity: str = "medium"
    details_json: dict | None = None


class RiskFlagActionInput(BaseModel):
    status: str
    action_taken: str = Field(min_length=3, max_length=2000)


class AdminNoteInput(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    entity_id: uuid.UUID
    visibility: str = "internal_only"
    note: str = Field(min_length=1, max_length=10000)


class NotificationTemplateInput(BaseModel):
    channel: str = Field(min_length=1, max_length=30)
    language: str = Field(default="en", min_length=2, max_length=10)
    subject: str | None = Field(default=None, max_length=500)
    body: str = Field(min_length=1, max_length=20000)
    variables_hint: str | None = Field(default=None, max_length=2000)
    active: bool = True


class PlatformSettingInput(BaseModel):
    value_json: dict
    description: str | None = Field(default=None, max_length=500)


class KycMediaRiskInput(BaseModel):
    note: str = Field(min_length=3, max_length=2000)
    severity: str = "high"


class ProjectMetricTemplateInput(BaseModel):
    project_type: str = "GENERAL"
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    data_type: str = Field(default="text", min_length=1, max_length=50)
    unit_options_json: list | None = None
    required: bool = False
    sort_order: int = 0
    prompt: str | None = Field(default=None, max_length=5000)
    active: bool = True


class ProjectMetricTemplatePatch(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    data_type: str | None = Field(default=None, min_length=1, max_length=50)
    unit_options_json: list | None = None
    required: bool | None = None
    sort_order: int | None = None
    prompt: str | None = Field(default=None, max_length=5000)
    active: bool | None = None


class CompanyBranchInput(BaseModel):
    company_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int = Field(default=30, ge=1, le=500)
    delivery_methods_json: list | None = None
    status: str = "ACTIVE"


class ServiceAreaInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    region_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    coverage_type: str = "RADIUS"
    center_lat: float | None = None
    center_lng: float | None = None
    radius_km: int | None = Field(default=15, ge=1, le=500)
    polygon_json: dict | None = None
    status: str = "ACTIVE"
    notes: str | None = None


class CompanyBranchPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int | None = Field(default=None, ge=1, le=500)
    delivery_methods_json: list | None = None
    status: str | None = None


class ServiceAreaPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    region_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    coverage_type: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    radius_km: int | None = Field(default=None, ge=1, le=500)
    polygon_json: dict | None = None
    status: str | None = None
    notes: str | None = None


class RegionPaymentConfigInput(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str = Field(min_length=2, max_length=120)
    local_currency: str = Field(min_length=3, max_length=10)
    default_settlement_currency: str = Field(min_length=3, max_length=10)
    default_transaction_mode: str = "LOCAL_ONLY"
    enabled_currencies: list = Field(default_factory=list)
    enabled_payment_methods: list = Field(default_factory=list)
    cross_border_currencies: list = Field(default_factory=list)
    force_usd_bridge: bool = False
    allow_supplier_payout_currency: bool = False
    is_active: bool = True


class DisputeResolutionInput(BaseModel):
    resolution: str
    reason: str | None = None
    resolution_json: dict | None = None


class TrustAdjustmentInput(BaseModel):
    delta: int = Field(ge=-100, le=100)
    reason: str = Field(min_length=3, max_length=500)


class NotificationTestInput(BaseModel):
    title: str = Field(default="Cebu Admin test notification", min_length=1, max_length=255)
    body: str | None = Field(default="This is a real in-app test notification.", max_length=2000)


class BackupScheduleInput(BaseModel):
    name: str = "Scheduled backup"
    frequency: str = "MONTHLY"
    cron_expr: str | None = None
    day_of_week: int | None = None
    day_of_month: int | None = None
    hour: int = 2
    minute: int = 0
    enabled: bool = True
    retention_count: int = 8
    retention_days: int = 120


class LegacyMigrationBundleInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    batch_key: str = Field(min_length=1, max_length=160)
    source_system: str = Field(default="cebu", min_length=1, max_length=50)
    portal_key: str = Field(default="cebu", min_length=1, max_length=64)
    companies: list[dict] = Field(default_factory=list)
    users: list[dict] = Field(default_factory=list)
    categories: list[dict] = Field(default_factory=list)
    catalog_items: list[dict] = Field(default_factory=list)
    intents: list[dict] = Field(default_factory=list)
    offers: list[dict] = Field(default_factory=list)
    orders: list[dict] = Field(default_factory=list)
    wallets: list[dict] = Field(default_factory=list)
    wallet_transactions: list[dict] = Field(default_factory=list)
    wallet_deposits: list[dict] = Field(default_factory=list)
    addresses: list[dict] = Field(default_factory=list)
    shipping_routes: list[dict] = Field(default_factory=list)
    shipping_rates: list[dict] = Field(default_factory=list)
    order_shipping: list[dict] = Field(default_factory=list)
    deliveries: list[dict] = Field(default_factory=list)
    ad_campaigns: list[dict] = Field(default_factory=list)
    escrow_transactions: list[dict] = Field(default_factory=list)
    payouts: list[dict] = Field(default_factory=list)
    disputes: list[dict] = Field(default_factory=list)
    trust_profiles: list[dict] = Field(default_factory=list)
    company_documents: list[dict] = Field(default_factory=list)
    verification_reviews: list[dict] = Field(default_factory=list)
    notifications: list[dict] = Field(default_factory=list)
    messages: list[dict] = Field(default_factory=list)


def _page(items: list) -> dict:
    return {"items": items, "total": len(items)}


async def _audit_status(
    db: DB,
    admin: AdminUser,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: str | bool | None,
    after: str | bool | None,
    reason: str | None,
) -> None:
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        portal_key="admin_cebu",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before={"value": before},
        after={"value": after},
        reason=reason,
        source="admin.cebu",
    )


async def _list_rows(db: DB, model, *, status: str | None = None, limit: int = 200):
    stmt = select(model).order_by(model.created_at.desc()).limit(limit)
    if status is not None and hasattr(model, "status"):
        stmt = stmt.where(model.status == status)
    return list((await db.execute(stmt)).scalars())


async def _list_admin_workspace_rows(
    db: DB,
    admin,
    model,
    *,
    status: str | None = None,
    limit: int = 200,
    include_unscoped: bool = True,
):
    stmt = select(model).order_by(model.created_at.desc()).limit(limit)
    if status is not None and hasattr(model, "status"):
        stmt = stmt.where(model.status == status)
    if hasattr(model, "workspace_id"):
        workspace_ids = await cebu_trade_admin_workspace_ids(db, admin)
        workspace_filter = model.workspace_id.in_(workspace_ids)
        if include_unscoped:
            workspace_filter = or_(workspace_filter, model.workspace_id.is_(None))
        stmt = stmt.where(workspace_filter)
    return list((await db.execute(stmt)).scalars())


def _user_dict(row: User) -> dict:
    return {
        "id": row.id,
        "email": row.email,
        "full_name": row.full_name,
        "role": row.role,
        "company_id": row.company_id,
        "country": row.country,
        "is_active": row.is_active,
        "created_at": row.created_at,
    }


def _note_dict(row: AdminNote) -> dict:
    return {
        "id": row.id,
        "portal_key": row.portal_key,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "author_id": row.author_id,
        "visibility": row.visibility,
        "note": row.note,
        "created_at": row.created_at,
    }


def _template_dict(row: NotificationTemplate) -> dict:
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
        "updated_at": row.updated_at,
    }


def _setting_dict(row: PlatformSetting) -> dict:
    return {
        "id": row.id,
        "portal_key": row.portal_key,
        "key": row.key,
        "value_json": row.value_json,
        "description": row.description,
        "updated_by": row.updated_by,
        "updated_at": row.updated_at,
    }


def _metric_template_dict(row: ProjectMetricTemplate) -> dict:
    return {
        "id": row.id,
        "project_type": row.project_type,
        "key": row.key,
        "label": row.label,
        "data_type": row.data_type,
        "unit_options_json": row.unit_options_json,
        "required": row.required,
        "sort_order": row.sort_order,
        "prompt": row.prompt,
        "active": row.active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _model_dict(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.get("/dashboard")
async def cebu_admin_dashboard(db: DB, admin: AdminUser):
    models = {
        "users": User,
        "companies": Company,
        "procurement_requests": ProcurementRequest,
        "offers": SupplierOffer,
        "orders": CommerceOrder,
        "open_disputes": OrderDispute,
        "open_risk_flags": RiskFlag,
        "pending_deposits": WalletDeposit,
        "pending_verifications": VerificationReview,
        "legacy_migrations": LegacyMigrationRun,
    }
    stats: dict[str, int] = {}
    for key, model in models.items():
        stmt = select(func.count()).select_from(model)
        if key == "open_disputes":
            stmt = stmt.where(OrderDispute.status.in_(["open", "under_review"]))
        elif key == "open_risk_flags":
            stmt = stmt.where(RiskFlag.status == "open")
        elif key == "pending_deposits":
            stmt = stmt.where(WalletDeposit.status.notin_(["VERIFIED", "REJECTED"]))
        elif key == "pending_verifications":
            stmt = stmt.where(VerificationReview.status.notin_(["APPROVED", "REJECTED"]))
        stats[key] = int((await db.execute(stmt)).scalar() or 0)
    recent_audit = list(
        (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10))).scalars()
    )
    return {
        "stats": stats,
        "recent_audit": [AuditLogRead.model_validate(row) for row in recent_audit],
    }


@router.post("/migrations/import")
async def cebu_admin_import_legacy_bundle(
    data: LegacyMigrationBundleInput, db: DB, admin: AdminUser
):
    try:
        run, reused = await import_cebu_bundle(
            db,
            bundle=data.model_dump(),
            actor_user_id=admin.id,
        )
    except LegacyMigrationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return migration_run_dict(run, reused=reused)


@router.get("/migrations")
async def cebu_admin_migration_runs(
    db: DB,
    admin: AdminUser,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    stmt = select(LegacyMigrationRun).order_by(LegacyMigrationRun.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(LegacyMigrationRun.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return _page([migration_run_dict(row) for row in rows])


@router.get("/migrations/readiness")
async def cebu_admin_migration_readiness(
    db: DB,
    admin: AdminUser,
    source_system: str = Query(default="cebu", min_length=1, max_length=50),
):
    return await build_legacy_cutover_readiness(db, source_system=source_system)


@router.get("/migrations/{run_id}")
async def cebu_admin_migration_run(run_id: uuid.UUID, db: DB, admin: AdminUser):
    run = await db.get(LegacyMigrationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Migration run not found")
    records = list(
        (
            await db.execute(
                select(LegacyMigrationRecord)
                .where(LegacyMigrationRecord.run_id == run.id)
                .order_by(LegacyMigrationRecord.entity_type, LegacyMigrationRecord.created_at)
            )
        ).scalars()
    )
    return {
        **migration_run_dict(run),
        "records": [migration_record_dict(row) for row in records],
    }


@router.get("/users")
async def cebu_admin_users(
    db: DB,
    admin: AdminUser,
    role: str | None = None,
    active: bool | None = None,
    limit: int = Query(default=200, ge=1, le=500),
):
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if role:
        stmt = stmt.where(User.role == role)
    if active is not None:
        stmt = stmt.where(User.is_active.is_(active))
    rows = list((await db.execute(stmt)).scalars())
    return _page([_user_dict(row) for row in rows])


@router.post("/staff/invite", status_code=201)
async def cebu_admin_invite_staff(data: StaffInviteInput, db: DB, admin: AdminUser):
    allowed_roles = {role.value for role in STAFF_ROLES}
    if data.role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Role must be an internal staff role")
    if data.role == "super_admin" and admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can invite a super admin")
    email = data.email.strip().lower()
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    row = User(
        email=email,
        full_name=data.full_name,
        role=data.role,
        password_hash=hash_password(secrets.token_urlsafe(48)),
        is_active=True,
    )
    db.add(row)
    await db.flush()
    await sync_role_portal_access(db, user_id=row.id, role=row.role, company_id=None)
    await _audit_status(
        db, admin, action="cebu.admin.staff_invited", entity_type="user",
        entity_id=row.id, before=None, after=row.role, reason="Password reset required",
    )
    await db.commit()
    await db.refresh(row)
    return {**_user_dict(row), "password_reset_required": True}


@router.get("/staff")
async def cebu_admin_staff(db: DB, admin: AdminUser):
    allowed_roles = {role.value for role in STAFF_ROLES}
    rows = list(
        (
            await db.execute(
                select(User).where(User.role.in_(allowed_roles)).order_by(User.created_at.desc())
            )
        ).scalars()
    )
    return _page([_user_dict(row) for row in rows])


@router.put("/staff/{staff_id}/role")
async def cebu_admin_update_staff_role(
    staff_id: uuid.UUID, data: StaffRoleUpdateInput, db: DB, admin: AdminUser
):
    allowed_roles = {role.value for role in STAFF_ROLES}
    if data.role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Role must be an internal staff role")
    row = await db.get(User, staff_id)
    if row is None or row.role not in allowed_roles:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if row.id == admin.id:
        raise HTTPException(status_code=409, detail="Admin cannot change own role")
    if (row.role == "super_admin" or data.role == "super_admin") and admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin roles")
    before = row.role
    row.role = data.role
    await sync_role_portal_access(db, user_id=row.id, role=row.role, company_id=row.company_id)
    await _audit_status(
        db, admin, action="cebu.admin.staff_role_changed", entity_type="user",
        entity_id=row.id, before=before, after=row.role, reason=data.reason,
    )
    await db.commit()
    await db.refresh(row)
    return _user_dict(row)


@router.patch("/users/{user_id}/active")
async def cebu_admin_update_user_active(
    user_id: uuid.UUID, data: StatusUpdate, db: DB, admin: AdminUser
):
    row = await db.get(User, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    if row.id == admin.id and data.status.lower() not in ("active", "true", "enabled"):
        raise HTTPException(status_code=409, detail="Admin cannot deactivate own account")
    if row.role == "super_admin" and admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only a super admin can manage super admin accounts")
    new_value = data.status.lower() in ("active", "true", "enabled")
    before = row.is_active
    row.is_active = new_value
    if new_value:
        await sync_role_portal_access(
            db,
            user_id=row.id,
            role=row.role,
            company_id=row.company_id,
        )
    else:
        await suspend_user_portal_access(db, user_id=row.id)
    await _audit_status(
        db,
        admin,
        action="cebu.admin.user_active_changed",
        entity_type="user",
        entity_id=row.id,
        before=before,
        after=new_value,
        reason=data.reason,
    )
    await db.commit()
    return {"id": row.id, "is_active": row.is_active}


@router.get("/companies")
async def cebu_admin_companies(
    db: DB,
    admin: AdminUser,
    type: str | None = None,
    verification_status: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
):
    stmt = select(Company).order_by(Company.created_at.desc()).limit(limit)
    if type:
        stmt = stmt.where(Company.type == type)
    if verification_status:
        stmt = stmt.where(Company.verification_status == verification_status)
    rows = list((await db.execute(stmt)).scalars())
    return _page(
        [
            {
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "country": row.country,
                "city": row.city,
                "verification_status": row.verification_status,
                "operational_status": (row.contact_info or {}).get("operational_status", "active"),
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )


@router.patch("/companies/{company_id}/verification")
async def cebu_admin_update_company_verification(
    company_id: uuid.UUID, data: VerificationUpdate, db: DB, admin: AdminUser
):
    row = await db.get(Company, company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    before = row.verification_status
    row.verification_status = data.verification_status
    await _audit_status(
        db,
        admin,
        action="cebu.admin.company_verification_changed",
        entity_type="company",
        entity_id=row.id,
        before=before,
        after=row.verification_status,
        reason=data.reason,
    )
    await db.commit()
    return {"id": row.id, "verification_status": row.verification_status}


@router.patch("/companies/{company_id}/status")
async def cebu_admin_update_company_status(
    company_id: uuid.UUID, data: CompanyStatusUpdate, db: DB, admin: AdminUser
):
    allowed = {"pending", "active", "restricted", "suspended"}
    if data.status not in allowed:
        raise HTTPException(status_code=422, detail="Invalid company operational status")
    row = await db.get(Company, company_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    contact = dict(row.contact_info or {})
    before = contact.get("operational_status", "active")
    contact["operational_status"] = data.status
    contact["operational_status_reason"] = data.reason
    row.contact_info = contact
    await _audit_status(
        db, admin, action="cebu.admin.company_status_changed", entity_type="company",
        entity_id=row.id, before=before, after=data.status, reason=data.reason,
    )
    await db.commit()
    return {"id": row.id, "operational_status": data.status}


@router.get("/procurement-requests")
async def cebu_admin_requests(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, ProcurementRequest, status=status)
    return _page([ProcurementRequestRead.model_validate(row) for row in rows])


@router.patch("/procurement-requests/{request_id}/status")
async def cebu_admin_update_request(
    request_id: uuid.UUID, data: StatusUpdate, db: DB, admin: AdminUser
):
    if data.status not in PROCUREMENT_REQUEST_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid procurement request status")
    row = await db.get(ProcurementRequest, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Procurement request not found")
    before = row.status
    row.status = data.status
    await _audit_status(
        db, admin, action="cebu.admin.request_status_changed", entity_type="procurement_request",
        entity_id=row.id, before=before, after=row.status, reason=data.reason,
    )
    await db.commit()
    return ProcurementRequestRead.model_validate(row)


@router.get("/offers")
async def cebu_admin_offers(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, SupplierOffer, status=status)
    return _page([SupplierOfferRead.model_validate(row) for row in rows])


@router.patch("/offers/{offer_id}/status")
async def cebu_admin_update_offer(offer_id: uuid.UUID, data: StatusUpdate, db: DB, admin: AdminUser):
    if data.status not in OFFER_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid offer status")
    row = await db.get(SupplierOffer, offer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    before = row.status
    row.status = data.status
    await _audit_status(
        db, admin, action="cebu.admin.offer_status_changed", entity_type="supplier_offer",
        entity_id=row.id, before=before, after=row.status, reason=data.reason,
    )
    await db.commit()
    return SupplierOfferRead.model_validate(row)


@router.get("/orders")
async def cebu_admin_orders(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, CommerceOrder, status=status)
    return _page(
        [
            {
                **CommerceOrderRead.model_validate(row).model_dump(),
                "admin_hold": bool((row.delivery_json or {}).get("admin_hold")),
                "admin_hold_reason": (row.delivery_json or {}).get("admin_hold_reason"),
            }
            for row in rows
        ]
    )


@router.patch("/orders/{order_id}/status")
async def cebu_admin_update_order(order_id: uuid.UUID, data: StatusUpdate, db: DB, admin: AdminUser):
    if data.status not in ORDER_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid order status")
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    before = row.status
    row.status = data.status
    if data.status == "completed" and row.completed_at is None:
        row.completed_at = datetime.now(timezone.utc)
    await _audit_status(
        db, admin, action="cebu.admin.order_status_changed", entity_type="commerce_order",
        entity_id=row.id, before=before, after=row.status, reason=data.reason,
    )
    await db.commit()
    return CommerceOrderRead.model_validate(row)


@router.post("/orders/{order_id}/hold")
async def cebu_admin_hold_order(order_id: uuid.UUID, data: OrderHoldInput, db: DB, admin: AdminUser):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    delivery = dict(row.delivery_json or {})
    before = bool(delivery.get("admin_hold"))
    delivery["admin_hold"] = True
    delivery["admin_hold_reason"] = data.reason
    delivery["admin_hold_by"] = str(admin.id)
    delivery["admin_hold_at"] = datetime.now(timezone.utc).isoformat()
    row.delivery_json = delivery
    await _audit_status(
        db, admin, action="cebu.admin.order_held", entity_type="commerce_order",
        entity_id=row.id, before=before, after=True, reason=data.reason,
    )
    await db.commit()
    return {"id": row.id, "admin_hold": True, "reason": data.reason}


@router.post("/orders/{order_id}/release-hold")
async def cebu_admin_release_order_hold(
    order_id: uuid.UUID, data: OrderHoldInput, db: DB, admin: AdminUser
):
    row = await db.get(CommerceOrder, order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    delivery = dict(row.delivery_json or {})
    before = bool(delivery.get("admin_hold"))
    delivery["admin_hold"] = False
    delivery["admin_hold_release_reason"] = data.reason
    delivery["admin_hold_released_by"] = str(admin.id)
    delivery["admin_hold_released_at"] = datetime.now(timezone.utc).isoformat()
    row.delivery_json = delivery
    await _audit_status(
        db, admin, action="cebu.admin.order_hold_released", entity_type="commerce_order",
        entity_id=row.id, before=before, after=False, reason=data.reason,
    )
    await db.commit()
    return {"id": row.id, "admin_hold": False, "reason": data.reason}


@router.get("/disputes")
async def cebu_admin_disputes(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, OrderDispute, status=status)
    return _page([OrderDisputeRead.model_validate(row) for row in rows])


@router.post("/disputes/{dispute_id}/resolve", response_model=OrderDisputeRead)
async def cebu_admin_resolve_dispute(
    dispute_id: uuid.UUID, data: DisputeResolutionInput, db: DB, admin: AdminUser
):
    from app.services.commerce_trade import CommerceTradeError, resolve_dispute

    current = await db.get(OrderDispute, dispute_id)
    before = current.status if current else None
    try:
        row = await resolve_dispute(
            db,
            dispute_id,
            resolution=data.resolution,
            resolution_json={**(data.resolution_json or {}), "admin_reason": data.reason},
        )
        await _audit_status(
            db, admin, action="cebu.admin.dispute_resolved", entity_type="order_dispute",
            entity_id=row.id, before=before, after=row.status, reason=data.reason,
        )
        await db.commit()
        await db.refresh(row)
        return OrderDisputeRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/risk-flags")
async def cebu_admin_risk_flags(db: DB, admin: AdminUser, status: str | None = "open"):
    rows = await _list_rows(db, RiskFlag, status=status)
    return _page([RiskFlagRead.model_validate(row) for row in rows])


@router.post("/risk-flags", status_code=201)
async def cebu_admin_create_risk_flag(data: RiskFlagCreateInput, db: DB, admin: AdminUser):
    if data.severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid risk severity")
    row = RiskFlag(
        subject_type=data.subject_type,
        subject_id=data.subject_id,
        company_id=data.company_id,
        reason_code=data.reason_code,
        severity=data.severity,
        status="open",
        source_event="cebu.admin.manual",
        details_json=data.details_json,
    )
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.risk_flag_created", entity_type="risk_flag",
        entity_id=row.id, before=None, after=row.status, reason=data.reason_code,
    )
    await db.commit()
    await db.refresh(row)
    return RiskFlagRead.model_validate(row)


@router.post("/risk-flags/{flag_id}/action")
async def cebu_admin_act_on_risk_flag(
    flag_id: uuid.UUID, data: RiskFlagActionInput, db: DB, admin: AdminUser
):
    if data.status not in RISK_FLAG_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid risk flag status")
    row = await db.get(RiskFlag, flag_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found")
    before = row.status
    row.status = data.status
    details = dict(row.details_json or {})
    actions = list(details.get("admin_actions") or [])
    actions.append({
        "action": data.action_taken,
        "status": data.status,
        "actor_user_id": str(admin.id),
        "at": datetime.now(timezone.utc).isoformat(),
    })
    details["admin_actions"] = actions[-50:]
    row.details_json = details
    if data.status != "open":
        row.resolved_at = datetime.now(timezone.utc)
        row.resolved_by_user_id = admin.id
    await _audit_status(
        db, admin, action="cebu.admin.risk_action_taken", entity_type="risk_flag",
        entity_id=row.id, before=before, after=row.status, reason=data.action_taken,
    )
    await db.commit()
    await db.refresh(row)
    return RiskFlagRead.model_validate(row)


@router.patch("/risk-flags/{flag_id}/status")
async def cebu_admin_update_risk_flag(
    flag_id: uuid.UUID, data: StatusUpdate, db: DB, admin: AdminUser
):
    if data.status not in RISK_FLAG_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid risk flag status")
    row = await db.get(RiskFlag, flag_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Risk flag not found")
    before = row.status
    row.status = data.status
    if data.status != "open":
        row.resolved_at = datetime.now(timezone.utc)
        row.resolved_by_user_id = admin.id
    await _audit_status(
        db, admin, action="cebu.admin.risk_status_changed", entity_type="risk_flag",
        entity_id=row.id, before=before, after=row.status, reason=data.reason,
    )
    await db.commit()
    return RiskFlagRead.model_validate(row)


@router.post("/trust-profiles/{profile_id}/adjust")
async def cebu_admin_adjust_trust_profile(
    profile_id: uuid.UUID, data: TrustAdjustmentInput, db: DB, admin: AdminUser
):
    row = await db.get(TrustProfile, profile_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Trust profile not found")
    before = row.trust_score
    row.trust_score = max(0, min(100, row.trust_score + data.delta))
    metrics = dict(row.metrics_json or {})
    adjustments = list(metrics.get("admin_adjustments") or [])
    adjustments.append({
        "delta": data.delta,
        "reason": data.reason,
        "actor_user_id": str(admin.id),
        "at": datetime.now(timezone.utc).isoformat(),
    })
    metrics["admin_adjustments"] = adjustments[-50:]
    row.metrics_json = metrics
    event = TrustScoreEvent(
        trust_profile_id=row.id,
        event_type="ADMIN_ADJUSTED",
        score_delta=row.trust_score - before,
        before_score=before,
        after_score=row.trust_score,
        reason=data.reason,
        related_entity_type="COMPANY",
        related_entity_id=row.company_id,
        created_by=admin.id,
    )
    db.add(event)
    await _audit_status(
        db, admin, action="cebu.admin.trust_score_adjusted", entity_type="trust_profile",
        entity_id=row.id, before=before, after=row.trust_score, reason=data.reason,
    )
    await db.commit()
    await db.refresh(row)
    return {
        "id": row.id,
        "company_id": row.company_id,
        "portal_key": row.portal_key,
        "trust_score": row.trust_score,
        "metrics_json": row.metrics_json,
    }


@router.get("/trust-profiles/{profile_id}/events")
async def cebu_admin_trust_profile_events(
    profile_id: uuid.UUID, db: DB, admin: AdminUser
):
    if await db.get(TrustProfile, profile_id) is None:
        raise HTTPException(status_code=404, detail="Trust profile not found")
    rows = list(
        (
            await db.execute(
                select(TrustScoreEvent)
                .where(TrustScoreEvent.trust_profile_id == profile_id)
                .order_by(TrustScoreEvent.created_at.desc())
            )
        ).scalars()
    )
    return _page([_model_dict(row) for row in rows])


@router.get("/branches")
async def cebu_admin_branches(db: DB, admin: AdminUser, company_id: uuid.UUID | None = None):
    stmt = select(CompanyBranch).order_by(CompanyBranch.created_at.desc())
    if company_id:
        stmt = stmt.where(CompanyBranch.company_id == company_id)
    rows = list((await db.execute(stmt)).scalars())
    return _page([_model_dict(row) for row in rows])


@router.post("/branches", status_code=201)
async def cebu_admin_create_branch(data: CompanyBranchInput, db: DB, admin: AdminUser):
    if await db.get(Company, data.company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if data.status not in {"ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=422, detail="Invalid branch status")
    row = CompanyBranch(**data.model_dump())
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.branch_created", entity_type="company_branch",
        entity_id=row.id, before=None, after=row.status, reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _model_dict(row)


@router.patch("/branches/{branch_id}")
async def cebu_admin_update_branch(
    branch_id: uuid.UUID, data: CompanyBranchPatch, db: DB, admin: AdminUser
):
    row = await db.get(CompanyBranch, branch_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    payload = data.model_dump(exclude_unset=True)
    if payload.get("status") not in {None, "ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=422, detail="Invalid branch status")
    before = row.status
    for key, value in payload.items():
        setattr(row, key, value)
    await _audit_status(
        db, admin, action="cebu.admin.branch_updated", entity_type="company_branch",
        entity_id=row.id, before=before, after=row.status, reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _model_dict(row)


@router.get("/service-areas")
async def cebu_admin_service_areas(db: DB, admin: AdminUser, company_id: uuid.UUID | None = None):
    stmt = select(ServiceArea).order_by(ServiceArea.created_at.desc())
    if company_id:
        stmt = stmt.where(ServiceArea.company_id == company_id)
    rows = list((await db.execute(stmt)).scalars())
    return _page([_model_dict(row) for row in rows])


@router.post("/service-areas", status_code=201)
async def cebu_admin_create_service_area(data: ServiceAreaInput, db: DB, admin: AdminUser):
    if data.company_id and await db.get(Company, data.company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if data.coverage_type not in {"RADIUS", "POLYGON", "ADMIN_REGION"}:
        raise HTTPException(status_code=422, detail="Invalid coverage type")
    if data.status not in {"ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=422, detail="Invalid service area status")
    row = ServiceArea(**data.model_dump())
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.service_area_created", entity_type="service_area",
        entity_id=row.id, before=None, after=row.status, reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _model_dict(row)


@router.patch("/service-areas/{area_id}")
async def cebu_admin_update_service_area(
    area_id: uuid.UUID, data: ServiceAreaPatch, db: DB, admin: AdminUser
):
    row = await db.get(ServiceArea, area_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Service area not found")
    payload = data.model_dump(exclude_unset=True)
    if payload.get("coverage_type") not in {None, "RADIUS", "POLYGON", "ADMIN_REGION"}:
        raise HTTPException(status_code=422, detail="Invalid coverage type")
    if payload.get("status") not in {None, "ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=422, detail="Invalid service area status")
    if payload.get("company_id") and await db.get(Company, payload["company_id"]) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    before = row.status
    for key, value in payload.items():
        setattr(row, key, value)
    await _audit_status(
        db, admin, action="cebu.admin.service_area_updated", entity_type="service_area",
        entity_id=row.id, before=before, after=row.status, reason=row.name,
    )
    await db.commit()
    await db.refresh(row)
    return _model_dict(row)


@router.get("/kyc-media/files")
async def cebu_admin_kyc_media_files(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, CompanyDocument, status=status)
    return _page(
        [
            {
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
            }
            for row in rows
        ]
    )


@router.get("/kyc-media/files/{document_id}")
async def cebu_admin_kyc_media_file(document_id: uuid.UUID, db: DB, admin: AdminUser):
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
    return {
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
        "analyses": [
            {
                "id": analysis.id,
                "authenticity": analysis.authenticity,
                "confidence": analysis.confidence,
                "overall_risk_score": analysis.overall_risk_score,
                "recommended_action": analysis.recommended_action,
                "tamper_suspected": analysis.tamper_suspected,
                "photoshop_suspected": analysis.photoshop_suspected,
                "text_photo_consistency": analysis.text_photo_consistency,
                "detected_issues": analysis.detected_issues,
                "concerns": analysis.concerns,
                "created_at": analysis.created_at,
            }
            for analysis in analyses
        ],
    }


@router.post("/kyc-media/files/{document_id}/flag-risk")
async def cebu_admin_flag_kyc_media(
    document_id: uuid.UUID, data: KycMediaRiskInput, db: DB, admin: AdminUser
):
    if data.severity not in {"low", "medium", "high", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid risk severity")
    document = await db.get(CompanyDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    before = document.status
    document.status = "REJECTED"
    document.reviewer_note = data.note
    document.reviewed_by = admin.id
    document.reviewed_at = datetime.now(timezone.utc)
    flag = RiskFlag(
        subject_type="company_document",
        subject_id=document.id,
        company_id=document.company_id,
        reason_code="kyc_media_risk",
        severity=data.severity,
        status="open",
        source_event="cebu.admin.kyc_media",
        details_json={"note": data.note, "document_type": document.doc_type},
    )
    db.add(flag)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.kyc_media_flagged", entity_type="company_document",
        entity_id=document.id, before=before, after=document.status, reason=data.note,
    )
    await db.commit()
    return {"document_id": document.id, "status": document.status, "risk_flag_id": flag.id}


@router.get("/project-metric-templates")
async def cebu_admin_project_metric_templates(
    db: DB, admin: AdminUser, project_type: str | None = None
):
    stmt = select(ProjectMetricTemplate).order_by(
        ProjectMetricTemplate.project_type, ProjectMetricTemplate.sort_order, ProjectMetricTemplate.key
    )
    if project_type:
        stmt = stmt.where(ProjectMetricTemplate.project_type == project_type.upper())
    rows = list((await db.execute(stmt)).scalars())
    return _page([_metric_template_dict(row) for row in rows])


@router.post("/project-metric-templates", status_code=201)
async def cebu_admin_create_project_metric_template(
    data: ProjectMetricTemplateInput, db: DB, admin: AdminUser
):
    project_type = data.project_type.upper()
    key = data.key.strip().lower()
    exists = (
        await db.execute(
            select(ProjectMetricTemplate).where(
                ProjectMetricTemplate.project_type == project_type,
                ProjectMetricTemplate.key == key,
            )
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Metric template already exists")
    payload = data.model_dump()
    payload.update(project_type=project_type, key=key)
    row = ProjectMetricTemplate(**payload)
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.project_metric_template_created",
        entity_type="project_metric_template", entity_id=row.id,
        before=None, after=row.active, reason=f"{project_type}:{key}",
    )
    await db.commit()
    await db.refresh(row)
    return _metric_template_dict(row)


@router.patch("/project-metric-templates/{template_id}")
async def cebu_admin_update_project_metric_template(
    template_id: uuid.UUID, data: ProjectMetricTemplatePatch, db: DB, admin: AdminUser
):
    row = await db.get(ProjectMetricTemplate, template_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Metric template not found")
    before = row.active
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await _audit_status(
        db, admin, action="cebu.admin.project_metric_template_updated",
        entity_type="project_metric_template", entity_id=row.id,
        before=before, after=row.active, reason=f"{row.project_type}:{row.key}",
    )
    await db.commit()
    await db.refresh(row)
    return _metric_template_dict(row)


@router.get("/payments")
async def cebu_admin_payments(db: DB, admin: AdminUser):
    intents = await _list_admin_workspace_rows(db, admin, CommercePaymentIntent)
    settlements = await _list_admin_workspace_rows(db, admin, CommerceSettlement)
    provider_intents = await _list_admin_workspace_rows(db, admin, ProviderPaymentIntent)
    provider_settlements = await _list_admin_workspace_rows(db, admin, SettlementEvent)
    return {
        "items": [
            {"kind": "payment_intent", **PaymentIntentRead.model_validate(row).model_dump()}
            for row in intents
        ] + [
            {
                "kind": "settlement",
                "id": row.id,
                "commerce_order_id": row.commerce_order_id,
                "status": row.status,
                "amount_minor": row.amount_minor,
                "currency": row.currency,
                "external_ref": row.external_ref,
                "created_at": row.created_at,
            }
            for row in settlements
        ] + [
            {"kind": "provider_payment_intent", **_model_dict(row)}
            for row in provider_intents
        ] + [
            {"kind": "provider_settlement_event", **_model_dict(row)}
            for row in provider_settlements
        ],
        "total": len(intents) + len(settlements) + len(provider_intents) + len(provider_settlements),
    }


@router.get("/payment-configs")
async def cebu_admin_payment_configs(db: DB, admin: AdminUser):
    resources = {
        "regions": RegionPaymentConfig,
        "currencies": CurrencyConfig,
        "methods": PaymentMethodConfig,
        "fee_rules": FeeRule,
    }
    result = {}
    for key, model in resources.items():
        rows = await _list_rows(db, model)
        result[key] = {"items": [_model_dict(row) for row in rows], "total": len(rows)}
    return result


@router.put("/payment-region-configs/{country_code}")
async def cebu_admin_upsert_payment_region_config(
    country_code: str, data: RegionPaymentConfigInput, db: DB, admin: AdminUser
):
    normalized = country_code.upper()[:2]
    if normalized != data.country_code.upper():
        raise HTTPException(status_code=422, detail="Path and payload country codes must match")
    row = (
        await db.execute(
            select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == normalized)
        )
    ).scalar_one_or_none()
    operation = "updated" if row else "created"
    before = row.is_active if row else None
    payload = data.model_dump()
    payload.update(
        country_code=normalized,
        local_currency=data.local_currency.upper(),
        default_settlement_currency=data.default_settlement_currency.upper(),
        default_transaction_mode=data.default_transaction_mode.upper(),
        enabled_currencies=[str(value).upper() for value in data.enabled_currencies],
        enabled_payment_methods=[str(value).upper() for value in data.enabled_payment_methods],
        cross_border_currencies=[str(value).upper() for value in data.cross_border_currencies],
    )
    if row is None:
        row = RegionPaymentConfig(**payload)
        db.add(row)
    else:
        for key, value in payload.items():
            setattr(row, key, value)
    await db.flush()
    await _audit_status(
        db, admin, action=f"cebu.admin.payment_region_config_{operation}",
        entity_type="region_payment_config", entity_id=row.id,
        before=before, after=row.is_active, reason=normalized,
    )
    await db.commit()
    await db.refresh(row)
    return _model_dict(row)


@router.get("/reconciliation/payment-events")
async def cebu_admin_payment_reconciliation(db: DB, admin: AdminUser):
    payment_events = await _list_admin_workspace_rows(db, admin, PaymentEvent)
    settlement_events = await _list_admin_workspace_rows(db, admin, SettlementEvent)
    adjustments = await _list_admin_workspace_rows(db, admin, SettlementAdjustment)
    unmatched = max(0, len(payment_events) - len(settlement_events))
    return {
        "payment_events": [_model_dict(row) for row in payment_events],
        "settlement_events": [_model_dict(row) for row in settlement_events],
        "settlement_adjustments": [_model_dict(row) for row in adjustments],
        "summary": {
            "payment_event_count": len(payment_events),
            "settlement_event_count": len(settlement_events),
            "adjustment_count": len(adjustments),
            "unmatched_payment_events": unmatched,
        },
    }


@router.get("/notifications")
async def cebu_admin_notifications(db: DB, admin: AdminUser, status: str | None = None):
    rows = await _list_rows(db, PortalNotification, status=status)
    return _page([PortalNotificationRead.model_validate(row) for row in rows])


@router.post("/notifications/test", status_code=201)
async def cebu_admin_test_notification(data: NotificationTestInput, db: DB, admin: AdminUser):
    row = PortalNotification(
        user_id=admin.id,
        portal_key="admin_cebu",
        domain="commerce",
        event_type="cebu.admin.test",
        title=data.title,
        body=data.body,
        link_path="/cebu-admin/notifications",
    )
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.notification_tested", entity_type="portal_notification",
        entity_id=row.id, before=None, after=row.status, reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return PortalNotificationRead.model_validate(row)


@router.post("/notes", status_code=201)
async def cebu_admin_create_note(data: AdminNoteInput, db: DB, admin: AdminUser):
    if data.visibility not in {"internal_only", "risk_team", "finance_team"}:
        raise HTTPException(status_code=422, detail="Invalid note visibility")
    row = AdminNote(
        portal_key="admin_cebu",
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        author_id=admin.id,
        visibility=data.visibility,
        note=data.note,
    )
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.note_created", entity_type=data.entity_type,
        entity_id=data.entity_id, before=None, after=data.visibility, reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return _note_dict(row)


@router.get("/notes/{entity_type}/{entity_id}")
async def cebu_admin_entity_notes(entity_type: str, entity_id: uuid.UUID, db: DB, admin: AdminUser):
    rows = list(
        (
            await db.execute(
                select(AdminNote)
                .where(
                    AdminNote.portal_key == "admin_cebu",
                    AdminNote.entity_type == entity_type,
                    AdminNote.entity_id == entity_id,
                )
                .order_by(AdminNote.created_at.desc())
            )
        ).scalars()
    )
    return _page([_note_dict(row) for row in rows])


@router.get("/notification-templates")
async def cebu_admin_notification_templates(db: DB, admin: AdminUser):
    rows = list(
        (
            await db.execute(
                select(NotificationTemplate)
                .where(NotificationTemplate.portal_key == "admin_cebu")
                .order_by(NotificationTemplate.template_key)
            )
        ).scalars()
    )
    return _page([_template_dict(row) for row in rows])


@router.put("/notification-templates/{template_key}")
async def cebu_admin_upsert_notification_template(
    template_key: str, data: NotificationTemplateInput, db: DB, admin: AdminUser
):
    row = (
        await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.portal_key == "admin_cebu",
                NotificationTemplate.template_key == template_key,
                NotificationTemplate.channel == data.channel,
                NotificationTemplate.language == data.language,
            )
        )
    ).scalar_one_or_none()
    operation = "updated" if row else "created"
    if row is None:
        row = NotificationTemplate(
            portal_key="admin_cebu",
            template_key=template_key,
            channel=data.channel,
            language=data.language,
            body=data.body,
        )
        db.add(row)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    await db.flush()
    await _audit_status(
        db, admin, action=f"cebu.admin.notification_template_{operation}",
        entity_type="notification_template", entity_id=row.id,
        before=None, after=row.active, reason=template_key,
    )
    await db.commit()
    await db.refresh(row)
    return _template_dict(row)


@router.get("/settings")
async def cebu_admin_settings(db: DB, admin: AdminUser):
    rows = list(
        (
            await db.execute(
                select(PlatformSetting)
                .where(PlatformSetting.portal_key == "admin_cebu")
                .order_by(PlatformSetting.key)
            )
        ).scalars()
    )
    return _page([_setting_dict(row) for row in rows])


@router.put("/settings/{key}")
async def cebu_admin_upsert_setting(
    key: str, data: PlatformSettingInput, db: DB, admin: AdminUser
):
    normalized_key = key.strip().lower()
    if any(part in normalized_key for part in ("password", "secret", "token", "api_key")):
        raise HTTPException(status_code=422, detail="Secrets belong in the integration secret store")
    row = (
        await db.execute(
            select(PlatformSetting).where(
                PlatformSetting.portal_key == "admin_cebu",
                PlatformSetting.key == normalized_key,
            )
        )
    ).scalar_one_or_none()
    before = row.value_json if row else None
    operation = "updated" if row else "created"
    if row is None:
        row = PlatformSetting(portal_key="admin_cebu", key=normalized_key, value_json={})
        db.add(row)
    row.value_json = data.value_json
    row.description = data.description
    row.updated_by = admin.id
    await db.flush()
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        portal_key="admin_cebu",
        action=f"cebu.admin.platform_setting_{operation}",
        entity_type="platform_setting",
        entity_id=row.id,
        before={"value_json": before},
        after={"value_json": row.value_json},
        source="admin.cebu",
    )
    await db.commit()
    await db.refresh(row)
    return _setting_dict(row)


@router.get("/audit-logs")
async def cebu_admin_audit_logs(db: DB, admin: AdminUser, action: str | None = None):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(300)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    rows = list((await db.execute(stmt)).scalars())
    return _page([AuditLogRead.model_validate(row) for row in rows])


@router.get("/trade")
async def cebu_admin_trade_resources(db: DB, admin: AdminUser):
    resources = {
        "shipping_routes": (ShippingRoute, None),
        "shipping_rates": (ShippingRate, None),
        "ad_campaigns": (AdCampaign, None),
        "escrow": (EscrowTransaction, None),
        "payouts": (Payout, None),
        "deposits": (WalletDeposit, None),
        "kyc_documents": (CompanyDocument, None),
        "verification_queue": (VerificationReview, None),
        "supplier_listings": (SupplierListing, None),
        "category_schemas": (TradeCategorySchema, None),
        "trust_profiles": (TrustProfile, None),
    }
    result: dict[str, dict] = {}
    for key, (model, status) in resources.items():
        rows = await _list_rows(db, model, status=status)
        result[key] = {
            "items": [
                {
                    column.name: getattr(row, column.name)
                    for column in model.__table__.columns
                    if column.name not in {"raw_event_json"}
                }
                for row in rows
            ],
            "total": len(rows),
        }
    return result


def _backup_schedule_dict(row: BackupSchedule) -> dict:
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
        "created_at": row.created_at,
    }


def _backup_job_dict(row: BackupJob) -> dict:
    return {
        "id": row.id,
        "schedule_id": row.schedule_id,
        "status": row.status,
        "archive_size_bytes": row.archive_size_bytes,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "error_message": row.error_message,
        "created_at": row.created_at,
    }


@router.get("/backups/schedules")
async def cebu_admin_backup_schedules(db: DB, admin: AdminUser):
    rows = await _list_rows(db, BackupSchedule)
    return _page([_backup_schedule_dict(row) for row in rows])


@router.post("/backups/schedules", status_code=201)
async def cebu_admin_create_backup_schedule(data: BackupScheduleInput, db: DB, admin: AdminUser):
    if data.frequency not in ("WEEKLY", "MONTHLY", "CUSTOM"):
        raise HTTPException(status_code=422, detail="Invalid backup frequency")
    row = BackupSchedule(**data.model_dump(), created_by=admin.id)
    row.next_run_at = next_run_at_for_schedule(row)
    db.add(row)
    await db.flush()
    await _audit_status(
        db, admin, action="cebu.admin.backup_schedule_created", entity_type="backup_schedule",
        entity_id=row.id, before=None, after=row.frequency, reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_schedule_dict(row)


@router.patch("/backups/schedules/{schedule_id}")
async def cebu_admin_update_backup_schedule(
    schedule_id: uuid.UUID, data: BackupScheduleInput, db: DB, admin: AdminUser
):
    row = await db.get(BackupSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Backup schedule not found")
    before = row.frequency
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    row.next_run_at = next_run_at_for_schedule(row)
    await _audit_status(
        db, admin, action="cebu.admin.backup_schedule_updated", entity_type="backup_schedule",
        entity_id=row.id, before=before, after=row.frequency, reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_schedule_dict(row)


@router.delete("/backups/schedules/{schedule_id}", status_code=204)
async def cebu_admin_delete_backup_schedule(schedule_id: uuid.UUID, db: DB, admin: AdminUser):
    row = await db.get(BackupSchedule, schedule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Backup schedule not found")
    await _audit_status(
        db, admin, action="cebu.admin.backup_schedule_deleted", entity_type="backup_schedule",
        entity_id=row.id, before=row.frequency, after=None, reason=None,
    )
    await db.delete(row)
    await db.commit()


@router.post("/backups/manual")
async def cebu_admin_manual_backup(db: DB, admin: AdminUser):
    row = await create_backup_archive(db, created_by=admin.id)
    await _audit_status(
        db, admin, action="cebu.admin.backup_executed", entity_type="backup_job",
        entity_id=row.id, before=None, after=row.status, reason=None,
    )
    await db.commit()
    await db.refresh(row)
    return _backup_job_dict(row)


@router.get("/backups/jobs")
async def cebu_admin_backup_jobs(
    db: DB, admin: AdminUser, limit: int = Query(default=50, ge=1, le=500)
):
    rows = await _list_rows(db, BackupJob, limit=limit)
    return _page([_backup_job_dict(row) for row in rows])


@router.get("/backups/jobs/{job_id}/download")
async def cebu_admin_download_backup(job_id: uuid.UUID, db: DB, admin: AdminUser):
    row = await db.get(BackupJob, job_id)
    if row is None or not row.archive_path:
        raise HTTPException(status_code=404, detail="Backup archive not found")
    path = Path(row.archive_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Backup archive not found")
    return FileResponse(path, media_type="application/zip", filename=path.name)

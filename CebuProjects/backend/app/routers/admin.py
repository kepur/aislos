"""Admin console API — full enterprise operations surface."""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.models.admin_note import AdminNote
from app.models.audit_log import AuditLog, RiskLevel
from app.models.backup import BackupFrequency, BackupJob, BackupSchedule
from app.models.buyer_project import ProjectAIRun, ProjectMessage, ProjectMetricTemplate, ProjectType
from app.models.company import Company, CompanyStatus, VerificationLevel
from app.models.company_document import CompanyDocument, DocumentStatus
from app.models.dispute import Dispute, DisputeStatus
from app.models.escrow import EscrowStatus, EscrowTransaction
from app.models.intent import Intent, IntentStatus
from app.models.kyc_analysis import KYCAnalysisResult
from app.models.notification import Notification, NotificationChannel
from app.models.notification_template import NotificationTemplate
from app.models.offer import Offer, OfferStatus
from app.models.order import Order, OrderStatus
from app.models.payment_event import PaymentEvent
from app.models.platform_setting import PlatformSetting
from app.models.payout import Payout, PayoutStatus
from app.models.risk_flag import RiskFlag, RiskFlagStatus
from app.models.user import ADMIN_ROLES, User, UserRole, UserStatus
from app.models.verification_review import VerificationDecision, VerificationQueueStatus, VerificationReview
from app.schemas.admin import (
    AdminNoteCreate,
    AdminNoteResponse,
    EscrowManualVerifyRequest,
    EscrowRefundRequest,
    EscrowReleaseRequest,
    IntentModerateRequest,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
    OfferRemoveRequest,
    OrderHoldRequest,
    PaymentEventResponse,
    PayoutResponse,
    PlatformSettingResponse,
    PlatformSettingUpdate,
    RiskFlagActionRequest,
    RiskFlagCreate,
    RiskFlagResponse,
    StaffInviteRequest,
    StaffRoleUpdateRequest,
    UserDetailResponse,
    UserStatusUpdateRequest,
    VerificationDecisionRequest,
    VerificationReviewResponse,
)
from app.schemas.audit_log import AuditLogResponse
from app.schemas.buyer_project import (
    ProjectMetricTemplateCreate,
    ProjectMetricTemplateResponse,
    ProjectMetricTemplateUpdate,
)
from app.schemas.company import CompanyResponse
from app.schemas.dispute import DisputeResponse
from app.schemas.escrow import EscrowResponse
from app.schemas.intent import IntentResponse
from app.schemas.offer import OfferResponse
from app.schemas.order import OrderResponse
from app.schemas.user import UserResponse
from app.services.audit_service import create_audit_log
from app.services.backup_service import create_backup_archive, next_run_at_for_schedule
from app.services.escrow_service import refund_escrow, release_escrow
from app.services.maps_config_service import get_maps_config
from app.services.notification_service import create_notification

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(*extra_roles: UserRole):
    """Accepts ADMIN, SUPER_ADMIN, plus any extra roles passed."""
    return require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, *extra_roles)


# ══════════════════════════════════════════════════════
# DASHBOARD & LIVE OPS
# ══════════════════════════════════════════════════════

@router.get("/dashboard")
async def dashboard(
    user: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    users_total = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    buyers = (await db.execute(select(func.count()).select_from(User).where(User.role == UserRole.BUYER))).scalar() or 0
    suppliers = (await db.execute(select(func.count()).select_from(User).where(User.role.in_([UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT])))).scalar() or 0
    active_intents = (await db.execute(select(func.count()).select_from(Intent).where(Intent.status == IntentStatus.ACTIVE))).scalar() or 0
    open_disputes = (await db.execute(select(func.count()).select_from(Dispute).where(Dispute.status == DisputeStatus.OPENED))).scalar() or 0
    pending_verif = (await db.execute(select(func.count()).select_from(VerificationReview).where(VerificationReview.status == VerificationQueueStatus.SUBMITTED))).scalar() or 0
    orders_escrow = (await db.execute(select(func.count()).select_from(Order).where(Order.status == OrderStatus.PAID_IN_ESCROW))).scalar() or 0
    open_risk = (await db.execute(select(func.count()).select_from(RiskFlag).where(RiskFlag.status == RiskFlagStatus.OPEN))).scalar() or 0

    escrow_held = (await db.execute(
        select(func.coalesce(func.sum(EscrowTransaction.captured_amount_minor), 0))
        .where(EscrowTransaction.status == EscrowStatus.CAPTURED)
    )).scalar() or 0

    return {
        "users_total": users_total,
        "buyers_total": buyers,
        "suppliers_total": suppliers,
        "active_intents": active_intents,
        "open_disputes": open_disputes,
        "pending_company_verifications": pending_verif,
        "orders_in_escrow": orders_escrow,
        "open_risk_flags": open_risk,
        "escrow_held_minor": escrow_held,
    }


@router.get("/live-ops")
async def live_ops(
    user: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    active_intents = (await db.execute(select(func.count()).select_from(Intent).where(Intent.status == IntentStatus.ACTIVE))).scalar() or 0
    awaiting_delivery = (await db.execute(select(func.count()).select_from(Order).where(Order.status == OrderStatus.IN_PROGRESS))).scalar() or 0
    awaiting_acceptance = (await db.execute(select(func.count()).select_from(Order).where(Order.status == OrderStatus.DELIVERED))).scalar() or 0
    new_disputes = (await db.execute(select(func.count()).select_from(Dispute).where(Dispute.status == DisputeStatus.OPENED))).scalar() or 0

    return {
        "active_intents": active_intents,
        "orders_awaiting_delivery": awaiting_delivery,
        "orders_awaiting_acceptance": awaiting_acceptance,
        "new_disputes_today": new_disputes,
    }


# ══════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
    role: UserRole | None = None,
    status: UserStatus | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(User)
    if role:
        q = q.where(User.role == role)
    if status:
        q = q.where(User.status == status)
    result = await db.execute(q.order_by(User.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return target


@router.post("/users/{user_id}/status", response_model=UserDetailResponse)
async def update_user_status(
    user_id: str,
    req: UserStatusUpdateRequest,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    old_status = target.status
    target.status = req.status

    risk = RiskLevel.CRITICAL if req.status in (UserStatus.SUSPENDED, UserStatus.BANNED) else RiskLevel.HIGH
    await create_audit_log(
        db, action="USER_SUSPENDED" if req.status == UserStatus.SUSPENDED else "ADMIN_MANUAL_ACTION",
        entity_type="User", entity_id=target.id, actor_id=admin.id, actor_role=admin.role.value,
        before_json={"status": old_status.value},
        after_json={"status": req.status.value, "reason_code": req.reason_code, "reason_text": req.reason_text},
        risk_level=risk,
    )
    await db.commit()
    await db.refresh(target)
    return target


# ══════════════════════════════════════════════════════
# STAFF MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/staff", response_model=list[UserDetailResponse])
async def list_staff(
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.role.in_(list(ADMIN_ROLES))).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/staff/invite", response_model=UserDetailResponse, status_code=201)
async def invite_staff(
    req: StaffInviteRequest,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if req.role not in ADMIN_ROLES:
        raise HTTPException(status_code=400, detail="Role must be an admin role")

    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    staff = User(
        email=req.email,
        full_name=req.full_name,
        password_hash=hash_password(req.password),
        role=req.role,
        status=UserStatus.ACTIVE,
    )
    db.add(staff)
    await db.flush()

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="User", entity_id=staff.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "staff_invited", "role": req.role.value},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(staff)
    return staff


@router.put("/staff/{staff_id}/role", response_model=UserDetailResponse)
async def update_staff_role(
    staff_id: str,
    req: StaffRoleUpdateRequest,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == staff_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Staff not found")

    old_role = target.role
    target.role = req.role

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="User", entity_id=target.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json={"role": old_role.value},
        after_json={"role": req.role.value, "reason": req.reason},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    await db.refresh(target)
    return target


# ══════════════════════════════════════════════════════
# COMPANY & VERIFICATION
# ══════════════════════════════════════════════════════

@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
    status: CompanyStatus | None = None,
    verification_level: VerificationLevel | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(Company)
    if status:
        q = q.where(Company.status == status)
    if verification_level:
        q = q.where(Company.verification_level == verification_level)
    result = await db.execute(q.order_by(Company.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.patch("/companies/{company_id}/verification", response_model=CompanyResponse)
async def update_verification(
    company_id: str,
    level: VerificationLevel,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    old = company.verification_level
    company.verification_level = level
    await create_audit_log(
        db, action="COMPANY_VERIFICATION_CHANGED", entity_type="Company", entity_id=company.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json={"verification_level": old.value}, after_json={"verification_level": level.value},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(company)
    return company


@router.patch("/companies/{company_id}/status", response_model=CompanyResponse)
async def update_company_status(
    company_id: str,
    status: CompanyStatus,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    old = company.status
    company.status = status
    await create_audit_log(
        db, action="COMPANY_SUSPENDED" if status == CompanyStatus.SUSPENDED else "ADMIN_MANUAL_ACTION",
        entity_type="Company", entity_id=company.id, actor_id=admin.id, actor_role=admin.role.value,
        before_json={"status": old.value}, after_json={"status": status.value},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    await db.refresh(company)
    return company


# ── Verification Queue ──

@router.get("/verification/queue", response_model=list[VerificationReviewResponse])
async def list_verification_queue(
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
    status: VerificationQueueStatus | None = None,
):
    q = select(VerificationReview)
    if status:
        q = q.where(VerificationReview.status == status)
    result = await db.execute(q.order_by(VerificationReview.created_at.asc()))
    return result.scalars().all()


@router.post("/verification/{company_id}/submit", response_model=VerificationReviewResponse, status_code=201)
async def submit_for_verification(
    company_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(VerificationReview).where(VerificationReview.company_id == company_id))
    review = existing.scalar_one_or_none()
    if review:
        review.status = VerificationQueueStatus.SUBMITTED
    else:
        review = VerificationReview(company_id=company_id, status=VerificationQueueStatus.SUBMITTED)
        db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.post("/verification/{company_id}/decide", response_model=VerificationReviewResponse)
async def decide_verification(
    company_id: str,
    req: VerificationDecisionRequest,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VerificationReview).where(VerificationReview.company_id == company_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Verification review not found")

    review.decision = req.decision
    review.decision_reason = req.decision_reason
    review.internal_note = req.internal_note
    review.user_facing_note = req.user_facing_note
    review.decided_at = datetime.now(timezone.utc)
    review.decided_by = admin.id

    # Update company verification level accordingly
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if company:
        if req.decision == VerificationDecision.APPROVE_BASIC:
            company.verification_level = VerificationLevel.BASIC
            company.status = CompanyStatus.ACTIVE
            review.status = VerificationQueueStatus.APPROVED_BASIC
        elif req.decision == VerificationDecision.APPROVE_BUSINESS:
            company.verification_level = VerificationLevel.BUSINESS
            company.status = CompanyStatus.ACTIVE
            review.status = VerificationQueueStatus.APPROVED_BUSINESS
        elif req.decision == VerificationDecision.REJECT:
            review.status = VerificationQueueStatus.REJECTED
        elif req.decision == VerificationDecision.REQUEST_MORE_INFO:
            review.status = VerificationQueueStatus.NEEDS_MORE_INFO
        elif req.decision == VerificationDecision.ESCALATE_TO_RISK:
            review.status = VerificationQueueStatus.IN_REVIEW

    await create_audit_log(
        db, action="COMPANY_VERIFICATION_CHANGED", entity_type="Company", entity_id=company.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"decision": req.decision.value, "reason": req.decision_reason},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/verification/{company_id}/documents", response_model=list)
async def list_company_documents(
    company_id: str,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CompanyDocument).where(CompanyDocument.company_id == company_id))
    docs = result.scalars().all()
    return [{"id": str(d.id), "doc_type": d.doc_type.value, "file_url": d.file_url, "status": d.status.value, "created_at": d.created_at.isoformat()} for d in docs]


# ══════════════════════════════════════════════════════
# INTENT MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/intents", response_model=list[IntentResponse])
async def list_intents(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
    status: IntentStatus | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(Intent)
    if status:
        q = q.where(Intent.status == status)
    result = await db.execute(q.order_by(Intent.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/intents/{intent_id}", response_model=IntentResponse)
async def get_intent_detail(
    intent_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    return intent


@router.post("/intents/{intent_id}/moderate")
async def moderate_intent(
    intent_id: str,
    req: IntentModerateRequest,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    old_status = intent.status
    if req.action == "cancel":
        intent.status = IntentStatus.CANCELED
    elif req.action == "expire":
        intent.status = IntentStatus.EXPIRED

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="Intent", entity_id=intent.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json={"status": old_status.value},
        after_json={"action": req.action, "reason": req.reason},
        risk_level=RiskLevel.MEDIUM,
    )
    await db.commit()
    return {"id": str(intent.id), "status": intent.status.value}


# ══════════════════════════════════════════════════════
# OFFER MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/offers", response_model=list[OfferResponse])
async def list_offers(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
    status: OfferStatus | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(Offer)
    if status:
        q = q.where(Offer.status == status)
    result = await db.execute(q.order_by(Offer.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer_detail(
    offer_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.post("/offers/{offer_id}/remove")
async def remove_offer(
    offer_id: str,
    req: OfferRemoveRequest,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    offer.status = OfferStatus.REJECTED
    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="Offer", entity_id=offer.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "offer_removed", "reason": req.reason},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    return {"id": str(offer.id), "status": offer.status.value}


# ══════════════════════════════════════════════════════
# ORDER MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.FINANCE_OFFICER, UserRole.DISPUTE_AGENT)),
    db: AsyncSession = Depends(get_db),
    status: OrderStatus | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(Order)
    if status:
        q = q.where(Order.status == status)
    result = await db.execute(q.order_by(Order.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.FINANCE_OFFICER, UserRole.DISPUTE_AGENT, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: str,
    new_status: OrderStatus,
    reason: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    order.status = new_status

    await create_audit_log(
        db, action="ORDER_STATUS_CHANGED", entity_type="Order", entity_id=order.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json={"status": old_status.value},
        after_json={"status": new_status.value, "reason": reason},
        risk_level=RiskLevel.HIGH,
    )
    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="Order", entity_id=order.id,
        actor_id=admin.id, actor_role=admin.role.value, risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/orders/{order_id}/hold")
async def hold_order(
    order_id: str,
    req: OrderHoldRequest,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="Order", entity_id=order.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "hold", "reason": req.reason},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    return {"id": str(order.id), "message": "Order flagged for hold review"}


# ══════════════════════════════════════════════════════
# ESCROW MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/escrow", response_model=list[EscrowResponse])
async def list_escrow(
    admin: User = Depends(_require_admin(UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
    status: EscrowStatus | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(EscrowTransaction)
    if status:
        q = q.where(EscrowTransaction.status == status)
    result = await db.execute(q.order_by(EscrowTransaction.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/escrow/{escrow_id}", response_model=EscrowResponse)
async def get_escrow_detail(
    escrow_id: str,
    admin: User = Depends(_require_admin(UserRole.FINANCE_OFFICER, UserRole.DISPUTE_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.id == escrow_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Escrow transaction not found")
    return tx


@router.post("/escrow/{escrow_id}/release")
async def admin_release_escrow(
    escrow_id: str,
    req: EscrowReleaseRequest,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.id == escrow_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if tx.status not in (EscrowStatus.CAPTURED, EscrowStatus.AUTH_HELD):
        raise HTTPException(status_code=400, detail="Escrow cannot be released in current status")

    await release_escrow(db, tx)

    # Update linked order
    order_result = await db.execute(select(Order).where(Order.id == tx.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.PAYOUT_RELEASED

    await create_audit_log(
        db, action="ESCROW_STATUS_CHANGED", entity_type="EscrowTransaction", entity_id=tx.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "release", "reason_code": req.reason_code, "reason_text": req.reason_text},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    return {"id": str(tx.id), "status": tx.status.value}


@router.post("/escrow/{escrow_id}/refund")
async def admin_refund_escrow(
    escrow_id: str,
    req: EscrowRefundRequest,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.id == escrow_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Escrow not found")

    await refund_escrow(db, tx, req.amount_minor)

    await create_audit_log(
        db, action="ESCROW_STATUS_CHANGED", entity_type="EscrowTransaction", entity_id=tx.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "refund", "amount": req.amount_minor, "reason_code": req.reason_code, "reason_text": req.reason_text},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    return {"id": str(tx.id), "status": tx.status.value, "refunded_minor": tx.refunded_amount_minor}


@router.post("/escrow/{escrow_id}/manual-verify")
async def manual_verify_payment(
    escrow_id: str,
    req: EscrowManualVerifyRequest,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.id == escrow_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Escrow not found")

    tx.status = EscrowStatus.CAPTURED
    tx.captured_amount_minor = req.received_amount_minor
    tx.raw_event_json = {
        "manual_verify": True,
        "payment_method": req.payment_method,
        "reference": req.reference,
        "note": req.note,
        "verified_by": str(admin.id),
    }

    order_result = await db.execute(select(Order).where(Order.id == tx.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.PAID_IN_ESCROW

    await create_audit_log(
        db, action="ESCROW_STATUS_CHANGED", entity_type="EscrowTransaction", entity_id=tx.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"action": "manual_verify", "method": req.payment_method, "amount": req.received_amount_minor},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    return {"id": str(tx.id), "status": tx.status.value}


# ══════════════════════════════════════════════════════
# PAYMENT EVENTS & PAYOUTS
# ══════════════════════════════════════════════════════

@router.get("/payment-events", response_model=list[PaymentEventResponse])
async def list_payment_events(
    admin: User = Depends(_require_admin(UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
    provider: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(PaymentEvent)
    if provider:
        q = q.where(PaymentEvent.provider == provider)
    if event_type:
        q = q.where(PaymentEvent.event_type == event_type)
    result = await db.execute(q.order_by(PaymentEvent.received_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/payouts", response_model=list[PayoutResponse])
async def list_payouts(
    admin: User = Depends(_require_admin(UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
    status: PayoutStatus | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(Payout)
    if status:
        q = q.where(Payout.status == status)
    result = await db.execute(q.order_by(Payout.created_at.desc()).limit(limit))
    return result.scalars().all()


# ══════════════════════════════════════════════════════
# DISPUTES
# ══════════════════════════════════════════════════════

@router.get("/disputes", response_model=list[DisputeResponse])
async def list_disputes(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.DISPUTE_AGENT)),
    db: AsyncSession = Depends(get_db),
    status: DisputeStatus | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(Dispute)
    if status:
        q = q.where(Dispute.status == status)
    result = await db.execute(q.order_by(Dispute.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
async def get_dispute_detail(
    dispute_id: str,
    admin: User = Depends(_require_admin(UserRole.DISPUTE_AGENT, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@router.post("/disputes/{dispute_id}/request-evidence")
async def request_dispute_evidence(
    dispute_id: str,
    from_party: str,  # "buyer" or "supplier"
    admin: User = Depends(_require_admin(UserRole.DISPUTE_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute.status = (
        DisputeStatus.WAITING_BUYER_EVIDENCE
        if from_party == "buyer"
        else DisputeStatus.WAITING_SUPPLIER_EVIDENCE
    )
    await db.commit()
    return {"id": str(dispute.id), "status": dispute.status.value}


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: str,
    decision: str,
    refund_amount_minor: int | None = None,
    resolution: str | None = None,
    admin: User = Depends(_require_admin(UserRole.DISPUTE_AGENT, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    result = await db.execute(select(Order).where(Order.id == dispute.order_id))
    order = result.scalar_one_or_none()
    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == dispute.order_id))
    escrow = result.scalar_one_or_none()

    dispute.resolution = resolution
    dispute.refund_amount_minor = refund_amount_minor

    if decision == "FULL_REFUND":
        dispute.status = DisputeStatus.RESOLVED_REFUND
        if order:
            order.status = OrderStatus.REFUNDED
        if escrow:
            await refund_escrow(db, escrow)
    elif decision == "PARTIAL_REFUND":
        dispute.status = DisputeStatus.RESOLVED_PARTIAL_REFUND
        if escrow and refund_amount_minor:
            await refund_escrow(db, escrow, refund_amount_minor)
        if order:
            order.status = OrderStatus.REFUNDED
    elif decision == "RELEASE_TO_SUPPLIER":
        dispute.status = DisputeStatus.RESOLVED_RELEASE
        if order:
            order.status = OrderStatus.PAYOUT_RELEASED
        if escrow:
            await release_escrow(db, escrow)
    elif decision == "ESCALATE":
        dispute.status = DisputeStatus.ESCALATED

    await create_audit_log(
        db, action="DISPUTE_RESOLVED", entity_type="Dispute", entity_id=dispute.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"decision": decision, "refund_amount": refund_amount_minor},
        risk_level=RiskLevel.CRITICAL,
    )
    await db.commit()
    await db.refresh(dispute)
    return dispute


# ══════════════════════════════════════════════════════
# RISK FLAGS
# ══════════════════════════════════════════════════════

@router.get("/risk-flags", response_model=list[RiskFlagResponse])
async def list_risk_flags(
    admin: User = Depends(_require_admin(UserRole.RISK_ANALYST, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
    status: RiskFlagStatus | None = None,
    entity_type: str | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(RiskFlag)
    if status:
        q = q.where(RiskFlag.status == status)
    if entity_type:
        q = q.where(RiskFlag.entity_type == entity_type)
    result = await db.execute(q.order_by(RiskFlag.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.post("/risk-flags", response_model=RiskFlagResponse, status_code=201)
async def create_risk_flag(
    req: RiskFlagCreate,
    admin: User = Depends(_require_admin(UserRole.RISK_ANALYST, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    flag = RiskFlag(**req.model_dump())
    db.add(flag)
    await db.flush()
    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="RiskFlag", entity_id=flag.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"risk_type": req.risk_type.value, "entity": req.entity_type},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(flag)
    return flag


@router.get("/risk-flags/{flag_id}", response_model=RiskFlagResponse)
async def get_risk_flag(
    flag_id: str,
    admin: User = Depends(_require_admin(UserRole.RISK_ANALYST, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RiskFlag).where(RiskFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Risk flag not found")
    return flag


@router.post("/risk-flags/{flag_id}/action", response_model=RiskFlagResponse)
async def act_on_risk_flag(
    flag_id: str,
    req: RiskFlagActionRequest,
    admin: User = Depends(_require_admin(UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RiskFlag).where(RiskFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Risk flag not found")

    flag.status = req.status
    flag.action_taken = req.action_taken
    if req.status in (RiskFlagStatus.MITIGATED, RiskFlagStatus.FALSE_POSITIVE, RiskFlagStatus.ACTION_TAKEN, RiskFlagStatus.CLOSED):
        flag.resolved_by = admin.id
        flag.resolved_at = datetime.now(timezone.utc)

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="RiskFlag", entity_id=flag.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json={"status": req.status.value, "action": req.action_taken},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(flag)
    return flag


# ══════════════════════════════════════════════════════
# ADMIN NOTES
# ══════════════════════════════════════════════════════

@router.post("/notes", response_model=AdminNoteResponse, status_code=201)
async def create_admin_note(
    req: AdminNoteCreate,
    admin: User = Depends(require_roles(*list(ADMIN_ROLES))),
    db: AsyncSession = Depends(get_db),
):
    note = AdminNote(**req.model_dump(), author_id=admin.id)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/notes/{entity_type}/{entity_id}", response_model=list[AdminNoteResponse])
async def list_entity_notes(
    entity_type: str,
    entity_id: str,
    admin: User = Depends(require_roles(*list(ADMIN_ROLES))),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminNote)
        .where(AdminNote.entity_type == entity_type, AdminNote.entity_id == entity_id)
        .order_by(AdminNote.created_at.desc())
    )
    return result.scalars().all()


# ══════════════════════════════════════════════════════
# NOTIFICATION TEMPLATES
# ══════════════════════════════════════════════════════

@router.get("/notification-templates", response_model=list[NotificationTemplateResponse])
async def list_notification_templates(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.template_key))
    return result.scalars().all()


@router.put("/notification-templates/{template_key}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_key: str,
    req: NotificationTemplateUpdate,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.template_key == template_key))
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)

    await create_audit_log(
        db, action="ADMIN_MANUAL_ACTION", entity_type="NotificationTemplate", entity_id=tpl.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json=req.model_dump(exclude_unset=True),
        risk_level=RiskLevel.LOW,
    )
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.post("/notifications/test")
async def test_notification(
    channel: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    ch = NotificationChannel(channel.upper())
    n = await create_notification(
        db, user_id=admin.id, channel=ch,
        notification_type="ADMIN_TEST",
        subject="Test Notification",
        body="This is a test notification from the admin console.",
    )
    await db.commit()
    return {"status": n.status.value, "channel": channel}


# ══════════════════════════════════════════════════════
# PLATFORM SETTINGS
# ══════════════════════════════════════════════════════

@router.get("/settings", response_model=list[PlatformSettingResponse])
async def list_settings(
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PlatformSetting).order_by(PlatformSetting.key))
    return result.scalars().all()


@router.put("/settings/{key}", response_model=PlatformSettingResponse)
async def update_setting(
    key: str,
    req: PlatformSettingUpdate,
    admin: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        setting = PlatformSetting(key=key, value=req.value, updated_by=admin.id)
        db.add(setting)
    else:
        old_value = setting.value
        setting.value = req.value
        setting.updated_by = admin.id
        await create_audit_log(
            db, action="ADMIN_MANUAL_ACTION", entity_type="PlatformSetting",
            actor_id=admin.id, actor_role=admin.role.value,
            before_json={"key": key, "value": old_value},
            after_json={"key": key, "value": req.value},
            risk_level=RiskLevel.HIGH,
        )
    await db.commit()
    await db.refresh(setting)
    return setting


# ══════════════════════════════════════════════════════
# AUDIT LOGS
# ══════════════════════════════════════════════════════

@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    admin: User = Depends(_require_admin(UserRole.AUDITOR, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
    action: str | None = None,
    entity_type: str | None = None,
    risk_level: RiskLevel | None = None,
    actor_id: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if risk_level:
        q = q.where(AuditLog.risk_level == risk_level)
    if actor_id:
        q = q.where(AuditLog.actor_id == actor_id)
    result = await db.execute(q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    admin: User = Depends(_require_admin(UserRole.AUDITOR, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


# ══════════════════════════════════════════════════════
# MAPS CONFIG
# ══════════════════════════════════════════════════════


def _mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return value[:4] + "***" + value[-4:]


async def _upsert_platform_setting(db: AsyncSession, key: str, value: str, admin_id: uuid.UUID) -> None:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
        setting.updated_by = admin_id
    else:
        db.add(PlatformSetting(key=key, value=value, updated_by=admin_id))


@router.get("/maps/config")
async def get_maps_config_endpoint(
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    cfg = await get_maps_config(db)
    cfg["google_maps_api_key_masked"] = _mask_key(cfg.get("google_maps_api_key", ""))
    cfg["google_maps_api_key"] = ""
    return cfg


@router.put("/maps/config")
async def update_maps_config_endpoint(
    payload: dict,
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    provider = (payload.get("provider") or "LOCAL").upper()
    maps_enabled = str(payload.get("maps_enabled", True)).lower()
    region = (payload.get("google_maps_region") or "PH").upper()
    language = payload.get("google_maps_language") or "en"
    ttl = str(payload.get("maps_cache_ttl_seconds") or 86400)

    await _upsert_platform_setting(db, "MAPS_PROVIDER", provider, admin.id)
    await _upsert_platform_setting(db, "MAPS_ENABLED", maps_enabled, admin.id)
    await _upsert_platform_setting(db, "GOOGLE_MAPS_REGION", region, admin.id)
    await _upsert_platform_setting(db, "GOOGLE_MAPS_LANGUAGE", language, admin.id)
    await _upsert_platform_setting(db, "MAPS_CACHE_TTL_SECONDS", ttl, admin.id)

    if payload.get("google_maps_api_key"):
        await _upsert_platform_setting(db, "GOOGLE_MAPS_API_KEY", str(payload["google_maps_api_key"]), admin.id)

    await create_audit_log(
        db,
        action="ADMIN_MANUAL_ACTION",
        entity_type="PlatformSetting",
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"maps_provider": provider, "maps_enabled": maps_enabled},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    return {"ok": True}


@router.post("/maps/test-connection")
async def test_maps_connection_endpoint(
    payload: dict,
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    cfg = await get_maps_config(db)
    provider = (payload.get("provider") or cfg.get("provider") or "LOCAL").upper()
    if provider != "GOOGLE":
        return {"ok": True, "provider": provider, "message": "Local map provider active"}

    api_key = payload.get("google_maps_api_key") or cfg.get("google_maps_api_key")
    if not api_key:
        return {"ok": False, "provider": provider, "error": "Google Maps API key missing"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": "Cebu City, Philippines",
                    "key": api_key,
                    "region": payload.get("google_maps_region") or cfg.get("google_maps_region") or "PH",
                    "language": payload.get("google_maps_language") or cfg.get("google_maps_language") or "en",
                },
            )
        data = response.json()
        status = data.get("status")
        return {"ok": status == "OK", "provider": provider, "status": status, "sample_result_count": len(data.get("results", []))}
    except Exception as exc:
        return {"ok": False, "provider": provider, "error": str(exc)[:200]}


# ══════════════════════════════════════════════════════
# AI / KYC ANALYSIS
# ══════════════════════════════════════════════════════

@router.get("/ai/config")
async def get_ai_config_endpoint(
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    from app.services.ai_service import get_ai_config

    cfg = await get_ai_config(db)
    if cfg.get("api_key"):
        cfg["api_key_masked"] = _mask_key(cfg["api_key"])
        cfg["api_key"] = ""
    return cfg


@router.post("/ai/test")
async def test_ai_connection_endpoint(
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    from app.services.ai_service import test_ai_connection

    return await test_ai_connection(db)


def _document_file_path(file_url: str) -> Path:
    upload_dir = Path(os.getenv("UPLOAD_DIR") or "backend/uploads")
    if "/" in file_url:
        name = file_url.split("/")[-1]
    else:
        name = file_url
    return upload_dir / name


async def _analyze_and_persist_document(
    db: AsyncSession,
    admin: User,
    doc: CompanyDocument,
    document_text: str | None = None,
) -> dict:
    from app.services.ai_service import analyze_kyc_document, get_ai_config

    cfg = await get_ai_config(db)
    result = await analyze_kyc_document(
        db,
        image_url=doc.file_url,
        document_text=document_text,
        doc_type_hint=doc.doc_type.value if doc.doc_type else None,
    )

    if result.get("ok"):
        analysis = result.get("analysis") or {}
        row = KYCAnalysisResult(
            company_id=doc.company_id,
            document_id=doc.id,
            analyzed_by=admin.id,
            ai_provider=cfg.get("provider") or "openai",
            ai_model=cfg.get("model") or "gpt-4o-mini",
            authenticity=analysis.get("authenticity", "SUSPICIOUS"),
            confidence=float(analysis.get("confidence") or 0),
            overall_risk_score=float(analysis.get("overall_risk_score") or 0),
            recommended_action=analysis.get("recommended_action", "MANUAL_REVIEW"),
            tamper_suspected=bool(analysis.get("tamper_suspected")),
            photoshop_suspected=bool(analysis.get("photoshop_suspected")),
            text_photo_consistency=bool(analysis.get("text_photo_consistency")),
            extracted_fields=analysis.get("extracted_fields"),
            detected_issues=analysis.get("detected_issues"),
            concerns=analysis.get("concerns"),
            raw_result_json=result,
        )
        db.add(row)
        await db.flush()
        result["analysis_id"] = str(row.id)

    db.add(AuditLog(
        actor_id=admin.id,
        actor_role=admin.role.value if admin.role else "ADMIN",
        action="AI_KYC_ANALYZE",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        risk_level=RiskLevel.LOW if result.get("ok") else RiskLevel.MEDIUM,
        after_json={"ok": result.get("ok"), "meets_threshold": result.get("meets_threshold")},
    ))
    return result


@router.post("/ai/analyze-document")
@router.post("/ai/analyze-kyc-document")
async def ai_analyze_document(
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    document_id = payload.get("document_id")
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")

    doc = (await db.execute(select(CompanyDocument).where(CompanyDocument.id == document_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await _analyze_and_persist_document(db, admin, doc, document_text=payload.get("document_text"))
    await db.commit()
    return result


@router.post("/ai/batch-analyze-kyc")
async def ai_batch_analyze_kyc(
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(100, int(payload.get("limit", 20))))
    status_filter = payload.get("status")
    q = select(CompanyDocument).order_by(CompanyDocument.created_at.desc()).limit(limit)
    if status_filter:
        q = q.where(CompanyDocument.status == status_filter)
    docs = (await db.execute(q)).scalars().all()

    results = []
    for doc in docs:
        result = await _analyze_and_persist_document(db, admin, doc)
        results.append({"document_id": str(doc.id), "ok": result.get("ok"), "analysis_id": result.get("analysis_id")})

    await db.commit()
    return {"ok": True, "count": len(results), "items": results}


# ══════════════════════════════════════════════════════
# KYC MEDIA LIBRARY
# ══════════════════════════════════════════════════════

@router.get("/kyc-media/files")
async def list_kyc_media_files(
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
    company_id: str | None = None,
    status: DocumentStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    q = select(CompanyDocument)
    if company_id:
        q = q.where(CompanyDocument.company_id == company_id)
    if status:
        q = q.where(CompanyDocument.status == status)

    docs = (await db.execute(q.order_by(CompanyDocument.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [{
        "id": str(d.id),
        "company_id": str(d.company_id),
        "doc_type": d.doc_type.value if d.doc_type else None,
        "file_url": d.file_url,
        "original_filename": d.original_filename,
        "status": d.status.value if d.status else None,
        "reviewer_note": d.reviewer_note,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    } for d in docs]


@router.get("/kyc-media/files/{document_id}")
async def get_kyc_media_file_detail(
    document_id: str,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    doc = (await db.execute(select(CompanyDocument).where(CompanyDocument.id == document_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    analyses = (await db.execute(
        select(KYCAnalysisResult).where(KYCAnalysisResult.document_id == doc.id).order_by(KYCAnalysisResult.created_at.desc()).limit(1)
    )).scalars().all()
    latest = analyses[0] if analyses else None

    return {
        "id": str(doc.id),
        "company_id": str(doc.company_id),
        "doc_type": doc.doc_type.value if doc.doc_type else None,
        "file_url": doc.file_url,
        "original_filename": doc.original_filename,
        "status": doc.status.value if doc.status else None,
        "reviewer_note": doc.reviewer_note,
        "reviewed_by": str(doc.reviewed_by) if doc.reviewed_by else None,
        "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "latest_analysis": {
            "id": str(latest.id),
            "authenticity": latest.authenticity.value if latest.authenticity else None,
            "confidence": latest.confidence,
            "overall_risk_score": latest.overall_risk_score,
            "recommended_action": latest.recommended_action.value if latest.recommended_action else None,
            "tamper_suspected": latest.tamper_suspected,
            "photoshop_suspected": latest.photoshop_suspected,
            "text_photo_consistency": latest.text_photo_consistency,
            "detected_issues": latest.detected_issues,
            "concerns": latest.concerns,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
        } if latest else None,
    }


@router.post("/kyc-media/files/{document_id}/flag-risk")
async def flag_kyc_media_risk(
    document_id: str,
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    doc = (await db.execute(select(CompanyDocument).where(CompanyDocument.id == document_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    note = payload.get("note") or "Flagged by admin"
    doc.status = DocumentStatus.REJECTED
    doc.reviewer_note = note
    doc.reviewed_by = admin.id
    doc.reviewed_at = datetime.now(timezone.utc)

    await create_audit_log(
        db,
        action="RISK_FLAG_CREATED",
        entity_type="CompanyDocument",
        entity_id=doc.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"note": note, "action": "flag_risk"},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    return {"ok": True, "document_id": str(doc.id), "status": doc.status.value}


@router.get("/kyc-media/files/{document_id}/analysis")
async def get_kyc_media_analysis(
    document_id: str,
    admin: User = Depends(_require_admin(UserRole.VERIFICATION_OFFICER, UserRole.RISK_ANALYST, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(KYCAnalysisResult).where(KYCAnalysisResult.document_id == document_id).order_by(KYCAnalysisResult.created_at.desc())
    )).scalars().all()

    return [{
        "id": str(r.id),
        "authenticity": r.authenticity.value if r.authenticity else None,
        "confidence": r.confidence,
        "overall_risk_score": r.overall_risk_score,
        "recommended_action": r.recommended_action.value if r.recommended_action else None,
        "tamper_suspected": r.tamper_suspected,
        "photoshop_suspected": r.photoshop_suspected,
        "text_photo_consistency": r.text_photo_consistency,
        "extracted_fields": r.extracted_fields,
        "detected_issues": r.detected_issues,
        "concerns": r.concerns,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]


# ══════════════════════════════════════════════════════
# BACKUP MANAGEMENT
# ══════════════════════════════════════════════════════

@router.get("/backups/config")
async def get_backup_config(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    keys = ["BACKUP_ENABLED", "BACKUP_INCLUDE_UPLOADS", "BACKUP_DEFAULT_RETENTION_COUNT", "BACKUP_DEFAULT_RETENTION_DAYS"]
    rows = (await db.execute(select(PlatformSetting).where(PlatformSetting.key.in_(keys)))).scalars().all()
    kv = {r.key: r.value for r in rows}
    return {
        "backup_enabled": (kv.get("BACKUP_ENABLED") or "true").lower() == "true",
        "include_uploads": (kv.get("BACKUP_INCLUDE_UPLOADS") or "true").lower() == "true",
        "default_retention_count": int(kv.get("BACKUP_DEFAULT_RETENTION_COUNT") or 8),
        "default_retention_days": int(kv.get("BACKUP_DEFAULT_RETENTION_DAYS") or 120),
    }


@router.put("/backups/config")
async def update_backup_config(
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    await _upsert_platform_setting(db, "BACKUP_ENABLED", str(payload.get("backup_enabled", True)).lower(), admin.id)
    await _upsert_platform_setting(db, "BACKUP_INCLUDE_UPLOADS", str(payload.get("include_uploads", True)).lower(), admin.id)
    await _upsert_platform_setting(db, "BACKUP_DEFAULT_RETENTION_COUNT", str(payload.get("default_retention_count") or 8), admin.id)
    await _upsert_platform_setting(db, "BACKUP_DEFAULT_RETENTION_DAYS", str(payload.get("default_retention_days") or 120), admin.id)
    await db.commit()
    return {"ok": True}


@router.get("/backups/schedules")
async def list_backup_schedules(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(BackupSchedule).order_by(BackupSchedule.created_at.desc()))).scalars().all()
    return [{
        "id": str(r.id),
        "name": r.name,
        "frequency": r.frequency.value if r.frequency else None,
        "cron_expr": r.cron_expr,
        "day_of_week": r.day_of_week,
        "day_of_month": r.day_of_month,
        "hour": r.hour,
        "minute": r.minute,
        "enabled": r.enabled,
        "retention_count": r.retention_count,
        "retention_days": r.retention_days,
        "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
        "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
    } for r in rows]


@router.post("/backups/schedules")
async def create_backup_schedule(
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    schedule = BackupSchedule(
        name=payload.get("name") or "Scheduled backup",
        frequency=payload.get("frequency") or BackupFrequency.MONTHLY,
        cron_expr=payload.get("cron_expr"),
        day_of_week=payload.get("day_of_week"),
        day_of_month=payload.get("day_of_month"),
        hour=payload.get("hour", 2),
        minute=payload.get("minute", 0),
        enabled=payload.get("enabled", True),
        retention_count=payload.get("retention_count", 8),
        retention_days=payload.get("retention_days", 120),
        created_by=admin.id,
    )
    schedule.next_run_at = next_run_at_for_schedule(schedule)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return {"id": str(schedule.id), "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None}


@router.patch("/backups/schedules/{schedule_id}")
async def update_backup_schedule(
    schedule_id: str,
    payload: dict,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    schedule = (await db.execute(select(BackupSchedule).where(BackupSchedule.id == schedule_id))).scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for key in ["name", "cron_expr", "day_of_week", "day_of_month", "hour", "minute", "enabled", "retention_count", "retention_days"]:
        if key in payload:
            setattr(schedule, key, payload[key])
    if "frequency" in payload:
        schedule.frequency = payload["frequency"]

    schedule.next_run_at = next_run_at_for_schedule(schedule)
    await db.commit()
    await db.refresh(schedule)
    return {"ok": True, "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None}


@router.delete("/backups/schedules/{schedule_id}")
async def delete_backup_schedule(
    schedule_id: str,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    schedule = (await db.execute(select(BackupSchedule).where(BackupSchedule.id == schedule_id))).scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
    return {"ok": True}


@router.post("/backups/manual")
async def run_manual_backup(
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    job = await create_backup_archive(db, created_by=admin.id)
    await db.commit()
    return {
        "id": str(job.id),
        "status": job.status.value if job.status else None,
        "archive_size_bytes": job.archive_size_bytes,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/backups/jobs")
async def list_backup_jobs(
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
):
    jobs = (await db.execute(select(BackupJob).order_by(BackupJob.created_at.desc()).limit(limit))).scalars().all()
    return [{
        "id": str(j.id),
        "schedule_id": str(j.schedule_id) if j.schedule_id else None,
        "status": j.status.value if j.status else None,
        "archive_path": j.archive_path,
        "archive_size_bytes": j.archive_size_bytes,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        "error_message": j.error_message,
        "created_at": j.created_at.isoformat() if j.created_at else None,
    } for j in jobs]


@router.get("/backups/jobs/{job_id}")
async def get_backup_job(
    job_id: str,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    job = (await db.execute(select(BackupJob).where(BackupJob.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return {
        "id": str(job.id),
        "schedule_id": str(job.schedule_id) if job.schedule_id else None,
        "status": job.status.value if job.status else None,
        "archive_path": job.archive_path,
        "archive_size_bytes": job.archive_size_bytes,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/backups/jobs/{job_id}/download")
async def download_backup_job(
    job_id: str,
    admin: User = Depends(_require_admin(UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    job = (await db.execute(select(BackupJob).where(BackupJob.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    if not job.archive_path or not os.path.exists(job.archive_path):
        raise HTTPException(status_code=404, detail="Backup archive not found")

    return FileResponse(job.archive_path, media_type="application/zip", filename=Path(job.archive_path).name)


# ══════════════════════════════════════════════════════
# AI PROJECT FORGE CONFIG & AUDIT
# ══════════════════════════════════════════════════════

AI_PROJECT_SETTING_KEYS = [
    "ai_project_estimation_enabled",
    "ai_project_model",
    "ai_multimodal_enabled",
    "ai_multimodal_model",
    "ai_project_prompt_version",
    "ai_project_max_files",
    "ai_project_max_file_size_mb",
]


@router.get("/integrations/ai-project")
async def get_ai_project_config(
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Get AI Project Forge configuration."""
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key.in_(AI_PROJECT_SETTING_KEYS)))
    settings_map = {s.key: s.value for s in result.scalars().all()}
    return {
        "ai_project_estimation_enabled": settings_map.get("ai_project_estimation_enabled") == "true",
        "ai_project_model": settings_map.get("ai_project_model", ""),
        "ai_multimodal_enabled": settings_map.get("ai_multimodal_enabled") == "true",
        "ai_multimodal_model": settings_map.get("ai_multimodal_model", ""),
        "ai_project_prompt_version": settings_map.get("ai_project_prompt_version", "v1"),
        "ai_project_max_files": int(settings_map.get("ai_project_max_files") or 10),
        "ai_project_max_file_size_mb": int(settings_map.get("ai_project_max_file_size_mb") or 10),
    }


@router.patch("/integrations/ai-project")
async def update_ai_project_config(
    payload: dict,
    admin: User = Depends(_require_admin()),
    db: AsyncSession = Depends(get_db),
):
    """Update AI Project Forge configuration."""
    before = {}
    after = {}
    for key in AI_PROJECT_SETTING_KEYS:
        if key in payload:
            val = str(payload[key])
            # Load existing
            result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
            setting = result.scalar_one_or_none()
            if setting:
                before[key] = setting.value
                setting.value = val
            else:
                before[key] = None
                db.add(PlatformSetting(key=key, value=val))
            after[key] = val

    await create_audit_log(
        db, action="AI_PROJECT_CONFIG_UPDATED", entity_type="PlatformSetting", entity_id=admin.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json=before, after_json=after,
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    return {"updated": list(after.keys())}


@router.get("/project-ai-runs")
async def list_project_ai_runs(
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List all AI project analysis runs for audit purposes."""
    from app.models.buyer_project import ProjectAIRun, AIRunStatus as ARStatus
    q = select(ProjectAIRun)
    if status:
        try:
            q = q.where(ProjectAIRun.status == ARStatus(status))
        except ValueError:
            pass
    result = await db.execute(q.order_by(ProjectAIRun.created_at.desc()).limit(limit).offset(offset))
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "project_id": str(r.project_id),
            "provider": r.provider,
            "model": r.model,
            "prompt_version": r.prompt_version,
            "status": r.status.value if r.status else None,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/project-ai-runs/{run_id}")
async def get_project_ai_run_detail(
    run_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get full AI run detail including input snapshot, raw output, structured output."""
    from app.models.buyer_project import ProjectAIRun
    result = await db.execute(select(ProjectAIRun).where(ProjectAIRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="AI run not found")
    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "provider": run.provider,
        "model": run.model,
        "prompt_version": run.prompt_version,
        "status": run.status.value if run.status else None,
        "input_snapshot_jsonb": run.input_snapshot_jsonb,
        "raw_output": run.raw_output,
        "structured_output_jsonb": run.structured_output_jsonb,
        "token_usage_jsonb": run.token_usage_jsonb,
        "estimated_cost": run.estimated_cost,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.get("/project-metric-templates", response_model=list[ProjectMetricTemplateResponse])
async def list_project_metric_templates(
    project_type: ProjectType | None = None,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    q = select(ProjectMetricTemplate)
    if project_type:
        q = q.where(ProjectMetricTemplate.project_type == project_type)
    result = await db.execute(q.order_by(ProjectMetricTemplate.project_type, ProjectMetricTemplate.sort_order))
    return result.scalars().all()


@router.post("/project-metric-templates", response_model=ProjectMetricTemplateResponse, status_code=201)
async def create_project_metric_template(
    payload: ProjectMetricTemplateCreate,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    template = ProjectMetricTemplate(**payload.model_dump())
    db.add(template)
    await create_audit_log(
        db, action="PROJECT_METRIC_TEMPLATE_CREATED", entity_type="ProjectMetricTemplate", entity_id=template.id,
        actor_id=admin.id, actor_role=admin.role.value,
        after_json=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(template)
    return template


@router.patch("/project-metric-templates/{template_id}", response_model=ProjectMetricTemplateResponse)
async def update_project_metric_template(
    template_id: str,
    payload: ProjectMetricTemplateUpdate,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProjectMetricTemplate).where(ProjectMetricTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Metric template not found")
    before = {
        "project_type": template.project_type.value if template.project_type else None,
        "key": template.key,
        "label": template.label,
        "data_type": template.data_type,
        "required": template.required,
        "active": template.active,
    }
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await create_audit_log(
        db, action="PROJECT_METRIC_TEMPLATE_UPDATED", entity_type="ProjectMetricTemplate", entity_id=template.id,
        actor_id=admin.id, actor_role=admin.role.value,
        before_json=before, after_json=payload.model_dump(exclude_unset=True, mode="json"),
    )
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/projects/{project_id}/conversation-audit")
async def get_project_conversation_audit(
    project_id: str,
    admin: User = Depends(_require_admin(UserRole.OPS_MANAGER, UserRole.AUDITOR)),
    db: AsyncSession = Depends(get_db),
):
    messages = (await db.execute(
        select(ProjectMessage).where(ProjectMessage.project_id == project_id).order_by(ProjectMessage.created_at)
    )).scalars().all()
    runs = (await db.execute(
        select(ProjectAIRun).where(ProjectAIRun.project_id == project_id).order_by(ProjectAIRun.created_at.desc())
    )).scalars().all()
    return {
        "project_id": project_id,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value if m.role else None,
                "workflow_node": m.workflow_node.value if m.workflow_node else None,
                "content": m.content,
                "file_ids": m.file_ids_jsonb,
                "structured_delta": m.structured_delta_jsonb,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "ai_runs": [
            {
                "id": str(r.id),
                "status": r.status.value if r.status else None,
                "provider": r.provider,
                "model": r.model,
                "prompt_version": r.prompt_version,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }

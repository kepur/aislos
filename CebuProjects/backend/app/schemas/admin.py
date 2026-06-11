"""Consolidated admin schemas for new admin console models."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.admin_note import NoteVisibility
from app.models.company_document import DocumentStatus, DocumentType
from app.models.notification_template import NotificationTemplate
from app.models.payout import PayoutStatus
from app.models.risk_flag import RiskFlagStatus, RiskType
from app.models.user import UserRole, UserStatus
from app.models.verification_review import VerificationDecision, VerificationQueueStatus


# ── User detail ──────────────────────────────────────────────────────────────

class UserDetailResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    role: UserRole
    status: UserStatus
    full_name: str
    avatar_url: str | None
    telegram_chat_id: str | None
    two_fa_enabled: bool
    last_login_at: datetime | None
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdateRequest(BaseModel):
    status: UserStatus
    reason_code: str
    reason_text: str
    notify_user: bool = False


class StaffInviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    password: str


class StaffRoleUpdateRequest(BaseModel):
    role: UserRole
    reason: str


# ── Company document ──────────────────────────────────────────────────────────

class CompanyDocumentResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    doc_type: DocumentType
    file_url: str
    original_filename: str | None
    status: DocumentStatus
    reviewer_note: str | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Verification review ───────────────────────────────────────────────────────

class VerificationReviewResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    status: VerificationQueueStatus
    assigned_reviewer_id: uuid.UUID | None
    decision: VerificationDecision | None
    decision_reason: str | None
    internal_note: str | None
    user_facing_note: str | None
    decided_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationDecisionRequest(BaseModel):
    decision: VerificationDecision
    decision_reason: str
    internal_note: str | None = None
    user_facing_note: str | None = None


# ── Payment event ─────────────────────────────────────────────────────────────

class PaymentEventResponse(BaseModel):
    id: uuid.UUID
    provider: str
    provider_event_id: str | None
    event_type: str
    order_id: uuid.UUID | None
    escrow_id: uuid.UUID | None
    amount_minor: int | None
    currency: str | None
    status: str
    error_message: str | None
    received_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


# ── Payout ────────────────────────────────────────────────────────────────────

class PayoutResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    amount_minor: int
    currency: str
    provider: str
    destination: str | None
    status: PayoutStatus
    risk_hold: bool
    scheduled_at: datetime | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Risk flag ─────────────────────────────────────────────────────────────────

class RiskFlagCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    risk_type: RiskType
    risk_level: str = "MEDIUM"
    description: str | None = None


class RiskFlagResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    risk_type: RiskType
    risk_level: str
    status: RiskFlagStatus
    description: str | None
    assigned_analyst_id: uuid.UUID | None
    action_taken: str | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskFlagActionRequest(BaseModel):
    status: RiskFlagStatus
    action_taken: str | None = None


# ── Admin note ────────────────────────────────────────────────────────────────

class AdminNoteCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    note: str
    visibility: NoteVisibility = NoteVisibility.INTERNAL_ONLY


class AdminNoteResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    author_id: uuid.UUID
    visibility: NoteVisibility
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Notification template ─────────────────────────────────────────────────────

class NotificationTemplateUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    active: bool | None = None


class NotificationTemplateResponse(BaseModel):
    id: uuid.UUID
    template_key: str
    channel: str
    language: str
    subject: str | None
    body: str
    variables_hint: str | None
    active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Platform setting ──────────────────────────────────────────────────────────

class PlatformSettingUpdate(BaseModel):
    value: str | None = None


class PlatformSettingResponse(BaseModel):
    key: str
    value: str | None
    description: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Escrow admin ops ──────────────────────────────────────────────────────────

class EscrowManualVerifyRequest(BaseModel):
    payment_method: str
    received_amount_minor: int
    currency: str
    reference: str | None = None
    note: str | None = None


class EscrowRefundRequest(BaseModel):
    amount_minor: int | None = None
    reason_code: str
    reason_text: str


class EscrowReleaseRequest(BaseModel):
    reason_code: str
    reason_text: str


# ── Intent moderation ─────────────────────────────────────────────────────────

class IntentModerateRequest(BaseModel):
    action: str  # pause | cancel | flag | restore
    reason: str | None = None


# ── Offer moderation ──────────────────────────────────────────────────────────

class OfferRemoveRequest(BaseModel):
    reason: str


# ── Order hold ────────────────────────────────────────────────────────────────

class OrderHoldRequest(BaseModel):
    reason: str

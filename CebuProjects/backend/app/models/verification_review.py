import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VerificationQueueStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    APPROVED_BASIC = "APPROVED_BASIC"
    APPROVED_BUSINESS = "APPROVED_BUSINESS"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class VerificationDecision(str, enum.Enum):
    APPROVE_BASIC = "APPROVE_BASIC"
    APPROVE_BUSINESS = "APPROVE_BUSINESS"
    REQUEST_MORE_INFO = "REQUEST_MORE_INFO"
    REJECT = "REJECT"
    ESCALATE_TO_RISK = "ESCALATE_TO_RISK"


class VerificationReview(Base):
    __tablename__ = "verification_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    status: Mapped[VerificationQueueStatus] = mapped_column(
        Enum(VerificationQueueStatus, name="verification_queue_status", create_type=False),
        default=VerificationQueueStatus.SUBMITTED,
    )
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    decision: Mapped[VerificationDecision | None] = mapped_column(Enum(VerificationDecision, name="verification_decision", create_type=False))
    decision_reason: Mapped[str | None] = mapped_column(String(500))
    internal_note: Mapped[str | None] = mapped_column(Text)
    user_facing_note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DisputeStatus(str, enum.Enum):
    OPENED = "OPENED"
    WAITING_BUYER_EVIDENCE = "WAITING_BUYER_EVIDENCE"
    WAITING_SUPPLIER_EVIDENCE = "WAITING_SUPPLIER_EVIDENCE"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED_REFUND = "RESOLVED_REFUND"
    RESOLVED_RELEASE = "RESOLVED_RELEASE"
    RESOLVED_PARTIAL_REFUND = "RESOLVED_PARTIAL_REFUND"
    ESCALATED = "ESCALATED"
    CANCELED = "CANCELED"


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    opened_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus, name="dispute_status", create_type=False), default=DisputeStatus.OPENED)
    evidence_json: Mapped[list | None] = mapped_column(JSON, default=list)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    refund_amount_minor: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

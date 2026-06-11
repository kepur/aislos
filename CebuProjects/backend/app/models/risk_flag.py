import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RiskType(str, enum.Enum):
    SUSPICIOUS_PRICE_LOW = "SUSPICIOUS_PRICE_LOW"
    SUSPICIOUS_PRICE_HIGH = "SUSPICIOUS_PRICE_HIGH"
    NEW_SUPPLIER_HIGH_VALUE_ORDER = "NEW_SUPPLIER_HIGH_VALUE_ORDER"
    HIGH_DISPUTE_RATE = "HIGH_DISPUTE_RATE"
    REPEATED_CANCELLATION = "REPEATED_CANCELLATION"
    FAILED_LOGIN_SPIKE = "FAILED_LOGIN_SPIKE"
    DEVICE_MULTI_ACCOUNT = "DEVICE_MULTI_ACCOUNT"
    POSSIBLE_COUNTERFEIT = "POSSIBLE_COUNTERFEIT"
    PAYMENT_MISMATCH = "PAYMENT_MISMATCH"
    USDT_UNCONFIRMED = "USDT_UNCONFIRMED"
    MANUAL_BANK_RECEIPT_SUSPICIOUS = "MANUAL_BANK_RECEIPT_SUSPICIOUS"
    OFF_PLATFORM_DEAL_ATTEMPT = "OFF_PLATFORM_DEAL_ATTEMPT"
    OTHER = "OTHER"


class RiskFlagStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    MITIGATED = "MITIGATED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ACTION_TAKEN = "ACTION_TAKEN"
    CLOSED = "CLOSED"


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    risk_type: Mapped[RiskType] = mapped_column(Enum(RiskType, name="risk_type", create_type=False))
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    status: Mapped[RiskFlagStatus] = mapped_column(Enum(RiskFlagStatus, name="risk_flag_status", create_type=False), default=RiskFlagStatus.OPEN)
    description: Mapped[str | None] = mapped_column(Text)
    assigned_analyst_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action_taken: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

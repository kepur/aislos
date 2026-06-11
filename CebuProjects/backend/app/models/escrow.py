import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EscrowProvider(str, enum.Enum):
    SIMULATED = "SIMULATED"
    PAYMONGO = "PAYMONGO"
    XENDIT = "XENDIT"
    STRIPE = "STRIPE"


class EscrowStatus(str, enum.Enum):
    AUTH_PENDING = "AUTH_PENDING"
    AUTH_HELD = "AUTH_HELD"
    CAPTURED = "CAPTURED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CHARGEBACK = "CHARGEBACK"
    FAILED = "FAILED"


class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    provider: Mapped[EscrowProvider] = mapped_column(Enum(EscrowProvider, name="escrow_provider", create_type=False), default=EscrowProvider.SIMULATED)
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    auth_amount_minor: Mapped[int] = mapped_column(Integer)
    captured_amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    released_amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    refunded_amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    status: Mapped[EscrowStatus] = mapped_column(Enum(EscrowStatus, name="escrow_status", create_type=False), default=EscrowStatus.AUTH_PENDING)
    raw_event_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

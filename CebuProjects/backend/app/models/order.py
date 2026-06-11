import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAID_IN_ESCROW = "PAID_IN_ESCROW"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    ACCEPTED = "ACCEPTED"
    PAYOUT_RELEASED = "PAYOUT_RELEASED"
    DISPUTED = "DISPUTED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    intent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    total_amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status", create_type=False), default=OrderStatus.CREATED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

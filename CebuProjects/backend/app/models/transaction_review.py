import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TransactionChannel(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class ReviewTargetType(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"


class TransactionReview(Base):
    __tablename__ = "transaction_reviews"
    __table_args__ = (
        UniqueConstraint("order_id", "reviewer_id", "target_type", name="uq_transaction_review_once"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    reviewee_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    reviewee_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    target_type: Mapped[ReviewTargetType] = mapped_column(Enum(ReviewTargetType, name="review_target_type", create_type=False), index=True)
    transaction_channel: Mapped[TransactionChannel] = mapped_column(Enum(TransactionChannel, name="transaction_channel", create_type=False), default=TransactionChannel.ONLINE)
    product_quality_rating: Mapped[int | None] = mapped_column(Integer)
    logistics_rating: Mapped[int | None] = mapped_column(Integer)
    communication_rating: Mapped[int | None] = mapped_column(Integer)
    buyer_rating: Mapped[int | None] = mapped_column(Integer)
    overall_rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

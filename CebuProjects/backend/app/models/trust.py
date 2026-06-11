import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrustEntityType(str, enum.Enum):
    USER = "USER"
    COMPANY = "COMPANY"


class TrustTier(str, enum.Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"


class TrustProfileStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    HIDDEN = "HIDDEN"


class TrustScoreEventType(str, enum.Enum):
    RECALCULATED = "RECALCULATED"
    ADMIN_ADJUSTED = "ADMIN_ADJUSTED"
    FROZEN = "FROZEN"
    UNFROZEN = "UNFROZEN"


class TrustProfile(Base):
    __tablename__ = "trust_profiles"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_trust_profile_entity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[TrustEntityType] = mapped_column(Enum(TrustEntityType, name="trust_entity_type", create_type=False), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    trust_tier: Mapped[TrustTier] = mapped_column(Enum(TrustTier, name="trust_tier", create_type=False), default=TrustTier.BRONZE)
    profile_completion_rate: Mapped[int] = mapped_column(Integer, default=0)
    deal_completion_rate: Mapped[int] = mapped_column(Integer, default=0)
    deposit_amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    deposit_currency: Mapped[str] = mapped_column(String(10), default="PHP")
    verified_deposit_minor: Mapped[int] = mapped_column(Integer, default=0)
    successful_deals_count: Mapped[int] = mapped_column(Integer, default=0)
    canceled_deals_count: Mapped[int] = mapped_column(Integer, default=0)
    dispute_rate: Mapped[int] = mapped_column(Integer, default=0)
    refund_rate: Mapped[int] = mapped_column(Integer, default=0)
    late_delivery_rate: Mapped[int] = mapped_column(Integer, default=0)
    late_payment_rate: Mapped[int] = mapped_column(Integer, default=0)
    score_breakdown_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    status: Mapped[TrustProfileStatus] = mapped_column(Enum(TrustProfileStatus, name="trust_profile_status", create_type=False), default=TrustProfileStatus.ACTIVE)
    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TrustScoreEvent(Base):
    __tablename__ = "trust_score_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trust_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    event_type: Mapped[TrustScoreEventType] = mapped_column(Enum(TrustScoreEventType, name="trust_score_event_type", create_type=False))
    score_delta: Mapped[int] = mapped_column(Integer, default=0)
    before_score: Mapped[int] = mapped_column(Integer, default=0)
    after_score: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str | None] = mapped_column(String(500))
    related_entity_type: Mapped[str | None] = mapped_column(String(50))
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

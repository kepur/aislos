"""Ad Campaign model for marketplace advertising."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdCampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AdPlacementType(str, enum.Enum):
    FEED_TOP = "FEED_TOP"
    FEED_INLINE = "FEED_INLINE"
    CATEGORY_TOP = "CATEGORY_TOP"
    SEARCH_TOP = "SEARCH_TOP"
    BANNER = "BANNER"


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(500))
    placement: Mapped[AdPlacementType] = mapped_column(
        Enum(AdPlacementType, name="ad_placement_type", create_type=False)
    )
    target_category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    target_keywords: Mapped[list | None] = mapped_column(JSON)
    target_countries: Mapped[list | None] = mapped_column(JSON)
    budget_minor: Mapped[int] = mapped_column(Integer)
    spent_minor: Mapped[int] = mapped_column(Integer, default=0)
    bid_per_click_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    status: Mapped[AdCampaignStatus] = mapped_column(
        Enum(AdCampaignStatus, name="ad_campaign_status", create_type=False),
        default=AdCampaignStatus.DRAFT
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

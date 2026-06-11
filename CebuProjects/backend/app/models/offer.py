import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OfferTier(str, enum.Enum):
    GOOD = "GOOD"
    BETTER = "BETTER"
    BEST = "BEST"
    CUSTOM = "CUSTOM"


class StockConfidence(str, enum.Enum):
    FIRM = "FIRM"
    BACKORDER = "BACKORDER"
    UNKNOWN = "UNKNOWN"


class OfferStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"
    AWARDED = "AWARDED"
    REJECTED = "REJECTED"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    supplier_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    unit_price_minor: Mapped[int] = mapped_column(Integer)
    qty_available: Mapped[int] = mapped_column(Integer)
    delivery_fee_minor: Mapped[int] = mapped_column(Integer, default=0)
    total_price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    eta_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    warranty: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[OfferTier] = mapped_column(Enum(OfferTier, name="offer_tier", create_type=False), default=OfferTier.GOOD)
    stock_confidence: Mapped[StockConfidence] = mapped_column(Enum(StockConfidence, name="stock_confidence", create_type=False), default=StockConfidence.UNKNOWN)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus, name="offer_status", create_type=False), default=OfferStatus.SUBMITTED)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

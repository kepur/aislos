"""Store request and Agent Marketplace data assets.

The Store captures commercial intent without taking customer funds. Marketplace
installations never imply data grants; third-party Agents start paused with all
scopes denied.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class StoreOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "store_orders"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="requested", nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    delivery_json: Mapped[dict | None] = mapped_column(JSONB)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StoreOrderItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "store_order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("store_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class MarketplaceListing(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        UniqueConstraint("slug", name="marketplace_listings_slug_key"),
        Index("ix_marketplace_listings_slug", "slug"),
    )

    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), index=True)
    developer_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    developer_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    workflows_json: Mapped[list | None] = mapped_column(JSONB)
    requested_scopes_json: Mapped[list | None] = mapped_column(JSONB)
    price_monthly: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentInstallation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_installations"
    __table_args__ = (
        UniqueConstraint("listing_id", "installed_by", name="uq_agent_installations_listing_user"),
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    installed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="installed", nullable=False, index=True)
    config_json: Mapped[dict | None] = mapped_column(JSONB)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uninstalled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

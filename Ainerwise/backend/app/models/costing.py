import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class ProductCost(Base, UUIDMixin, TimestampMixin):
    """Pre-quote landed cost per region x product (Cost Engine).

    Project-level actual costs stay in ProjectFinance; this is the forward
    estimate that feeds the Pricing Engine before any project exists.
    """

    __tablename__ = "product_costs"
    __table_args__ = (
        UniqueConstraint("region_id", "product_id", "valid_from", name="uq_product_costs_region_product_from"),
    )

    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    freight_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    freight_fixed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    customs_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    customs_fixed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    warehousing_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    labor_estimate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    landed_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)


class PriceList(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "price_lists"
    __table_args__ = (
        UniqueConstraint("region_id", "product_id", "valid_from", name="uq_price_lists_region_product_from"),
    )

    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    list_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    partner_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    vip_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)


class ExchangeRate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("base", "quote", "as_of", name="uq_exchange_rates_pair_date"),
    )

    base: Mapped[str] = mapped_column(String(3), nullable=False)
    quote: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=False)

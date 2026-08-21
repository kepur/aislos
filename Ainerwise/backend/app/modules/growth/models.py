"""Growth module ORM models (P0).

Persistence for the sourcing → localisation → auto-pricing → syndication
pipeline. The authoritative *contracts* (DTOs / Protocols / pricing formula)
live in ``app.modules.growth.contracts``; these tables are where a sourced
item and its pricing rule are stored so the rest of the platform
(MarketingAsset drafts, PublishJob, ProviderJob queue) can reference them.

Money is stored as integer minor units + an ISO currency, matching the
platform-wide ``*_minor`` convention. Percentages are ``Numeric`` fractions
(e.g. ``0.30`` = 30%).
"""
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class SourcedListing(Base, UUIDMixin, TimestampMixin):
    """A single item pulled from a source (e.g. 1688/闲鱼/淘宝) plus its
    pipeline state as it moves through translation, pricing and publishing.

    ``(source, external_id)`` is unique so re-importing the same item is
    idempotent (aligns with the ProviderJob / idempotency conventions).
    """

    __tablename__ = "growth_sourced_listings"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_growth_sourced_listing_source_ext"),
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )

    # --- provenance ---
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    seller_ref: Mapped[str | None] = mapped_column(String(255))

    # --- original content (source language) ---
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    source_lang: Mapped[str | None] = mapped_column(String(10))
    images_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    attributes_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    raw_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # --- source price (minor units, source currency) ---
    source_price_minor: Mapped[int | None] = mapped_column(BigInteger)
    source_currency: Mapped[str | None] = mapped_column(String(3))

    # --- localised content (target market) ---
    target_lang: Mapped[str | None] = mapped_column(String(10))
    translated_title: Mapped[str | None] = mapped_column(Text)
    translated_description: Mapped[str | None] = mapped_column(Text)
    translated_images_json: Mapped[list | None] = mapped_column(JSONB, default=list)

    # --- computed sell price (minor units, sell currency) ---
    price_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("growth_price_rules.id"), nullable=True
    )
    sell_price_minor: Mapped[int | None] = mapped_column(BigInteger)
    sell_currency: Mapped[str | None] = mapped_column(String(3))
    price_quote_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # --- promotion linkage (optional): a promoted item becomes a real product ---
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True
    )

    # imported | translated | priced | drafted | published | archived | failed
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="imported", index=True)
    failure_code: Mapped[str | None] = mapped_column(String(120))


class PriceRule(Base, UUIDMixin, TimestampMixin):
    """Auto-markup / reprice configuration for ``compute_sell_price``.

    A rule can apply at ``listing`` / ``category`` / ``global`` scope. Fields
    map 1:1 to ``contracts.PriceInputs``. ``freight_pct`` / ``duties_pct`` /
    ``target_margin_pct`` / ``platform_fee_pct`` are fractions (0.30 = 30%).
    """

    __tablename__ = "growth_price_rules"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="global")  # listing|category|global
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True, index=True
    )

    sell_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    # freight
    freight_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0"))
    freight_fixed_minor: Mapped[int | None] = mapped_column(BigInteger)
    freight_currency: Mapped[str | None] = mapped_column(String(3))

    # duties/tax + margin + platform fee (fractions)
    duties_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0"))
    target_margin_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0.30"))
    platform_fee_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0"))

    # rounding + clamp
    round_to_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_price_minor: Mapped[int | None] = mapped_column(BigInteger)
    max_price_minor: Mapped[int | None] = mapped_column(BigInteger)

    # scheduled reprice
    reprice_cadence: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # manual|daily|weekly
    reprice_threshold_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0"))

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

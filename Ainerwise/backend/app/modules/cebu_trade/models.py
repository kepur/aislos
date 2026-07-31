"""Cebu zero-loss migration models — Wallet, Address, Shipping, Ads, Escrow, Payout.

These replicate CebuProjects domain models inside Ainerwise Core,
using the same column names for data-layer parity.  ForeignKey
references point at the unified Ainerwise tables (users, companies,
commerce_orders, supplier_listings).
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
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


# ── Wallet ──────────────────────────────────────────────────────────


class Wallet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wallets"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(10), default="USDT", nullable=False, index=True)
    available_balance_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    locked_balance_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_deposited_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)


class WalletTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wallet_transactions"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    tx_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount_delta_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    available_balance_after_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    locked_balance_after_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USDT", nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    note: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


class WalletDeposit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wallet_deposits"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USDT", nullable=False)
    network: Mapped[str] = mapped_column(String(50), default="TRC20", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="MANUAL_BANK", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="PHP_MANUAL_BANK", nullable=False)
    source_currency: Mapped[str | None] = mapped_column(String(10))
    target_currency: Mapped[str | None] = mapped_column(String(10))
    deposit_address: Mapped[str] = mapped_column(String(255), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(255), index=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING_TX", nullable=False, index=True)
    submitter_note: Mapped[str | None] = mapped_column(Text)
    admin_note: Mapped[str | None] = mapped_column(Text)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Address ─────────────────────────────────────────────────────────


class Address(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    address_type: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_province: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    address_line1: Mapped[str] = mapped_column(Text, nullable=False)
    address_line2: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


# ── Shipping ────────────────────────────────────────────────────────


class ShippingRoute(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shipping_routes"

    origin_country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    origin_region: Mapped[str | None] = mapped_column(String(100))
    dest_country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    dest_region: Mapped[str | None] = mapped_column(String(100))
    shipping_method: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class ShippingRate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shipping_rates"

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipping_routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight_min_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    weight_max_kg: Mapped[float] = mapped_column(Float, default=99999, nullable=False)
    price_per_kg_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    min_charge_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    volume_factor: Mapped[float] = mapped_column(Float, default=5000, nullable=False)
    estimated_days_min: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    estimated_days_max: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    surcharges_json: Mapped[dict | None] = mapped_column(JSONB)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class OrderShipping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order_shipping"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    shipping_method: Mapped[str] = mapped_column(String(32), nullable=False)
    origin_address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=True
    )
    dest_address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=True
    )
    chargeable_weight_kg: Mapped[float | None] = mapped_column(Float)
    shipping_cost_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    estimated_days_min: Mapped[int | None] = mapped_column(Integer)
    estimated_days_max: Mapped[int | None] = mapped_column(Integer)
    tracking_number: Mapped[str | None] = mapped_column(String(200))
    carrier_name: Mapped[str | None] = mapped_column(String(200))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)


# ── Marketplace Ads ─────────────────────────────────────────────────


class AdCampaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ad_campaigns"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    placement: Mapped[str] = mapped_column(String(32), nullable=False)
    target_category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    target_keywords: Mapped[list | None] = mapped_column(JSONB)
    target_countries: Mapped[list | None] = mapped_column(JSONB)
    budget_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spent_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bid_per_click_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ── Escrow ──────────────────────────────────────────────────────────


class EscrowTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "escrow_transactions"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="SIMULATED", nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    auth_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    captured_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    released_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    refunded_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="PHP", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="AUTH_PENDING", nullable=False, index=True)
    raw_event_json: Mapped[dict | None] = mapped_column(JSONB)


# ── Payout ──────────────────────────────────────────────────────────


class Payout(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payouts"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id"), nullable=False, index=True
    )
    escrow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("escrow_transactions.id"), nullable=True
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="PHP", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="SIMULATED", nullable=False)
    destination: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    risk_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Regional payment policy, quote and provider reconciliation ─────


class RegionPaymentConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "region_payment_configs"

    country_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False)
    local_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    default_settlement_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    default_transaction_mode: Mapped[str] = mapped_column(String(64), default="LOCAL_ONLY", nullable=False)
    enabled_currencies: Mapped[list | None] = mapped_column(JSONB)
    enabled_payment_methods: Mapped[list | None] = mapped_column(JSONB)
    cross_border_currencies: Mapped[list | None] = mapped_column(JSONB)
    force_usd_bridge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_supplier_payout_currency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class CurrencyConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "currency_configs"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    minor_unit: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_fiat: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class PaymentMethodConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_method_configs"
    __table_args__ = (
        UniqueConstraint("country_code", "method_code", "currency", name="uq_payment_method_config_scope"),
    )

    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    method_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="SIMULATED", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    config_json: Mapped[dict | None] = mapped_column(JSONB)


class FeeRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_rules"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), index=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), index=True)
    fee_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="PHP", nullable=False)
    fixed_fee_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    variable_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_fee_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    max_fee_minor: Mapped[int | None] = mapped_column(BigInteger)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class FxQuote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fx_quotes"

    source_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    target_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    rate_source: Mapped[str] = mapped_column(String(80), default="SIMULATED_RATE_TABLE", nullable=False)
    provider_quote_id: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class PaymentQuote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_quotes"

    buyer_country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    supplier_country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    payer_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    settlement_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payer_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    escrow_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    supplier_estimated_net_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    platform_revenue_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rate: Mapped[float | None] = mapped_column(Numeric(18, 8))
    rate_source: Mapped[str | None] = mapped_column(String(80))
    fx_quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fx_quotes.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


class ProviderPaymentIntent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "provider_payment_intents"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payment_quotes.id"), index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("commerce_orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), default="SIMULATED", nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class FeeLineItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_line_items"

    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payment_quotes.id"), index=True)
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("provider_payment_intents.id"), index=True)
    fee_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


class SettlementEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "settlement_events"

    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("provider_payment_intents.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    gross_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    net_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="RECEIVED", nullable=False, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class SettlementAdjustment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "settlement_adjustments"

    settlement_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("settlement_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    adjustment_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)


class PaymentEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_events"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("commerce_orders.id"), index=True)
    escrow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("escrow_transactions.id"))
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

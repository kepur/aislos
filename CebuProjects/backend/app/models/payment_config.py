import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TransactionCurrencyMode(str, enum.Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    USD_BRIDGE = "USD_BRIDGE"
    BUYER_LOCAL_TO_SUPPLIER_LOCAL = "BUYER_LOCAL_TO_SUPPLIER_LOCAL"
    ORDER_CURRENCY_FIXED = "ORDER_CURRENCY_FIXED"


class FeeType(str, enum.Enum):
    PROVIDER_FEE = "PROVIDER_FEE"
    PLATFORM_SERVICE_FEE = "PLATFORM_SERVICE_FEE"
    CROSS_BORDER_FEE = "CROSS_BORDER_FEE"
    FX_FEE = "FX_FEE"
    PLATFORM_FX_MARKUP = "PLATFORM_FX_MARKUP"
    SETTLEMENT_FEE = "SETTLEMENT_FEE"
    NETWORK_FEE = "NETWORK_FEE"
    MANUAL_REVIEW_FEE = "MANUAL_REVIEW_FEE"


class QuoteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


class PaymentIntentStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"
    CHARGEBACK = "CHARGEBACK"


class SettlementEventStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    MATCHED = "MATCHED"
    ADJUSTED = "ADJUSTED"
    FAILED = "FAILED"


class RegionPaymentConfig(Base):
    __tablename__ = "region_payment_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    country_name: Mapped[str] = mapped_column(String(120))
    local_currency: Mapped[str] = mapped_column(String(10), index=True)
    default_settlement_currency: Mapped[str] = mapped_column(String(10))
    default_transaction_mode: Mapped[TransactionCurrencyMode] = mapped_column(Enum(TransactionCurrencyMode, name="transaction_currency_mode", create_type=False), default=TransactionCurrencyMode.LOCAL_ONLY)
    enabled_currencies: Mapped[list] = mapped_column(JSONB, default=list)
    enabled_payment_methods: Mapped[list] = mapped_column(JSONB, default=list)
    cross_border_currencies: Mapped[list] = mapped_column(JSONB, default=list)
    force_usd_bridge: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_supplier_payout_currency: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CurrencyConfig(Base):
    __tablename__ = "currency_configs"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    minor_unit: Mapped[int] = mapped_column(Integer, default=2)
    is_fiat: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaymentMethodConfig(Base):
    __tablename__ = "payment_method_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    method_code: Mapped[str] = mapped_column(String(50), index=True)
    provider: Mapped[str] = mapped_column(String(50), default="SIMULATED")
    currency: Mapped[str] = mapped_column(String(10), index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    config_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeeRule(Base):
    __tablename__ = "fee_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    country_code: Mapped[str | None] = mapped_column(String(2), index=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), index=True)
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType, name="payment_fee_type", create_type=False), index=True)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    fixed_fee_minor: Mapped[int] = mapped_column(Integer, default=0)
    variable_bps: Mapped[int] = mapped_column(Integer, default=0)
    min_fee_minor: Mapped[int] = mapped_column(Integer, default=0)
    max_fee_minor: Mapped[int | None] = mapped_column(Integer)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FxQuote(Base):
    __tablename__ = "fx_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_currency: Mapped[str] = mapped_column(String(10), index=True)
    target_currency: Mapped[str] = mapped_column(String(10), index=True)
    rate: Mapped[float] = mapped_column(Numeric(18, 8))
    rate_source: Mapped[str] = mapped_column(String(80), default="SIMULATED_RATE_TABLE")
    provider_quote_id: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PaymentQuote(Base):
    __tablename__ = "payment_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_country: Mapped[str] = mapped_column(String(2), index=True)
    supplier_country: Mapped[str] = mapped_column(String(2), index=True)
    mode: Mapped[TransactionCurrencyMode] = mapped_column(Enum(TransactionCurrencyMode, name="transaction_currency_mode", create_type=False), index=True)
    payment_method: Mapped[str] = mapped_column(String(50), index=True)
    order_currency: Mapped[str] = mapped_column(String(10))
    payer_currency: Mapped[str] = mapped_column(String(10))
    settlement_currency: Mapped[str] = mapped_column(String(10))
    amount_minor: Mapped[int] = mapped_column(Integer)
    payer_total_minor: Mapped[int] = mapped_column(Integer)
    escrow_amount_minor: Mapped[int] = mapped_column(Integer)
    supplier_estimated_net_minor: Mapped[int] = mapped_column(Integer)
    platform_revenue_minor: Mapped[int] = mapped_column(Integer, default=0)
    rate: Mapped[float | None] = mapped_column(Numeric(18, 8))
    rate_source: Mapped[str | None] = mapped_column(String(80))
    fx_quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[QuoteStatus] = mapped_column(Enum(QuoteStatus, name="payment_quote_status", create_type=False), default=QuoteStatus.ACTIVE, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeeLineItem(Base):
    __tablename__ = "fee_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType, name="payment_fee_type", create_type=False), index=True)
    label: Mapped[str] = mapped_column(String(120))
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10))
    refundable: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str] = mapped_column(String(50), default="SIMULATED")
    provider_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    payment_method: Mapped[str] = mapped_column(String(50))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[PaymentIntentStatus] = mapped_column(Enum(PaymentIntentStatus, name="payment_intent_status", create_type=False), default=PaymentIntentStatus.CREATED, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SettlementEvent(Base):
    __tablename__ = "settlement_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    gross_amount_minor: Mapped[int] = mapped_column(Integer)
    fee_amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    net_amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[SettlementEventStatus] = mapped_column(Enum(SettlementEventStatus, name="settlement_event_status", create_type=False), default=SettlementEventStatus.RECEIVED, index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SettlementAdjustment(Base):
    __tablename__ = "settlement_adjustments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    settlement_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    adjustment_type: Mapped[str] = mapped_column(String(80), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.payment_config import (
    FeeType,
    PaymentIntentStatus,
    QuoteStatus,
    SettlementEventStatus,
    TransactionCurrencyMode,
)


class RegionPaymentConfigResponse(BaseModel):
    id: uuid.UUID
    country_code: str
    country_name: str
    local_currency: str
    default_settlement_currency: str
    default_transaction_mode: TransactionCurrencyMode
    enabled_currencies: list[str]
    enabled_payment_methods: list[str]
    cross_border_currencies: list[str]
    force_usd_bridge: bool
    allow_supplier_payout_currency: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RegionPaymentConfigUpsert(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str = Field(min_length=2, max_length=120)
    local_currency: str = Field(min_length=3, max_length=10)
    default_settlement_currency: str = Field(min_length=3, max_length=10)
    default_transaction_mode: TransactionCurrencyMode = TransactionCurrencyMode.LOCAL_ONLY
    enabled_currencies: list[str] = Field(default_factory=list)
    enabled_payment_methods: list[str] = Field(default_factory=list)
    cross_border_currencies: list[str] = Field(default_factory=list)
    force_usd_bridge: bool = False
    allow_supplier_payout_currency: bool = False
    is_active: bool = True


class RegionPaymentConfigPatch(BaseModel):
    country_name: str | None = None
    local_currency: str | None = None
    default_settlement_currency: str | None = None
    default_transaction_mode: TransactionCurrencyMode | None = None
    enabled_currencies: list[str] | None = None
    enabled_payment_methods: list[str] | None = None
    cross_border_currencies: list[str] | None = None
    force_usd_bridge: bool | None = None
    allow_supplier_payout_currency: bool | None = None
    is_active: bool | None = None


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    country_code: str
    method_code: str
    provider: str
    currency: str
    is_enabled: bool
    config_json: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeeLineItemResponse(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID | None
    payment_intent_id: uuid.UUID | None
    fee_type: FeeType
    label: str
    amount_minor: int
    currency: str
    refundable: bool
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentQuoteCreateRequest(BaseModel):
    buyer_country: str = Field(default="PH", min_length=2, max_length=2)
    supplier_country: str = Field(default="PH", min_length=2, max_length=2)
    order_currency: str = Field(default="PHP", min_length=3, max_length=10)
    payer_currency: str = Field(default="PHP", min_length=3, max_length=10)
    settlement_currency: str = Field(default="PHP", min_length=3, max_length=10)
    amount_minor: int = Field(gt=0)
    payment_method: str = Field(default="PHP_MANUAL_BANK", min_length=2, max_length=50)
    order_id: uuid.UUID | None = None


class PaymentQuoteResponse(BaseModel):
    id: uuid.UUID
    buyer_country: str
    supplier_country: str
    mode: TransactionCurrencyMode
    payment_method: str
    order_currency: str
    payer_currency: str
    settlement_currency: str
    amount_minor: int
    payer_total_minor: int
    escrow_amount_minor: int
    supplier_estimated_net_minor: int
    platform_revenue_minor: int
    rate: float | None
    rate_source: str | None
    fx_quote_id: uuid.UUID | None
    expires_at: datetime
    status: QuoteStatus
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    fee_line_items: list[FeeLineItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PaymentIntentCreateRequest(BaseModel):
    quote_id: uuid.UUID
    order_id: uuid.UUID | None = None
    provider: str = "SIMULATED"


class PaymentIntentResponse(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID | None
    order_id: uuid.UUID | None
    provider: str
    provider_reference: str | None
    payment_method: str
    amount_minor: int
    currency: str
    status: PaymentIntentStatus
    raw_payload: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PayoutQuoteCreateRequest(BaseModel):
    supplier_country: str = Field(default="PH", min_length=2, max_length=2)
    source_currency: str = Field(default="PHP", min_length=3, max_length=10)
    payout_currency: str = Field(default="PHP", min_length=3, max_length=10)
    amount_minor: int = Field(gt=0)
    payout_method: str = "PHP_BANK_TRANSFER"


class PayoutQuoteResponse(BaseModel):
    source_currency: str
    payout_currency: str
    amount_minor: int
    rate: float
    fee_line_items: list[dict]
    supplier_estimated_net_minor: int
    expires_at: datetime


class SettlementEventResponse(BaseModel):
    id: uuid.UUID
    payment_intent_id: uuid.UUID | None
    provider: str
    provider_reference: str | None
    gross_amount_minor: int
    fee_amount_minor: int
    net_amount_minor: int
    currency: str
    status: SettlementEventStatus
    raw_payload: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}

"""Cebu zero-loss migration schemas — Wallet, Address, Shipping, Ads, Escrow, Payout."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Wallet ──────────────────────────────────────────────────────────


class WalletRead(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    currency: str
    available_balance_minor: int
    locked_balance_minor: int
    total_deposited_minor: int
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class WalletTransactionRead(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    owner_user_id: uuid.UUID
    tx_type: str
    amount_delta_minor: int
    available_balance_after_minor: int
    locked_balance_after_minor: int
    currency: str
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    note: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class WalletDepositCreate(BaseModel):
    amount_minor: int = Field(..., gt=0)
    currency: str = "USDT"
    network: str = "TRC20"
    provider: str = "MANUAL_BANK"
    payment_method: str = "PHP_MANUAL_BANK"
    source_currency: str | None = None
    target_currency: str | None = None
    deposit_address: str
    tx_hash: str | None = None
    submitter_note: str | None = None


class WalletDepositRead(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    owner_user_id: uuid.UUID
    amount_minor: int
    currency: str
    status: str
    tx_hash: str | None = None
    deposit_address: str
    submitter_note: str | None = None
    admin_note: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DepositVerifyRequest(BaseModel):
    admin_note: str | None = None


class DepositRejectRequest(BaseModel):
    admin_note: str | None = None


# ── Address ─────────────────────────────────────────────────────────


class AddressCreate(BaseModel):
    address_type: str = "DELIVERY_TO"
    label: str
    contact_name: str
    contact_phone: str
    country_code: str = Field(..., min_length=2, max_length=5)
    country_name: str
    state_province: str | None = None
    city: str
    district: str | None = None
    postal_code: str | None = None
    address_line1: str
    address_line2: str | None = None
    lat: float | None = None
    lng: float | None = None
    is_default: bool = False


class AddressRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID | None = None
    address_type: str
    label: str
    contact_name: str
    contact_phone: str
    country_code: str
    country_name: str
    state_province: str | None = None
    city: str
    district: str | None = None
    postal_code: str | None = None
    address_line1: str
    address_line2: str | None = None
    lat: float | None = None
    lng: float | None = None
    is_default: bool = False
    status: str = "ACTIVE"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AddressUpdate(BaseModel):
    label: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    is_default: bool | None = None


# ── Shipping ────────────────────────────────────────────────────────


class ShippingRouteCreate(BaseModel):
    origin_country: str
    origin_region: str | None = None
    dest_country: str
    dest_region: str | None = None
    shipping_method: str
    description: str | None = None


class ShippingRouteRead(BaseModel):
    id: uuid.UUID
    origin_country: str
    dest_country: str
    shipping_method: str
    description: str | None = None
    status: str = "ACTIVE"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShippingRouteUpdate(BaseModel):
    origin_country: str | None = None
    origin_region: str | None = None
    dest_country: str | None = None
    dest_region: str | None = None
    shipping_method: str | None = None
    description: str | None = None
    status: str | None = None


class ShippingRateCreate(BaseModel):
    route_id: uuid.UUID
    weight_min_kg: float = 0
    weight_max_kg: float = 99999
    price_per_kg_minor: int
    currency: str = "USD"
    min_charge_minor: int = 0
    volume_factor: float = 5000
    estimated_days_min: int = 1
    estimated_days_max: int = 7
    surcharges_json: dict | None = None
    valid_from: date
    valid_until: date | None = None
    notes: str | None = None


class ShippingRateRead(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    weight_min_kg: float
    weight_max_kg: float
    price_per_kg_minor: int
    currency: str
    min_charge_minor: int
    estimated_days_min: int
    estimated_days_max: int
    status: str = "ACTIVE"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShippingRateUpdate(BaseModel):
    weight_min_kg: float | None = None
    weight_max_kg: float | None = None
    price_per_kg_minor: int | None = None
    currency: str | None = None
    min_charge_minor: int | None = None
    volume_factor: float | None = None
    estimated_days_min: int | None = None
    estimated_days_max: int | None = None
    surcharges_json: dict | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    status: str | None = None


class ShippingEstimateRequest(BaseModel):
    origin_country: str
    dest_country: str
    weight_kg: float
    shipping_method: str | None = None


class ShippingEstimateRead(BaseModel):
    route_id: uuid.UUID
    shipping_method: str
    cost_minor: int
    currency: str
    estimated_days_min: int
    estimated_days_max: int


# ── Ads ─────────────────────────────────────────────────────────────


class AdCampaignCreate(BaseModel):
    listing_id: uuid.UUID | None = None
    title: str
    placement: str = "FEED_TOP"
    target_category_id: uuid.UUID | None = None
    target_keywords: list[str] | None = None
    target_countries: list[str] | None = None
    budget_minor: int = Field(..., gt=0)
    bid_per_click_minor: int = Field(..., gt=0)
    currency: str = "USD"
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AdCampaignRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    listing_id: uuid.UUID | None = None
    title: str
    placement: str
    budget_minor: int
    spent_minor: int = 0
    bid_per_click_minor: int
    currency: str
    status: str = "DRAFT"
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdCampaignStatusUpdate(BaseModel):
    status: str
    rejection_reason: str | None = None


# ── Escrow ──────────────────────────────────────────────────────────


class EscrowTransactionRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    order_id: uuid.UUID
    provider: str
    provider_reference: str | None = None
    auth_amount_minor: int
    captured_amount_minor: int
    released_amount_minor: int
    refunded_amount_minor: int
    currency: str
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class EscrowCaptureRequest(BaseModel):
    amount_minor: int | None = None


class EscrowReleaseRequest(BaseModel):
    amount_minor: int | None = None


class EscrowRefundRequest(BaseModel):
    amount_minor: int | None = None
    reason: str | None = None


# ── Payout ──────────────────────────────────────────────────────────


class PayoutRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    company_id: uuid.UUID
    order_id: uuid.UUID
    escrow_id: uuid.UUID | None = None
    amount_minor: int
    currency: str
    provider: str
    destination: str | None = None
    status: str = "PENDING"
    risk_hold: bool = False
    scheduled_at: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

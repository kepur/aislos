"""API request/response schemas for the Growth admin surface."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ImportListingIn(BaseModel):
    source: str = "manual"
    external_id: str
    url: str | None = None
    title: str | None = None
    description: str | None = None
    source_lang: str | None = None
    images: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    price_minor: int | None = None
    price_currency: str | None = "CNY"
    seller_ref: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    workspace_id: uuid.UUID | None = None


class TranslateIn(BaseModel):
    target_lang: str
    source_lang: str | None = None
    glossary: dict[str, str] = Field(default_factory=dict)


class PriceRuleIn(BaseModel):
    name: str
    scope: str = "global"  # listing | category | global
    category_id: uuid.UUID | None = None
    sell_currency: str = "EUR"
    freight_pct: Decimal = Decimal("0")
    freight_fixed_minor: int | None = None
    freight_currency: str | None = None
    duties_pct: Decimal = Decimal("0")
    target_margin_pct: Decimal = Decimal("0.30")
    platform_fee_pct: Decimal = Decimal("0")
    round_to_minor: int = 0
    min_price_minor: int | None = None
    max_price_minor: int | None = None
    reprice_cadence: str = "manual"
    reprice_threshold_pct: Decimal = Decimal("0")
    is_active: bool = True
    workspace_id: uuid.UUID | None = None


class PriceRuleOut(PriceRuleIn):
    id: uuid.UUID


class PriceIn(BaseModel):
    price_rule_id: uuid.UUID
    fx_rate: Decimal | None = None


class DraftIn(BaseModel):
    channel: str = "instagram"
    lang: str | None = None


class PublishIn(BaseModel):
    asset_id: uuid.UUID
    platforms: list[str] = Field(min_length=1)
    scheduled_at: datetime | None = None
    account_ref: str | None = None


class RepriceIn(BaseModel):
    fx_rate: Decimal | None = None


class PipelineIn(ImportListingIn):
    target_lang: str
    price_rule_id: uuid.UUID
    fx_rate: Decimal | None = None
    channel: str = "instagram"


class ListingOut(BaseModel):
    id: uuid.UUID
    source: str
    external_id: str
    status: str
    title: str | None = None
    description: str | None = None
    source_lang: str | None = None
    source_price_minor: int | None = None
    source_currency: str | None = None
    target_lang: str | None = None
    translated_title: str | None = None
    translated_description: str | None = None
    sell_price_minor: int | None = None
    sell_currency: str | None = None
    price_quote_json: dict[str, Any] | None = None
    images_json: list[Any] | None = None
    failure_code: str | None = None

    model_config = {"from_attributes": True}

"""Marketplace feed and ad campaign schemas."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.ad_campaign import AdCampaignStatus, AdPlacementType
from app.models.catalog import CatalogItemStatus, MarketMode


# ──────────────── Feed ────────────────

class FeedItemResponse(BaseModel):
    """A single item in the marketplace feed."""
    id: uuid.UUID
    title: str
    description: str | None
    price_minor: int
    currency: str
    unit: str
    stock_qty: int
    images: list | None
    tags: list | None
    market_mode: MarketMode
    min_order_qty: int
    origin_country: str | None
    view_count: int
    order_count: int
    status: CatalogItemStatus
    # Category info
    category_id: uuid.UUID
    category_name: str | None
    # Company info (supplier)
    company_id: uuid.UUID
    company_name: str | None
    company_trust_score: float | None
    # Ad info
    is_sponsored: bool = False
    ad_placement: str | None = None
    # Metadata
    created_at: datetime
    rank_score: float | None = None

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class FeedFiltersResponse(BaseModel):
    categories: list[dict]
    market_modes: list[str]
    currencies: list[str]
    origin_countries: list[str]
    price_range: dict  # {"min": int, "max": int}


# ──────────────── Ad Campaigns ────────────────

class AdCampaignCreate(BaseModel):
    catalog_item_id: uuid.UUID | None = None
    title: str
    placement: AdPlacementType
    target_category_id: uuid.UUID | None = None
    target_keywords: list[str] | None = None
    target_countries: list[str] | None = None
    budget_minor: int
    bid_per_click_minor: int
    currency: str = "USD"
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AdCampaignUpdate(BaseModel):
    title: str | None = None
    target_category_id: uuid.UUID | None = None
    target_keywords: list[str] | None = None
    target_countries: list[str] | None = None
    budget_minor: int | None = None
    bid_per_click_minor: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AdCampaignResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    catalog_item_id: uuid.UUID | None
    title: str
    placement: AdPlacementType
    target_category_id: uuid.UUID | None
    target_keywords: list | None
    target_countries: list | None
    budget_minor: int
    spent_minor: int
    bid_per_click_minor: int
    currency: str
    status: AdCampaignStatus
    rejection_reason: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    impressions: int
    clicks: int
    conversions: int
    created_at: datetime
    updated_at: datetime
    # Computed
    remaining_budget_minor: int | None = None
    ctr: float | None = None  # click-through rate

    model_config = {"from_attributes": True}


class AdCampaignMetricsResponse(BaseModel):
    campaign_id: uuid.UUID
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    cvr: float  # conversion rate
    spent_minor: int
    remaining_budget_minor: int
    avg_cpc_minor: float  # average cost per click
    currency: str


class AdminAdCampaignAction(BaseModel):
    reason: str | None = None

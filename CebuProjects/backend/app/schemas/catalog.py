import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.catalog import CatalogItemStatus, MarketMode


class CatalogItemCreate(BaseModel):
    branch_id: uuid.UUID | None = None
    category_id: uuid.UUID
    title: str
    description: str | None = None
    attrs_jsonb: dict | None = None
    price_minor: int
    currency: str = "PHP"
    stock_qty: int = 0
    unit: str
    images: list[str] = Field(default_factory=list, max_length=10)
    tags: list[str] = []
    market_mode: MarketMode = MarketMode.B2B
    min_order_qty: int = 1
    weight_kg: float | None = None
    origin_country: str | None = None
    status: CatalogItemStatus = CatalogItemStatus.ACTIVE


class CatalogItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    attrs_jsonb: dict | None = None
    price_minor: int | None = None
    currency: str | None = None
    stock_qty: int | None = None
    images: list[str] | None = Field(default=None, max_length=10)
    tags: list[str] | None = None
    market_mode: MarketMode | None = None
    min_order_qty: int | None = None
    weight_kg: float | None = None
    origin_country: str | None = None
    status: CatalogItemStatus | None = None


class CatalogItemResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    branch_id: uuid.UUID | None
    category_id: uuid.UUID
    title: str
    description: str | None
    attrs_jsonb: dict | None
    price_minor: int
    currency: str
    stock_qty: int
    unit: str
    images: list | None
    tags: list | None
    market_mode: MarketMode
    min_order_qty: int
    weight_kg: float | None
    origin_country: str | None
    view_count: int
    order_count: int
    status: CatalogItemStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.offer import OfferStatus, OfferTier, StockConfidence


class OfferCreate(BaseModel):
    catalog_item_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    unit_price_minor: int
    qty_available: int
    delivery_fee_minor: int = 0
    currency: str = "PHP"
    eta_date: datetime | None = None
    warranty: str | None = None
    tier: OfferTier = OfferTier.GOOD
    stock_confidence: StockConfidence = StockConfidence.UNKNOWN
    message: str | None = None
    expires_at: datetime | None = None


class OfferResponse(BaseModel):
    id: uuid.UUID
    intent_id: uuid.UUID
    company_id: uuid.UUID
    branch_id: uuid.UUID | None
    catalog_item_id: uuid.UUID | None
    supplier_user_id: uuid.UUID
    unit_price_minor: int
    qty_available: int
    delivery_fee_minor: int
    total_price_minor: int
    currency: str
    eta_date: datetime | None
    warranty: str | None
    tier: OfferTier
    stock_confidence: StockConfidence
    message: str | None
    status: OfferStatus
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

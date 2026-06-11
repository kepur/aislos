import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderCreateFromCatalog(BaseModel):
    catalog_item_id: uuid.UUID
    qty: int
    delivery_address_id: uuid.UUID | None = None
    delivery_city: str | None = None
    notes: str | None = None
class EscrowSummary(BaseModel):
    id: uuid.UUID
    status: str
    auth_amount_minor: int
    released_amount_minor: int
    currency: str

    model_config = {"from_attributes": True}


class DeliverySummary(BaseModel):
    id: uuid.UUID
    status: str
    tracking_number: str | None = None
    carrier: str | None = None
    estimated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    offer_id: uuid.UUID
    intent_id: uuid.UUID
    buyer_id: uuid.UUID
    company_id: uuid.UUID
    branch_id: uuid.UUID | None
    total_amount_minor: int
    currency: str
    status: OrderStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    escrow: EscrowSummary | None = None
    delivery: DeliverySummary | None = None

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

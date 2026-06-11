import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.delivery import DeliveryStatus


class DeliveryCreate(BaseModel):
    status: DeliveryStatus
    carrier: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    proofs: list[str] = []


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: DeliveryStatus
    carrier: str | None
    tracking_number: str | None
    notes: str | None
    proofs: list | None
    actor_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}

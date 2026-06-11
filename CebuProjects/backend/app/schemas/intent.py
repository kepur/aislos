import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.intent import IntentStatus


class IntentCreate(BaseModel):
    category_id: uuid.UUID
    title: str
    attrs_jsonb: dict | None = None
    qty: int
    unit: str
    budget_min_minor: int | None = None
    budget_max_minor: int | None = None
    currency: str = "PHP"
    country: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int = 30
    delivery_window_start: datetime | None = None
    delivery_window_end: datetime | None = None
    notes: str | None = None
    attachments: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class IntentUpdate(BaseModel):
    title: str | None = None
    attrs_jsonb: dict | None = None
    qty: int | None = None
    budget_min_minor: int | None = None
    budget_max_minor: int | None = None
    notes: str | None = None
    attachments: list[str] | None = Field(default=None)


class IntentResponse(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    category_id: uuid.UUID
    title: str
    attrs_jsonb: dict | None
    qty: int
    unit: str
    budget_min_minor: int | None
    budget_max_minor: int | None
    currency: str
    country: str | None
    city: str | None
    lat: float | None
    lng: float | None
    radius_km: int
    delivery_window_start: datetime | None
    delivery_window_end: datetime | None
    notes: str | None
    attachments: list | None
    status: IntentStatus
    expires_at: datetime | None
    project_id: uuid.UUID | None = None
    project_line_item_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

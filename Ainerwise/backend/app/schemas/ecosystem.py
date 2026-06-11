import uuid
from datetime import datetime

from pydantic import Field

from app.models.agent import AGENT_GRANT_SCOPES
from app.schemas.base import BaseSchema


class StoreOrderItemCreate(BaseSchema):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=1000)


class StoreOrderCreate(BaseSchema):
    items: list[StoreOrderItemCreate] = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)
    delivery_json: dict | None = None


class StoreOrderStatusUpdate(BaseSchema):
    status: str


class MarketplaceListingCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    role_title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    version: str = Field(default="1.0.0", max_length=50)
    workflows: list[str] = Field(default_factory=list, max_length=50)
    requested_scopes: list[str] = Field(default_factory=list, max_length=len(AGENT_GRANT_SCOPES))
    price_monthly: float | None = Field(default=None, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=10)


class MarketplaceReview(BaseSchema):
    notes: str | None = Field(default=None, max_length=4000)


class AgentInstallationCreate(BaseSchema):
    config_json: dict | None = None


class MarketplaceListingRead(BaseSchema):
    id: uuid.UUID
    agent_id: uuid.UUID | None = None
    slug: str
    name: str
    role_title: str | None = None
    description: str | None = None
    version: str
    workflows_json: list | None = None
    requested_scopes_json: list | None = None
    price_monthly: float | None = None
    currency: str
    status: str
    review_notes: str | None = None
    created_at: datetime

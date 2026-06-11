import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.category import CategoryStatus


class CategoryCreate(BaseModel):
    parent_id: uuid.UUID | None = None
    name: str
    name_zh: str | None = None
    name_tl: str | None = None
    slug: str
    level: int = 1
    icon: str | None = None
    description: str | None = None
    sort_order: int = 0
    schema_json: dict | None = None
    typical_weight_kg: float | None = None
    customs_hs_code: str | None = None
    status: CategoryStatus = CategoryStatus.ACTIVE


class CategoryUpdate(BaseModel):
    name: str | None = None
    name_zh: str | None = None
    name_tl: str | None = None
    slug: str | None = None
    level: int | None = None
    icon: str | None = None
    description: str | None = None
    sort_order: int | None = None
    schema_json: dict | None = None
    typical_weight_kg: float | None = None
    customs_hs_code: str | None = None
    status: CategoryStatus | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    name_zh: str | None
    name_tl: str | None
    slug: str
    level: int
    icon: str | None
    description: str | None
    sort_order: int
    schema_json: dict | None
    typical_weight_kg: float | None
    customs_hs_code: str | None
    status: CategoryStatus
    created_at: datetime

    model_config = {"from_attributes": True}

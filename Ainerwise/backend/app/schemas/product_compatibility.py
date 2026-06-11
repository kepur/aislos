import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ProductCompatibilityRead(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    protocol: str
    compatibility_level: str
    tested_by: str | None = None
    test_status: str | None = None
    notes: str | None = None
    test_artifact_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductCompatibilityCreate(BaseSchema):
    product_id: uuid.UUID
    protocol: str
    compatibility_level: str = "unknown"
    tested_by: str | None = None
    test_status: str | None = None
    notes: str | None = None
    test_artifact_url: str | None = None


class ProductCompatibilityUpdate(BaseSchema):
    protocol: str | None = None
    compatibility_level: str | None = None
    tested_by: str | None = None
    test_status: str | None = None
    notes: str | None = None
    test_artifact_url: str | None = None

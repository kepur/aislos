import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class RegionRead(BaseSchema):
    id: uuid.UUID
    code: str
    name: str
    currency_code: str
    language_codes_json: list | None = None
    tax_rules_json: dict | None = None
    timezone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegionCreate(BaseSchema):
    code: str
    name: str
    currency_code: str = "EUR"
    language_codes_json: list | None = None
    tax_rules_json: dict | None = None
    timezone: str | None = None


class RegionUpdate(BaseSchema):
    name: str | None = None
    currency_code: str | None = None
    language_codes_json: list | None = None
    tax_rules_json: dict | None = None
    timezone: str | None = None
    is_active: bool | None = None

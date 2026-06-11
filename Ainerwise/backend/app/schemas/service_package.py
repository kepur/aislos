import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ServicePackageRead(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    years: int | None = None
    description: str | None = None
    included_services_json: list | None = None
    sla_json: dict | None = None
    price_rule_json: dict | None = None
    public_visible: bool
    sort_order: int
    created_at: datetime


class ServicePackageCreate(BaseSchema):
    name: str
    slug: str | None = None
    years: int | None = None
    description: str | None = None
    included_services_json: list | None = None
    sla_json: dict | None = None
    price_rule_json: dict | None = None
    public_visible: bool = True
    sort_order: int = 0


class ServicePackageUpdate(BaseSchema):
    name: str | None = None
    years: int | None = None
    description: str | None = None
    included_services_json: list | None = None
    sla_json: dict | None = None
    price_rule_json: dict | None = None
    public_visible: bool | None = None
    sort_order: int | None = None

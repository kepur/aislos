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


class ServicePackagePublicRead(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    years: int | None = None
    description: str | None = None
    included_services_json: list | None = None
    sla_json: dict | None = None
    price_rule_json: dict | None = None
    sort_order: int

    @classmethod
    def from_package(cls, package) -> "ServicePackagePublicRead":
        rule = package.price_rule_json if isinstance(package.price_rule_json, dict) else {}
        public_rule_keys = {"billing", "remote_support", "on_site", "term_label"}
        return cls(
            id=package.id,
            name=package.name,
            slug=package.slug,
            years=package.years,
            description=package.description,
            included_services_json=package.included_services_json,
            sla_json=package.sla_json,
            price_rule_json={key: rule[key] for key in public_rule_keys if key in rule} or None,
            sort_order=package.sort_order,
        )


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

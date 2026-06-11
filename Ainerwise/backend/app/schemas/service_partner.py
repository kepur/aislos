import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ServicePartnerRead(BaseSchema):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    partner_type: str
    country: str | None = None
    city: str | None = None
    service_radius_km: int | None = None
    languages_json: list | None = None
    skills_json: list | None = None
    certifications_json: list | None = None
    hourly_rate: float | None = None
    day_rate: float | None = None
    project_rate_rule_json: dict | None = None
    availability_status: str
    rating_internal: float | None = None
    public_visible: bool
    verification_status: str
    telegram_chat_id: str | None = None
    notes_internal: str | None = None
    created_at: datetime
    updated_at: datetime


class ServicePartnerCreate(BaseSchema):
    company_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    partner_type: str
    country: str | None = None
    city: str | None = None
    service_radius_km: int | None = None
    languages_json: list | None = None
    skills_json: list | None = None
    certifications_json: list | None = None
    hourly_rate: float | None = None
    day_rate: float | None = None
    project_rate_rule_json: dict | None = None
    notes_internal: str | None = None


class ServicePartnerUpdate(BaseSchema):
    partner_type: str | None = None
    country: str | None = None
    city: str | None = None
    service_radius_km: int | None = None
    languages_json: list | None = None
    skills_json: list | None = None
    certifications_json: list | None = None
    hourly_rate: float | None = None
    day_rate: float | None = None
    project_rate_rule_json: dict | None = None
    availability_status: str | None = None
    public_visible: bool | None = None
    telegram_chat_id: str | None = None
    notes_internal: str | None = None


class ServicePartnerStatusUpdate(BaseSchema):
    verification_status: str

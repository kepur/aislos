import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import BaseSchema


class VendorApply(BaseSchema):
    company_name: str
    country: str | None = None
    city: str | None = None
    company_type: str | None = None
    email: EmailStr
    phone: str | None = None
    contact_info: dict | None = None
    address: str | None = None
    website: str | None = None
    description: str | None = None


class VendorRead(BaseSchema):
    id: uuid.UUID
    name: str
    type: str
    country: str | None = None
    city: str | None = None
    address: str | None = None
    verification_status: str
    contact_info: dict | None = None
    logo_url: str | None = None
    description: str | None = None
    website: str | None = None
    created_at: datetime


class VendorStatusUpdate(BaseSchema):
    verification_status: str

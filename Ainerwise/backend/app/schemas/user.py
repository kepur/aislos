import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import BaseSchema


class UserRead(BaseSchema):
    id: uuid.UUID
    email: EmailStr
    phone: str | None = None
    full_name: str | None = None
    role: str
    language: str
    country: str | None = None
    company_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseSchema):
    full_name: str | None = None
    phone: str | None = None
    language: str | None = None
    country: str | None = None


class CompanyRead(BaseSchema):
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


class CompanyCreate(BaseSchema):
    name: str
    type: str
    country: str | None = None
    city: str | None = None
    address: str | None = None
    contact_info: dict | None = None
    description: str | None = None
    website: str | None = None


class CompanyUpdate(BaseSchema):
    name: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    contact_info: dict | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.address import AddressType


class AddressCreate(BaseModel):
    address_type: AddressType
    label: str = Field(..., max_length=100)
    contact_name: str = Field(..., max_length=255)
    contact_phone: str = Field(..., max_length=50)
    country_code: str = Field(..., max_length=5)
    country_name: str = Field(..., max_length=100)
    state_province: str | None = None
    city: str = Field(..., max_length=100)
    district: str | None = None
    postal_code: str | None = None
    address_line1: str
    address_line2: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_place_id: str | None = None
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    state_province: str | None = None
    city: str | None = None
    district: str | None = None
    postal_code: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_place_id: str | None = None


class AddressResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID | None = None
    address_type: str
    label: str
    contact_name: str
    contact_phone: str
    country_code: str
    country_name: str
    state_province: str | None = None
    city: str
    district: str | None = None
    postal_code: str | None = None
    address_line1: str
    address_line2: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_place_id: str | None = None
    is_default: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

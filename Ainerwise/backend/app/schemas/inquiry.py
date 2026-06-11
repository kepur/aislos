import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class InquiryRead(BaseSchema):
    id: uuid.UUID
    buyer_company_id: uuid.UUID | None = None
    buyer_user_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    vendor_company_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    message: str | None = None
    quantity: int | None = None
    status: str
    admin_notes: str | None = None
    campaign_id: uuid.UUID | None = None
    source_channel: str | None = None
    source_detail: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    landing_page: str | None = None
    referrer: str | None = None
    created_at: datetime


class InquiryCreate(BaseSchema):
    product_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    message: str | None = None
    quantity: int | None = None
    campaign_id: uuid.UUID | None = None
    source_channel: str | None = None
    source_detail: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    landing_page: str | None = None
    referrer: str | None = None


class InquiryUpdate(BaseSchema):
    message: str | None = None
    admin_notes: str | None = None
    quantity: int | None = None


class InquiryStatusUpdate(BaseSchema):
    status: str

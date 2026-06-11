import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


class QuoteRead(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    quote_items_json: list | None = None
    device_total: float
    service_total: float
    platform_fee: float
    support_package_fee: float
    spare_parts_fee: float
    logistics_fee: float
    tax_fee: float
    discount: float
    total: float
    currency: str
    status: str
    valid_until: date | None = None
    notes: str | None = None
    # FI.4.4 — customer-facing packages (no supplier cost). internal_economics_json
    # is intentionally NOT exposed here; it is admin-only via the economics endpoint.
    customer_line_items_json: list | None = None
    first_year_total: float = 0
    annual_recurring_total: float = 0
    created_at: datetime


class QuoteCreate(BaseSchema):
    lead_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    quote_items_json: list | None = None
    device_total: float = 0
    service_total: float = 0
    platform_fee: float = 0
    support_package_fee: float = 0
    spare_parts_fee: float = 0
    logistics_fee: float = 0
    tax_fee: float = 0
    discount: float = 0
    total: float = 0
    currency: str = "EUR"
    valid_until: date | None = None
    notes: str | None = None
    customer_line_items_json: list | None = None
    internal_economics_json: dict | None = None
    first_year_total: float = 0
    annual_recurring_total: float = 0


class QuoteUpdate(BaseSchema):
    quote_items_json: list | None = None
    device_total: float | None = None
    service_total: float | None = None
    platform_fee: float | None = None
    support_package_fee: float | None = None
    spare_parts_fee: float | None = None
    logistics_fee: float | None = None
    tax_fee: float | None = None
    discount: float | None = None
    total: float | None = None
    currency: str | None = None
    valid_until: date | None = None
    notes: str | None = None
    customer_line_items_json: list | None = None
    internal_economics_json: dict | None = None
    first_year_total: float | None = None
    annual_recurring_total: float | None = None


class QuoteStatusUpdate(BaseSchema):
    status: str

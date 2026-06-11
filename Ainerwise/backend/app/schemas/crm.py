"""Schemas for CRM (supplier scorecard, FI.6.6)."""
import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class SupplierScorecardBase(BaseSchema):
    company_id: uuid.UUID | None = None
    supplier_name: str | None = None
    quality: int | None = None
    delivery: int | None = None
    response: int | None = None
    warranty_cooperation: int | None = None
    documentation: int | None = None
    price_stability: int | None = None
    long_term_fit: int | None = None
    notes: str | None = None


class SupplierScorecardCreate(SupplierScorecardBase):
    pass


class SupplierScorecardUpdate(SupplierScorecardBase):
    pass


class SupplierScorecardRead(SupplierScorecardBase):
    id: uuid.UUID
    overall_score: float | None = None
    created_at: datetime

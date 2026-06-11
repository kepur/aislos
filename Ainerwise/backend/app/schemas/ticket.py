import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class TicketRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    buyer_company_id: uuid.UUID | None = None
    buyer_user_id: uuid.UUID | None = None
    issue_type: str | None = None
    priority: str
    title: str
    description: str | None = None
    files_json: list | None = None
    status: str
    assigned_to: uuid.UUID | None = None
    # FI.2.4 coverage fields
    affected_device: str | None = None
    monitoring_point_id: uuid.UUID | None = None
    warranty_related: bool | None = None
    amc_covered: bool | None = None
    is_paid_service: bool | None = None
    coverage_type: str | None = None
    estimated_cost: float | None = None
    resolution: str | None = None
    created_at: datetime


class TicketCreate(BaseSchema):
    project_id: uuid.UUID | None = None
    issue_type: str | None = None
    priority: str = "medium"
    title: str
    description: str | None = None
    affected_device: str | None = None
    monitoring_point_id: uuid.UUID | None = None


class TicketUpdate(BaseSchema):
    issue_type: str | None = None
    priority: str | None = None
    title: str | None = None
    description: str | None = None
    # FI.2.4 coverage fields (admin triage)
    affected_device: str | None = None
    monitoring_point_id: uuid.UUID | None = None
    warranty_related: bool | None = None
    amc_covered: bool | None = None
    is_paid_service: bool | None = None
    coverage_type: str | None = None
    estimated_cost: float | None = None
    resolution: str | None = None


class TicketStatusUpdate(BaseSchema):
    status: str

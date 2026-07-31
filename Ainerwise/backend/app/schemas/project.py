import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


class ProjectRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    buyer_company_id: uuid.UUID | None = None
    title: str
    status: str
    region: str | None = None
    start_date: date | None = None
    expected_delivery_date: date | None = None
    project_plan_json: dict | None = None
    team_json: list | None = None
    telegram_chat_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectCustomerRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    title: str
    status: str
    region: str | None = None
    start_date: date | None = None
    expected_delivery_date: date | None = None
    project_plan_json: dict | None = None
    team_json: list | None = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseSchema):
    workspace_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    buyer_company_id: uuid.UUID | None = None
    title: str
    region: str | None = None
    start_date: date | None = None
    expected_delivery_date: date | None = None
    project_plan_json: dict | None = None
    team_json: list | None = None
    notes: str | None = None


class ProjectUpdate(BaseSchema):
    title: str | None = None
    region: str | None = None
    start_date: date | None = None
    expected_delivery_date: date | None = None
    project_plan_json: dict | None = None
    team_json: list | None = None
    telegram_chat_id: str | None = None
    notes: str | None = None


class ProjectStatusUpdate(BaseSchema):
    status: str

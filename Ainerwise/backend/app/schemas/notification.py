"""Schemas for notification preferences + report jobs (FI.8.3, FI.8.5)."""
import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


class NotificationPreferenceRead(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    telegram_enabled: bool
    email_enabled: bool
    whatsapp_enabled: bool
    telegram_chat_id: str | None = None
    email: str | None = None
    whatsapp_number: str | None = None
    alerts_enabled: bool
    reports_enabled: bool
    maintenance_enabled: bool
    renewal_enabled: bool


class NotificationPreferenceUpdate(BaseSchema):
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    telegram_chat_id: str | None = None
    email: str | None = None
    whatsapp_number: str | None = None
    alerts_enabled: bool | None = None
    reports_enabled: bool | None = None
    maintenance_enabled: bool | None = None
    renewal_enabled: bool | None = None


class ReportJobRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    report_type: str
    period_label: str | None = None
    status: str
    review_status: str
    file_id: uuid.UUID | None = None
    scheduled_for: date | None = None
    notes: str | None = None
    created_at: datetime


class ReportJobReview(BaseSchema):
    review_status: str  # approved | rejected
    notes: str | None = None

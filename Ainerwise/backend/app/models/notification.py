"""Notification preferences + scheduled report jobs (FI.8.3, FI.8.5)."""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """FI.8.3 — per-customer channel + event preferences."""
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, unique=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    # Channels
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    whatsapp_number: Mapped[str | None] = mapped_column(String(50))
    # Event categories
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reports_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    maintenance_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    renewal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ReportJob(Base, UUIDMixin, TimestampMixin):
    """FI.8.5 — scheduled compliance report job with review gate before delivery."""
    __tablename__ = "report_jobs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly|annual
    period_label: Mapped[str | None] = mapped_column(String(50))  # e.g. "2026-05"
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|generating|pending_review|approved|delivered|failed
    review_status: Mapped[str] = mapped_column(String(30), default="pending_review")  # pending_review|approved|rejected
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("file_assets.id"), nullable=True
    )
    scheduled_for: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

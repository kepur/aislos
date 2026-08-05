"""Notification preferences + scheduled report jobs (FI.8.3, FI.8.5)."""
import uuid
from datetime import date

from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    viber_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    whatsapp_number: Mapped[str | None] = mapped_column(String(50))
    viber_number: Mapped[str | None] = mapped_column(String(50))
    # Event categories
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reports_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    maintenance_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    renewal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    supplier_category_ids_json: Mapped[list | None] = mapped_column(JSONB)
    supplier_region_ids_json: Mapped[list | None] = mapped_column(JSONB)


def apply_notification_preference_defaults(
    pref: NotificationPreference,
    *,
    email: str | None = None,
) -> bool:
    """Backfill safe defaults for older preference rows created before Telegram was default-on."""
    changed = False
    if email and not pref.email:
        pref.email = email
        changed = True

    has_external_contact = any(
        [
            pref.telegram_chat_id,
            pref.whatsapp_enabled,
            pref.viber_enabled,
            pref.whatsapp_number,
            pref.viber_number,
        ]
    )
    timestamps_look_untouched = True
    if pref.created_at and pref.updated_at:
        timestamps_look_untouched = (
            abs((pref.updated_at - pref.created_at).total_seconds()) < 1
        )
    if pref.telegram_enabled is False and not has_external_contact and timestamps_look_untouched:
        pref.telegram_enabled = True
        changed = True

    return changed


class ReportJob(Base, UUIDMixin, TimestampMixin):
    """FI.8.5 — scheduled compliance report job with review gate before delivery."""
    __tablename__ = "report_jobs"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
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


class PortalNotification(Base, UUIDMixin, TimestampMixin):
    """In-app notification inbox (Cebu parity) — separate from AI conversation messages."""

    __tablename__ = "portal_notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    portal_key: Mapped[str] = mapped_column(String(64), default="cebu", nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(32), default="commerce", nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    link_path: Mapped[str | None] = mapped_column(String(512))
    aggregate_type: Mapped[str | None] = mapped_column(String(64))
    aggregate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="unread", nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

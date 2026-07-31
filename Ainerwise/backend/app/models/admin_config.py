"""Shared admin notes, notification templates, and non-secret platform settings."""
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class AdminNote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "admin_notes"

    portal_key: Mapped[str] = mapped_column(String(64), default="admin_cebu", nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    visibility: Mapped[str] = mapped_column(String(32), default="internal_only", nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)


class NotificationTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint(
            "portal_key", "template_key", "channel", "language",
            name="uq_notification_template_scope",
        ),
    )

    portal_key: Mapped[str] = mapped_column(String(64), default="admin_cebu", nullable=False, index=True)
    template_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables_hint: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PlatformSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "platform_settings"
    __table_args__ = (
        UniqueConstraint("portal_key", "key", name="uq_platform_setting_scope"),
    )

    portal_key: Mapped[str] = mapped_column(String(64), default="admin_cebu", nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(String(500))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

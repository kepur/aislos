"""Shared platform legacy bridge models (SP03/SP04)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class LegacyBridgeIdempotency(Base, UUIDMixin):
    __tablename__ = "legacy_bridge_idempotency"
    __table_args__ = (
        UniqueConstraint("client_id", "idempotency_key", name="uq_legacy_bridge_idempotency"),
    )

    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LegacyIdentityMapping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legacy_identity_mappings"
    __table_args__ = (
        UniqueConstraint(
            "portal_key",
            "legacy_system",
            "legacy_user_id",
            name="uq_legacy_identity_user",
        ),
    )

    portal_key: Mapped[str] = mapped_column(String(50), nullable=False)
    legacy_system: Mapped[str] = mapped_column(String(50), nullable=False, default="cebu")
    legacy_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    legacy_company_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    core_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    core_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

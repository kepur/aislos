"""Auditable, idempotent historical migration ledger for legacy systems."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class LegacyMigrationRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legacy_migration_runs"
    __table_args__ = (
        UniqueConstraint("source_system", "batch_key", name="uq_legacy_migration_batch"),
    )

    source_system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    portal_key: Mapped[str] = mapped_column(String(64), nullable=False, default="cebu")
    batch_key: Mapped[str] = mapped_column(String(160), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING", index=True)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    counts_json: Mapped[dict | None] = mapped_column(JSONB)
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LegacyMigrationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legacy_migration_records"
    __table_args__ = (
        UniqueConstraint(
            "source_system",
            "entity_type",
            "legacy_id",
            name="uq_legacy_migration_object",
        ),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legacy_migration_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    legacy_id: Mapped[str] = mapped_column(String(160), nullable=False)
    core_entity_type: Mapped[str | None] = mapped_column(String(64))
    core_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_payload_json: Mapped[dict | None] = mapped_column(JSONB)
    operation: Mapped[str | None] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    details_json: Mapped[dict | None] = mapped_column(JSONB)

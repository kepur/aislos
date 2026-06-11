import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class IntegrationEvent(Base, UUIDMixin, TimestampMixin):
    """Outbox row: written in the same transaction as the business change.

    `status` tracks notification delivery (telegram etc.); `published_at`
    tracks relay to the Redis Stream event bus — the two are independent.
    """

    __tablename__ = "integration_events"
    __table_args__ = (
        Index(
            "ix_integration_events_unpublished",
            "created_at",
            postgresql_where=text("published_at IS NULL"),
        ),
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB)
    target_channel: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    aggregate_type: Mapped[str | None] = mapped_column(String(50))
    aggregate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_runs"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_json: Mapped[dict | None] = mapped_column(JSONB)
    output_json: Mapped[dict | None] = mapped_column(JSONB)
    model_name: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

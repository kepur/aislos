import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class ChannelAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_accounts"
    __table_args__ = {"schema": "channels"}

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credentials_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class ChannelThread(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_threads"
    __table_args__ = (
        UniqueConstraint("account_id", "external_thread_id", name="uq_channel_threads_account_external"),
        {"schema": "channels"},
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.channel_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.conversations.id")
    )
    contact_name: Mapped[str | None] = mapped_column(String(255))
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class ChannelMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_messages"
    __table_args__ = (
        Index(
            "uq_channels_channel_messages_thread_external",
            "thread_id",
            "external_message_id",
            unique=True,
            postgresql_where=text("external_message_id IS NOT NULL"),
        ),
        {"schema": "channels"},
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.channel_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False, index=True)


class ChannelDeliveryLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "delivery_log"
    __table_args__ = {"schema": "channels"}

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.channel_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

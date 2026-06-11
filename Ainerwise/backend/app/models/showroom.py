"""Experience Center (Portal 10): stores, kiosk devices, showroom sessions
and in-store orders. Constitution red lines apply: devices are dumb terminals
(token-scoped API surface only), transcripts not raw audio, AI self-discloses.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

SESSION_OUTCOMES = ("purchase", "lead", "browse", "abandoned")
SHOWROOM_ORDER_STATUSES = ("draft", "confirmed", "paid_in_store", "cancelled")
VOICE_MODES = ("text", "realtime", "pipeline")


class Store(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stores"

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class KioskDevice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kiosk_devices"

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    agent_slug: Mapped[str] = mapped_column(String(100), ForeignKey("agents.slug"), nullable=False)
    default_lang: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    voice_mode: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShowroomSession(Base, UUIDMixin, TimestampMixin):
    """One walk-up conversation — the conversion dataset (Rule #1 asset)."""

    __tablename__ = "showroom_sessions"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kiosk_devices.id"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.conversations.id")
    )
    lang: Mapped[str | None] = mapped_column(String(10))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    need_category: Mapped[str | None] = mapped_column(String(100))
    budget_hint: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    products_viewed_json: Mapped[list | None] = mapped_column(JSONB)
    outcome: Mapped[str | None] = mapped_column(String(50), index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"))


class ShowroomOrder(Base, UUIDMixin, TimestampMixin):
    """In-store order draft -> POS confirmation. Aligned with future Store
    orders; no online payment in store (POS terminal + ledger entry)."""

    __tablename__ = "showroom_orders"

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("showroom_sessions.id"), index=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    items_json: Mapped[list] = mapped_column(JSONB, nullable=False)  # [{product_id, name, qty, unit_price}]
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    pickup_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text)

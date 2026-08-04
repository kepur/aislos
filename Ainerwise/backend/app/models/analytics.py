"""Analytics event spine (P2).

One append-only table is the source of truth for every question the business
asks: which SKUs sell, which channel converts, which ad image gets clicked.
Aggregate counters cannot answer those — `AdCampaign.impressions/clicks` is
exactly the shape that loses creative-level attribution — so events are stored
at full grain and rolled up on read.

Lives in its own `analytics` schema alongside public/ai/channels, per the
single-Postgres architecture. Nothing here changes an existing table.

GDPR: no raw visitor PII. `actor_hash` is a salted hash and `session_id` is an
opaque client token; neither can be reversed to a person.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

# The funnel, in order. Keeping these as one vocabulary across onsite and
# syndicated traffic is what makes channels comparable at all.
EVENT_TYPES = (
    "listing.impression",   # appeared in a list, feed or external channel
    "listing.view",         # detail page opened
    "contact.requested",    # buyer asked for the pickup address — a real lead
    "contact.granted",      # seller approved that buyer
    "deal.reserved",        # item held for a buyer
    "deal.completed",       # sold, carries value_minor
    "deal.cancelled",
    "listing.published",    # went live on our own storefront
    "channel.published",    # went live on an external channel
    "channel.delisted",
    "creative.impression",  # a specific image/copy variant was shown
    "creative.click",       # …and was clicked
)

# Events that represent money changing hands.
VALUE_EVENT_TYPES = ("deal.completed",)

CREATIVE_STATUSES = ("active", "retired")
GENERATED_BY = ("human", "ai")


class AnalyticsEvent(Base, UUIDMixin, TimestampMixin):
    """One thing that happened, with everything needed to attribute it.

    Append-only: rows are never updated. Corrections arrive as new events.
    """

    __tablename__ = "events"
    __table_args__ = (
        # The three questions this table exists to answer, each indexed.
        Index("ix_analytics_events_sku", "listing_id", "event_type", "occurred_at"),
        Index("ix_analytics_events_channel", "channel_account_id", "event_type", "occurred_at"),
        Index("ix_analytics_events_creative", "creative_id", "event_type", "occurred_at"),
        Index("ix_analytics_events_portal_time", "portal_key", "occurred_at"),
        {"schema": "analytics"},
    )

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # ── attribution ───────────────────────────────────────────────────────
    portal_key: Mapped[str | None] = mapped_column(String(64), index=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, index=True
    )
    # NULL means our own storefront; set means it came from that channel.
    channel_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.channel_accounts.id", ondelete="SET NULL"), nullable=True
    )
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id", ondelete="SET NULL"), nullable=True
    )
    creative_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analytics.creatives.id", ondelete="SET NULL"), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # ── actor (never raw PII) ─────────────────────────────────────────────
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    actor_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # ── value ─────────────────────────────────────────────────────────────
    value_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(3))

    # ── provenance ────────────────────────────────────────────────────────
    # Which app produced this: "2hands", "market", or an external project key.
    source_app: Mapped[str | None] = mapped_column(String(64), index=True)
    # Set by producers that may retry. Unique, so a replay cannot double-count.
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class Creative(Base, UUIDMixin, TimestampMixin):
    """An ad image or copy variant, so click-through can be compared per asset.

    Without this the platform can only say "the campaign got clicks", never
    "this photo gets clicked twice as often as that one".
    """

    __tablename__ = "creatives"
    __table_args__ = {"schema": "analytics"}

    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    channel_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.channel_accounts.id", ondelete="SET NULL"), nullable=True
    )
    variant_label: Mapped[str] = mapped_column(String(80), default="default", nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    copy_text: Mapped[str | None] = mapped_column(Text)
    generated_by: Mapped[str] = mapped_column(String(16), default="human", nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False, index=True)


class AnalyticsClient(Base, UUIDMixin, TimestampMixin):
    """An external project allowed to push events.

    `source_app` is bound to the key, not taken from the request body: a client
    must not be able to attribute its traffic to somebody else's app, which is
    the whole basis of cross-project reporting.
    """

    __tablename__ = "clients"
    __table_args__ = {"schema": "analytics"}

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Server-assigned attribution. Immutable once issued.
    source_app: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    scopes_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Empty/NULL means every region; otherwise the key is fenced to these.
    allowed_region_ids_json: Mapped[list | None] = mapped_column(JSONB)
    allowed_portal_keys_json: Mapped[list | None] = mapped_column(JSONB)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


ANALYTICS_SCOPES = ("events:write", "reports:read")


class AnalyticsProjectionCursor(Base, UUIDMixin, TimestampMixin):
    """Watermark for projecting the existing integration_events outbox.

    Lets the platform's own flows feed analytics without changing a single
    producer, and makes a backfill a matter of moving the cursor back.
    """

    __tablename__ = "projection_cursors"
    __table_args__ = {"schema": "analytics"}

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    last_event_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    processed_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

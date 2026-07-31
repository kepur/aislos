"""Multi-channel listing syndication (P1).

Purely additive: nothing here changes how existing listings, orders or the
Market/Cebu flows behave. A syndication channel is an existing
`channels.channel_accounts` row tagged `meta_json.kind = "syndication"`, so no
existing table is altered either.

The driver contract in `app/services/syndication.py` is the seam that later
lets an AI agent publish through exactly the same mapping and job path.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

CHANNEL_LISTING_STATUSES = (
    "draft",              # mapped, not sent anywhere yet
    "pending_review",     # waiting for a human to POST it (assisted / AI drafts)
    "published",          # live on the external channel
    "pending_takedown",   # sold, waiting for a human to REMOVE the live post
    "failed",             # last attempt errored — see last_error
    "delisted",           # confirmed gone from the channel
)

# Rows an operator still has to act on. Kept distinct from `published` so a
# sold item is never mistaken for a live one, and from `pending_review` so the
# operator queue says whether to post or to take down.
ACTION_REQUIRED_STATUSES = ("pending_review", "pending_takedown", "failed")

# Statuses that still occupy the channel and therefore need a takedown.
LIVE_STATUSES = ("draft", "pending_review", "published")

# Ordered by compliance preference. Automated posting breaks most classifieds'
# terms of service, so `api`/`feed`/`assisted` come first by design.
DRIVER_KINDS = ("api", "feed", "assisted", "agent")


class ChannelListing(Base, UUIDMixin, TimestampMixin):
    """One of our SKUs as published on one external channel account."""

    __tablename__ = "channel_listings"
    __table_args__ = (
        UniqueConstraint("supplier_listing_id", "account_id", name="uq_channel_listing_account"),
        {"schema": "channels"},
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    supplier_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("supplier_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.channel_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)

    # Fingerprint of the mapped payload. Re-publishing is skipped when it is
    # unchanged — repeated identical posts are what gets accounts flagged.
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB)
    stats_json: Mapped[dict | None] = mapped_column(JSONB)

    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelCategoryMap(Base, UUIDMixin, TimestampMixin):
    """Our category -> the channel's category, plus per-channel field mapping.

    Kept as data rather than code: every classifieds site names its taxonomy
    differently, and operators need to fix mappings without a deploy.
    """

    __tablename__ = "channel_category_maps"
    __table_args__ = (
        UniqueConstraint("account_id", "category_schema_id", name="uq_channel_category_map"),
        {"schema": "channels"},
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.channel_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_schema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trade_category_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_category_code: Mapped[str] = mapped_column(String(120), nullable=False)
    external_category_path: Mapped[str | None] = mapped_column(String(500))
    # {"our_field": "their_field"} overrides applied on top of the base mapping.
    field_map_json: Mapped[dict | None] = mapped_column(JSONB)
    # Constants every post on this channel/category needs (e.g. currency, region id).
    defaults_json: Mapped[dict | None] = mapped_column(JSONB)

"""Analytics event spine (P2): append-only events, creatives, projection cursor.

New `analytics` schema. Purely additive — no existing table is touched.

Revision ID: 082
Revises: 081
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "082"
down_revision: Union[str, None] = "081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    op.create_table(
        "creatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier_listings.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "channel_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.channel_accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("variant_label", sa.String(80), server_default="default", nullable=False),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("copy_text", sa.Text(), nullable=True),
        sa.Column("generated_by", sa.String(16), server_default="human", nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        schema="analytics",
    )
    op.create_index("ix_analytics_creatives_listing_id", "creatives", ["listing_id"], schema="analytics")
    op.create_index("ix_analytics_creatives_content_hash", "creatives", ["content_hash"], schema="analytics")
    op.create_index("ix_analytics_creatives_status", "creatives", ["status"], schema="analytics")

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("portal_key", sa.String(64), nullable=True),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column(
            "channel_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.channel_accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier_listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "creative_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analytics.creatives.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("actor_hash", sa.String(64), nullable=True),
        sa.Column("value_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("source_app", sa.String(64), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True, unique=True),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="analytics",
    )
    op.create_index("ix_analytics_events_occurred_at", "events", ["occurred_at"], schema="analytics")
    op.create_index("ix_analytics_events_event_type", "events", ["event_type"], schema="analytics")
    op.create_index("ix_analytics_events_portal_key", "events", ["portal_key"], schema="analytics")
    op.create_index("ix_analytics_events_region_id", "events", ["region_id"], schema="analytics")
    op.create_index("ix_analytics_events_session_id", "events", ["session_id"], schema="analytics")
    op.create_index("ix_analytics_events_actor_hash", "events", ["actor_hash"], schema="analytics")
    op.create_index("ix_analytics_events_source_app", "events", ["source_app"], schema="analytics")
    op.create_index("ix_analytics_events_idempotency_key", "events", ["idempotency_key"], schema="analytics")
    # Composite indexes for the three questions this table exists to answer.
    op.create_index(
        "ix_analytics_events_sku", "events", ["listing_id", "event_type", "occurred_at"], schema="analytics"
    )
    op.create_index(
        "ix_analytics_events_channel",
        "events",
        ["channel_account_id", "event_type", "occurred_at"],
        schema="analytics",
    )
    op.create_index(
        "ix_analytics_events_creative",
        "events",
        ["creative_id", "event_type", "occurred_at"],
        schema="analytics",
    )
    op.create_index(
        "ix_analytics_events_portal_time", "events", ["portal_key", "occurred_at"], schema="analytics"
    )

    op.create_table(
        "projection_cursors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("last_event_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("processed_count", sa.BigInteger(), server_default="0", nullable=False),
        schema="analytics",
    )
    op.create_index("ix_analytics_projection_cursors_name", "projection_cursors", ["name"], schema="analytics")


def downgrade() -> None:
    op.drop_table("projection_cursors", schema="analytics")
    op.drop_table("events", schema="analytics")
    op.drop_table("creatives", schema="analytics")

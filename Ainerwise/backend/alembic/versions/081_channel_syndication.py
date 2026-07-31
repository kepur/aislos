"""Channel syndication mapping tables (P1).

Purely additive — no existing table is altered. Syndication accounts reuse
channels.channel_accounts, tagged via meta_json.kind = "syndication".

Revision ID: 081
Revises: 080
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "081"
down_revision: Union[str, None] = "080"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column(
            "supplier_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier_listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.channel_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("external_url", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("stats_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delisted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("supplier_listing_id", "account_id", name="uq_channel_listing_account"),
        schema="channels",
    )
    op.create_index("ix_channels_channel_listings_workspace_id", "channel_listings", ["workspace_id"], schema="channels")
    op.create_index(
        "ix_channels_channel_listings_supplier_listing_id", "channel_listings", ["supplier_listing_id"], schema="channels"
    )
    op.create_index("ix_channels_channel_listings_account_id", "channel_listings", ["account_id"], schema="channels")
    op.create_index("ix_channels_channel_listings_status", "channel_listings", ["status"], schema="channels")
    op.create_index("ix_channels_channel_listings_external_id", "channel_listings", ["external_id"], schema="channels")
    op.create_index("ix_channels_channel_listings_content_hash", "channel_listings", ["content_hash"], schema="channels")

    op.create_table(
        "channel_category_maps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.channel_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_schema_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trade_category_schemas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_category_code", sa.String(120), nullable=False),
        sa.Column("external_category_path", sa.String(500), nullable=True),
        sa.Column("field_map_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("defaults_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("account_id", "category_schema_id", name="uq_channel_category_map"),
        schema="channels",
    )
    op.create_index(
        "ix_channels_channel_category_maps_account_id", "channel_category_maps", ["account_id"], schema="channels"
    )
    op.create_index(
        "ix_channels_channel_category_maps_category_id",
        "channel_category_maps",
        ["category_schema_id"],
        schema="channels",
    )


def downgrade() -> None:
    op.drop_table("channel_category_maps", schema="channels")
    op.drop_table("channel_listings", schema="channels")

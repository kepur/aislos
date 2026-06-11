"""marketplace feed, B2B/B2C mode, ad campaigns

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PgENUM

revision: str = "0006"
down_revision: str = "0005"
branch_labels = None
depends_on = None

market_mode_enum = PgENUM("B2B", "B2C", "BOTH", name="market_mode", create_type=False)
ad_status_enum = PgENUM(
    "DRAFT", "PENDING_REVIEW", "ACTIVE", "PAUSED", "REJECTED", "EXPIRED",
    name="ad_campaign_status", create_type=False
)
ad_placement_enum = PgENUM(
    "FEED_TOP", "FEED_INLINE", "CATEGORY_TOP", "SEARCH_TOP", "BANNER",
    name="ad_placement_type", create_type=False
)


def upgrade() -> None:
    conn = op.get_bind()

    # --- Enum types ---
    op.execute("DO $$ BEGIN CREATE TYPE market_mode AS ENUM ('B2B','B2C','BOTH'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE ad_campaign_status AS ENUM ('DRAFT','PENDING_REVIEW','ACTIVE','PAUSED','REJECTED','EXPIRED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE ad_placement_type AS ENUM ('FEED_TOP','FEED_INLINE','CATEGORY_TOP','SEARCH_TOP','BANNER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # --- Add market_mode to catalog_items ---
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS market_mode market_mode DEFAULT 'B2B'"
    ))
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS min_order_qty INTEGER DEFAULT 1"
    ))
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS weight_kg FLOAT"
    ))
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS origin_country VARCHAR(5)"
    ))
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0"
    ))
    conn.execute(sa.text(
        "ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS order_count INTEGER DEFAULT 0"
    ))

    # --- Ad campaigns table ---
    op.create_table(
        "ad_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("catalog_item_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("placement", ad_placement_enum, nullable=False),
        sa.Column("target_category_id", UUID(as_uuid=True), nullable=True),
        sa.Column("target_keywords", JSON(), nullable=True),
        sa.Column("target_countries", JSON(), nullable=True),
        sa.Column("budget_minor", sa.Integer(), nullable=False),
        sa.Column("spent_minor", sa.Integer(), server_default="0"),
        sa.Column("bid_per_click_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), server_default=sa.text("'USD'")),
        sa.Column("status", ad_status_enum, server_default="DRAFT"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("impressions", sa.Integer(), server_default="0"),
        sa.Column("clicks", sa.Integer(), server_default="0"),
        sa.Column("conversions", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Ranking rules table ---
    op.create_table(
        "ranking_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("weight_trust_score", sa.Float(), server_default="0.3"),
        sa.Column("weight_order_count", sa.Float(), server_default="0.25"),
        sa.Column("weight_price", sa.Float(), server_default="0.2"),
        sa.Column("weight_ad_bid", sa.Float(), server_default="0.15"),
        sa.Column("weight_recency", sa.Float(), server_default="0.1"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ranking_rules")
    op.drop_table("ad_campaigns")
    op.execute("DROP TYPE IF EXISTS ad_placement_type")
    op.execute("DROP TYPE IF EXISTS ad_campaign_status")
    op.execute("DROP TYPE IF EXISTS market_mode")

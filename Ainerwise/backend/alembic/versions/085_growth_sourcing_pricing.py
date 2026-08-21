"""Growth module P0: sourced listings + price rules.

Revision ID: 085
Revises: 084
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "085"
down_revision: Union[str, None] = "084"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "growth_price_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="global"),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("sell_currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("freight_pct", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("freight_fixed_minor", sa.BigInteger(), nullable=True),
        sa.Column("freight_currency", sa.String(length=3), nullable=True),
        sa.Column("duties_pct", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("target_margin_pct", sa.Numeric(6, 4), nullable=False, server_default="0.30"),
        sa.Column("platform_fee_pct", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("round_to_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("max_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("reprice_cadence", sa.String(length=20), nullable=False, server_default="manual"),
        sa.Column("reprice_threshold_pct", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_price_rules_workspace_id", "growth_price_rules", ["workspace_id"])
    op.create_index("ix_growth_price_rules_category_id", "growth_price_rules", ["category_id"])

    op.create_table(
        "growth_sourced_listings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("seller_ref", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_lang", sa.String(length=10), nullable=True),
        sa.Column("images_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attributes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("source_currency", sa.String(length=3), nullable=True),
        sa.Column("target_lang", sa.String(length=10), nullable=True),
        sa.Column("translated_title", sa.Text(), nullable=True),
        sa.Column("translated_description", sa.Text(), nullable=True),
        sa.Column("translated_images_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("price_rule_id", sa.UUID(), nullable=True),
        sa.Column("sell_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("sell_currency", sa.String(length=3), nullable=True),
        sa.Column("price_quote_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="imported"),
        sa.Column("failure_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["price_rule_id"], ["growth_price_rules.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_growth_sourced_listing_source_ext"),
    )
    op.create_index("ix_growth_sourced_listings_workspace_id", "growth_sourced_listings", ["workspace_id"])
    op.create_index("ix_growth_sourced_listings_source", "growth_sourced_listings", ["source"])
    op.create_index("ix_growth_sourced_listings_status", "growth_sourced_listings", ["status"])
    op.create_index("ix_growth_sourced_listings_product_id", "growth_sourced_listings", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_growth_sourced_listings_product_id", table_name="growth_sourced_listings")
    op.drop_index("ix_growth_sourced_listings_status", table_name="growth_sourced_listings")
    op.drop_index("ix_growth_sourced_listings_source", table_name="growth_sourced_listings")
    op.drop_index("ix_growth_sourced_listings_workspace_id", table_name="growth_sourced_listings")
    op.drop_table("growth_sourced_listings")
    op.drop_index("ix_growth_price_rules_category_id", table_name="growth_price_rules")
    op.drop_index("ix_growth_price_rules_workspace_id", table_name="growth_price_rules")
    op.drop_table("growth_price_rules")

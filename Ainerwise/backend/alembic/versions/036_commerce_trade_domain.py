"""Phase 2: Cebu trade domain slice — category schema, listings, requests, offers, orders.

Revision ID: 036
Revises: 035
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "036"
down_revision: Union[str, None] = "035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trade_category_schemas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schema_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_trade_category_schemas_slug", "trade_category_schemas", ["slug"], unique=True)

    op.create_table(
        "supplier_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("category_schema_id", UUID(as_uuid=True), sa.ForeignKey("trade_category_schemas.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("attributes_json", JSONB, nullable=True),
        sa.Column("price_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("legacy_catalog_item_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_supplier_listings_company_id", "supplier_listings", ["company_id"])

    op.create_table(
        "procurement_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("buyer_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("portal_key", sa.String(64), nullable=False, server_default="cebu"),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("category_schema_id", UUID(as_uuid=True), sa.ForeignKey("trade_category_schemas.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements_json", JSONB, nullable=True),
        sa.Column("attrs_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("legacy_request_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_procurement_requests_status", "procurement_requests", ["status"])
    op.create_index("ix_procurement_requests_legacy", "procurement_requests", ["legacy_request_id"], unique=True)

    op.create_table(
        "supplier_offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("procurement_request_id", UUID(as_uuid=True), sa.ForeignKey("procurement_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_listing_id", UUID(as_uuid=True), sa.ForeignKey("supplier_listings.id"), nullable=True),
        sa.Column("supplier_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("terms_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="submitted"),
        sa.Column("legacy_offer_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("procurement_request_id", "supplier_company_id", name="uq_offer_per_supplier"),
    )

    op.create_table(
        "commerce_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("procurement_request_id", UUID(as_uuid=True), sa.ForeignKey("procurement_requests.id"), nullable=False),
        sa.Column("winning_offer_id", UUID(as_uuid=True), sa.ForeignKey("supplier_offers.id"), nullable=True),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("supplier_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("delivery_json", JSONB, nullable=True),
        sa.Column("legacy_order_id", sa.String(120), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_orders_legacy", "commerce_orders", ["legacy_order_id"], unique=True)


def downgrade() -> None:
    op.drop_table("commerce_orders")
    op.drop_table("supplier_offers")
    op.drop_table("procurement_requests")
    op.drop_table("supplier_listings")
    op.drop_table("trade_category_schemas")

"""2Hands C2C deals — records-first receipt trail and per-SKU sales signal.

Revision ID: 080
Revises: 079
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "080"
down_revision: Union[str, None] = "079"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "secondhand_deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column(
            "secondhand_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("secondhand_listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier_listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seller_company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column(
            "buyer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agreed_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(3), server_default="EUR", nullable=False),
        sa.Column("fulfillment_mode", sa.String(32), server_default="SELLER_PICKUP", nullable=False),
        sa.Column("status", sa.String(24), server_default="reserved", nullable=False),
        sa.Column("payment_method", sa.String(24), nullable=True),
        sa.Column("payment_reference", sa.String(255), nullable=True),
        sa.Column("picked_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_secondhand_deals_workspace_id", "secondhand_deals", ["workspace_id"])
    op.create_index("ix_secondhand_deals_listing_id", "secondhand_deals", ["secondhand_listing_id"])
    op.create_index("ix_secondhand_deals_supplier_listing_id", "secondhand_deals", ["supplier_listing_id"])
    op.create_index("ix_secondhand_deals_seller_company_id", "secondhand_deals", ["seller_company_id"])
    op.create_index("ix_secondhand_deals_buyer_user_id", "secondhand_deals", ["buyer_user_id"])
    op.create_index("ix_secondhand_deals_status", "secondhand_deals", ["status"])


def downgrade() -> None:
    op.drop_table("secondhand_deals")

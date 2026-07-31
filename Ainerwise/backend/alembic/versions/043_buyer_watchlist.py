"""buyer watchlist

Revision ID: 043
Revises: 042
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "043"
down_revision: Union[str, None] = "042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buyer_watchlist_items",
        sa.Column("buyer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_price_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_listing_id"], ["supplier_listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("buyer_user_id", "supplier_listing_id", name="uq_buyer_watchlist_listing"),
    )
    op.create_index("ix_buyer_watchlist_items_buyer_user_id", "buyer_watchlist_items", ["buyer_user_id"])
    op.create_index("ix_buyer_watchlist_items_supplier_listing_id", "buyer_watchlist_items", ["supplier_listing_id"])
    op.create_index("ix_buyer_watchlist_items_status", "buyer_watchlist_items", ["status"])


def downgrade() -> None:
    op.drop_index("ix_buyer_watchlist_items_status", table_name="buyer_watchlist_items")
    op.drop_index("ix_buyer_watchlist_items_supplier_listing_id", table_name="buyer_watchlist_items")
    op.drop_index("ix_buyer_watchlist_items_buyer_user_id", table_name="buyer_watchlist_items")
    op.drop_table("buyer_watchlist_items")

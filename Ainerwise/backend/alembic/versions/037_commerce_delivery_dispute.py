"""Phase 2: order deliveries and disputes.

Revision ID: 037
Revises: 036
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_deliveries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrier", sa.String(120), nullable=True),
        sa.Column("tracking_number", sa.String(120), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("ship_from_json", JSONB, nullable=True),
        sa.Column("ship_to_json", JSONB, nullable=True),
        sa.Column("estimated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof_json", JSONB, nullable=True),
        sa.Column("legacy_delivery_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_order_deliveries_order_id", "order_deliveries", ["commerce_order_id"])
    op.create_index("ix_order_deliveries_status", "order_deliveries", ["status"])

    op.create_table(
        "order_disputes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opened_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("opened_by_role", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("resolution_json", JSONB, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("legacy_dispute_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_order_disputes_order_id", "order_disputes", ["commerce_order_id"])
    op.create_index("ix_order_disputes_status", "order_disputes", ["status"])
    op.create_index("ix_order_disputes_legacy", "order_disputes", ["legacy_dispute_id"], unique=True)


def downgrade() -> None:
    op.drop_table("order_disputes")
    op.drop_table("order_deliveries")

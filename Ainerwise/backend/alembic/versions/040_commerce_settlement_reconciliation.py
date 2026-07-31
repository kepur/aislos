"""Phase 2: commerce settlements and reconciliation runs.

Revision ID: 040
Revises: 039
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "040"
down_revision: Union[str, None] = "039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commerce_settlements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_intent_id", UUID(as_uuid=True), sa.ForeignKey("commerce_payment_intents.id"), nullable=True),
        sa.Column("payment_plan_id", UUID(as_uuid=True), sa.ForeignKey("payment_plans.id"), nullable=True),
        sa.Column("milestone_id", UUID(as_uuid=True), sa.ForeignKey("payment_milestones.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("platform_fee_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("psp_provider", sa.String(32), nullable=False, server_default="stripe"),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("psp_settlement_ref", sa.String(255), nullable=True),
        sa.Column("funded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_settlements_status", "commerce_settlements", ["status"])
    op.create_index("ix_commerce_settlements_order", "commerce_settlements", ["commerce_order_id"])

    op.create_table(
        "commerce_reconciliation_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("matched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mismatch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_json", JSONB, nullable=True),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_recon_runs_status", "commerce_reconciliation_runs", ["status"])


def downgrade() -> None:
    op.drop_table("commerce_reconciliation_runs")
    op.drop_table("commerce_settlements")

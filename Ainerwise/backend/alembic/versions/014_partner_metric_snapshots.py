"""Partner metric snapshots: append-only score history for the future
Risk Engine — time series cannot be backfilled, so capture starts now.

Revision ID: 014
Revises: 013
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_metric_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=False),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("breakdown_json", JSONB, nullable=True),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_partner_metric_snapshots_partner_id", "partner_metric_snapshots", ["partner_id"])
    op.create_index(
        "ix_partner_metric_snapshots_partner_date",
        "partner_metric_snapshots",
        ["partner_id", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_table("partner_metric_snapshots")

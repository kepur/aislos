"""Supplier scorecard (FI.6.6)

Revision ID: 007
Revises: 006
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supplier_scorecards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("supplier_name", sa.Text, nullable=True),
        sa.Column("quality", sa.Integer, nullable=True),
        sa.Column("delivery", sa.Integer, nullable=True),
        sa.Column("response", sa.Integer, nullable=True),
        sa.Column("warranty_cooperation", sa.Integer, nullable=True),
        sa.Column("documentation", sa.Integer, nullable=True),
        sa.Column("price_stability", sa.Integer, nullable=True),
        sa.Column("long_term_fit", sa.Integer, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("supplier_scorecards")

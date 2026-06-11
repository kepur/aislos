"""Living Case Dataset: operational fields on cases (moat asset #8)

Revision ID: 013
Revises: 012
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("rework_count", sa.Integer, nullable=True))
    op.add_column("cases", sa.Column("satisfaction_score", sa.Numeric(2, 1), nullable=True))
    op.add_column("cases", sa.Column("ai_summary", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "ai_summary")
    op.drop_column("cases", "satisfaction_score")
    op.drop_column("cases", "rework_count")

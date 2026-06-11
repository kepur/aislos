"""Add include-in-estimate flag to project line items.

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: str = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE project_line_items "
        "ADD COLUMN IF NOT EXISTS include_in_estimate BOOLEAN NOT NULL DEFAULT true"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE project_line_items "
        "DROP COLUMN IF EXISTS include_in_estimate"
    ))

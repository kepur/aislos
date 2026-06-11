"""Field completion record on tasks (photos, device serials, test results) —
the operational dataset behind the acceptance loop.

Revision ID: 017
Revises: 016
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("maintenance_schedules", sa.Column("completion_json", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("maintenance_schedules", "completion_json")

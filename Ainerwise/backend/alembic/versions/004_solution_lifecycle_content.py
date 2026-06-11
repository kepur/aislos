"""Add solution lifecycle landing content field

Revision ID: 004
Revises: 003
Create Date: 2026-06-01

Adds a reusable JSONB column to solutions so lifecycle solution lines
(StorageGuard first, then KitchenGuard / AquaGuard) can carry rich public
landing sections: monitoring points, alert channels, reports, calibration,
consumables, recurring charges, and AMC options.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("solutions", sa.Column("lifecycle_content_json", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("solutions", "lifecycle_content_json")

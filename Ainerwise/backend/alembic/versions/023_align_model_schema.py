"""Align public model column types with the current SQLAlchemy models.

Revision ID: 023
Revises: 022
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("inquiries", "referrer", existing_type=sa.String(1000), type_=sa.Text())
    op.alter_column("leads", "referrer", existing_type=sa.String(1000), type_=sa.Text())


def downgrade() -> None:
    op.alter_column("leads", "referrer", existing_type=sa.Text(), type_=sa.String(1000))
    op.alter_column("inquiries", "referrer", existing_type=sa.Text(), type_=sa.String(1000))

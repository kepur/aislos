"""Add Viber notification preferences.

Revision ID: 084
Revises: 083
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "084"
down_revision: Union[str, None] = "083"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notification_preferences",
        sa.Column("viber_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("notification_preferences", sa.Column("viber_number", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("notification_preferences", "viber_number")
    op.drop_column("notification_preferences", "viber_enabled")

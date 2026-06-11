"""Add user notification preferences JSON field

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{}'::jsonb"
    ))
    conn.execute(sa.text(
        "UPDATE users SET notification_preferences = '{}'::jsonb WHERE notification_preferences IS NULL"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS notification_preferences"))
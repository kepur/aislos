"""Add account_type to users table

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE account_type AS ENUM ('INDIVIDUAL', 'BUSINESS'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type account_type "
        "DEFAULT 'INDIVIDUAL' NOT NULL"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS account_type"))
    conn.execute(sa.text("DROP TYPE IF EXISTS account_type"))

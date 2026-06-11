"""C02: extend audit_logs for procurement atomic audit events.

Revision ID: 028
Revises: 027
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("actor_type", sa.String(20), nullable=False, server_default="user"),
    )
    op.add_column("audit_logs", sa.Column("agent_slug", sa.String(100), nullable=True))
    op.add_column("audit_logs", sa.Column("portal_key", sa.String(50), nullable=True))
    op.add_column("audit_logs", sa.Column("reason", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("source", sa.String(100), nullable=True))
    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(64), nullable=True))
    op.add_column("audit_logs", sa.Column("user_agent", sa.String(500), nullable=True))
    op.create_index("ix_audit_logs_portal_key", "audit_logs", ["portal_key"])
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    op.alter_column("audit_logs", "actor_type", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_portal_key", table_name="audit_logs")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "correlation_id")
    op.drop_column("audit_logs", "source")
    op.drop_column("audit_logs", "reason")
    op.drop_column("audit_logs", "portal_key")
    op.drop_column("audit_logs", "agent_slug")
    op.drop_column("audit_logs", "actor_type")

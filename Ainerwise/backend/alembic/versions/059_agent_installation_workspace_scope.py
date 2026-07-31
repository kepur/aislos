"""Scope Agent Marketplace installations to a Workspace.

Revision ID: 059
Revises: 058
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "059"
down_revision: Union[str, None] = "058"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_installations",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_agent_installations_workspace_id",
        "agent_installations",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_agent_installations_workspace_id",
        "agent_installations",
        ["workspace_id"],
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE agent_installations AS installation
            SET workspace_id = (
                SELECT membership.workspace_id
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.user_id = installation.installed_by
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                ORDER BY membership.created_at ASC
                LIMIT 1
            )
            WHERE installation.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE agent_installations
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )
    missing = conn.execute(
        sa.text("SELECT count(*) FROM agent_installations WHERE workspace_id IS NULL")
    ).scalar_one()
    if missing:
        raise RuntimeError("Cannot scope existing Agent installations without an active Workspace")

    op.alter_column("agent_installations", "workspace_id", nullable=False)
    op.drop_constraint(
        "uq_agent_installations_listing_user",
        "agent_installations",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_agent_installations_listing_workspace_user",
        "agent_installations",
        ["listing_id", "workspace_id", "installed_by"],
    )


def downgrade() -> None:
    conn = op.get_bind()
    duplicate = conn.execute(
        sa.text(
            """
            SELECT listing_id, installed_by
            FROM agent_installations
            GROUP BY listing_id, installed_by
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate:
        raise RuntimeError(
            "Cannot downgrade migration 059: the same Agent listing is installed "
            "by one user in multiple Workspaces."
        )

    op.drop_constraint(
        "uq_agent_installations_listing_workspace_user",
        "agent_installations",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_agent_installations_listing_user",
        "agent_installations",
        ["listing_id", "installed_by"],
    )
    op.drop_index("ix_agent_installations_workspace_id", table_name="agent_installations")
    op.drop_constraint(
        "fk_agent_installations_workspace_id",
        "agent_installations",
        type_="foreignkey",
    )
    op.drop_column("agent_installations", "workspace_id")

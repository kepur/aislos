"""Backfill Project object grants to the Project Workspace.

Revision ID: 062
Revises: 061
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "062"
down_revision: Union[str, None] = "061"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    collision = conn.execute(
        sa.text(
            """
            SELECT global_grant.id
            FROM agent_object_grants AS global_grant
            JOIN projects AS project ON project.id = global_grant.object_id
            JOIN agent_object_grants AS scoped_grant
              ON scoped_grant.agent_id = global_grant.agent_id
             AND scoped_grant.object_type = global_grant.object_type
             AND scoped_grant.object_id = global_grant.object_id
             AND scoped_grant.scope = global_grant.scope
             AND scoped_grant.workspace_id = project.workspace_id
            WHERE global_grant.object_type = 'project'
              AND global_grant.workspace_id IS NULL
              AND project.workspace_id IS NOT NULL
            LIMIT 1
            """
        )
    ).first()
    if collision:
        raise RuntimeError(
            "Cannot scope Project Agent grants: both global and Workspace-scoped grants exist."
        )
    conn.execute(
        sa.text(
            """
            UPDATE agent_object_grants AS object_grant
            SET workspace_id = project.workspace_id
            FROM projects AS project
            WHERE object_grant.object_type = 'project'
              AND object_grant.object_id = project.id
              AND object_grant.workspace_id IS NULL
              AND project.workspace_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    collision = conn.execute(
        sa.text(
            """
            SELECT scoped_grant.id
            FROM agent_object_grants AS scoped_grant
            JOIN projects AS project ON project.id = scoped_grant.object_id
            JOIN agent_object_grants AS global_grant
              ON global_grant.agent_id = scoped_grant.agent_id
             AND global_grant.object_type = scoped_grant.object_type
             AND global_grant.object_id = scoped_grant.object_id
             AND global_grant.scope = scoped_grant.scope
             AND global_grant.workspace_id IS NULL
            WHERE scoped_grant.object_type = 'project'
              AND scoped_grant.workspace_id = project.workspace_id
            LIMIT 1
            """
        )
    ).first()
    if collision:
        raise RuntimeError(
            "Cannot downgrade migration 062: global Project Agent grant collisions exist."
        )
    conn.execute(
        sa.text(
            """
            UPDATE agent_object_grants AS object_grant
            SET workspace_id = NULL
            FROM projects AS project
            WHERE object_grant.object_type = 'project'
              AND object_grant.object_id = project.id
              AND object_grant.workspace_id = project.workspace_id
            """
        )
    )

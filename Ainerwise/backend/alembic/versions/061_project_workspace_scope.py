"""Bind delivery Projects to a Workspace.

Revision ID: 061
Revises: 060
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "061"
down_revision: Union[str, None] = "060"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_workspace_id",
        "projects",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])

    conn = op.get_bind()
    ambiguous = conn.execute(
        sa.text(
            """
            SELECT project_id
            FROM work_packages
            WHERE project_id IS NOT NULL
            GROUP BY project_id
            HAVING count(DISTINCT workspace_id) > 1
            LIMIT 1
            """
        )
    ).first()
    if ambiguous:
        raise RuntimeError(
            "Cannot bind Projects to Workspaces: a Project has WorkPackages in multiple Workspaces."
        )

    conn.execute(
        sa.text(
            """
            UPDATE projects AS project
            SET workspace_id = (
                SELECT min(package.workspace_id::text)::uuid
                FROM work_packages AS package
                WHERE package.project_id = project.id
            )
            WHERE project.workspace_id IS NULL
              AND EXISTS (
                SELECT 1 FROM work_packages AS package WHERE package.project_id = project.id
              )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE projects AS project
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.company_id = project.buyer_company_id
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE project.workspace_id IS NULL
              AND project.buyer_company_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE projects
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_projects_workspace_id", table_name="projects")
    op.drop_constraint("fk_projects_workspace_id", "projects", type_="foreignkey")
    op.drop_column("projects", "workspace_id")

"""Bind Procurement child resources and generated RFQs to a Workspace.

Revision ID: 073
Revises: 072
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "073"
down_revision: Union[str, None] = "072"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "procurement_project_facts",
    "boq_versions",
    "procurement_packages",
    "commercial_snapshots",
)


def _add(table: str) -> None:
    op.add_column(
        table,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        f"fk_{table}_workspace_id",
        table,
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


def _assert_none(conn, query: str, message: str) -> None:
    if conn.execute(sa.text(query)).first():
        raise RuntimeError(message)


def _backfill_unscoped_projects(conn) -> None:
    # Records created after migration 065 by older workers/tests still need the
    # same deterministic root inference before children can inherit scope.
    conn.execute(
        sa.text(
            """
            UPDATE procurement_projects AS project
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.user_id = project.owner_user_id
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE project.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE procurement_projects
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )


def upgrade() -> None:
    for table in TABLES:
        _add(table)
    conn = op.get_bind()
    _backfill_unscoped_projects(conn)

    _assert_none(
        conn,
        "SELECT f.id FROM procurement_project_facts f JOIN procurement_projects p ON p.id = f.project_id WHERE p.workspace_id IS NULL LIMIT 1",
        "Cannot bind procurement_project_facts: parent project has no Workspace.",
    )
    conn.execute(sa.text("UPDATE procurement_project_facts AS f SET workspace_id = p.workspace_id FROM procurement_projects p WHERE p.id = f.project_id"))

    _assert_none(
        conn,
        "SELECT b.id FROM boq_versions b JOIN procurement_projects p ON p.id = b.project_id WHERE p.workspace_id IS NULL LIMIT 1",
        "Cannot bind boq_versions: parent project has no Workspace.",
    )
    conn.execute(sa.text("UPDATE boq_versions AS b SET workspace_id = p.workspace_id FROM procurement_projects p WHERE p.id = b.project_id"))

    _assert_none(
        conn,
        "SELECT pkg.id FROM procurement_packages pkg JOIN boq_versions b ON b.id = pkg.boq_version_id WHERE b.project_id <> pkg.project_id LIMIT 1",
        "Cannot bind procurement_packages: BOQ and package reference different projects.",
    )
    _assert_none(
        conn,
        "SELECT pkg.id FROM procurement_packages pkg JOIN procurement_projects p ON p.id = pkg.project_id WHERE p.workspace_id IS NULL LIMIT 1",
        "Cannot bind procurement_packages: parent project has no Workspace.",
    )
    conn.execute(sa.text("UPDATE procurement_packages AS pkg SET workspace_id = p.workspace_id FROM procurement_projects p WHERE p.id = pkg.project_id"))

    _assert_none(
        conn,
        """
        SELECT s.id
        FROM commercial_snapshots s
        JOIN procurement_packages pkg ON pkg.id = s.package_id
        JOIN boq_versions b ON b.id = s.boq_version_id
        WHERE pkg.project_id <> s.procurement_project_id
           OR b.project_id <> s.procurement_project_id
           OR pkg.boq_version_id <> s.boq_version_id
        LIMIT 1
        """,
        "Cannot bind commercial_snapshots: linked project, BOQ, and package disagree.",
    )
    _assert_none(
        conn,
        "SELECT s.id FROM commercial_snapshots s JOIN procurement_projects p ON p.id = s.procurement_project_id WHERE p.workspace_id IS NULL LIMIT 1",
        "Cannot bind commercial_snapshots: parent project has no Workspace.",
    )
    conn.execute(sa.text("UPDATE commercial_snapshots AS s SET workspace_id = p.workspace_id FROM procurement_projects p WHERE p.id = s.procurement_project_id"))

    conn.execute(
        sa.text(
            """
            UPDATE rfqs AS r
            SET workspace_id = p.workspace_id
            FROM procurement_packages pkg
            JOIN procurement_projects p ON p.id = pkg.project_id
            WHERE r.procurement_package_id = pkg.id
              AND p.workspace_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

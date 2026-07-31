"""Bind Living Cases and Design Revisions to a Workspace.

Revision ID: 071
Revises: 070
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "071"
down_revision: Union[str, None] = "070"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add(table: str) -> None:
    op.add_column(table, sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(f"fk_{table}_workspace_id", table, "workspaces", ["workspace_id"], ["id"])
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


def upgrade() -> None:
    _add("cases")
    _add("design_revisions")
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE cases AS c SET workspace_id = p.workspace_id FROM projects p WHERE p.id = c.project_id AND p.workspace_id IS NOT NULL"))
    mismatch = conn.execute(sa.text("SELECT d.id FROM design_revisions d JOIN sites s ON s.id = d.site_id JOIN projects p ON p.id = d.project_id WHERE s.workspace_id IS NOT NULL AND p.workspace_id IS NOT NULL AND s.workspace_id <> p.workspace_id LIMIT 1")).first()
    if mismatch:
        raise RuntimeError("Cannot bind design_revisions: Site and Project use different Workspaces.")
    conn.execute(sa.text("UPDATE design_revisions AS d SET workspace_id = p.workspace_id FROM projects p WHERE p.id = d.project_id AND p.workspace_id IS NOT NULL"))
    conn.execute(sa.text("UPDATE design_revisions AS d SET workspace_id = s.workspace_id FROM sites s WHERE s.id = d.site_id AND d.workspace_id IS NULL AND s.workspace_id IS NOT NULL"))
    for table in ("cases", "design_revisions"):
        conn.execute(sa.text(f"UPDATE {table} SET workspace_id = (SELECT id FROM workspaces WHERE slug = 'default' AND status = 'active' LIMIT 1) WHERE workspace_id IS NULL"))


def downgrade() -> None:
    for table in ("design_revisions", "cases"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")


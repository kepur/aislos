"""Bind Quotes and RFQs to a Workspace.

Revision ID: 064
Revises: 063
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "064"
down_revision: Union[str, None] = "063"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _bind_table(table: str) -> None:
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


def _backfill_linked_table(conn, table: str) -> None:
    mismatch = conn.execute(
        sa.text(
            f"""
            SELECT resource_row.id
            FROM {table} AS resource_row
            JOIN projects AS project ON project.id = resource_row.project_id
            JOIN leads AS lead ON lead.id = resource_row.lead_id
            WHERE project.workspace_id IS NOT NULL
              AND lead.workspace_id IS NOT NULL
              AND project.workspace_id != lead.workspace_id
            LIMIT 1
            """
        )
    ).first()
    if mismatch:
        raise RuntimeError(f"Cannot bind {table}: linked Project and Lead use different Workspaces.")
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = project.workspace_id
            FROM projects AS project
            WHERE resource_row.project_id = project.id
              AND resource_row.workspace_id IS NULL
              AND project.workspace_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = lead.workspace_id
            FROM leads AS lead
            WHERE resource_row.lead_id = lead.id
              AND resource_row.workspace_id IS NULL
              AND lead.workspace_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE {table}
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
    _bind_table("quotes")
    _bind_table("rfqs")
    conn = op.get_bind()
    _backfill_linked_table(conn, "quotes")
    _backfill_linked_table(conn, "rfqs")


def downgrade() -> None:
    for table in ("rfqs", "quotes"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

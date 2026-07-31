"""Bind Payment Milestones and Ledger Entries to a Workspace.

Revision ID: 076
Revises: 075
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "076"
down_revision: Union[str, None] = "075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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


def _backfill_plans(conn) -> None:
    for parent, fk in (("projects", "project_id"), ("quotes", "quote_id")):
        _assert_none(
            conn,
            f"""
            SELECT plan.id
            FROM payment_plans AS plan
            JOIN {parent} AS parent ON parent.id = plan.{fk}
            WHERE plan.workspace_id IS NOT NULL
              AND parent.workspace_id IS NOT NULL
              AND plan.workspace_id <> parent.workspace_id
            LIMIT 1
            """,
            f"Cannot bind payment children: Payment Plan and {parent} use different Workspaces.",
        )
        conn.execute(
            sa.text(
                f"""
                UPDATE payment_plans AS plan
                SET workspace_id = parent.workspace_id
                FROM {parent} AS parent
                WHERE parent.id = plan.{fk}
                  AND plan.workspace_id IS NULL
                  AND parent.workspace_id IS NOT NULL
                """
            )
        )
    conn.execute(
        sa.text(
            """
            UPDATE payment_plans
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
    _add("payment_milestones")
    _add("ledger_entries")
    conn = op.get_bind()
    _backfill_plans(conn)

    _assert_none(
        conn,
        "SELECT milestone.id FROM payment_milestones milestone JOIN payment_plans plan ON plan.id = milestone.plan_id WHERE plan.workspace_id IS NULL LIMIT 1",
        "Cannot bind payment_milestones: Payment Plan has no Workspace.",
    )
    conn.execute(
        sa.text(
            """
            UPDATE payment_milestones AS milestone
            SET workspace_id = plan.workspace_id
            FROM payment_plans AS plan
            WHERE plan.id = milestone.plan_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE ledger_entries AS entry
            SET workspace_id = milestone.workspace_id
            FROM payment_milestones AS milestone
            WHERE milestone.id = entry.milestone_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE ledger_entries
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
    for table in ("ledger_entries", "payment_milestones"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

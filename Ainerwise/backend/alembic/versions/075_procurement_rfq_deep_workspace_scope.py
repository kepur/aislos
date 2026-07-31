"""Bind Procurement and RFQ deep child resources to a Workspace.

Revision ID: 075
Revises: 074
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "075"
down_revision: Union[str, None] = "074"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "boq_items",
    "boq_item_options",
    "solution_plans",
    "procurement_package_items",
    "rfq_invitations",
    "partner_bids",
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


def _bind(conn, *, table: str, parent: str, fk: str) -> None:
    _assert_none(
        conn,
        f"SELECT child.id FROM {table} AS child JOIN {parent} AS parent ON parent.id = child.{fk} WHERE parent.workspace_id IS NULL LIMIT 1",
        f"Cannot bind {table}: parent resource has no Workspace.",
    )
    conn.execute(
        sa.text(
            f"UPDATE {table} AS child SET workspace_id = parent.workspace_id FROM {parent} AS parent WHERE parent.id = child.{fk}"
        )
    )


def _backfill_rfqs(conn) -> None:
    for parent, fk in (
        ("procurement_packages", "procurement_package_id"),
        ("projects", "project_id"),
        ("leads", "lead_id"),
    ):
        _assert_none(
            conn,
            f"""
            SELECT rfq.id
            FROM rfqs AS rfq
            JOIN {parent} AS parent ON parent.id = rfq.{fk}
            WHERE rfq.workspace_id IS NOT NULL
              AND parent.workspace_id IS NOT NULL
              AND rfq.workspace_id <> parent.workspace_id
            LIMIT 1
            """,
            f"Cannot bind RFQ children: RFQ and {parent} use different Workspaces.",
        )
        conn.execute(
            sa.text(
                f"""
                UPDATE rfqs AS rfq
                SET workspace_id = parent.workspace_id
                FROM {parent} AS parent
                WHERE parent.id = rfq.{fk}
                  AND rfq.workspace_id IS NULL
                  AND parent.workspace_id IS NOT NULL
                """
            )
        )
    conn.execute(
        sa.text(
            """
            UPDATE rfqs
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

    _bind(conn, table="boq_items", parent="boq_versions", fk="boq_version_id")
    _bind(conn, table="boq_item_options", parent="boq_items", fk="boq_item_id")
    _bind(conn, table="solution_plans", parent="boq_versions", fk="boq_version_id")
    _bind(
        conn,
        table="procurement_package_items",
        parent="procurement_packages",
        fk="package_id",
    )
    _assert_none(
        conn,
        """
        SELECT item.id
        FROM procurement_package_items AS item
        JOIN boq_items AS boq_item ON boq_item.id = item.boq_item_id
        WHERE item.workspace_id <> boq_item.workspace_id
        LIMIT 1
        """,
        "Cannot bind procurement_package_items: Package and BOQ Item use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT item.id
        FROM procurement_package_items AS item
        JOIN boq_item_options AS option ON option.id = item.boq_item_option_id
        WHERE item.workspace_id <> option.workspace_id
        LIMIT 1
        """,
        "Cannot bind procurement_package_items: Package and BOQ Option use different Workspaces.",
    )

    _backfill_rfqs(conn)
    _bind(conn, table="rfq_invitations", parent="rfqs", fk="rfq_id")
    _bind(conn, table="partner_bids", parent="rfqs", fk="rfq_id")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

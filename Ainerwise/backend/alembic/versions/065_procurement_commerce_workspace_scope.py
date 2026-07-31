"""Bind Procurement and Commerce roots to a Workspace.

Revision ID: 065
Revises: 064
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "065"
down_revision: Union[str, None] = "064"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_workspace_column(table: str) -> None:
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


def _backfill_from_unique_user_membership(conn, table: str, user_column: str) -> None:
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.user_id = resource_row.{user_column}
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE resource_row.workspace_id IS NULL
              AND resource_row.{user_column} IS NOT NULL
            """
        )
    )


def _backfill_from_unique_company_membership(conn, table: str, company_column: str) -> None:
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.company_id = resource_row.{company_column}
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE resource_row.workspace_id IS NULL
              AND resource_row.{company_column} IS NOT NULL
            """
        )
    )


def _backfill_default(conn, table: str) -> None:
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
    for table in ("procurement_projects", "procurement_requests", "commerce_orders"):
        _add_workspace_column(table)

    conn = op.get_bind()
    _backfill_from_unique_user_membership(
        conn, "procurement_projects", "owner_user_id"
    )
    _backfill_from_unique_company_membership(
        conn, "procurement_projects", "company_id"
    )
    _backfill_default(conn, "procurement_projects")

    conn.execute(
        sa.text(
            """
            UPDATE procurement_requests AS request
            SET workspace_id = lead.workspace_id
            FROM leads AS lead
            WHERE request.lead_id = lead.id
              AND request.workspace_id IS NULL
              AND lead.workspace_id IS NOT NULL
            """
        )
    )
    _backfill_from_unique_user_membership(
        conn, "procurement_requests", "buyer_user_id"
    )
    _backfill_from_unique_company_membership(
        conn, "procurement_requests", "buyer_company_id"
    )
    _backfill_default(conn, "procurement_requests")

    conn.execute(
        sa.text(
            """
            UPDATE commerce_orders AS commerce_order
            SET workspace_id = request.workspace_id
            FROM procurement_requests AS request
            WHERE commerce_order.procurement_request_id = request.id
              AND commerce_order.workspace_id IS NULL
              AND request.workspace_id IS NOT NULL
            """
        )
    )
    _backfill_default(conn, "commerce_orders")


def downgrade() -> None:
    for table in ("commerce_orders", "procurement_requests", "procurement_projects"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

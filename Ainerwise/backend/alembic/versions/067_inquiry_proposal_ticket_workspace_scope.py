"""Bind Inquiry, Proposal Plan, and Ticket roots to a Workspace.

Revision ID: 067
Revises: 066
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "067"
down_revision: Union[str, None] = "066"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("inquiries", "proposal_plans", "tickets")


def _add_workspace(table: str) -> None:
    op.add_column(table, sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        f"fk_{table}_workspace_id", table, "workspaces", ["workspace_id"], ["id"]
    )
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


def _backfill_link(conn, table: str, source_table: str, foreign_key: str) -> None:
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = source.workspace_id
            FROM {source_table} AS source
            WHERE source.id = resource_row.{foreign_key}
              AND resource_row.workspace_id IS NULL
              AND source.workspace_id IS NOT NULL
            """
        )
    )


def _backfill_membership(conn, table: str, resource_column: str, membership_column: str) -> None:
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS resource_row
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.{membership_column} = resource_row.{resource_column}
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE resource_row.workspace_id IS NULL
              AND resource_row.{resource_column} IS NOT NULL
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


def _assert_links_agree(conn, table: str, sources: list[tuple[str, str]]) -> None:
    unions = " UNION ALL ".join(
        f"""
        SELECT resource_row.id AS resource_id, source.workspace_id
        FROM {table} AS resource_row
        JOIN {source_table} AS source ON source.id = resource_row.{foreign_key}
        WHERE source.workspace_id IS NOT NULL
        """
        for source_table, foreign_key in sources
    )
    mismatch = conn.execute(
        sa.text(
            f"""
            SELECT resource_id
            FROM ({unions}) AS linked_scopes
            GROUP BY resource_id
            HAVING count(DISTINCT workspace_id) > 1
            LIMIT 1
            """
        )
    ).first()
    if mismatch:
        raise RuntimeError(f"Cannot bind {table}: linked resources use different Workspaces.")


def upgrade() -> None:
    for table in TABLES:
        _add_workspace(table)
    conn = op.get_bind()

    _backfill_link(conn, "inquiries", "leads", "lead_id")
    _backfill_membership(conn, "inquiries", "buyer_user_id", "user_id")
    _backfill_membership(conn, "inquiries", "buyer_company_id", "company_id")
    _backfill_default(conn, "inquiries")

    proposal_sources = [("projects", "project_id"), ("leads", "lead_id")]
    _assert_links_agree(conn, "proposal_plans", proposal_sources)
    for source_table, foreign_key in proposal_sources:
        _backfill_link(conn, "proposal_plans", source_table, foreign_key)
    _backfill_default(conn, "proposal_plans")

    ticket_sources = [
        ("projects", "project_id"),
        ("assets", "asset_id"),
        ("monitoring_points", "monitoring_point_id"),
    ]
    _assert_links_agree(conn, "tickets", ticket_sources)
    for source_table, foreign_key in ticket_sources:
        _backfill_link(conn, "tickets", source_table, foreign_key)
    _backfill_membership(conn, "tickets", "buyer_user_id", "user_id")
    _backfill_membership(conn, "tickets", "buyer_company_id", "company_id")
    _backfill_default(conn, "tickets")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

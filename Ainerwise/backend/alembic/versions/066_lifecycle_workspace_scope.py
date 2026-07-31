"""Bind lifecycle and installed-asset resources to a Workspace.

Revision ID: 066
Revises: 065
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "066"
down_revision: Union[str, None] = "065"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "sites",
    "assets",
    "customer_warranties",
    "amc_contracts",
    "monitoring_points",
    "inventory_items",
    "stock_movements",
    "maintenance_schedules",
    "calibration_records",
)


def _add_workspace(table: str) -> None:
    op.add_column(table, sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        f"fk_{table}_workspace_id", table, "workspaces", ["workspace_id"], ["id"]
    )
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


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


def _backfill_company(conn, table: str, company_column: str) -> None:
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
    for table in TABLES:
        _add_workspace(table)

    conn = op.get_bind()
    ambiguous_site = conn.execute(
        sa.text(
            """
            SELECT asset.site_id
            FROM assets AS asset
            JOIN projects AS project ON project.id = asset.project_id
            WHERE project.workspace_id IS NOT NULL
            GROUP BY asset.site_id
            HAVING count(DISTINCT project.workspace_id) > 1
            LIMIT 1
            """
        )
    ).first()
    if ambiguous_site:
        raise RuntimeError("Cannot bind sites: one Site contains Assets from multiple Workspaces.")
    conn.execute(
        sa.text(
            """
            UPDATE sites AS site
            SET workspace_id = (
                SELECT min(project.workspace_id::text)::uuid
                FROM assets AS asset
                JOIN projects AS project ON project.id = asset.project_id
                WHERE asset.site_id = site.id
                  AND project.workspace_id IS NOT NULL
            )
            WHERE site.workspace_id IS NULL
              AND EXISTS (
                SELECT 1
                FROM assets AS asset
                JOIN projects AS project ON project.id = asset.project_id
                WHERE asset.site_id = site.id
                  AND project.workspace_id IS NOT NULL
              )
            """
        )
    )
    _backfill_company(conn, "sites", "company_id")
    _backfill_default(conn, "sites")

    link_sets = {
        "assets": [("projects", "project_id"), ("sites", "site_id")],
        "customer_warranties": [("projects", "project_id")],
        "amc_contracts": [("projects", "project_id")],
        "monitoring_points": [("projects", "project_id")],
        "inventory_items": [("projects", "reserved_for_project_id")],
    }
    for table, sources in link_sets.items():
        _assert_links_agree(conn, table, sources)
        for source_table, foreign_key in sources:
            _backfill_link(conn, table, source_table, foreign_key)
    _backfill_company(conn, "customer_warranties", "customer_id")
    _backfill_company(conn, "amc_contracts", "customer_id")
    for table in link_sets:
        _backfill_default(conn, table)

    dependent_sets = {
        "stock_movements": [
            ("inventory_items", "inventory_item_id"),
            ("projects", "project_id"),
        ],
        "maintenance_schedules": [
            ("projects", "project_id"),
            ("monitoring_points", "monitoring_point_id"),
            ("assets", "asset_id"),
        ],
        "calibration_records": [
            ("projects", "project_id"),
            ("monitoring_points", "monitoring_point_id"),
        ],
    }
    for table, sources in dependent_sets.items():
        _assert_links_agree(conn, table, sources)
        for source_table, foreign_key in sources:
            _backfill_link(conn, table, source_table, foreign_key)
        _backfill_default(conn, table)


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")

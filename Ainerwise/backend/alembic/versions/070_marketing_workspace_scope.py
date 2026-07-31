"""Bind Marketing workspace roots and media work items to a Workspace.

Revision ID: 070
Revises: 069
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "070"
down_revision: Union[str, None] = "069"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "marketing_campaigns",
    "marketing_contacts",
    "marketing_activities",
    "marketing_creative_briefs",
    "marketing_media_requests",
    "marketing_assets",
)


def _add_workspace(table: str) -> None:
    op.add_column(table, sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        f"fk_{table}_workspace_id", table, "workspaces", ["workspace_id"], ["id"]
    )
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


def _backfill(conn, table: str, source_sql: str) -> None:
    conn.execute(sa.text(f"UPDATE {table} AS target SET workspace_id = source.workspace_id FROM ({source_sql}) AS source WHERE source.id = target.id AND target.workspace_id IS NULL AND source.workspace_id IS NOT NULL"))


def _default(conn, table: str) -> None:
    conn.execute(sa.text(f"UPDATE {table} SET workspace_id = (SELECT id FROM workspaces WHERE slug = 'default' AND status = 'active' LIMIT 1) WHERE workspace_id IS NULL"))


def upgrade() -> None:
    for table in TABLES:
        _add_workspace(table)
    conn = op.get_bind()
    _default(conn, "marketing_campaigns")
    _backfill(conn, "marketing_contacts", "SELECT contact.id, lead.workspace_id FROM marketing_contacts contact JOIN leads lead ON lead.id = contact.lead_id")
    _default(conn, "marketing_contacts")
    _backfill(conn, "marketing_activities", "SELECT activity.id, lead.workspace_id FROM marketing_activities activity JOIN leads lead ON lead.id = activity.lead_id")
    _backfill(conn, "marketing_activities", "SELECT activity.id, inquiry.workspace_id FROM marketing_activities activity JOIN inquiries inquiry ON inquiry.id = activity.inquiry_id")
    _backfill(conn, "marketing_activities", "SELECT activity.id, campaign.workspace_id FROM marketing_activities activity JOIN marketing_campaigns campaign ON campaign.id = activity.campaign_id")
    _backfill(conn, "marketing_activities", "SELECT activity.id, contact.workspace_id FROM marketing_activities activity JOIN marketing_contacts contact ON contact.id = activity.contact_id")
    _default(conn, "marketing_activities")
    _backfill(conn, "marketing_creative_briefs", "SELECT brief.id, campaign.workspace_id FROM marketing_creative_briefs brief JOIN marketing_campaigns campaign ON campaign.id = brief.campaign_id")
    _default(conn, "marketing_creative_briefs")
    _backfill(conn, "marketing_media_requests", "SELECT request.id, brief.workspace_id FROM marketing_media_requests request JOIN marketing_creative_brief_versions version ON version.id = request.brief_version_id JOIN marketing_creative_briefs brief ON brief.id = version.brief_id")
    _default(conn, "marketing_media_requests")
    _backfill(conn, "marketing_assets", "SELECT asset.id, campaign.workspace_id FROM marketing_assets asset JOIN marketing_campaigns campaign ON campaign.id = asset.campaign_id")
    _backfill(conn, "marketing_assets", "SELECT asset.id, brief.workspace_id FROM marketing_assets asset JOIN marketing_creative_brief_versions version ON version.id = asset.brief_version_id JOIN marketing_creative_briefs brief ON brief.id = version.brief_id")
    _default(conn, "marketing_assets")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")


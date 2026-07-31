"""Bind CRM Leads to a Workspace.

Revision ID: 063
Revises: 062
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "063"
down_revision: Union[str, None] = "062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_leads_workspace_id",
        "leads",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index("ix_leads_workspace_id", "leads", ["workspace_id"])

    conn = op.get_bind()
    ambiguous = conn.execute(
        sa.text(
            """
            SELECT lead_id
            FROM projects
            WHERE lead_id IS NOT NULL AND workspace_id IS NOT NULL
            GROUP BY lead_id
            HAVING count(DISTINCT workspace_id) > 1
            LIMIT 1
            """
        )
    ).first()
    if ambiguous:
        raise RuntimeError("Cannot bind Leads: one Lead is linked to Projects in multiple Workspaces.")
    conn.execute(
        sa.text(
            """
            UPDATE leads AS lead
            SET workspace_id = (
                SELECT min(project.workspace_id::text)::uuid
                FROM projects AS project
                WHERE project.lead_id = lead.id AND project.workspace_id IS NOT NULL
            )
            WHERE lead.workspace_id IS NULL
              AND EXISTS (SELECT 1 FROM projects AS project WHERE project.lead_id = lead.id)
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE leads AS lead
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.company_id = lead.buyer_company_id
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE lead.workspace_id IS NULL
              AND lead.buyer_company_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE leads
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
    op.drop_index("ix_leads_workspace_id", table_name="leads")
    op.drop_constraint("fk_leads_workspace_id", "leads", type_="foreignkey")
    op.drop_column("leads", "workspace_id")

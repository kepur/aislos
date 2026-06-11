"""Phase G hardening: explicit run attribution and required official grant

Revision ID: 019
Revises: 018
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("agent_slug", sa.String(100), nullable=True), schema="ai")
    op.create_index("ix_ai_agent_runs_agent_slug", "agent_runs", ["agent_slug"], schema="ai")

    op.execute(
        """
        UPDATE ai.agent_runs
        SET agent_slug = CASE
          WHEN workflow IN ('consult', 'lead_score', 'quote_draft') THEN 'sales-agent'
          WHEN workflow IN ('content_gen', 'seo_page', 'publish') THEN 'marketing-agent'
          WHEN workflow = 'bid_evaluation' THEN 'procurement-agent'
          WHEN workflow = 'daily_briefing' THEN 'business-brain'
          ELSE NULL
        END
        WHERE agent_slug IS NULL
        """
    )
    op.execute(
        """
        UPDATE agent_grants
        SET granted = true, granted_at = COALESCE(granted_at, now())
        WHERE agent_id = (SELECT id FROM agents WHERE slug = 'marketing-agent')
          AND scope = 'project_data'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_ai_agent_runs_agent_slug", table_name="agent_runs", schema="ai")
    op.drop_column("agent_runs", "agent_slug", schema="ai")

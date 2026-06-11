"""Phase H: project-scoped Agent Team and Support Agent

Revision ID: 020
Revises: 019
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_object_grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_type", sa.String(50), nullable=False),
        sa.Column("object_id", UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "agent_id", "object_type", "object_id", "scope",
            name="uq_agent_object_grants_target_scope",
        ),
    )
    op.create_index("ix_agent_object_grants_agent_id", "agent_object_grants", ["agent_id"])
    op.create_index("ix_agent_object_grants_object_type", "agent_object_grants", ["object_type"])
    op.create_index("ix_agent_object_grants_object_id", "agent_object_grants", ["object_id"])

    op.create_table(
        "agent_missions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("context_json", JSONB, nullable=True),
        sa.Column("agent_slugs_json", JSONB, nullable=True),
        sa.Column("plan_json", JSONB, nullable=True),
        sa.Column("final_report_json", JSONB, nullable=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("ai.ai_reviews.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="requested"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_missions_project_id", "agent_missions", ["project_id"])
    op.create_index("ix_agent_missions_status", "agent_missions", ["status"])

    op.create_table(
        "agent_mission_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", UUID(as_uuid=True), sa.ForeignKey("agent_missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_slug", sa.String(100), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("output_json", JSONB, nullable=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("ai.agent_runs.id"), nullable=True),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_mission_tasks_mission_id", "agent_mission_tasks", ["mission_id"])
    op.create_index("ix_agent_mission_tasks_project_id", "agent_mission_tasks", ["project_id"])
    op.create_index("ix_agent_mission_tasks_agent_slug", "agent_mission_tasks", ["agent_slug"])
    op.create_index("ix_agent_mission_tasks_status", "agent_mission_tasks", ["status"])

    op.execute(
        """
        UPDATE agents
        SET workflows_json = CASE slug
          WHEN 'marketing-agent' THEN '["content_gen","seo_page","publish","marketing_weekly_report","mission_task"]'::jsonb
          WHEN 'sales-agent' THEN '["consult","lead_score","quote_draft","mission_task"]'::jsonb
          WHEN 'procurement-agent' THEN '["bid_evaluation","mission_task"]'::jsonb
          WHEN 'business-brain' THEN '["daily_briefing","mission_task"]'::jsonb
          WHEN 'support-agent' THEN '["ticket_triage","mission_task"]'::jsonb
          ELSE workflows_json
        END,
        status = CASE WHEN slug = 'support-agent' THEN 'active' ELSE status END
        WHERE vendor = 'official'
        """
    )
    op.execute(
        """
        UPDATE agent_grants
        SET granted = true, granted_at = COALESCE(granted_at, now())
        WHERE scope = 'project_data'
          AND agent_id IN (
            SELECT id FROM agents
            WHERE vendor = 'official' AND workflows_json ? 'mission_task'
          )
        """
    )
    op.execute(
        """
        UPDATE agent_grants
        SET granted = true, granted_at = COALESCE(granted_at, now())
        WHERE scope = 'customer_data'
          AND agent_id = (SELECT id FROM agents WHERE slug = 'marketing-agent')
        """
    )


def downgrade() -> None:
    op.drop_table("agent_mission_tasks")
    op.drop_table("agent_missions")
    op.drop_table("agent_object_grants")
    op.execute(
        """
        UPDATE agents
        SET workflows_json = CASE slug
          WHEN 'marketing-agent' THEN '["content_gen","seo_page","publish"]'::jsonb
          WHEN 'sales-agent' THEN '["consult","lead_score","quote_draft"]'::jsonb
          WHEN 'procurement-agent' THEN '["bid_evaluation"]'::jsonb
          WHEN 'business-brain' THEN '["daily_briefing"]'::jsonb
          WHEN 'support-agent' THEN '[]'::jsonb
          ELSE workflows_json
        END,
        status = CASE WHEN slug = 'support-agent' THEN 'paused' ELSE status END
        WHERE vendor = 'official'
        """
    )
    op.execute(
        """
        UPDATE agent_grants
        SET granted = false, granted_at = NULL
        WHERE scope = 'project_data'
          AND agent_id IN (SELECT id FROM agents WHERE slug IN ('sales-agent', 'support-agent'))
        """
    )
    op.execute(
        """
        UPDATE agent_grants
        SET granted = false, granted_at = NULL
        WHERE scope = 'customer_data'
          AND agent_id = (SELECT id FROM agents WHERE slug = 'marketing-agent')
        """
    )

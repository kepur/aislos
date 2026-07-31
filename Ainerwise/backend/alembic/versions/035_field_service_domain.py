"""PF03: Field Service domain tables.

Revision ID: 035
Revises: 034
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_crews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("partner_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trade", sa.String(64), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_partner_crews_workspace_id", "partner_crews", ["workspace_id"])

    op.create_table(
        "crew_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("crew_id", UUID(as_uuid=True), sa.ForeignKey("partner_crews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_in_crew", sa.String(64), nullable=False, server_default="worker"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "work_packages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("partner_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("trade", sa.String(64), nullable=True),
        sa.Column("scope_json", JSONB, nullable=True),
        sa.Column("site_json", JSONB, nullable=True),
        sa.Column("planned_start", sa.Date(), nullable=True),
        sa.Column("planned_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_work_packages_status", "work_packages", ["status"])

    op.create_table(
        "field_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("work_package_id", UUID(as_uuid=True), sa.ForeignKey("work_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("site_json", JSONB, nullable=True),
        sa.Column("checklist_json", JSONB, nullable=True),
        sa.Column("required_skill", sa.String(64), nullable=True),
        sa.Column("schedule_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schedule_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("offline_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_field_tasks_status", "field_tasks", ["status"])

    op.create_table(
        "task_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("field_task_id", UUID(as_uuid=True), sa.ForeignKey("field_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignee_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("crew_id", UUID(as_uuid=True), sa.ForeignKey("partner_crews.id"), nullable=True),
        sa.Column("assigned_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_task_assignments_assignee", "task_assignments", ["assignee_user_id"])

    op.create_table(
        "task_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("field_task_id", UUID(as_uuid=True), sa.ForeignKey("field_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_id", UUID(as_uuid=True), sa.ForeignKey("task_assignments.id"), nullable=True),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("payload_json", JSONB, nullable=True),
        sa.Column("captured_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True, unique=True),
        sa.Column("sync_status", sa.String(50), nullable=False, server_default="synced"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("task_evidence")
    op.drop_table("task_assignments")
    op.drop_table("field_tasks")
    op.drop_table("work_packages")
    op.drop_table("crew_memberships")
    op.drop_table("partner_crews")

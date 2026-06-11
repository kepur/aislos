"""Notification preferences + report jobs (FI.8.3, FI.8.5)

Revision ID: 008
Revises: 007
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_T = sa.text("true")
_F = sa.text("false")


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, unique=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("telegram_enabled", sa.Boolean, nullable=False, server_default=_F),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default=_T),
        sa.Column("whatsapp_enabled", sa.Boolean, nullable=False, server_default=_F),
        sa.Column("telegram_chat_id", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("whatsapp_number", sa.String(50), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean, nullable=False, server_default=_T),
        sa.Column("reports_enabled", sa.Boolean, nullable=False, server_default=_T),
        sa.Column("maintenance_enabled", sa.Boolean, nullable=False, server_default=_T),
        sa.Column("renewal_enabled", sa.Boolean, nullable=False, server_default=_T),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "report_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("report_type", sa.String(20), nullable=False, server_default=sa.text("'monthly'")),
        sa.Column("period_label", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("review_status", sa.String(30), nullable=False, server_default=sa.text("'pending_review'")),
        sa.Column("file_id", UUID(as_uuid=True), sa.ForeignKey("file_assets.id"), nullable=True),
        sa.Column("scheduled_for", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("report_jobs")
    op.drop_table("notification_preferences")

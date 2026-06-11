"""Marketing attribution and nurture foundation

Revision ID: 010
Revises: 009
Create Date: 2026-06-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_attribution_columns(table: str) -> None:
    op.add_column(table, sa.Column("campaign_id", UUID(as_uuid=True), nullable=True))
    op.add_column(table, sa.Column("source_channel", sa.String(100), nullable=True))
    op.add_column(table, sa.Column("source_detail", sa.String(255), nullable=True))
    op.add_column(table, sa.Column("utm_source", sa.String(100), nullable=True))
    op.add_column(table, sa.Column("utm_medium", sa.String(100), nullable=True))
    op.add_column(table, sa.Column("utm_campaign", sa.String(150), nullable=True))
    op.add_column(table, sa.Column("utm_content", sa.String(150), nullable=True))
    op.add_column(table, sa.Column("landing_page", sa.String(500), nullable=True))
    op.add_column(table, sa.Column("referrer", sa.String(1000), nullable=True))
    op.create_foreign_key(
        f"fk_{table}_campaign_id", table, "marketing_campaigns", ["campaign_id"], ["id"]
    )


def upgrade() -> None:
    op.create_table(
        "marketing_campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("objective", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("landing_path", sa.String(500), nullable=True),
        sa.Column("utm_source", sa.String(100), nullable=True),
        sa.Column("utm_medium", sa.String(100), nullable=True),
        sa.Column("utm_campaign", sa.String(150), nullable=False),
        sa.Column("audience_json", JSONB, nullable=True),
        sa.Column("offer_json", JSONB, nullable=True),
        sa.Column("content_json", JSONB, nullable=True),
        sa.Column("budget", sa.Float, nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketing_campaigns_utm_campaign", "marketing_campaigns", ["utm_campaign"])

    _add_attribution_columns("leads")
    _add_attribution_columns("inquiries")

    op.create_table(
        "marketing_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("segment", sa.String(100), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="prospect"),
        sa.Column("consent_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("tags_json", JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketing_contacts_email", "marketing_contacts", ["email"])
    op.create_index("ix_marketing_contacts_segment", "marketing_contacts", ["segment"])
    op.create_index("ix_marketing_contacts_status", "marketing_contacts", ["status"])
    op.create_index("ix_marketing_contacts_next_follow_up_at", "marketing_contacts", ["next_follow_up_at"])

    op.create_table(
        "marketing_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("marketing_campaigns.id"), nullable=True),
        sa.Column("contact_id", UUID(as_uuid=True), sa.ForeignKey("marketing_contacts.id"), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("inquiry_id", UUID(as_uuid=True), sa.ForeignKey("inquiries.id"), nullable=True),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False, server_default="outbound"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending_approval"),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_json", JSONB, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("lead_id", "inquiry_id", "status", "scheduled_at"):
        op.create_index(f"ix_marketing_activities_{column}", "marketing_activities", [column])


def downgrade() -> None:
    op.drop_table("marketing_activities")
    op.drop_table("marketing_contacts")
    for table in ("inquiries", "leads"):
        op.drop_constraint(f"fk_{table}_campaign_id", table, type_="foreignkey")
        for column in (
            "referrer", "landing_page", "utm_content", "utm_campaign", "utm_medium",
            "utm_source", "source_detail", "source_channel", "campaign_id",
        ):
            op.drop_column(table, column)
    op.drop_table("marketing_campaigns")

"""MI01: Creative Brief, immutable versions and Media Request foundation.

Revision ID: 025
Revises: 024
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketing_creative_briefs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("marketing_campaigns.id"), nullable=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("current_version_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketing_creative_briefs_status", "marketing_creative_briefs", ["status"])
    op.create_index("ix_marketing_creative_briefs_campaign_id", "marketing_creative_briefs", ["campaign_id"])
    op.create_index("ix_marketing_creative_briefs_region_id", "marketing_creative_briefs", ["region_id"])

    op.create_table(
        "marketing_creative_brief_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("brief_id", UUID(as_uuid=True), sa.ForeignKey("marketing_creative_briefs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("copy_json", JSONB, nullable=True),
        sa.Column("audience_json", JSONB, nullable=True),
        sa.Column("brand_constraints_json", JSONB, nullable=True),
        sa.Column("channel_specs_json", JSONB, nullable=True),
        sa.Column("deliverables_json", JSONB, nullable=True),
        sa.Column("source_refs_json", JSONB, nullable=True),
        sa.Column("compliance_json", JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("ai.ai_reviews.id"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("brief_id", "version", name="uq_marketing_brief_versions_brief_version"),
    )
    op.create_index("ix_marketing_brief_versions_brief_id", "marketing_creative_brief_versions", ["brief_id"])
    op.create_index("ix_marketing_brief_versions_status", "marketing_creative_brief_versions", ["status"])

    op.create_foreign_key(
        "fk_brief_current_version",
        "marketing_creative_briefs",
        "marketing_creative_brief_versions",
        ["current_version_id"],
        ["id"],
    )

    op.create_table(
        "marketing_media_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brief_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketing_creative_brief_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("deliverable_key", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("claimed_by_client_id", UUID(as_uuid=True), nullable=True),
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_job_ref", sa.String(255), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column("progress_message", sa.Text(), nullable=True),
        sa.Column("failure_code", sa.String(100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("submitted_asset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "brief_version_id",
            "deliverable_key",
            name="uq_marketing_media_requests_version_deliverable",
        ),
    )
    op.create_index("ix_marketing_media_requests_status", "marketing_media_requests", ["status"])
    op.create_index("ix_marketing_media_requests_brief_version_id", "marketing_media_requests", ["brief_version_id"])


def downgrade() -> None:
    op.drop_table("marketing_media_requests")
    op.drop_constraint("fk_brief_current_version", "marketing_creative_briefs", type_="foreignkey")
    op.drop_table("marketing_creative_brief_versions")
    op.drop_table("marketing_creative_briefs")

"""Phase D content modules: seo_pages, document center, publish_jobs,
design_revisions

Revision ID: 015
Revises: 014
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "seo_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("target_keyword", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column("content_md", sa.Text, nullable=True),
        sa.Column("ai_generated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("ai.ai_reviews.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.UniqueConstraint("slug", name="uq_seo_pages_slug"),
    )
    op.create_index("ix_seo_pages_status", "seo_pages", ["status"])

    op.create_table(
        "document_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("body_md", sa.Text, nullable=False),
        sa.Column("variables_json", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        *_ts(),
    )
    op.create_index("ix_document_templates_kind", "document_templates", ["kind"])

    op.create_table(
        "generated_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("document_templates.id"), nullable=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("subject_type", sa.String(50), nullable=True),
        sa.Column("subject_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body_md", sa.Text, nullable=True),
        sa.Column("pdf_minio_key", sa.String(500), nullable=True),
        sa.Column("ai_generated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("ai.ai_reviews.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        *_ts(),
    )
    op.create_index("ix_generated_documents_status", "generated_documents", ["status"])
    op.create_index("ix_generated_documents_subject", "generated_documents", ["subject_type", "subject_id"])

    op.create_table(
        "publish_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("marketing_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("account_ref", sa.String(255), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_post_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("error_message", sa.Text, nullable=True),
        *_ts(),
    )
    op.create_index("ix_publish_jobs_asset_id", "publish_jobs", ["asset_id"])
    op.create_index("ix_publish_jobs_status", "publish_jobs", ["status"])
    op.create_index("ix_publish_jobs_scheduled_at", "publish_jobs", ["scheduled_at"])

    op.create_table(
        "design_revisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("file_minio_key", sa.String(500), nullable=False),
        sa.Column("file_kind", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_design_revisions_site_id", "design_revisions", ["site_id"])
    op.create_index("ix_design_revisions_project_id", "design_revisions", ["project_id"])


def downgrade() -> None:
    op.drop_table("design_revisions")
    op.drop_table("publish_jobs")
    op.drop_table("generated_documents")
    op.drop_table("document_templates")
    op.drop_table("seo_pages")

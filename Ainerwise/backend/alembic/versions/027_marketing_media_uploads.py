"""MI03: external media uploads, MarketingAsset extensions.

Revision ID: 027
Revises: 026
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("marketing_assets", sa.Column("brief_version_id", UUID(as_uuid=True), nullable=True))
    op.add_column("marketing_assets", sa.Column("media_request_id", UUID(as_uuid=True), nullable=True))
    op.add_column("marketing_assets", sa.Column("integration_client_id", UUID(as_uuid=True), nullable=True))
    op.add_column("marketing_assets", sa.Column("external_asset_ref", sa.String(255), nullable=True))
    op.add_column("marketing_assets", sa.Column("variant_key", sa.String(100), nullable=True))
    op.add_column("marketing_assets", sa.Column("mime_type", sa.String(100), nullable=True))
    op.add_column("marketing_assets", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column("marketing_assets", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("marketing_assets", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column("marketing_assets", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    op.add_column("marketing_assets", sa.Column("sha256", sa.String(64), nullable=True))
    op.add_column("marketing_assets", sa.Column("source_metadata_json", JSONB, nullable=True))

    op.create_foreign_key(
        "fk_marketing_assets_brief_version",
        "marketing_assets",
        "marketing_creative_brief_versions",
        ["brief_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_marketing_assets_media_request",
        "marketing_assets",
        "marketing_media_requests",
        ["media_request_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_marketing_assets_integration_client",
        "marketing_assets",
        "marketing_integration_clients",
        ["integration_client_id"],
        ["id"],
    )
    op.create_index("ix_marketing_assets_brief_version_id", "marketing_assets", ["brief_version_id"])
    op.create_index("ix_marketing_assets_media_request_id", "marketing_assets", ["media_request_id"])
    op.create_index("ix_marketing_assets_integration_client_id", "marketing_assets", ["integration_client_id"])
    op.create_unique_constraint(
        "uq_marketing_assets_client_external_ref",
        "marketing_assets",
        ["integration_client_id", "external_asset_ref"],
    )

    op.create_table(
        "marketing_media_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "media_request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketing_media_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "integration_client_id",
            UUID(as_uuid=True),
            sa.ForeignKey("marketing_integration_clients.id"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_expected", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False, unique=True),
        sa.Column("bucket", sa.String(100), nullable=False, server_default="marketing-assets"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketing_media_uploads_status", "marketing_media_uploads", ["status"])
    op.create_index("ix_marketing_media_uploads_media_request_id", "marketing_media_uploads", ["media_request_id"])


def downgrade() -> None:
    op.drop_table("marketing_media_uploads")
    op.drop_constraint("uq_marketing_assets_client_external_ref", "marketing_assets", type_="unique")
    op.drop_constraint("fk_marketing_assets_integration_client", "marketing_assets", type_="foreignkey")
    op.drop_constraint("fk_marketing_assets_media_request", "marketing_assets", type_="foreignkey")
    op.drop_constraint("fk_marketing_assets_brief_version", "marketing_assets", type_="foreignkey")
    for col in (
        "source_metadata_json", "sha256", "duration_seconds", "height", "width", "size_bytes",
        "mime_type", "variant_key", "external_asset_ref", "integration_client_id",
        "media_request_id", "brief_version_id",
    ):
        op.drop_column("marketing_assets", col)

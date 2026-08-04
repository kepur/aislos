"""Analytics ingest clients — API keys for external projects.

Revision ID: 083
Revises: 082
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "083"
down_revision: Union[str, None] = "082"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_app", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(24), nullable=False),
        sa.Column("secret_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("scopes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allowed_region_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("allowed_portal_keys_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        schema="analytics",
    )
    op.create_index("ix_analytics_clients_source_app", "clients", ["source_app"], schema="analytics")
    op.create_index("ix_analytics_clients_key_prefix", "clients", ["key_prefix"], schema="analytics")
    op.create_index("ix_analytics_clients_status", "clients", ["status"], schema="analytics")


def downgrade() -> None:
    op.drop_table("clients", schema="analytics")

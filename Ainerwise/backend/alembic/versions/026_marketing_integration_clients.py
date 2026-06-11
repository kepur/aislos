"""MI02: Integration Client auth, idempotency and media request claim FK.

Revision ID: 026
Revises: 025
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketing_integration_clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("secret_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("scopes_json", JSONB, nullable=False),
        sa.Column("allowed_region_ids_json", JSONB, nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketing_integration_clients_status", "marketing_integration_clients", ["status"])
    op.create_index("ix_marketing_integration_clients_key_prefix", "marketing_integration_clients", ["key_prefix"])

    op.create_table(
        "marketing_integration_idempotency",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("marketing_integration_clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_json", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("client_id", "operation", "idempotency_key", name="uq_marketing_integration_idempotency"),
    )

    op.create_foreign_key(
        "fk_media_requests_claimed_by_client",
        "marketing_media_requests",
        "marketing_integration_clients",
        ["claimed_by_client_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_media_requests_claimed_by_client", "marketing_media_requests", type_="foreignkey")
    op.drop_table("marketing_integration_idempotency")
    op.drop_table("marketing_integration_clients")

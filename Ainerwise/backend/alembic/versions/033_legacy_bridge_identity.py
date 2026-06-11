"""SP03/SP04: legacy bridge idempotency and identity mappings.

Revision ID: 033
Revises: 032
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legacy_bridge_idempotency",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("response_json", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("client_id", "idempotency_key", name="uq_legacy_bridge_idempotency"),
    )
    op.create_index(
        "ix_legacy_bridge_idempotency_created_at",
        "legacy_bridge_idempotency",
        ["created_at"],
    )

    op.create_table(
        "legacy_identity_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("portal_key", sa.String(50), nullable=False),
        sa.Column("legacy_system", sa.String(50), nullable=False, server_default="cebu"),
        sa.Column("legacy_user_id", sa.String(128), nullable=True),
        sa.Column("legacy_company_id", sa.String(128), nullable=True),
        sa.Column("core_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("core_company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "portal_key",
            "legacy_system",
            "legacy_user_id",
            name="uq_legacy_identity_user",
        ),
    )
    op.create_index(
        "ix_legacy_identity_mappings_core_user",
        "legacy_identity_mappings",
        ["core_user_id"],
    )


def downgrade() -> None:
    op.drop_table("legacy_identity_mappings")
    op.drop_table("legacy_bridge_idempotency")

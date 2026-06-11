"""Phase E: e-signature audit table + partner Stripe Connect account ref

Revision ID: 016
Revises: 015
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_signatures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True),
                  sa.ForeignKey("generated_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signer_name", sa.String(255), nullable=False),
        sa.Column("signer_email", sa.String(255), nullable=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="sent"),
        sa.Column("document_sha256", sa.String(64), nullable=False),
        sa.Column("signature_minio_key", sa.String(500), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signer_ip", sa.String(64), nullable=True),
        sa.Column("signer_user_agent", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_signatures_document_id", "document_signatures", ["document_id"])
    op.create_index("ix_document_signatures_status", "document_signatures", ["status"])

    op.add_column("service_partners", sa.Column("stripe_account_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("service_partners", "stripe_account_id")
    op.drop_table("document_signatures")

"""Phase 2: commerce threads, messages, portal notifications.

Revision ID: 039
Revises: 038
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "039"
down_revision: Union[str, None] = "038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portal_notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("portal_key", sa.String(64), nullable=False, server_default="cebu"),
        sa.Column("domain", sa.String(32), nullable=False, server_default="commerce"),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link_path", sa.String(512), nullable=True),
        sa.Column("aggregate_type", sa.String(64), nullable=True),
        sa.Column("aggregate_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="unread"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_portal_notifications_user_status", "portal_notifications", ["user_id", "status"])

    op.create_table(
        "commerce_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("portal_key", sa.String(64), nullable=False, server_default="cebu"),
        sa.Column("procurement_request_id", UUID(as_uuid=True), sa.ForeignKey("procurement_requests.id"), nullable=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id"), nullable=True),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("supplier_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_threads_order", "commerce_threads", ["commerce_order_id"])
    op.create_index("ix_commerce_threads_request", "commerce_threads", ["procurement_request_id"])

    op.create_table(
        "commerce_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("commerce_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sender_role", sa.String(32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("attachments_json", JSONB, nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_messages_thread", "commerce_messages", ["thread_id"])


def downgrade() -> None:
    op.drop_table("commerce_messages")
    op.drop_table("commerce_threads")
    op.drop_table("portal_notifications")

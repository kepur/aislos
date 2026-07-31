"""Add shared admin notes, notification templates, and platform settings.

Revision ID: 049
Revises: 048
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "049"
down_revision: Union[str, None] = "048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_notes",
        sa.Column("portal_key", sa.String(length=64), nullable=False, server_default="admin_cebu"),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="internal_only"),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("portal_key", "entity_type", "entity_id", "author_id"):
        op.create_index(f"ix_admin_notes_{column}", "admin_notes", [column])

    op.create_table(
        "notification_templates",
        sa.Column("portal_key", sa.String(length=64), nullable=False, server_default="admin_cebu"),
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables_hint", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portal_key", "template_key", "channel", "language", name="uq_notification_template_scope"),
    )
    op.create_index("ix_notification_templates_portal_key", "notification_templates", ["portal_key"])
    op.create_index("ix_notification_templates_template_key", "notification_templates", ["template_key"])

    op.create_table(
        "platform_settings",
        sa.Column("portal_key", sa.String(length=64), nullable=False, server_default="admin_cebu"),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portal_key", "key", name="uq_platform_setting_scope"),
    )
    op.create_index("ix_platform_settings_portal_key", "platform_settings", ["portal_key"])
    op.create_index("ix_platform_settings_key", "platform_settings", ["key"])


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_table("notification_templates")
    op.drop_table("admin_notes")

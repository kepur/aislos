"""Add shared buyer project metric templates.

Revision ID: 050
Revises: 049
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "050"
down_revision: Union[str, None] = "049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buyer_project_metric_templates",
        sa.Column("project_type", sa.String(length=50), nullable=False, server_default="GENERAL"),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("data_type", sa.String(length=50), nullable=False, server_default="text"),
        sa.Column("unit_options_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_type", "key", name="uq_buyer_project_metric_template_scope"),
    )
    for column in ("project_type", "key", "active"):
        op.create_index(
            f"ix_buyer_project_metric_templates_{column}",
            "buyer_project_metric_templates",
            [column],
        )


def downgrade() -> None:
    op.drop_table("buyer_project_metric_templates")

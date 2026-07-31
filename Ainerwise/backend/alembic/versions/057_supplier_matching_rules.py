"""Add supplier category and region matching rules.

Revision ID: 057
Revises: 056
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "057"
down_revision: Union[str, None] = "056"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notification_preferences",
        sa.Column("supplier_category_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("supplier_region_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "procurement_requests",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_procurement_requests_region_id_regions",
        "procurement_requests",
        "regions",
        ["region_id"],
        ["id"],
    )
    op.create_index("ix_procurement_requests_region_id", "procurement_requests", ["region_id"])


def downgrade() -> None:
    op.drop_index("ix_procurement_requests_region_id", table_name="procurement_requests")
    op.drop_constraint(
        "fk_procurement_requests_region_id_regions",
        "procurement_requests",
        type_="foreignkey",
    )
    op.drop_column("procurement_requests", "region_id")
    op.drop_column("notification_preferences", "supplier_region_ids_json")
    op.drop_column("notification_preferences", "supplier_category_ids_json")

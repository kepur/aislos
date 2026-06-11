"""Add product supply chain and lifecycle pricing fields

Revision ID: 003
Revises: ce8620520aac
Create Date: 2026-05-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003"
down_revision: Union[str, None] = "ce8620520aac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("service_term_years_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("price_options_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("lifecycle_pricing_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("project_pricing_mode", sa.String(100), nullable=True))
    op.add_column("products", sa.Column("service_pricing_note", sa.Text, nullable=True))
    op.add_column("products", sa.Column("supply_tier", sa.String(255), nullable=True))
    op.add_column("products", sa.Column("supplier_ecosystem_json", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("products", "supplier_ecosystem_json")
    op.drop_column("products", "supply_tier")
    op.drop_column("products", "service_pricing_note")
    op.drop_column("products", "project_pricing_mode")
    op.drop_column("products", "lifecycle_pricing_json")
    op.drop_column("products", "price_options_json")
    op.drop_column("products", "service_term_years_json")

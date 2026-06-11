"""C06: procurement packages, package items and partner capabilities.

Revision ID: 031
Revises: 030
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_capabilities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "partner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("service_partners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trade", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("capability_keys_json", JSONB, nullable=False, server_default="[]"),
        sa.Column("supported_regions_json", JSONB, nullable=False, server_default="[]"),
        sa.Column("supply", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("install", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("maintain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("verification_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_partner_capabilities_partner_id", "partner_capabilities", ["partner_id"])
    op.create_index("ix_partner_capabilities_trade", "partner_capabilities", ["trade"])

    op.create_table(
        "procurement_packages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "boq_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("trade", sa.String(50), nullable=False),
        sa.Column("commercial_type", sa.String(30), nullable=False),
        sa.Column("procurement_mode", sa.String(20), nullable=False),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("compatibility_json", JSONB, nullable=True),
        sa.Column("delivery_constraints_json", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id",
            "boq_version_id",
            "trade",
            "commercial_type",
            "revision",
            name="uq_procurement_packages_project_boq_trade_type_rev",
        ),
    )
    op.create_index("ix_procurement_packages_project_id", "procurement_packages", ["project_id"])

    op.create_table(
        "procurement_package_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "package_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "boq_item_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "boq_item_option_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_item_options.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "package_id",
            "boq_item_id",
            name="uq_procurement_package_items_pkg_boq",
        ),
    )
    op.create_index(
        "ix_procurement_package_items_package_id",
        "procurement_package_items",
        ["package_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_procurement_package_items_package_id", table_name="procurement_package_items")
    op.drop_table("procurement_package_items")
    op.drop_index("ix_procurement_packages_project_id", table_name="procurement_packages")
    op.drop_table("procurement_packages")
    op.drop_index("ix_partner_capabilities_trade", table_name="partner_capabilities")
    op.drop_index("ix_partner_capabilities_partner_id", table_name="partner_capabilities")
    op.drop_table("partner_capabilities")

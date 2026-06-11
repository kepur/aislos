"""C07: commercial snapshots and procurement RFQ linkage.

Revision ID: 032
Revises: 031
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("portal_key", sa.String(50), nullable=False),
        sa.Column(
            "portal_policy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("portal_policies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "procurement_project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "boq_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "package_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_packages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("package_revision", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("exchange_rate_snapshot_json", JSONB, nullable=False),
        sa.Column("tax_mode", sa.String(50), nullable=False),
        sa.Column("margin_rule_json", JSONB, nullable=False),
        sa.Column("service_fee_json", JSONB, nullable=False),
        sa.Column("warranty_rule_json", JSONB, nullable=False),
        sa.Column("delivery_region_json", JSONB, nullable=False),
        sa.Column("quote_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_terms_json", JSONB, nullable=False),
        sa.Column("terms_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("package_id", "package_revision", name="uq_commercial_snapshots_package_rev"),
    )
    op.create_index(
        "ix_commercial_snapshots_procurement_project_id",
        "commercial_snapshots",
        ["procurement_project_id"],
    )
    op.create_index("ix_commercial_snapshots_package_id", "commercial_snapshots", ["package_id"])

    op.add_column(
        "rfqs",
        sa.Column(
            "procurement_package_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_packages.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "rfqs",
        sa.Column(
            "commercial_snapshot_id",
            UUID(as_uuid=True),
            sa.ForeignKey("commercial_snapshots.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column("rfqs", sa.Column("portal_key", sa.String(50), nullable=True))
    op.add_column("rfqs", sa.Column("revision", sa.Integer(), nullable=True))
    op.create_index("ix_rfqs_procurement_package_id", "rfqs", ["procurement_package_id"])
    op.create_index("ix_rfqs_portal_key", "rfqs", ["portal_key"])
    op.create_unique_constraint(
        "uq_rfqs_procurement_package_revision",
        "rfqs",
        ["procurement_package_id", "revision"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_rfqs_procurement_package_revision", "rfqs", type_="unique")
    op.drop_index("ix_rfqs_portal_key", table_name="rfqs")
    op.drop_index("ix_rfqs_procurement_package_id", table_name="rfqs")
    op.drop_column("rfqs", "revision")
    op.drop_column("rfqs", "portal_key")
    op.drop_column("rfqs", "commercial_snapshot_id")
    op.drop_column("rfqs", "procurement_package_id")
    op.drop_index("ix_commercial_snapshots_package_id", table_name="commercial_snapshots")
    op.drop_index(
        "ix_commercial_snapshots_procurement_project_id",
        table_name="commercial_snapshots",
    )
    op.drop_table("commercial_snapshots")

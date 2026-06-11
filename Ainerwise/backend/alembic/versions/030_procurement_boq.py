"""C04: BOQ versions, items, tier options and solution plans.

Revision ID: 030
Revises: 029
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "boq_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("source_run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("facts_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("boq_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("overall_confidence", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("disclaimer", sa.Text(), nullable=True),
        sa.Column(
            "review_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ai.ai_reviews.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("frozen_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "version", name="uq_boq_versions_project_version"),
    )
    op.create_index("ix_boq_versions_project_id", "boq_versions", ["project_id"])

    op.create_table(
        "boq_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "boq_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("trade", sa.String(100), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs", sa.Text(), nullable=True),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(50), nullable=False, server_default="ea"),
        sa.Column("quantity_basis", sa.Text(), nullable=True),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("source", sa.String(20), nullable=False, server_default="system"),
        sa.Column("source_ref_json", JSONB, nullable=True),
        sa.Column("critical", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("weight", sa.Numeric(6, 3), nullable=False, server_default="1"),
        sa.Column("included", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_boq_items_boq_version_id", "boq_items", ["boq_version_id"])

    op.create_table(
        "boq_item_options",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "boq_item_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("capability", sa.String(500), nullable=False),
        sa.Column("recommended_brand", sa.String(255), nullable=True),
        sa.Column("unit_price_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_price_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_price_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_price_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("supply_included", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("install_included", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("maintain_included", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("boq_item_id", "tier", name="uq_boq_item_options_item_tier"),
    )
    op.create_index("ix_boq_item_options_boq_item_id", "boq_item_options", ["boq_item_id"])

    op.create_table(
        "solution_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "boq_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("boq_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("total_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("exclusions", sa.Text(), nullable=True),
        sa.Column("estimate_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("boq_version_id", "tier", name="uq_solution_plans_version_tier"),
    )
    op.create_index("ix_solution_plans_boq_version_id", "solution_plans", ["boq_version_id"])

    # Dev/test DB may hold stale UUIDs in current_boq_version_id before FK exists.
    op.execute(sa.text("UPDATE procurement_projects SET current_boq_version_id = NULL"))
    op.create_foreign_key(
        "fk_procurement_projects_current_boq_version",
        "procurement_projects",
        "boq_versions",
        ["current_boq_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE procurement_projects SET current_boq_version_id = NULL"))
    op.drop_constraint(
        "fk_procurement_projects_current_boq_version",
        "procurement_projects",
        type_="foreignkey",
    )
    op.drop_index("ix_solution_plans_boq_version_id", table_name="solution_plans")
    op.drop_table("solution_plans")
    op.drop_index("ix_boq_item_options_boq_item_id", table_name="boq_item_options")
    op.drop_table("boq_item_options")
    op.drop_index("ix_boq_items_boq_version_id", table_name="boq_items")
    op.drop_table("boq_items")
    op.drop_index("ix_boq_versions_project_id", table_name="boq_versions")
    op.drop_table("boq_versions")

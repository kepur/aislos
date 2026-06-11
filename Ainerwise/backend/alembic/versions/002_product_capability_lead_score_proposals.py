"""Add product capability fields, lead score/stage, and proposal/BOM tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Product capability fields ---
    op.add_column("products", sa.Column("protocol_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("scenario_tags_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("intelligence_level_min", sa.Integer, nullable=True))
    op.add_column("products", sa.Column("intelligence_level_max", sa.Integer, nullable=True))
    op.add_column("products", sa.Column("feature_status", sa.String(50), nullable=True))
    op.add_column("products", sa.Column("risk_level", sa.String(50), nullable=True))

    # --- Lead score and stage fields ---
    op.add_column("leads", sa.Column("lead_score", sa.Integer, nullable=True))
    op.add_column("leads", sa.Column("lead_stage", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("desired_intelligence_level", sa.Integer, nullable=True))
    op.add_column("leads", sa.Column("conversation_json", JSONB, nullable=True))
    op.add_column("leads", sa.Column("proposal_tiers_json", JSONB, nullable=True))

    # --- ProposalPlan table ---
    op.create_table(
        "proposal_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("intelligence_level_min", sa.Integer, nullable=True),
        sa.Column("intelligence_level_max", sa.Integer, nullable=True),
        sa.Column("device_cost_estimate", sa.Float, server_default="0"),
        sa.Column("design_fee_estimate", sa.Float, server_default="0"),
        sa.Column("installation_fee_estimate", sa.Float, server_default="0"),
        sa.Column("platform_fee_estimate", sa.Float, server_default="0"),
        sa.Column("maintenance_fee_estimate", sa.Float, server_default="0"),
        sa.Column("spare_parts_reserve", sa.Float, server_default="0"),
        sa.Column("total_min", sa.Float, server_default="0"),
        sa.Column("total_max", sa.Float, server_default="0"),
        sa.Column("currency", sa.String(10), server_default="EUR"),
        sa.Column("complexity", sa.String(50), nullable=True),
        sa.Column("risk_level", sa.String(50), nullable=True),
        sa.Column("recommended_next_step", sa.Text, nullable=True),
        sa.Column("estimate_only", sa.Boolean, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- BOMItem table ---
    op.create_table(
        "bom_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_plan_id", UUID(as_uuid=True), sa.ForeignKey("proposal_plans.id"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("qty", sa.Integer, server_default="1"),
        sa.Column("unit_price", sa.Float, server_default="0"),
        sa.Column("device_cost", sa.Float, server_default="0"),
        sa.Column("installation_cost", sa.Float, server_default="0"),
        sa.Column("service_fee", sa.Float, server_default="0"),
        sa.Column("maintenance_years", sa.Integer, nullable=True),
        sa.Column("already_owned", sa.Boolean, server_default="false"),
        sa.Column("need_ainerwise_supply", sa.Boolean, server_default="true"),
        sa.Column("need_installation", sa.Boolean, server_default="true"),
        sa.Column("design_only", sa.Boolean, server_default="false"),
        sa.Column("total", sa.Float, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("bom_items")
    op.drop_table("proposal_plans")

    op.drop_column("leads", "proposal_tiers_json")
    op.drop_column("leads", "conversation_json")
    op.drop_column("leads", "desired_intelligence_level")
    op.drop_column("leads", "lead_stage")
    op.drop_column("leads", "lead_score")

    op.drop_column("products", "risk_level")
    op.drop_column("products", "feature_status")
    op.drop_column("products", "intelligence_level_max")
    op.drop_column("products", "intelligence_level_min")
    op.drop_column("products", "scenario_tags_json")
    op.drop_column("products", "protocol_json")

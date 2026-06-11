"""Add Project Forge conversation, metrics, and price snapshots.

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_message_role AS ENUM "
        "('USER','ASSISTANT','SYSTEM'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_workflow_node AS ENUM "
        "('intake_chat','metric_extract','gap_question','file_multimodal_extract',"
        "'line_item_plan','price_tier_estimate','supplier_match','form_freeze'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE metric_value_source AS ENUM "
        "('USER','AI','FILE','SYSTEM'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "project_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", postgresql.ENUM("USER", "ASSISTANT", "SYSTEM",
                                           name="project_message_role", create_type=False),
                  nullable=False, server_default="USER"),
        sa.Column("workflow_node", postgresql.ENUM(
            "intake_chat", "metric_extract", "gap_question", "file_multimodal_extract",
            "line_item_plan", "price_tier_estimate", "supplier_match", "form_freeze",
            name="project_workflow_node", create_type=False,
        ), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_ids_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("structured_delta_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_messages_project_id", "project_messages", ["project_id"])
    op.create_index("ix_project_messages_role", "project_messages", ["role"])

    op.create_table(
        "project_metric_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_type", postgresql.ENUM("CONSTRUCTION", "SOLAR", "TECH_BUILD", "RENOVATION", "GENERAL",
                                                   name="project_type", create_type=False),
                  nullable=False, server_default="GENERAL"),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("unit_options_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_metric_templates_project_type", "project_metric_templates", ["project_type"])
    op.create_index("ix_project_metric_templates_key", "project_metric_templates", ["key"])
    op.create_index("ix_project_metric_templates_active", "project_metric_templates", ["active"])

    op.create_table(
        "project_metric_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("value_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("source", postgresql.ENUM("USER", "AI", "FILE", "SYSTEM",
                                            name="metric_value_source", create_type=False),
                  nullable=False, server_default="USER"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_metric_values_project_id", "project_metric_values", ["project_id"])
    op.create_index("ix_project_metric_values_key", "project_metric_values", ["key"])

    op.create_table(
        "project_price_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_unit_price", sa.Float(), nullable=True),
        sa.Column("avg_unit_price", sa.Float(), nullable=True),
        sa.Column("median_unit_price", sa.Float(), nullable=True),
        sa.Column("p20_unit_price", sa.Float(), nullable=True),
        sa.Column("p80_unit_price", sa.Float(), nullable=True),
        sa.Column("price_tiers_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("samples_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("source_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_price_snapshots_project_id", "project_price_snapshots", ["project_id"])
    op.create_index("ix_project_price_snapshots_line_item_id", "project_price_snapshots", ["line_item_id"])

    conn.execute(sa.text(
        "ALTER TABLE project_line_items "
        "ADD COLUMN IF NOT EXISTS price_tiers_jsonb JSON"
    ))


def downgrade() -> None:
    op.drop_column("project_line_items", "price_tiers_jsonb")

    op.drop_index("ix_project_price_snapshots_line_item_id", table_name="project_price_snapshots")
    op.drop_index("ix_project_price_snapshots_project_id", table_name="project_price_snapshots")
    op.drop_table("project_price_snapshots")

    op.drop_index("ix_project_metric_values_key", table_name="project_metric_values")
    op.drop_index("ix_project_metric_values_project_id", table_name="project_metric_values")
    op.drop_table("project_metric_values")

    op.drop_index("ix_project_metric_templates_active", table_name="project_metric_templates")
    op.drop_index("ix_project_metric_templates_key", table_name="project_metric_templates")
    op.drop_index("ix_project_metric_templates_project_type", table_name="project_metric_templates")
    op.drop_table("project_metric_templates")

    op.drop_index("ix_project_messages_role", table_name="project_messages")
    op.drop_index("ix_project_messages_project_id", table_name="project_messages")
    op.drop_table("project_messages")

    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS metric_value_source"))
    conn.execute(sa.text("DROP TYPE IF EXISTS project_workflow_node"))
    conn.execute(sa.text("DROP TYPE IF EXISTS project_message_role"))

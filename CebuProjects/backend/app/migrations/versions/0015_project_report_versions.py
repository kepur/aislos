"""Add versioned Project Forge reports.

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_report_version_status AS ENUM "
        "('DRAFT','ESTIMATED','USER_REVIEWED','FROZEN','PUBLISHED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_report_patch_status AS ENUM "
        "('PENDING','APPLIED','REJECTED','FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "project_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("frozen_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_reports_project_id", "project_reports", ["project_id"])

    op.create_table(
        "project_report_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", postgresql.ENUM(
            "DRAFT", "ESTIMATED", "USER_REVIEWED", "FROZEN", "PUBLISHED",
            name="project_report_version_status", create_type=False,
        ), nullable=False, server_default="DRAFT"),
        sa.Column("source", sa.String(50), nullable=False, server_default="SYSTEM"),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("summary_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("totals_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_report_versions_report_id", "project_report_versions", ["report_id"])
    op.create_index("ix_project_report_versions_project_id", "project_report_versions", ["project_id"])
    op.create_index("ix_project_report_versions_status", "project_report_versions", ["status"])

    op.create_table(
        "project_report_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("editable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_report_columns_report_version_id", "project_report_columns", ["report_version_id"])
    op.create_index("ix_project_report_columns_key", "project_report_columns", ["key"])

    op.create_table(
        "project_report_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("qty", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(50), nullable=False, server_default="pcs"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("quality_tier", postgresql.ENUM("BUDGET", "MID_RANGE", "PREMIUM", name="quality_tier", create_type=False), nullable=False, server_default="MID_RANGE"),
        sa.Column("selected_tier", sa.String(20), nullable=False, server_default="MID_RANGE"),
        sa.Column("include_in_total", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("selected_for_purchase", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("price_tiers_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("custom_values_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("match_status", sa.String(50), nullable=False, server_default="UNMATCHED"),
        sa.Column("samples_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("price_source", sa.String(50), nullable=False, server_default="AI_ESTIMATE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_report_rows_report_version_id", "project_report_rows", ["report_version_id"])
    op.create_index("ix_project_report_rows_project_id", "project_report_rows", ["project_id"])

    op.create_table(
        "project_report_change_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_type", sa.String(50), nullable=False, server_default="MANUAL_EDIT"),
        sa.Column("status", postgresql.ENUM(
            "PENDING", "APPLIED", "REJECTED", "FAILED",
            name="project_report_patch_status", create_type=False,
        ), nullable=False, server_default="PENDING"),
        sa.Column("user_message", sa.Text(), nullable=True),
        sa.Column("patch_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("before_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("after_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_project_report_change_logs_project_id", "project_report_change_logs", ["project_id"])
    op.create_index("ix_project_report_change_logs_report_id", "project_report_change_logs", ["report_id"])
    op.create_index("ix_project_report_change_logs_version_id", "project_report_change_logs", ["version_id"])
    op.create_index("ix_project_report_change_logs_status", "project_report_change_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_project_report_change_logs_status", table_name="project_report_change_logs")
    op.drop_index("ix_project_report_change_logs_version_id", table_name="project_report_change_logs")
    op.drop_index("ix_project_report_change_logs_report_id", table_name="project_report_change_logs")
    op.drop_index("ix_project_report_change_logs_project_id", table_name="project_report_change_logs")
    op.drop_table("project_report_change_logs")
    op.drop_index("ix_project_report_rows_project_id", table_name="project_report_rows")
    op.drop_index("ix_project_report_rows_report_version_id", table_name="project_report_rows")
    op.drop_table("project_report_rows")
    op.drop_index("ix_project_report_columns_key", table_name="project_report_columns")
    op.drop_index("ix_project_report_columns_report_version_id", table_name="project_report_columns")
    op.drop_table("project_report_columns")
    op.drop_index("ix_project_report_versions_status", table_name="project_report_versions")
    op.drop_index("ix_project_report_versions_project_id", table_name="project_report_versions")
    op.drop_index("ix_project_report_versions_report_id", table_name="project_report_versions")
    op.drop_table("project_report_versions")
    op.drop_index("ix_project_reports_project_id", table_name="project_reports")
    op.drop_table("project_reports")

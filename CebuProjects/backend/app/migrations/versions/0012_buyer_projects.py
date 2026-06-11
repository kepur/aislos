"""Add buyer_projects, project_files, project_ai_runs, project_line_items tables.
Add project_id and project_line_item_id to intents.

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ─── Create ENUM types ─────────────────────────────────────
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_type AS ENUM "
        "('CONSTRUCTION','SOLAR','TECH_BUILD','RENOVATION','GENERAL'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_status AS ENUM "
        "('DRAFT','COLLECTING_INFO','ANALYZING','AI_ANALYZED','READY_FOR_SOURCING',"
        "'SOURCING','ORDERING','COMPLETED','CANCELED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE quality_preference AS ENUM "
        "('BUDGET','MID_RANGE','PREMIUM','NOT_SURE'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE project_file_status AS ENUM "
        "('UPLOADED','EXTRACTED','FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE ai_run_status AS ENUM "
        "('PENDING','RUNNING','SUCCESS','FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE line_item_status AS ENUM "
        "('DRAFT','CONFIRMED','SOURCING','MATCHED','QUOTED','ORDERED','REMOVED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE line_item_source AS ENUM "
        "('AI','USER'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE quality_tier AS ENUM "
        "('BUDGET','MID_RANGE','PREMIUM'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    # ─── buyer_projects ────────────────────────────────────────
    op.create_table(
        "buyer_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("project_type", postgresql.ENUM("CONSTRUCTION", "SOLAR", "TECH_BUILD", "RENOVATION", "GENERAL",
                                                   name="project_type", create_type=False),
                  nullable=False, server_default="GENERAL"),
        sa.Column("status", postgresql.ENUM("DRAFT", "COLLECTING_INFO", "ANALYZING", "AI_ANALYZED",
                                             "READY_FOR_SOURCING", "SOURCING", "ORDERING", "COMPLETED", "CANCELED",
                                             name="project_status", create_type=False),
                  nullable=False, server_default="DRAFT"),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("area_value", sa.Float(), nullable=True),
        sa.Column("area_unit", sa.String(50), nullable=True),
        sa.Column("scale_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("budget_min", sa.Integer(), nullable=True),
        sa.Column("budget_max", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("quality_preference", postgresql.ENUM("BUDGET", "MID_RANGE", "PREMIUM", "NOT_SURE",
                                                         name="quality_preference", create_type=False),
                  nullable=False, server_default="NOT_SURE"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("missing_questions_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("assumptions_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("risk_notes_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("acceptance_criteria_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("estimated_budget_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_buyer_projects_buyer_id", "buyer_projects", ["buyer_id"])
    op.create_index("ix_buyer_projects_status", "buyer_projects", ["status"])

    # ─── project_files ─────────────────────────────────────────
    op.create_table(
        "project_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(200), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("vision_summary", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM("UPLOADED", "EXTRACTED", "FAILED",
                                             name="project_file_status", create_type=False),
                  nullable=False, server_default="UPLOADED"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_files_project_id", "project_files", ["project_id"])

    # ─── project_ai_runs ───────────────────────────────────────
    op.create_table(
        "project_ai_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("model", sa.String(200), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("status", postgresql.ENUM("PENDING", "RUNNING", "SUCCESS", "FAILED",
                                             name="ai_run_status", create_type=False),
                  nullable=False, server_default="PENDING"),
        sa.Column("input_snapshot_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("raw_output", sa.Text(), nullable=True),
        sa.Column("structured_output_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("token_usage_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_ai_runs_project_id", "project_ai_runs", ["project_id"])
    op.create_index("ix_project_ai_runs_status", "project_ai_runs", ["status"])

    # ─── project_line_items ────────────────────────────────────
    op.create_table(
        "project_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs_jsonb", postgresql.JSON(), nullable=True),
        sa.Column("qty", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(50), nullable=False, server_default="pcs"),
        sa.Column("quality_tier", postgresql.ENUM("BUDGET", "MID_RANGE", "PREMIUM",
                                                   name="quality_tier", create_type=False),
                  nullable=False, server_default="MID_RANGE"),
        sa.Column("estimated_unit_price", sa.Float(), nullable=True),
        sa.Column("estimated_total_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("sourcing_notes", sa.Text(), nullable=True),
        sa.Column("category_hint", sa.String(200), nullable=True),
        sa.Column("source", postgresql.ENUM("AI", "USER", name="line_item_source", create_type=False),
                  nullable=False, server_default="AI"),
        sa.Column("status", postgresql.ENUM("DRAFT", "CONFIRMED", "SOURCING", "MATCHED", "QUOTED", "ORDERED", "REMOVED",
                                             name="line_item_status", create_type=False),
                  nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_project_line_items_project_id", "project_line_items", ["project_id"])
    op.create_index("ix_project_line_items_status", "project_line_items", ["status"])

    # ─── Add project_id + project_line_item_id to intents ──────
    op.add_column("intents", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("intents", sa.Column("project_line_item_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_intents_project_id", "intents", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_intents_project_id", table_name="intents")
    op.drop_column("intents", "project_line_item_id")
    op.drop_column("intents", "project_id")

    op.drop_index("ix_project_line_items_status", table_name="project_line_items")
    op.drop_index("ix_project_line_items_project_id", table_name="project_line_items")
    op.drop_table("project_line_items")

    op.drop_index("ix_project_ai_runs_status", table_name="project_ai_runs")
    op.drop_index("ix_project_ai_runs_project_id", table_name="project_ai_runs")
    op.drop_table("project_ai_runs")

    op.drop_index("ix_project_files_project_id", table_name="project_files")
    op.drop_table("project_files")

    op.drop_index("ix_buyer_projects_status", table_name="buyer_projects")
    op.drop_index("ix_buyer_projects_buyer_id", table_name="buyer_projects")
    op.drop_table("buyer_projects")

    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS quality_tier"))
    conn.execute(sa.text("DROP TYPE IF EXISTS line_item_source"))
    conn.execute(sa.text("DROP TYPE IF EXISTS line_item_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ai_run_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS project_file_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS quality_preference"))
    conn.execute(sa.text("DROP TYPE IF EXISTS project_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS project_type"))

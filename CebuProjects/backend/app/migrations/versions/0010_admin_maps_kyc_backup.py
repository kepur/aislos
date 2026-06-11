"""Admin maps config, KYC analysis results, backup schedules/jobs

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE kyc_authenticity AS ENUM ('AUTHENTIC','SUSPICIOUS','FAKE'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE kyc_recommended_action AS ENUM ('APPROVE','MANUAL_REVIEW','REJECT'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE backup_frequency AS ENUM ('WEEKLY','MONTHLY','CUSTOM'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE backup_job_status AS ENUM ('PENDING','RUNNING','SUCCESS','FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "kyc_analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analyzed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_provider", sa.String(length=50), nullable=False, server_default="openai"),
        sa.Column("ai_model", sa.String(length=100), nullable=False, server_default="gpt-4o-mini"),
        sa.Column("authenticity", postgresql.ENUM("AUTHENTIC", "SUSPICIOUS", "FAKE", name="kyc_authenticity", create_type=False), nullable=False, server_default="SUSPICIOUS"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("overall_risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recommended_action", postgresql.ENUM("APPROVE", "MANUAL_REVIEW", "REJECT", name="kyc_recommended_action", create_type=False), nullable=False, server_default="MANUAL_REVIEW"),
        sa.Column("tamper_suspected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("photoshop_suspected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("text_photo_consistency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("extracted_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_issues", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("concerns", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_kyc_analysis_results_company_id", "kyc_analysis_results", ["company_id"])
    op.create_index("ix_kyc_analysis_results_document_id", "kyc_analysis_results", ["document_id"])
    op.create_index("ix_kyc_analysis_results_analyzed_by", "kyc_analysis_results", ["analyzed_by"])

    op.create_table(
        "backup_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("frequency", postgresql.ENUM("WEEKLY", "MONTHLY", "CUSTOM", name="backup_frequency", create_type=False), nullable=False, server_default="MONTHLY"),
        sa.Column("cron_expr", sa.String(length=120), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("hour", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("minute", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("retention_count", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "backup_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM("PENDING", "RUNNING", "SUCCESS", "FAILED", name="backup_job_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("archive_path", sa.Text(), nullable=True),
        sa.Column("archive_size_bytes", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_backup_jobs_schedule_id", "backup_jobs", ["schedule_id"])


def downgrade() -> None:
    op.drop_index("ix_backup_jobs_schedule_id", table_name="backup_jobs")
    op.drop_table("backup_jobs")
    op.drop_table("backup_schedules")
    op.drop_index("ix_kyc_analysis_results_analyzed_by", table_name="kyc_analysis_results")
    op.drop_index("ix_kyc_analysis_results_document_id", table_name="kyc_analysis_results")
    op.drop_index("ix_kyc_analysis_results_company_id", table_name="kyc_analysis_results")
    op.drop_table("kyc_analysis_results")

    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS backup_job_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS backup_frequency"))
    conn.execute(sa.text("DROP TYPE IF EXISTS kyc_recommended_action"))
    conn.execute(sa.text("DROP TYPE IF EXISTS kyc_authenticity"))

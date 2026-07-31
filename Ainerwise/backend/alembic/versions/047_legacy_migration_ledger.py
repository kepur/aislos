"""Add auditable historical legacy migration ledger.

Revision ID: 047
Revises: 046
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "047"
down_revision: Union[str, None] = "046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legacy_migration_runs",
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("portal_key", sa.String(length=64), nullable=False, server_default="cebu"),
        sa.Column("batch_key", sa.String(length=160), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("counts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_system", "batch_key", name="uq_legacy_migration_batch"),
    )
    op.create_index("ix_legacy_migration_runs_source_system", "legacy_migration_runs", ["source_system"])
    op.create_index("ix_legacy_migration_runs_status", "legacy_migration_runs", ["status"])

    op.create_table(
        "legacy_migration_records",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("legacy_id", sa.String(length=160), nullable=False),
        sa.Column("core_entity_type", sa.String(length=64), nullable=True),
        sa.Column("core_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=24), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["legacy_migration_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system", "entity_type", "legacy_id", name="uq_legacy_migration_object"
        ),
    )
    op.create_index("ix_legacy_migration_records_run_id", "legacy_migration_records", ["run_id"])
    op.create_index("ix_legacy_migration_records_source_system", "legacy_migration_records", ["source_system"])
    op.create_index("ix_legacy_migration_records_entity_type", "legacy_migration_records", ["entity_type"])
    op.create_index("ix_legacy_migration_records_core_entity_id", "legacy_migration_records", ["core_entity_id"])
    op.create_index("ix_legacy_migration_records_status", "legacy_migration_records", ["status"])


def downgrade() -> None:
    op.drop_table("legacy_migration_records")
    op.drop_table("legacy_migration_runs")

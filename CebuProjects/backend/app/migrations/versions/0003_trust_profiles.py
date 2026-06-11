"""Trust profiles and score events

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DO $$ BEGIN CREATE TYPE trust_entity_type AS ENUM ('USER','COMPANY'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE trust_tier AS ENUM ('BRONZE','SILVER','GOLD','PLATINUM','DIAMOND'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE trust_profile_status AS ENUM ('ACTIVE','FROZEN','HIDDEN'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE trust_score_event_type AS ENUM ('RECALCULATED','ADMIN_ADJUSTED','FROZEN','UNFROZEN'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    op.create_table(
        "trust_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", postgresql.ENUM("USER", "COMPANY", name="trust_entity_type", create_type=False), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trust_tier", postgresql.ENUM("BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", name="trust_tier", create_type=False), nullable=False, server_default="BRONZE"),
        sa.Column("profile_completion_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deal_completion_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deposit_amount_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deposit_currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("verified_deposit_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_deals_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("canceled_deals_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispute_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refund_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("late_delivery_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("late_payment_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_breakdown_json", postgresql.JSON),
        sa.Column("status", postgresql.ENUM("ACTIVE", "FROZEN", "HIDDEN", name="trust_profile_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("entity_type", "entity_id", name="uq_trust_profile_entity"),
    )
    op.create_index("ix_trust_profiles_entity_type", "trust_profiles", ["entity_type"])
    op.create_index("ix_trust_profiles_entity_id", "trust_profiles", ["entity_id"])

    op.create_table(
        "trust_score_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trust_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", postgresql.ENUM("RECALCULATED", "ADMIN_ADJUSTED", "FROZEN", "UNFROZEN", name="trust_score_event_type", create_type=False), nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("before_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("after_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(500)),
        sa.Column("related_entity_type", sa.String(50)),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trust_score_events_trust_profile_id", "trust_score_events", ["trust_profile_id"])


def downgrade() -> None:
    op.drop_table("trust_score_events")
    op.drop_table("trust_profiles")
    for enum in ["trust_score_event_type", "trust_profile_status", "trust_tier", "trust_entity_type"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

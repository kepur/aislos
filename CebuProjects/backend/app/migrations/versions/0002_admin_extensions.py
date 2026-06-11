"""Admin console extensions: new roles, new tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extend user_role enum ──────────────────────────────────────────────
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'OPS_MANAGER'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'VERIFICATION_OFFICER'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'DISPUTE_AGENT'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'FINANCE_OFFICER'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'RISK_ANALYST'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPPORT_AGENT'")

    # ── Extend user_status enum ────────────────────────────────────────────
    op.execute("ALTER TYPE user_status ADD VALUE IF NOT EXISTS 'RESTRICTED'")
    op.execute("ALTER TYPE user_status ADD VALUE IF NOT EXISTS 'BANNED'")

    # ── Add new columns to users ───────────────────────────────────────────
    op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("two_fa_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    # ── New enums ──────────────────────────────────────────────────────────
    op.execute("DO $$ BEGIN CREATE TYPE document_type AS ENUM ('BUSINESS_REGISTRATION','TAX_ID','OWNER_ID','PROOF_OF_ADDRESS','BANK_ACCOUNT','USDT_WALLET','WAREHOUSE_PHOTO','CATEGORY_LICENSE','OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE document_status AS ENUM ('PENDING','ACCEPTED','REJECTED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE verification_queue_status AS ENUM ('NOT_STARTED','SUBMITTED','IN_REVIEW','NEEDS_MORE_INFO','APPROVED_BASIC','APPROVED_BUSINESS','REJECTED','SUSPENDED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE verification_decision AS ENUM ('APPROVE_BASIC','APPROVE_BUSINESS','REQUEST_MORE_INFO','REJECT','ESCALATE_TO_RISK'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE payout_status AS ENUM ('PENDING','ON_HOLD','SCHEDULED','PROCESSING','PAID','FAILED','CANCELED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE risk_type AS ENUM ('SUSPICIOUS_PRICE_LOW','SUSPICIOUS_PRICE_HIGH','NEW_SUPPLIER_HIGH_VALUE_ORDER','HIGH_DISPUTE_RATE','REPEATED_CANCELLATION','FAILED_LOGIN_SPIKE','DEVICE_MULTI_ACCOUNT','POSSIBLE_COUNTERFEIT','PAYMENT_MISMATCH','USDT_UNCONFIRMED','MANUAL_BANK_RECEIPT_SUSPICIOUS','OFF_PLATFORM_DEAL_ATTEMPT','OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE risk_flag_status AS ENUM ('OPEN','IN_REVIEW','MITIGATED','FALSE_POSITIVE','ACTION_TAKEN','CLOSED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE note_visibility AS ENUM ('INTERNAL_ONLY','RISK_TEAM','FINANCE_TEAM'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # ── company_documents ──────────────────────────────────────────────────
    op.create_table(
        "company_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", postgresql.ENUM("BUSINESS_REGISTRATION","TAX_ID","OWNER_ID","PROOF_OF_ADDRESS","BANK_ACCOUNT","USDT_WALLET","WAREHOUSE_PHOTO","CATEGORY_LICENSE","OTHER", name="document_type", create_type=False), nullable=False),
        sa.Column("file_url", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("status", postgresql.ENUM("PENDING","ACCEPTED","REJECTED", name="document_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("reviewer_note", sa.Text),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_company_documents_company_id", "company_documents", ["company_id"])

    # ── verification_reviews ───────────────────────────────────────────────
    op.create_table(
        "verification_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("NOT_STARTED","SUBMITTED","IN_REVIEW","NEEDS_MORE_INFO","APPROVED_BASIC","APPROVED_BUSINESS","REJECTED","SUSPENDED", name="verification_queue_status", create_type=False), nullable=False, server_default="SUBMITTED"),
        sa.Column("assigned_reviewer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("decision", postgresql.ENUM("APPROVE_BASIC","APPROVE_BUSINESS","REQUEST_MORE_INFO","REJECT","ESCALATE_TO_RISK", name="verification_decision", create_type=False)),
        sa.Column("decision_reason", sa.String(500)),
        sa.Column("internal_note", sa.Text),
        sa.Column("user_facing_note", sa.Text),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_verification_reviews_company_id", "verification_reviews", ["company_id"])

    # ── payment_events ─────────────────────────────────────────────────────
    op.create_table(
        "payment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_event_id", sa.String(255)),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True)),
        sa.Column("escrow_id", postgresql.UUID(as_uuid=True)),
        sa.Column("amount_minor", sa.Integer),
        sa.Column("currency", sa.String(10)),
        sa.Column("status", sa.String(50), nullable=False, server_default="RECEIVED"),
        sa.Column("error_message", sa.Text),
        sa.Column("raw_payload", postgresql.JSON),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_payment_events_provider", "payment_events", ["provider"])
    op.create_index("ix_payment_events_order_id", "payment_events", ["order_id"])

    # ── payouts ────────────────────────────────────────────────────────────
    op.create_table(
        "payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escrow_id", postgresql.UUID(as_uuid=True)),
        sa.Column("amount_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="PHP"),
        sa.Column("provider", sa.String(50), nullable=False, server_default="SIMULATED"),
        sa.Column("destination", sa.String(255)),
        sa.Column("status", postgresql.ENUM("PENDING","ON_HOLD","SCHEDULED","PROCESSING","PAID","FAILED","CANCELED", name="payout_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("risk_hold", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("provider_reference", sa.String(255)),
        sa.Column("failure_reason", sa.Text),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payouts_company_id", "payouts", ["company_id"])
    op.create_index("ix_payouts_order_id", "payouts", ["order_id"])

    # ── risk_flags ─────────────────────────────────────────────────────────
    op.create_table(
        "risk_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_type", postgresql.ENUM("SUSPICIOUS_PRICE_LOW","SUSPICIOUS_PRICE_HIGH","NEW_SUPPLIER_HIGH_VALUE_ORDER","HIGH_DISPUTE_RATE","REPEATED_CANCELLATION","FAILED_LOGIN_SPIKE","DEVICE_MULTI_ACCOUNT","POSSIBLE_COUNTERFEIT","PAYMENT_MISMATCH","USDT_UNCONFIRMED","MANUAL_BANK_RECEIPT_SUSPICIOUS","OFF_PLATFORM_DEAL_ATTEMPT","OTHER", name="risk_type", create_type=False), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", postgresql.ENUM("OPEN","IN_REVIEW","MITIGATED","FALSE_POSITIVE","ACTION_TAKEN","CLOSED", name="risk_flag_status", create_type=False), nullable=False, server_default="OPEN"),
        sa.Column("description", sa.Text),
        sa.Column("assigned_analyst_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action_taken", sa.Text),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_flags_entity_type", "risk_flags", ["entity_type"])
    op.create_index("ix_risk_flags_entity_id", "risk_flags", ["entity_id"])

    # ── admin_notes ────────────────────────────────────────────────────────
    op.create_table(
        "admin_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visibility", postgresql.ENUM("INTERNAL_ONLY","RISK_TEAM","FINANCE_TEAM", name="note_visibility", create_type=False), nullable=False, server_default="INTERNAL_ONLY"),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_admin_notes_entity_type", "admin_notes", ["entity_type"])
    op.create_index("ix_admin_notes_entity_id", "admin_notes", ["entity_id"])

    # ── notification_templates ─────────────────────────────────────────────
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_key", sa.String(100), unique=True, nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("subject", sa.String(500)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("variables_hint", sa.Text),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_templates_key", "notification_templates", ["template_key"])

    # ── platform_settings ──────────────────────────────────────────────────
    op.create_table(
        "platform_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("description", sa.String(500)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_platform_settings_key", "platform_settings", ["key"])


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_table("notification_templates")
    op.drop_table("admin_notes")
    op.drop_table("risk_flags")
    op.drop_table("payouts")
    op.drop_table("payment_events")
    op.drop_table("verification_reviews")
    op.drop_table("company_documents")

    op.drop_column("users", "last_login_at")
    op.drop_column("users", "two_fa_enabled")
    op.drop_column("users", "totp_secret")

    for enum in ["note_visibility", "risk_flag_status", "risk_type", "payout_status",
                 "verification_decision", "verification_queue_status", "document_status", "document_type"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

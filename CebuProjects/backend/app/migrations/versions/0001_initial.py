"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums — use DO block so re-runs are idempotent
    def _create_enum(name: str, values: str) -> None:
        op.execute(f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    _create_enum("user_role", "'BUYER','SUPPLIER_ADMIN','SUPPLIER_AGENT','ADMIN','AUDITOR'")
    _create_enum("user_status", "'ACTIVE','PENDING','SUSPENDED','DELETED'")
    _create_enum("verification_level", "'UNVERIFIED','BASIC','BUSINESS','TRUSTED'")
    _create_enum("company_status", "'PENDING','ACTIVE','RESTRICTED','SUSPENDED'")
    _create_enum("branch_status", "'ACTIVE','INACTIVE'")
    _create_enum("category_status", "'ACTIVE','INACTIVE'")
    _create_enum("catalog_item_status", "'DRAFT','ACTIVE','INACTIVE','OUT_OF_STOCK'")
    _create_enum("intent_status", "'DRAFT','ACTIVE','AWARDED','EXPIRED','CANCELED'")
    _create_enum("offer_tier", "'GOOD','BETTER','BEST','CUSTOM'")
    _create_enum("stock_confidence", "'FIRM','BACKORDER','UNKNOWN'")
    _create_enum("offer_status", "'SUBMITTED','WITHDRAWN','EXPIRED','AWARDED','REJECTED'")
    _create_enum("order_status", "'CREATED','AWAITING_PAYMENT','PAID_IN_ESCROW','IN_PROGRESS','DELIVERED','ACCEPTED','PAYOUT_RELEASED','DISPUTED','CANCELED','REFUNDED'")
    _create_enum("escrow_provider", "'SIMULATED','PAYMONGO','XENDIT','STRIPE'")
    _create_enum("escrow_status", "'AUTH_PENDING','AUTH_HELD','CAPTURED','RELEASED','REFUNDED','CHARGEBACK','FAILED'")
    _create_enum("delivery_status", "'PENDING','READY_FOR_PICKUP','DISPATCHED','DELIVERED','ACCEPTED','FAILED'")
    _create_enum("dispute_status", "'OPENED','WAITING_BUYER_EVIDENCE','WAITING_SUPPLIER_EVIDENCE','UNDER_REVIEW','RESOLVED_REFUND','RESOLVED_RELEASE','RESOLVED_PARTIAL_REFUND','ESCALATED','CANCELED'")
    _create_enum("notification_channel", "'IN_APP','EMAIL','TELEGRAM'")
    _create_enum("notification_status", "'PENDING','SENT','FAILED','READ'")
    _create_enum("risk_level", "'LOW','MEDIUM','HIGH','CRITICAL'")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("BUYER","SUPPLIER_ADMIN","SUPPLIER_AGENT","ADMIN","AUDITOR", name="user_role", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM("ACTIVE","PENDING","SUSPENDED","DELETED", name="user_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(512)),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_id", sa.String(100)),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("city", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("verification_level", postgresql.ENUM("UNVERIFIED","BASIC","BUSINESS","TRUSTED", name="verification_level", create_type=False), nullable=False, server_default="UNVERIFIED"),
        sa.Column("status", postgresql.ENUM("PENDING","ACTIVE","RESTRICTED","SUSPENDED", name="company_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("kyb_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_companies_owner_user_id", "companies", ["owner_user_id"])

    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("radius_km", sa.Integer, server_default="30"),
        sa.Column("delivery_methods", postgresql.JSON),
        sa.Column("status", postgresql.ENUM("ACTIVE","INACTIVE", name="branch_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_branches_company_id", "branches", ["company_id"])

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("schema_json", postgresql.JSON),
        sa.Column("status", postgresql.ENUM("ACTIVE","INACTIVE", name="category_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])

    op.create_table(
        "catalog_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("attrs_jsonb", postgresql.JSON),
        sa.Column("price_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(10), server_default="PHP"),
        sa.Column("stock_qty", sa.Integer, server_default="0"),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("images", postgresql.JSON),
        sa.Column("tags", postgresql.ARRAY(sa.String)),
        sa.Column("status", postgresql.ENUM("DRAFT","ACTIVE","INACTIVE","OUT_OF_STOCK", name="catalog_item_status", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_catalog_items_company_id", "catalog_items", ["company_id"])
    op.create_index("ix_catalog_items_category_id", "catalog_items", ["category_id"])

    op.create_table(
        "intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("attrs_jsonb", postgresql.JSON),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("budget_min_minor", sa.Integer),
        sa.Column("budget_max_minor", sa.Integer),
        sa.Column("currency", sa.String(10), server_default="PHP"),
        sa.Column("country", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("radius_km", sa.Integer, server_default="30"),
        sa.Column("delivery_window_start", sa.DateTime(timezone=True)),
        sa.Column("delivery_window_end", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("attachments", postgresql.JSON),
        sa.Column("status", postgresql.ENUM("DRAFT","ACTIVE","AWARDED","EXPIRED","CANCELED", name="intent_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_intents_buyer_id", "intents", ["buyer_id"])
    op.create_index("ix_intents_category_id", "intents", ["category_id"])

    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True)),
        sa.Column("supplier_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_price_minor", sa.Integer, nullable=False),
        sa.Column("qty_available", sa.Integer, nullable=False),
        sa.Column("delivery_fee_minor", sa.Integer, server_default="0"),
        sa.Column("total_price_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(10), server_default="PHP"),
        sa.Column("eta_date", sa.DateTime(timezone=True)),
        sa.Column("warranty", sa.Text),
        sa.Column("tier", postgresql.ENUM("GOOD","BETTER","BEST","CUSTOM", name="offer_tier", create_type=False), nullable=False),
        sa.Column("stock_confidence", postgresql.ENUM("FIRM","BACKORDER","UNKNOWN", name="stock_confidence", create_type=False), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("status", postgresql.ENUM("SUBMITTED","WITHDRAWN","EXPIRED","AWARDED","REJECTED", name="offer_status", create_type=False), nullable=False, server_default="SUBMITTED"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_offers_intent_id", "offers", ["intent_id"])
    op.create_index("ix_offers_company_id", "offers", ["company_id"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("offer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("total_amount_minor", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(10), server_default="PHP"),
        sa.Column("status", postgresql.ENUM("CREATED","AWAITING_PAYMENT","PAID_IN_ESCROW","IN_PROGRESS","DELIVERED","ACCEPTED","PAYOUT_RELEASED","DISPUTED","CANCELED","REFUNDED", name="order_status", create_type=False), nullable=False, server_default="CREATED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_offer_id", "orders", ["offer_id"])
    op.create_index("ix_orders_intent_id", "orders", ["intent_id"])
    op.create_index("ix_orders_buyer_id", "orders", ["buyer_id"])

    op.create_table(
        "escrow_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column("provider", postgresql.ENUM("SIMULATED","PAYMONGO","XENDIT","STRIPE", name="escrow_provider", create_type=False), nullable=False),
        sa.Column("provider_reference", sa.String(255)),
        sa.Column("auth_amount_minor", sa.Integer, nullable=False),
        sa.Column("captured_amount_minor", sa.Integer, server_default="0"),
        sa.Column("released_amount_minor", sa.Integer, server_default="0"),
        sa.Column("refunded_amount_minor", sa.Integer, server_default="0"),
        sa.Column("currency", sa.String(10), server_default="PHP"),
        sa.Column("status", postgresql.ENUM("AUTH_PENDING","AUTH_HELD","CAPTURED","RELEASED","REFUNDED","CHARGEBACK","FAILED", name="escrow_status", create_type=False), nullable=False),
        sa.Column("raw_event_json", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_escrow_transactions_order_id", "escrow_transactions", ["order_id"])

    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING","READY_FOR_PICKUP","DISPATCHED","DELIVERED","ACCEPTED","FAILED", name="delivery_status", create_type=False), nullable=False),
        sa.Column("carrier", sa.String(255)),
        sa.Column("tracking_number", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("proofs", postgresql.JSON),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_deliveries_order_id", "deliveries", ["order_id"])

    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opened_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("status", postgresql.ENUM("OPENED","WAITING_BUYER_EVIDENCE","WAITING_SUPPLIER_EVIDENCE","UNDER_REVIEW","RESOLVED_REFUND","RESOLVED_RELEASE","RESOLVED_PARTIAL_REFUND","ESCALATED","CANCELED", name="dispute_status", create_type=False), nullable=False, server_default="OPENED"),
        sa.Column("evidence_json", postgresql.JSON),
        sa.Column("admin_notes", sa.Text),
        sa.Column("resolution", sa.Text),
        sa.Column("refund_amount_minor", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_disputes_order_id", "disputes", ["order_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_type", sa.String(50), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("attachments", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", postgresql.ENUM("IN_APP","EMAIL","TELEGRAM", name="notification_channel", create_type=False), nullable=False),
        sa.Column("notification_type", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(500)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING","SENT","FAILED","READ", name="notification_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("provider_response", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_role", sa.String(50)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("before_json", postgresql.JSON),
        sa.Column("after_json", postgresql.JSON),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("user_agent", sa.Text),
        sa.Column("risk_level", postgresql.ENUM("LOW","MEDIUM","HIGH","CRITICAL", name="risk_level", create_type=False), nullable=False, server_default="LOW"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("disputes")
    op.drop_table("deliveries")
    op.drop_table("escrow_transactions")
    op.drop_table("orders")
    op.drop_table("offers")
    op.drop_table("intents")
    op.drop_table("catalog_items")
    op.drop_table("categories")
    op.drop_table("branches")
    op.drop_table("companies")
    op.drop_table("users")

    for enum in [
        "risk_level", "notification_status", "notification_channel",
        "dispute_status", "delivery_status", "escrow_status", "escrow_provider",
        "order_status", "offer_status", "stock_confidence", "offer_tier",
        "intent_status", "catalog_item_status", "category_status",
        "branch_status", "company_status", "verification_level",
        "user_status", "user_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

"""Payment region configs, FX quotes, fee rules, payment intents

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str = "0010"
branch_labels = None
depends_on = None


def _jsonb_default(value: str):
    return sa.text(f"'{value}'::jsonb")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE transaction_currency_mode AS ENUM "
        "('LOCAL_ONLY','USD_BRIDGE','BUYER_LOCAL_TO_SUPPLIER_LOCAL','ORDER_CURRENCY_FIXED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE payment_fee_type AS ENUM "
        "('PROVIDER_FEE','PLATFORM_SERVICE_FEE','CROSS_BORDER_FEE','FX_FEE','PLATFORM_FX_MARKUP','SETTLEMENT_FEE','NETWORK_FEE','MANUAL_REVIEW_FEE'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE payment_quote_status AS ENUM "
        "('ACTIVE','CONFIRMED','EXPIRED','CANCELED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE payment_intent_status AS ENUM "
        "('CREATED','PENDING','SUCCEEDED','FAILED','CANCELED','REFUNDED','CHARGEBACK'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE settlement_event_status AS ENUM "
        "('RECEIVED','MATCHED','ADJUSTED','FAILED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "region_payment_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("country_name", sa.String(length=120), nullable=False),
        sa.Column("local_currency", sa.String(length=10), nullable=False),
        sa.Column("default_settlement_currency", sa.String(length=10), nullable=False),
        sa.Column("default_transaction_mode", postgresql.ENUM("LOCAL_ONLY", "USD_BRIDGE", "BUYER_LOCAL_TO_SUPPLIER_LOCAL", "ORDER_CURRENCY_FIXED", name="transaction_currency_mode", create_type=False), nullable=False, server_default="LOCAL_ONLY"),
        sa.Column("enabled_currencies", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default("[]")),
        sa.Column("enabled_payment_methods", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default("[]")),
        sa.Column("cross_border_currencies", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default("[]")),
        sa.Column("force_usd_bridge", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allow_supplier_payout_currency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_region_payment_configs_country_code", "region_payment_configs", ["country_code"], unique=True)
    op.create_index("ix_region_payment_configs_local_currency", "region_payment_configs", ["local_currency"])
    op.create_index("ix_region_payment_configs_is_active", "region_payment_configs", ["is_active"])

    op.create_table(
        "currency_configs",
        sa.Column("code", sa.String(length=10), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("minor_unit", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_fiat", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_currency_configs_is_enabled", "currency_configs", ["is_enabled"])

    op.create_table(
        "payment_method_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("method_code", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="SIMULATED"),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_payment_method_configs_country_code", "payment_method_configs", ["country_code"])
    op.create_index("ix_payment_method_configs_method_code", "payment_method_configs", ["method_code"])
    op.create_index("ix_payment_method_configs_currency", "payment_method_configs", ["currency"])
    op.create_index("ix_payment_method_configs_is_enabled", "payment_method_configs", ["is_enabled"])

    op.create_table(
        "fee_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("fee_type", postgresql.ENUM("PROVIDER_FEE", "PLATFORM_SERVICE_FEE", "CROSS_BORDER_FEE", "FX_FEE", "PLATFORM_FX_MARKUP", "SETTLEMENT_FEE", "NETWORK_FEE", "MANUAL_REVIEW_FEE", name="payment_fee_type", create_type=False), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="PHP"),
        sa.Column("fixed_fee_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("variable_bps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_fee_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_fee_minor", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_fee_rules_country_code", "fee_rules", ["country_code"])
    op.create_index("ix_fee_rules_payment_method", "fee_rules", ["payment_method"])
    op.create_index("ix_fee_rules_fee_type", "fee_rules", ["fee_type"])
    op.create_index("ix_fee_rules_is_enabled", "fee_rules", ["is_enabled"])

    op.create_table(
        "fx_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_currency", sa.String(length=10), nullable=False),
        sa.Column("target_currency", sa.String(length=10), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("rate_source", sa.String(length=80), nullable=False, server_default="SIMULATED_RATE_TABLE"),
        sa.Column("provider_quote_id", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_fx_quotes_source_currency", "fx_quotes", ["source_currency"])
    op.create_index("ix_fx_quotes_target_currency", "fx_quotes", ["target_currency"])
    op.create_index("ix_fx_quotes_expires_at", "fx_quotes", ["expires_at"])

    op.create_table(
        "payment_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("buyer_country", sa.String(length=2), nullable=False),
        sa.Column("supplier_country", sa.String(length=2), nullable=False),
        sa.Column("mode", postgresql.ENUM("LOCAL_ONLY", "USD_BRIDGE", "BUYER_LOCAL_TO_SUPPLIER_LOCAL", "ORDER_CURRENCY_FIXED", name="transaction_currency_mode", create_type=False), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("order_currency", sa.String(length=10), nullable=False),
        sa.Column("payer_currency", sa.String(length=10), nullable=False),
        sa.Column("settlement_currency", sa.String(length=10), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("payer_total_minor", sa.Integer(), nullable=False),
        sa.Column("escrow_amount_minor", sa.Integer(), nullable=False),
        sa.Column("supplier_estimated_net_minor", sa.Integer(), nullable=False),
        sa.Column("platform_revenue_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rate", sa.Numeric(18, 8), nullable=True),
        sa.Column("rate_source", sa.String(length=80), nullable=True),
        sa.Column("fx_quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", postgresql.ENUM("ACTIVE", "CONFIRMED", "EXPIRED", "CANCELED", name="payment_quote_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_payment_quotes_buyer_country", "payment_quotes", ["buyer_country"])
    op.create_index("ix_payment_quotes_supplier_country", "payment_quotes", ["supplier_country"])
    op.create_index("ix_payment_quotes_mode", "payment_quotes", ["mode"])
    op.create_index("ix_payment_quotes_payment_method", "payment_quotes", ["payment_method"])
    op.create_index("ix_payment_quotes_fx_quote_id", "payment_quotes", ["fx_quote_id"])
    op.create_index("ix_payment_quotes_expires_at", "payment_quotes", ["expires_at"])
    op.create_index("ix_payment_quotes_status", "payment_quotes", ["status"])

    op.create_table(
        "payment_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="SIMULATED"),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", postgresql.ENUM("CREATED", "PENDING", "SUCCEEDED", "FAILED", "CANCELED", "REFUNDED", "CHARGEBACK", name="payment_intent_status", create_type=False), nullable=False, server_default="CREATED"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_payment_intents_quote_id", "payment_intents", ["quote_id"])
    op.create_index("ix_payment_intents_order_id", "payment_intents", ["order_id"])
    op.create_index("ix_payment_intents_provider_reference", "payment_intents", ["provider_reference"])
    op.create_index("ix_payment_intents_status", "payment_intents", ["status"])

    op.create_table(
        "fee_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fee_type", postgresql.ENUM("PROVIDER_FEE", "PLATFORM_SERVICE_FEE", "CROSS_BORDER_FEE", "FX_FEE", "PLATFORM_FX_MARKUP", "SETTLEMENT_FEE", "NETWORK_FEE", "MANUAL_REVIEW_FEE", name="payment_fee_type", create_type=False), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("refundable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_fee_line_items_quote_id", "fee_line_items", ["quote_id"])
    op.create_index("ix_fee_line_items_payment_intent_id", "fee_line_items", ["payment_intent_id"])
    op.create_index("ix_fee_line_items_fee_type", "fee_line_items", ["fee_type"])

    op.create_table(
        "settlement_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("gross_amount_minor", sa.Integer(), nullable=False),
        sa.Column("fee_amount_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", postgresql.ENUM("RECEIVED", "MATCHED", "ADJUSTED", "FAILED", name="settlement_event_status", create_type=False), nullable=False, server_default="RECEIVED"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=_jsonb_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_settlement_events_payment_intent_id", "settlement_events", ["payment_intent_id"])
    op.create_index("ix_settlement_events_provider", "settlement_events", ["provider"])
    op.create_index("ix_settlement_events_provider_reference", "settlement_events", ["provider_reference"])
    op.create_index("ix_settlement_events_status", "settlement_events", ["status"])

    op.create_table(
        "settlement_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("settlement_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adjustment_type", sa.String(length=80), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_settlement_adjustments_settlement_event_id", "settlement_adjustments", ["settlement_event_id"])
    op.create_index("ix_settlement_adjustments_adjustment_type", "settlement_adjustments", ["adjustment_type"])

    op.add_column("wallet_deposits", sa.Column("provider", sa.String(length=50), nullable=False, server_default="MANUAL_BANK"))
    op.add_column("wallet_deposits", sa.Column("payment_method", sa.String(length=50), nullable=False, server_default="PHP_MANUAL_BANK"))
    op.add_column("wallet_deposits", sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("wallet_deposits", sa.Column("source_currency", sa.String(length=10), nullable=True))
    op.add_column("wallet_deposits", sa.Column("target_currency", sa.String(length=10), nullable=True))
    op.create_index("ix_wallet_deposits_quote_id", "wallet_deposits", ["quote_id"])

    op.execute(sa.text("""
        INSERT INTO currency_configs (code, name, minor_unit, is_fiat, is_enabled)
        VALUES
          ('PHP','Philippine Peso',2,true,true),
          ('USD','US Dollar',2,true,true),
          ('JPY','Japanese Yen',0,true,true),
          ('SGD','Singapore Dollar',2,true,true),
          ('USDT','Tether USD',2,false,false),
          ('USDC','USD Coin',2,false,false)
        ON CONFLICT (code) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO region_payment_configs
          (id, country_code, country_name, local_currency, default_settlement_currency, default_transaction_mode,
           enabled_currencies, enabled_payment_methods, cross_border_currencies, force_usd_bridge, allow_supplier_payout_currency, is_active)
        VALUES
          (gen_random_uuid(), 'PH', 'Philippines', 'PHP', 'PHP', 'LOCAL_ONLY',
           '["PHP"]'::jsonb,
           '["PHP_CARD","PHP_EWALLET","PHP_BANK_TRANSFER","PHP_MANUAL_BANK","PHP_WALLET_BALANCE"]'::jsonb,
           '["USD"]'::jsonb, false, false, true),
          (gen_random_uuid(), 'US', 'United States', 'USD', 'USD', 'LOCAL_ONLY',
           '["USD"]'::jsonb,
           '["USD_CARD","USD_BANK_TRANSFER","USD_WALLET_BALANCE"]'::jsonb,
           '["USD"]'::jsonb, false, false, true),
          (gen_random_uuid(), 'JP', 'Japan', 'JPY', 'JPY', 'LOCAL_ONLY',
           '["JPY"]'::jsonb,
           '["JPY_CARD","JPY_BANK_TRANSFER","JPY_WALLET_BALANCE"]'::jsonb,
           '["USD"]'::jsonb, false, false, true),
          (gen_random_uuid(), 'SG', 'Singapore', 'SGD', 'SGD', 'LOCAL_ONLY',
           '["SGD"]'::jsonb,
           '["SGD_CARD","SGD_BANK_TRANSFER","SGD_WALLET_BALANCE"]'::jsonb,
           '["USD"]'::jsonb, false, false, true)
        ON CONFLICT (country_code) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO payment_method_configs (id, country_code, method_code, provider, currency, is_enabled, config_json)
        VALUES
          (gen_random_uuid(), 'PH', 'PHP_CARD', 'PAYMONGO', 'PHP', true, '{"capture":"manual"}'::jsonb),
          (gen_random_uuid(), 'PH', 'PHP_EWALLET', 'PAYMONGO', 'PHP', true, '{"channels":["gcash","maya"]}'::jsonb),
          (gen_random_uuid(), 'PH', 'PHP_BANK_TRANSFER', 'MANUAL_BANK', 'PHP', true, '{"requires_review": true}'::jsonb),
          (gen_random_uuid(), 'PH', 'PHP_MANUAL_BANK', 'MANUAL_BANK', 'PHP', true, '{"requires_review": true}'::jsonb),
          (gen_random_uuid(), 'PH', 'PHP_WALLET_BALANCE', 'INTERNAL_WALLET', 'PHP', true, '{}'::jsonb)
    """))
    op.execute(sa.text("""
        INSERT INTO fee_rules (id, name, country_code, payment_method, fee_type, currency, fixed_fee_minor, variable_bps, min_fee_minor, max_fee_minor, is_enabled)
        VALUES
          (gen_random_uuid(), 'PH card provider fee', 'PH', 'PHP_CARD', 'PROVIDER_FEE', 'PHP', 1500, 290, 0, null, true),
          (gen_random_uuid(), 'PH e-wallet provider fee', 'PH', 'PHP_EWALLET', 'PROVIDER_FEE', 'PHP', 1000, 250, 0, null, true),
          (gen_random_uuid(), 'PH bank transfer provider fee', 'PH', 'PHP_BANK_TRANSFER', 'PROVIDER_FEE', 'PHP', 1000, 100, 0, null, true),
          (gen_random_uuid(), 'PH manual bank provider fee', 'PH', 'PHP_MANUAL_BANK', 'PROVIDER_FEE', 'PHP', 0, 0, 0, null, true),
          (gen_random_uuid(), 'PH platform service fee', 'PH', null, 'PLATFORM_SERVICE_FEE', 'PHP', 0, 200, 0, null, true)
    """))


def downgrade() -> None:
    op.drop_index("ix_wallet_deposits_quote_id", table_name="wallet_deposits")
    op.drop_column("wallet_deposits", "target_currency")
    op.drop_column("wallet_deposits", "source_currency")
    op.drop_column("wallet_deposits", "quote_id")
    op.drop_column("wallet_deposits", "payment_method")
    op.drop_column("wallet_deposits", "provider")

    op.drop_index("ix_settlement_adjustments_adjustment_type", table_name="settlement_adjustments")
    op.drop_index("ix_settlement_adjustments_settlement_event_id", table_name="settlement_adjustments")
    op.drop_table("settlement_adjustments")
    op.drop_index("ix_settlement_events_status", table_name="settlement_events")
    op.drop_index("ix_settlement_events_provider_reference", table_name="settlement_events")
    op.drop_index("ix_settlement_events_provider", table_name="settlement_events")
    op.drop_index("ix_settlement_events_payment_intent_id", table_name="settlement_events")
    op.drop_table("settlement_events")
    op.drop_index("ix_fee_line_items_fee_type", table_name="fee_line_items")
    op.drop_index("ix_fee_line_items_payment_intent_id", table_name="fee_line_items")
    op.drop_index("ix_fee_line_items_quote_id", table_name="fee_line_items")
    op.drop_table("fee_line_items")
    op.drop_index("ix_payment_intents_status", table_name="payment_intents")
    op.drop_index("ix_payment_intents_provider_reference", table_name="payment_intents")
    op.drop_index("ix_payment_intents_order_id", table_name="payment_intents")
    op.drop_index("ix_payment_intents_quote_id", table_name="payment_intents")
    op.drop_table("payment_intents")
    op.drop_index("ix_payment_quotes_status", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_expires_at", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_fx_quote_id", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_payment_method", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_mode", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_supplier_country", table_name="payment_quotes")
    op.drop_index("ix_payment_quotes_buyer_country", table_name="payment_quotes")
    op.drop_table("payment_quotes")
    op.drop_index("ix_fx_quotes_expires_at", table_name="fx_quotes")
    op.drop_index("ix_fx_quotes_target_currency", table_name="fx_quotes")
    op.drop_index("ix_fx_quotes_source_currency", table_name="fx_quotes")
    op.drop_table("fx_quotes")
    op.drop_index("ix_fee_rules_is_enabled", table_name="fee_rules")
    op.drop_index("ix_fee_rules_fee_type", table_name="fee_rules")
    op.drop_index("ix_fee_rules_payment_method", table_name="fee_rules")
    op.drop_index("ix_fee_rules_country_code", table_name="fee_rules")
    op.drop_table("fee_rules")
    op.drop_index("ix_payment_method_configs_is_enabled", table_name="payment_method_configs")
    op.drop_index("ix_payment_method_configs_currency", table_name="payment_method_configs")
    op.drop_index("ix_payment_method_configs_method_code", table_name="payment_method_configs")
    op.drop_index("ix_payment_method_configs_country_code", table_name="payment_method_configs")
    op.drop_table("payment_method_configs")
    op.drop_index("ix_currency_configs_is_enabled", table_name="currency_configs")
    op.drop_table("currency_configs")
    op.drop_index("ix_region_payment_configs_is_active", table_name="region_payment_configs")
    op.drop_index("ix_region_payment_configs_local_currency", table_name="region_payment_configs")
    op.drop_index("ix_region_payment_configs_country_code", table_name="region_payment_configs")
    op.drop_table("region_payment_configs")

    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS settlement_event_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS payment_intent_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS payment_quote_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS payment_fee_type"))
    conn.execute(sa.text("DROP TYPE IF EXISTS transaction_currency_mode"))

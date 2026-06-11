"""P0 wallets, deposits, maps, regions, service areas

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DO $$ BEGIN CREATE TYPE wallet_status AS ENUM ('ACTIVE','FROZEN','CLOSED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE wallet_transaction_type AS ENUM ('DEPOSIT_INTENT_CREATED','DEPOSIT_TX_SUBMITTED','DEPOSIT_VERIFIED','DEPOSIT_REJECTED','ESCROW_LOCK','ESCROW_RELEASE','ESCROW_REFUND','ADMIN_ADJUSTMENT'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE deposit_status AS ENUM ('PENDING_TX','SUBMITTED','UNDER_REVIEW','VERIFIED','REJECTED','EXPIRED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE region_status AS ENUM ('ACTIVE','INACTIVE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE region_type AS ENUM ('COUNTRY','CITY','DISTRICT','BUSINESS_AREA'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE coverage_type AS ENUM ('RADIUS','POLYGON','ADMIN_REGION'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE service_area_status AS ENUM ('ACTIVE','INACTIVE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("available_balance_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_balance_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_deposited_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", postgresql.ENUM("ACTIVE", "FROZEN", "CLOSED", name="wallet_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "currency", name="uq_wallet_owner_currency"),
    )
    op.create_index("ix_wallets_owner_user_id", "wallets", ["owner_user_id"])
    op.create_index("ix_wallets_currency", "wallets", ["currency"])

    op.create_table(
        "wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tx_type", postgresql.ENUM("DEPOSIT_INTENT_CREATED", "DEPOSIT_TX_SUBMITTED", "DEPOSIT_VERIFIED", "DEPOSIT_REJECTED", "ESCROW_LOCK", "ESCROW_RELEASE", "ESCROW_REFUND", "ADMIN_ADJUSTMENT", name="wallet_transaction_type", create_type=False), nullable=False),
        sa.Column("amount_delta_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_balance_after_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_balance_after_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("reference_type", sa.String(50)),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("note", sa.Text()),
        sa.Column("metadata_json", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_wallet_transactions_wallet_id", "wallet_transactions", ["wallet_id"])
    op.create_index("ix_wallet_transactions_owner_user_id", "wallet_transactions", ["owner_user_id"])
    op.create_index("ix_wallet_transactions_tx_type", "wallet_transactions", ["tx_type"])

    op.create_table(
        "wallet_deposits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("network", sa.String(50), nullable=False, server_default="TRC20"),
        sa.Column("deposit_address", sa.String(255), nullable=False),
        sa.Column("tx_hash", sa.String(255)),
        sa.Column("confirmations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", postgresql.ENUM("PENDING_TX", "SUBMITTED", "UNDER_REVIEW", "VERIFIED", "REJECTED", "EXPIRED", name="deposit_status", create_type=False), nullable=False, server_default="PENDING_TX"),
        sa.Column("submitter_note", sa.Text()),
        sa.Column("admin_note", sa.Text()),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_wallet_deposits_wallet_id", "wallet_deposits", ["wallet_id"])
    op.create_index("ix_wallet_deposits_owner_user_id", "wallet_deposits", ["owner_user_id"])
    op.create_index("ix_wallet_deposits_status", "wallet_deposits", ["status"])
    op.create_index("ix_wallet_deposits_tx_hash", "wallet_deposits", ["tx_hash"])

    op.create_table(
        "regions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False, server_default="Philippines"),
        sa.Column("city", sa.String(100)),
        sa.Column("region_type", postgresql.ENUM("COUNTRY", "CITY", "DISTRICT", "BUSINESS_AREA", name="region_type", create_type=False), nullable=False, server_default="CITY"),
        sa.Column("center_lat", sa.Float()),
        sa.Column("center_lng", sa.Float()),
        sa.Column("default_radius_km", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("polygon_json", postgresql.JSON),
        sa.Column("provider_place_id", sa.String(255)),
        sa.Column("status", postgresql.ENUM("ACTIVE", "INACTIVE", name="region_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", name="uq_regions_slug"),
    )
    op.create_index("ix_regions_name", "regions", ["name"])
    op.create_index("ix_regions_slug", "regions", ["slug"])

    op.create_table(
        "service_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True)),
        sa.Column("coverage_type", postgresql.ENUM("RADIUS", "POLYGON", "ADMIN_REGION", name="coverage_type", create_type=False), nullable=False, server_default="RADIUS"),
        sa.Column("center_lat", sa.Float()),
        sa.Column("center_lng", sa.Float()),
        sa.Column("radius_km", sa.Integer()),
        sa.Column("polygon_json", postgresql.JSON),
        sa.Column("status", postgresql.ENUM("ACTIVE", "INACTIVE", name="service_area_status", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_service_areas_name", "service_areas", ["name"])
    op.create_index("ix_service_areas_region_id", "service_areas", ["region_id"])
    op.create_index("ix_service_areas_company_id", "service_areas", ["company_id"])

    op.execute(
        """
        INSERT INTO regions (id, name, slug, country, city, region_type, center_lat, center_lng, default_radius_km, status, created_at, updated_at)
        VALUES
          ('00000000-0000-4000-8000-000000000101', 'Cebu City', 'cebu-city', 'Philippines', 'Cebu City', 'CITY', 10.3157, 123.8854, 20, 'ACTIVE', now(), now()),
          ('00000000-0000-4000-8000-000000000102', 'Mandaue City', 'mandaue-city', 'Philippines', 'Mandaue City', 'CITY', 10.3333, 123.9333, 15, 'ACTIVE', now(), now()),
          ('00000000-0000-4000-8000-000000000103', 'Lapu-Lapu City', 'lapu-lapu-city', 'Philippines', 'Lapu-Lapu City', 'CITY', 10.3103, 123.9494, 15, 'ACTIVE', now(), now())
        ON CONFLICT (slug) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("service_areas")
    op.drop_table("regions")
    op.drop_table("wallet_deposits")
    op.drop_table("wallet_transactions")
    op.drop_table("wallets")
    for enum in [
        "service_area_status",
        "coverage_type",
        "region_type",
        "region_status",
        "deposit_status",
        "wallet_transaction_type",
        "wallet_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

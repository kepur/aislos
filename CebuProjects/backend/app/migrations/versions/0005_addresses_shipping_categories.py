"""addresses, shipping, category enhancements

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PgENUM

revision: str = "0005"
down_revision: str = "0004"
branch_labels = None
depends_on = None


# Define PostgreSQL ENUMs with create_type=False (we create them manually first)
address_type_enum = PgENUM(
    "SHIPPING_FROM", "DELIVERY_TO", "WAREHOUSE", "BILLING",
    name="address_type", create_type=False
)
address_status_enum = PgENUM(
    "ACTIVE", "DELETED",
    name="address_status", create_type=False
)
shipping_method_enum = PgENUM(
    "SEA_FREIGHT", "AIR_FREIGHT", "EXPRESS", "LAND_FREIGHT", "LOCAL_DELIVERY", "SELF_PICKUP",
    name="shipping_method", create_type=False
)
shipping_route_status_enum = PgENUM(
    "ACTIVE", "INACTIVE",
    name="shipping_route_status", create_type=False
)
shipping_rate_status_enum = PgENUM(
    "ACTIVE", "INACTIVE",
    name="shipping_rate_status", create_type=False
)
order_shipping_status_enum = PgENUM(
    "PENDING", "SHIPPED", "IN_TRANSIT", "DELIVERED", "RETURNED",
    name="order_shipping_status", create_type=False
)


def upgrade() -> None:
    # --- Category enhancements (idempotent) ---
    conn = op.get_bind()
    for col_name, col_def in [
        ("level", "INTEGER DEFAULT 1"),
        ("name_zh", "VARCHAR(255)"),
        ("name_tl", "VARCHAR(255)"),
        ("icon", "VARCHAR(100)"),
        ("description", "TEXT"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("typical_weight_kg", "FLOAT"),
        ("customs_hs_code", "VARCHAR(20)"),
    ]:
        conn.execute(sa.text(
            f"ALTER TABLE categories ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
        ))

    # --- Create all enum types (idempotent) ---
    op.execute("DO $$ BEGIN CREATE TYPE address_type AS ENUM ('SHIPPING_FROM','DELIVERY_TO','WAREHOUSE','BILLING'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE address_status AS ENUM ('ACTIVE','DELETED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE shipping_method AS ENUM ('SEA_FREIGHT','AIR_FREIGHT','EXPRESS','LAND_FREIGHT','LOCAL_DELIVERY','SELF_PICKUP'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE shipping_route_status AS ENUM ('ACTIVE','INACTIVE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE shipping_rate_status AS ENUM ('ACTIVE','INACTIVE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE order_shipping_status AS ENUM ('PENDING','SHIPPED','IN_TRANSIT','DELIVERED','RETURNED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # --- Addresses table ---
    op.create_table(
        "addresses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("address_type", address_type_enum, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=False),
        sa.Column("contact_phone", sa.String(50), nullable=False),
        sa.Column("country_code", sa.String(5), nullable=False, index=True),
        sa.Column("country_name", sa.String(100), nullable=False),
        sa.Column("state_province", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("address_line1", sa.Text(), nullable=False),
        sa.Column("address_line2", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("google_place_id", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
        sa.Column("status", address_status_enum, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Shipping routes ---
    op.create_table(
        "shipping_routes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("origin_country", sa.String(5), nullable=False, index=True),
        sa.Column("origin_region", sa.String(100), nullable=True),
        sa.Column("dest_country", sa.String(5), nullable=False, index=True),
        sa.Column("dest_region", sa.String(100), nullable=True),
        sa.Column("shipping_method", shipping_method_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", shipping_route_status_enum, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Shipping rates ---
    op.create_table(
        "shipping_rates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("route_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("weight_min_kg", sa.Float(), server_default="0"),
        sa.Column("weight_max_kg", sa.Float(), server_default="99999"),
        sa.Column("price_per_kg_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), server_default=sa.text("'USD'")),
        sa.Column("min_charge_minor", sa.Integer(), server_default="0"),
        sa.Column("volume_factor", sa.Float(), server_default="5000"),
        sa.Column("estimated_days_min", sa.Integer(), server_default="1"),
        sa.Column("estimated_days_max", sa.Integer(), server_default="7"),
        sa.Column("surcharges_json", JSON(), nullable=True),
        sa.Column("valid_from", sa.Date(), server_default=sa.func.current_date()),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", shipping_rate_status_enum, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Order shipping ---
    op.create_table(
        "order_shipping",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("shipping_method", shipping_method_enum, nullable=False),
        sa.Column("origin_address_id", UUID(as_uuid=True), nullable=True),
        sa.Column("dest_address_id", UUID(as_uuid=True), nullable=True),
        sa.Column("chargeable_weight_kg", sa.Float(), nullable=True),
        sa.Column("shipping_cost_minor", sa.Integer(), server_default="0"),
        sa.Column("currency", sa.String(10), server_default=sa.text("'USD'")),
        sa.Column("estimated_days_min", sa.Integer(), nullable=True),
        sa.Column("estimated_days_max", sa.Integer(), nullable=True),
        sa.Column("tracking_number", sa.String(200), nullable=True),
        sa.Column("carrier_name", sa.String(200), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", order_shipping_status_enum, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("order_shipping")
    op.drop_table("shipping_rates")
    op.drop_table("shipping_routes")
    op.drop_table("addresses")
    op.execute("DROP TYPE IF EXISTS order_shipping_status")
    op.execute("DROP TYPE IF EXISTS shipping_rate_status")
    op.execute("DROP TYPE IF EXISTS shipping_route_status")
    op.execute("DROP TYPE IF EXISTS shipping_method")
    op.execute("DROP TYPE IF EXISTS address_status")
    op.execute("DROP TYPE IF EXISTS address_type")
    op.drop_column("categories", "customs_hs_code")
    op.drop_column("categories", "typical_weight_kg")
    op.drop_column("categories", "sort_order")
    op.drop_column("categories", "description")
    op.drop_column("categories", "icon")
    op.drop_column("categories", "name_tl")
    op.drop_column("categories", "name_zh")
    op.drop_column("categories", "level")

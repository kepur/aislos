"""Experience Center (Portal 10): stores, kiosk devices, showroom sessions,
in-store orders + the five showroom personas in the agents registry.

Revision ID: 022
Revises: 021
Create Date: 2026-06-11
"""
import uuid as uuid_lib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Five tablet personas = five new rows in the agents registry (design §5).
# All run only the 'showroom' workflow; none may ever hold 'payment'.
SHOWROOM_AGENTS = [
    ("smart-home-expert", "Smart Home Expert", "Showroom Consultant",
     "Warm and patient; guides DIY retrofit customers through smart home options.",
     ["product_data", "customer_data", "project_data"]),
    ("solar-expert", "Solar Expert", "Showroom Consultant",
     "Data-driven; explains payback periods and sizing for solar installations.",
     ["product_data", "customer_data", "project_data"]),
    ("security-expert", "Security Expert", "Showroom Consultant",
     "Rigorous; covers regulations and real cases for security systems.",
     ["product_data", "customer_data", "project_data"]),
    ("shopping-assistant", "Shopping Assistant", "Showroom Sales",
     "Efficient; compares products, checks stock and drafts in-store orders.",
     ["product_data", "customer_data", "project_data", "quotes"]),
    ("design-consultant", "Design Consultant", "Showroom Designer",
     "Visual; renders retrofit concepts from customer room photos.",
     ["product_data", "customer_data", "project_data", "ads"]),
]

ALL_SCOPES = ["product_data", "customer_data", "project_data", "quotes",
              "email", "ads", "payment", "partners"]


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "kiosk_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("device_token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("agent_slug", sa.String(100), sa.ForeignKey("agents.slug"), nullable=False),
        sa.Column("default_lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("voice_mode", sa.String(20), nullable=False, server_default="text"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_kiosk_devices_store_id", "kiosk_devices", ["store_id"])
    op.create_index("ix_kiosk_devices_status", "kiosk_devices", ["status"])

    op.create_table(
        "showroom_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", UUID(as_uuid=True), sa.ForeignKey("kiosk_devices.id"), nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("ai.conversations.id"), nullable=True),
        sa.Column("lang", sa.String(10), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("need_category", sa.String(100), nullable=True),
        sa.Column("budget_hint", sa.Numeric(12, 2), nullable=True),
        sa.Column("products_viewed_json", JSONB, nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_showroom_sessions_device_id", "showroom_sessions", ["device_id"])
    op.create_index("ix_showroom_sessions_outcome", "showroom_sessions", ["outcome"])

    op.create_table(
        "showroom_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("showroom_sessions.id"), nullable=True),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("items_json", JSONB, nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("pickup_code", sa.String(12), nullable=False, unique=True),
        sa.Column("confirmed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_showroom_orders_session_id", "showroom_orders", ["session_id"])
    op.create_index("ix_showroom_orders_status", "showroom_orders", ["status"])

    # Seed the five showroom personas (idempotent against re-seeded envs).
    agents_table = sa.table(
        "agents",
        sa.column("id", UUID(as_uuid=True)), sa.column("slug", sa.String),
        sa.column("name", sa.String), sa.column("role_title", sa.String),
        sa.column("description", sa.Text), sa.column("vendor", sa.String),
        sa.column("workflows_json", JSONB), sa.column("status", sa.String),
    )
    grants_table = sa.table(
        "agent_grants",
        sa.column("id", UUID(as_uuid=True)), sa.column("agent_id", UUID(as_uuid=True)),
        sa.column("scope", sa.String), sa.column("granted", sa.Boolean),
    )
    conn = op.get_bind()
    for slug, name, role, desc, granted_scopes in SHOWROOM_AGENTS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM agents WHERE slug = :slug"), {"slug": slug}
        ).first()
        if exists:
            continue
        agent_id = uuid_lib.uuid4()
        op.bulk_insert(agents_table, [{
            "id": agent_id, "slug": slug, "name": name, "role_title": role,
            "description": desc, "vendor": "official",
            "workflows_json": ["showroom"], "status": "active",
        }])
        op.bulk_insert(grants_table, [
            {"id": uuid_lib.uuid4(), "agent_id": agent_id, "scope": scope,
             "granted": scope in granted_scopes}
            for scope in ALL_SCOPES
        ])

    # Official agents must always carry an approved marketplace listing
    # (invariant established in 021).
    conn.execute(sa.text(
        """
        INSERT INTO marketplace_listings (
          id, agent_id, slug, name, role_title, description, version,
          workflows_json, requested_scopes_json, price_monthly, currency,
          status, created_at, updated_at
        )
        SELECT gen_random_uuid(), id, slug, name, role_title, description, '1.0.0',
               workflows_json, '[]'::jsonb, price_monthly, currency,
               'approved', now(), now()
        FROM agents
        WHERE vendor = 'official'
        ON CONFLICT (slug) DO NOTHING
        """
    ))


def downgrade() -> None:
    op.drop_table("showroom_orders")
    op.drop_table("showroom_sessions")
    op.drop_table("kiosk_devices")
    op.drop_table("stores")
    conn = op.get_bind()
    slugs = tuple(a[0] for a in SHOWROOM_AGENTS)
    conn.execute(sa.text(
        "DELETE FROM marketplace_listings WHERE agent_id IN (SELECT id FROM agents WHERE slug = ANY(:slugs))"
    ), {"slugs": list(slugs)})
    conn.execute(sa.text(
        "DELETE FROM agent_grants WHERE agent_id IN (SELECT id FROM agents WHERE slug = ANY(:slugs))"
    ), {"slugs": list(slugs)})
    conn.execute(sa.text("DELETE FROM agents WHERE slug = ANY(:slugs)"), {"slugs": list(slugs)})

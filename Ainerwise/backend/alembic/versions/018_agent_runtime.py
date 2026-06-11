"""V3 Phase G: Agent Runtime — digital employee registry + permission grants

Revision ID: 018
Revises: 017
Create Date: 2026-06-10
"""
import uuid as uuid_lib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OFFICIAL_AGENTS = [
    ("marketing-agent", "Marketing Agent", "Marketing Manager",
     "Plans campaigns, generates multilingual content, runs SEO pages and publishing, reports ROI.",
     ["content_gen", "seo_page", "publish"], True),
    ("sales-agent", "Sales Agent", "Sales Consultant",
     "Talks to website visitors, scores leads, drafts quotations grounded in real pricing.",
     ["consult", "lead_score", "quote_draft"], True),
    ("procurement-agent", "Procurement Agent", "Procurement Manager",
     "Scores partner bids with explainable factors and recommends awards.",
     ["bid_evaluation"], True),
    ("business-brain", "Business Brain", "Chief of Staff",
     "Aggregates the whole operation every morning: leads, money, risks, regional margins.",
     ["daily_briefing"], True),
    ("support-agent", "Support Agent", "Support Engineer",
     "Will handle tickets and maintenance advice from asset history (activates in Phase H).",
     [], False),
]


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role_title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("vendor", sa.String(50), nullable=False, server_default="official"),
        sa.Column("workflows_json", JSONB, nullable=True),
        sa.Column("config_json", JSONB, nullable=True),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agents_status", "agents", ["status"])
    op.create_index("ix_agents_vendor", "agents", ["vendor"])

    op.create_table(
        "agent_grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_id", "scope", name="uq_agent_grants_agent_scope"),
    )
    op.create_index("ix_agent_grants_agent_id", "agent_grants", ["agent_id"])

    # seed the official digital employees; official agents get working grants
    # by default (they already run today), third-party defaults to zero.
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
    default_scopes = {
        "marketing-agent": ["product_data", "ads", "email"],
        "sales-agent": ["product_data", "customer_data", "quotes"],
        "procurement-agent": ["partners", "project_data"],
        "business-brain": ["product_data", "customer_data", "project_data", "partners"],
        "support-agent": [],
    }
    all_scopes = ["product_data", "customer_data", "project_data", "quotes",
                  "email", "ads", "payment", "partners"]
    for slug, name, role, desc, workflows, active in OFFICIAL_AGENTS:
        agent_id = uuid_lib.uuid4()
        op.bulk_insert(agents_table, [{
            "id": agent_id, "slug": slug, "name": name, "role_title": role,
            "description": desc, "vendor": "official",
            "workflows_json": workflows, "status": "active" if active else "paused",
        }])
        granted = set(default_scopes.get(slug, []))
        op.bulk_insert(grants_table, [
            {"id": uuid_lib.uuid4(), "agent_id": agent_id, "scope": scope, "granted": scope in granted}
            for scope in all_scopes
        ])


def downgrade() -> None:
    op.drop_table("agent_grants")
    op.drop_table("agents")

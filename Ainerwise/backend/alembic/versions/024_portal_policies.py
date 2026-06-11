"""Procurement C01: versioned portal_policies + default AISLOS/Cebu policies.

Revision ID: 024
Revises: 023
Create Date: 2026-06-11
"""
import json
import uuid as uuid_lib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen confidence gate (task board §4.2); thresholds as strings for Decimal exactness.
FROZEN_CONFIDENCE_GATE = {
    "ask_below": "0.600",
    "estimate_min": "0.600",
    "estimate_max": "0.800",
    "review_above": "0.800",
    "freeze_min_critical_confidence": "0.800",
    "score_decimals": 3,
    "aggregation": "min",
}

PHASE1_PROJECT_TYPES = ["villa_smart_home", "small_hotel_smart_upgrade"]

DEFAULT_POLICIES = [
    {
        "portal_key": "aislos",
        "default_procurement_mode": "managed",
        "price_visibility_rule": "customer_totals_only",
        "supplier_visibility_rule": "hidden",
        "lead_routing_rule_json": {"queue": "aislos_sales"},
    },
    {
        "portal_key": "cebu",
        "default_procurement_mode": "self_service",
        "price_visibility_rule": "line_estimates",
        "supplier_visibility_rule": "visible_when_self_service",
        "lead_routing_rule_json": {"queue": "cebu_procurement"},
    },
]


def upgrade() -> None:
    op.create_table(
        "portal_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("portal_key", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("visible_categories_json", JSONB, nullable=True),
        sa.Column("default_procurement_mode", sa.String(20), nullable=False),
        sa.Column("allowed_project_types_json", JSONB, nullable=False),
        sa.Column("price_visibility_rule", sa.String(50), nullable=False),
        sa.Column("supplier_visibility_rule", sa.String(50), nullable=False),
        sa.Column("lead_routing_rule_json", JSONB, nullable=True),
        sa.Column("confidence_gate_json", JSONB, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("portal_key", "version", name="uq_portal_policies_key_version"),
    )
    op.create_index("ix_portal_policies_portal_key", "portal_policies", ["portal_key"])
    op.create_index(
        "uq_portal_policies_one_active",
        "portal_policies",
        ["portal_key"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    # Seed one active default policy per portal, idempotently: skip a portal
    # that already has any policy rows (never overwrite operator data).
    conn = op.get_bind()
    for policy in DEFAULT_POLICIES:
        exists = conn.execute(
            sa.text("SELECT 1 FROM portal_policies WHERE portal_key = :pk LIMIT 1"),
            {"pk": policy["portal_key"]},
        ).first()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO portal_policies (
                    id, portal_key, version, status,
                    visible_categories_json, default_procurement_mode,
                    allowed_project_types_json, price_visibility_rule,
                    supplier_visibility_rule, lead_routing_rule_json,
                    confidence_gate_json, activated_at, created_at, updated_at
                ) VALUES (
                    :id, :pk, 1, 'active',
                    NULL, :mode,
                    :types, :price_rule,
                    :supplier_rule, :lead_routing,
                    :gate, now(), now(), now()
                )
                """
            ),
            {
                "id": str(uuid_lib.uuid4()),
                "pk": policy["portal_key"],
                "mode": policy["default_procurement_mode"],
                "types": json.dumps(PHASE1_PROJECT_TYPES),
                "price_rule": policy["price_visibility_rule"],
                "supplier_rule": policy["supplier_visibility_rule"],
                "lead_routing": json.dumps(policy["lead_routing_rule_json"]),
                "gate": json.dumps(FROZEN_CONFIDENCE_GATE),
            },
        )


def downgrade() -> None:
    op.drop_index("uq_portal_policies_one_active", table_name="portal_policies")
    op.drop_index("ix_portal_policies_portal_key", table_name="portal_policies")
    op.drop_table("portal_policies")

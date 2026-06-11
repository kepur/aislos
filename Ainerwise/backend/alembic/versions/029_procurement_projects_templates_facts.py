"""C03: procurement projects, templates, facts.

Revision ID: 029
Revises: 028
Create Date: 2026-06-11
"""
import json
import uuid as uuid_lib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fact(
    key: str,
    label: str,
    data_type: str,
    *,
    required: bool = True,
    critical: bool = False,
    weight: str = "1.000",
    question: str,
    validation: dict | None = None,
) -> dict:
    return {
        "key": key,
        "label": label,
        "data_type": data_type,
        "required": required,
        "critical": critical,
        "weight": weight,
        "question": question,
        "validation": validation or {},
    }


VILLA_FACT_DEFINITIONS = [
    _fact(
        "property_area_sqm",
        "Property Area (sqm)",
        "number",
        critical=True,
        weight="1.500",
        question="What is the total built-up area in square meters?",
        validation={"min": 50, "max": 50000},
    ),
    _fact(
        "floor_count",
        "Floor Count",
        "integer",
        question="How many floors does the property have?",
        validation={"min": 1, "max": 20},
    ),
    _fact(
        "room_count",
        "Room Count",
        "integer",
        critical=True,
        question="How many rooms require smart home coverage?",
        validation={"min": 1, "max": 200},
    ),
    _fact(
        "target_budget",
        "Target Budget",
        "money",
        critical=True,
        weight="2.000",
        question="What is your target budget for the smart home project?",
        validation={"min": 0},
    ),
    _fact(
        "preferred_brands",
        "Preferred Brands",
        "string_list",
        required=False,
        question="Do you have preferred equipment brands?",
    ),
    _fact(
        "installation_timeline",
        "Installation Timeline",
        "string",
        critical=True,
        question="When do you need installation completed?",
    ),
    _fact(
        "existing_network_infra",
        "Existing Network Infrastructure",
        "string",
        question="Describe existing network cabling and Wi-Fi infrastructure.",
    ),
    _fact(
        "primary_use_case",
        "Primary Use Case",
        "string",
        critical=True,
        question="What is the primary use case (residence, rental, showcase)?",
    ),
]

HOTEL_FACT_DEFINITIONS = [
    _fact(
        "room_count",
        "Guest Room Count",
        "integer",
        critical=True,
        weight="2.000",
        question="How many guest rooms need smart upgrades?",
        validation={"min": 5, "max": 500},
    ),
    _fact(
        "property_area_sqm",
        "Property Area (sqm)",
        "number",
        critical=True,
        question="What is the total property area in square meters?",
        validation={"min": 200, "max": 200000},
    ),
    _fact(
        "star_rating",
        "Star Rating",
        "integer",
        critical=True,
        question="What is the hotel star rating?",
        validation={"min": 1, "max": 5},
    ),
    _fact(
        "target_budget",
        "Target Budget",
        "money",
        critical=True,
        weight="2.000",
        question="What is your target budget for the smart upgrade?",
        validation={"min": 0},
    ),
    _fact(
        "public_area_coverage",
        "Public Area Coverage",
        "string",
        critical=True,
        question="Which public areas need smart systems (lobby, restaurant, spa)?",
    ),
    _fact(
        "back_of_house_systems",
        "Back-of-House Systems",
        "string",
        question="Which back-of-house systems should be integrated?",
    ),
    _fact(
        "installation_timeline",
        "Installation Timeline",
        "string",
        critical=True,
        question="What is the target installation timeline?",
    ),
    _fact(
        "brand_standards",
        "Brand Standards",
        "string",
        question="Are there franchise or brand technology standards to follow?",
    ),
]

SEED_TEMPLATES = [
    {
        "project_type": "villa_smart_home",
        "version": 1,
        "status": "active",
        "fact_definitions_json": VILLA_FACT_DEFINITIONS,
        "boq_rules_json": {"template": "villa_smart_home_v1"},
    },
    {
        "project_type": "small_hotel_smart_upgrade",
        "version": 1,
        "status": "active",
        "fact_definitions_json": HOTEL_FACT_DEFINITIONS,
        "boq_rules_json": {"template": "small_hotel_smart_upgrade_v1"},
    },
]


def upgrade() -> None:
    op.create_table(
        "procurement_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_type", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("fact_definitions_json", JSONB, nullable=False),
        sa.Column("boq_rules_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_type", "version", name="uq_procurement_templates_type_version"),
    )
    op.create_index("ix_procurement_templates_project_type", "procurement_templates", ["project_type"])
    op.create_index(
        "uq_procurement_templates_one_active",
        "procurement_templates",
        ["project_type"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "procurement_projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("portal_key", sa.String(50), nullable=False),
        sa.Column(
            "portal_policy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("portal_policies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("policy_snapshot_json", JSONB, nullable=False),
        sa.Column("project_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("facts_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("boq_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("overall_confidence", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("current_boq_version_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_procurement_projects_owner_user_id", "procurement_projects", ["owner_user_id"])
    op.create_index("ix_procurement_projects_portal_key", "procurement_projects", ["portal_key"])

    op.create_table(
        "procurement_project_facts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("procurement_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("value_json", JSONB, nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("critical", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("weight", sa.Numeric(6, 3), nullable=False, server_default="1"),
        sa.Column("source", sa.String(20), nullable=False, server_default="system"),
        sa.Column("source_ref_json", JSONB, nullable=True),
        sa.Column("confidence", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("user_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("assumption", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "template_key", name="uq_procurement_facts_project_key"),
    )
    op.create_index(
        "ix_procurement_project_facts_project_id",
        "procurement_project_facts",
        ["project_id"],
    )

    conn = op.get_bind()
    for tpl in SEED_TEMPLATES:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM procurement_templates WHERE project_type = :pt LIMIT 1"
            ),
            {"pt": tpl["project_type"]},
        ).first()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO procurement_templates (
                    id, project_type, version, status,
                    fact_definitions_json, boq_rules_json,
                    created_at, updated_at
                ) VALUES (
                    :id, :pt, :ver, :status,
                    :facts, :boq,
                    now(), now()
                )
                """
            ),
            {
                "id": str(uuid_lib.uuid4()),
                "pt": tpl["project_type"],
                "ver": tpl["version"],
                "status": tpl["status"],
                "facts": json.dumps(tpl["fact_definitions_json"]),
                "boq": json.dumps(tpl["boq_rules_json"]),
            },
        )


def downgrade() -> None:
    op.drop_index("ix_procurement_project_facts_project_id", table_name="procurement_project_facts")
    op.drop_table("procurement_project_facts")
    op.drop_index("ix_procurement_projects_portal_key", table_name="procurement_projects")
    op.drop_index("ix_procurement_projects_owner_user_id", table_name="procurement_projects")
    op.drop_table("procurement_projects")
    op.drop_index("uq_procurement_templates_one_active", table_name="procurement_templates")
    op.drop_index("ix_procurement_templates_project_type", table_name="procurement_templates")
    op.drop_table("procurement_templates")

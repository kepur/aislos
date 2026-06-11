"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # companies
    op.create_table(
        "companies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("country", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("verification_status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("contact_info", JSONB),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.String(500)),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("phone", sa.String(50)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), server_default="buyer", nullable=False),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("country", sa.String(100)),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # product_categories
    op.create_table(
        "product_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("product_categories.id")),
        sa.Column("icon", sa.String(100)),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # products
    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("source_type", sa.String(50), server_default="official", nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("product_categories.id")),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False, index=True),
        sa.Column("brand", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("specs_json", JSONB),
        sa.Column("images_json", JSONB),
        sa.Column("cost_price", sa.Float),
        sa.Column("list_price", sa.Float),
        sa.Column("currency", sa.String(10), server_default="EUR"),
        sa.Column("moq", sa.Integer, server_default="1"),
        sa.Column("lead_time_days", sa.Integer),
        sa.Column("warranty_years", sa.Integer),
        sa.Column("spare_policy_json", JSONB),
        sa.Column("service_available", sa.Boolean, server_default="false"),
        sa.Column("supported_regions_json", JSONB),
        sa.Column("certifications_json", JSONB),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # product_compatibility
    op.create_table(
        "product_compatibility",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("protocol", sa.String(100), nullable=False),
        sa.Column("compatibility_level", sa.String(50), server_default="unknown"),
        sa.Column("tested_by", sa.String(50)),
        sa.Column("test_status", sa.String(50)),
        sa.Column("notes", sa.Text),
        sa.Column("test_artifact_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # solutions
    op.create_table(
        "solutions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False, index=True),
        sa.Column("category", sa.String(100)),
        sa.Column("target_scenarios_json", JSONB),
        sa.Column("description", sa.Text),
        sa.Column("pain_points_json", JSONB),
        sa.Column("architecture_json", JSONB),
        sa.Column("recommended_products_json", JSONB),
        sa.Column("service_packages_json", JSONB),
        sa.Column("budget_tiers_json", JSONB),
        sa.Column("delivery_flow_json", JSONB),
        sa.Column("regions_json", JSONB),
        sa.Column("language_content_json", JSONB),
        sa.Column("hero_image_url", sa.String(500)),
        sa.Column("icon", sa.String(100)),
        sa.Column("public_visible", sa.Boolean, server_default="true"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # solution_packages
    op.create_table(
        "solution_packages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False, index=True),
        sa.Column("target_customer_type", sa.String(100)),
        sa.Column("suitable_regions_json", JSONB),
        sa.Column("included_systems_json", JSONB),
        sa.Column("recommended_products_json", JSONB),
        sa.Column("required_service_partner_types_json", JSONB),
        sa.Column("base_price_rule_json", JSONB),
        sa.Column("estimated_timeline_days", sa.Integer),
        sa.Column("risk_notes", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("public_visible", sa.Boolean, server_default="true"),
        sa.Column("language_content_json", JSONB),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # service_packages
    op.create_table(
        "service_packages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("years", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("included_services_json", JSONB),
        sa.Column("sla_json", JSONB),
        sa.Column("price_rule_json", JSONB),
        sa.Column("public_visible", sa.Boolean, server_default="true"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("language_content_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # service_partners
    op.create_table(
        "service_partners",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", UUID(as_uuid=True)),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("partner_type", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("service_radius_km", sa.Integer),
        sa.Column("languages_json", JSONB),
        sa.Column("skills_json", JSONB),
        sa.Column("certifications_json", JSONB),
        sa.Column("hourly_rate", sa.Float),
        sa.Column("day_rate", sa.Float),
        sa.Column("project_rate_rule_json", JSONB),
        sa.Column("availability_status", sa.String(50), server_default="available"),
        sa.Column("rating_internal", sa.Float),
        sa.Column("public_visible", sa.Boolean, server_default="false"),
        sa.Column("verification_status", sa.String(50), server_default="pending"),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("notes_internal", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # leads
    op.create_table(
        "leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("buyer_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("contact_phone", sa.String(50)),
        sa.Column("project_type", sa.String(100)),
        sa.Column("country", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("site_info_json", JSONB),
        sa.Column("budget_range", sa.String(100)),
        sa.Column("systems_needed_json", JSONB),
        sa.Column("description", sa.Text),
        sa.Column("uploaded_files_json", JSONB),
        sa.Column("ai_analysis_json", JSONB),
        sa.Column("status", sa.String(50), server_default="new", nullable=False),
        sa.Column("assigned_admin_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("solution_id", UUID(as_uuid=True), sa.ForeignKey("solutions.id")),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # site_surveys
    op.create_table(
        "site_surveys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("survey_type", sa.String(50), server_default="quick", nullable=False),
        sa.Column("survey_json", JSONB),
        sa.Column("uploaded_files_json", JSONB),
        sa.Column("completeness_score", sa.Float),
        sa.Column("risk_score", sa.Float),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # projects
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), server_default="planning", nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("start_date", sa.Date),
        sa.Column("expected_delivery_date", sa.Date),
        sa.Column("project_plan_json", JSONB),
        sa.Column("team_json", JSONB),
        sa.Column("telegram_chat_id", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # quotes
    op.create_table(
        "quotes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("quote_items_json", JSONB),
        sa.Column("device_total", sa.Float, server_default="0"),
        sa.Column("service_total", sa.Float, server_default="0"),
        sa.Column("platform_fee", sa.Float, server_default="0"),
        sa.Column("support_package_fee", sa.Float, server_default="0"),
        sa.Column("spare_parts_fee", sa.Float, server_default="0"),
        sa.Column("logistics_fee", sa.Float, server_default="0"),
        sa.Column("tax_fee", sa.Float, server_default="0"),
        sa.Column("discount", sa.Float, server_default="0"),
        sa.Column("total", sa.Float, server_default="0"),
        sa.Column("currency", sa.String(10), server_default="EUR"),
        sa.Column("status", sa.String(50), server_default="draft", nullable=False),
        sa.Column("valid_until", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # inquiries
    op.create_table(
        "inquiries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("vendor_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id")),
        sa.Column("message", sa.Text),
        sa.Column("status", sa.String(50), server_default="new", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # tickets
    op.create_table(
        "tickets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("buyer_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("buyer_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("issue_type", sa.String(100)),
        sa.Column("priority", sa.String(50), server_default="medium", nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("files_json", JSONB),
        sa.Column("status", sa.String(50), server_default="open", nullable=False),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # integration_events
    op.create_table(
        "integration_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("payload_json", JSONB),
        sa.Column("target_channel", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ai_runs
    op.create_table(
        "ai_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("input_json", JSONB),
        sa.Column("output_json", JSONB),
        sa.Column("model_name", sa.String(100)),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("status", sa.String(50), server_default="running", nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # file_assets
    op.create_table(
        "file_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # certification_records
    op.create_table(
        "certification_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_type", sa.String(50), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("certification_name", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255)),
        sa.Column("country", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="planned", nullable=False),
        sa.Column("issue_date", sa.Date),
        sa.Column("expiry_date", sa.Date),
        sa.Column("certificate_file_url", sa.String(500)),
        sa.Column("public_visible", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # warranty_policies
    op.create_table(
        "warranty_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("region", sa.String(100)),
        sa.Column("manufacturer_warranty_months", sa.Integer),
        sa.Column("platform_support_months", sa.Integer),
        sa.Column("local_installation_warranty_months", sa.Integer),
        sa.Column("spare_parts_policy_json", JSONB),
        sa.Column("response_sla_json", JSONB),
        sa.Column("exclusions_text", sa.Text),
        sa.Column("active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # regions
    op.create_table(
        "regions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(10), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("currency_code", sa.String(10), server_default="EUR"),
        sa.Column("language_codes_json", JSONB),
        sa.Column("tax_rules_json", JSONB),
        sa.Column("timezone", sa.String(50)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_user_id", UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("before_json", JSONB),
        sa.Column("after_json", JSONB),
        sa.Column("ip", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # founder_profiles
    op.create_table(
        "founder_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("bio_short", sa.String(500)),
        sa.Column("bio_long", sa.Text),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("skills_json", JSONB),
        sa.Column("certifications_json", JSONB),
        sa.Column("service_regions_json", JSONB),
        sa.Column("languages_json", JSONB),
        sa.Column("visible_on_site", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("founder_profiles")
    op.drop_table("audit_logs")
    op.drop_table("regions")
    op.drop_table("warranty_policies")
    op.drop_table("certification_records")
    op.drop_table("file_assets")
    op.drop_table("ai_runs")
    op.drop_table("integration_events")
    op.drop_table("tickets")
    op.drop_table("inquiries")
    op.drop_table("quotes")
    op.drop_table("projects")
    op.drop_table("site_surveys")
    op.drop_table("leads")
    op.drop_table("service_partners")
    op.drop_table("service_packages")
    op.drop_table("solution_packages")
    op.drop_table("solutions")
    op.drop_table("product_compatibility")
    op.drop_table("products")
    op.drop_table("product_categories")
    op.drop_table("users")
    op.drop_table("companies")

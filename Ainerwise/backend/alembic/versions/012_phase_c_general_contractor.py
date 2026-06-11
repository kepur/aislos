"""Phase C: cost/pricing, RFQ bidding, partner metrics, assets, cases,
AI memories, marketing assets, payment ledger (offline money first)

Revision ID: 012
Revises: 011
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # ── Cost + Pricing engine ──────────────────────────────────
    op.create_table(
        "product_costs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("freight_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("freight_fixed", sa.Numeric(12, 2), nullable=True),
        sa.Column("customs_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("customs_fixed", sa.Numeric(12, 2), nullable=True),
        sa.Column("warehousing_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("labor_estimate", sa.Numeric(12, 2), nullable=True),
        sa.Column("landed_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_to", sa.Date, nullable=True),
        *_ts(),
        sa.UniqueConstraint("region_id", "product_id", "valid_from", name="uq_product_costs_region_product_from"),
    )
    op.create_index("ix_product_costs_product_id", "product_costs", ["product_id"])

    op.create_table(
        "price_lists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("list_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("partner_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("vip_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_to", sa.Date, nullable=True),
        *_ts(),
        sa.UniqueConstraint("region_id", "product_id", "valid_from", name="uq_price_lists_region_product_from"),
    )
    op.create_index("ix_price_lists_product_id", "price_lists", ["product_id"])

    op.create_table(
        "exchange_rates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("base", sa.String(3), nullable=False),
        sa.Column("quote", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(14, 6), nullable=False),
        sa.Column("as_of", sa.Date, nullable=False),
        *_ts(),
        sa.UniqueConstraint("base", "quote", "as_of", name="uq_exchange_rates_pair_date"),
    )

    # ── RFQ bidding + partner metrics ──────────────────────────
    op.create_table(
        "rfqs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("solution_id", UUID(as_uuid=True), sa.ForeignKey("solutions.id"), nullable=True),
        sa.Column("trade", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("scope_json", JSONB, nullable=True),
        sa.Column("budget_hint", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("bid_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("awarded_bid_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_rfqs_status", "rfqs", ["status"])
    op.create_index("ix_rfqs_lead_id", "rfqs", ["lead_id"])
    op.create_index("ix_rfqs_project_id", "rfqs", ["project_id"])

    op.create_table(
        "rfq_invitations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rfq_id", UUID(as_uuid=True), sa.ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="sent"),
        sa.Column("sent_via", sa.String(50), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.UniqueConstraint("rfq_id", "partner_id", name="uq_rfq_invitations_rfq_partner"),
    )
    op.create_index("ix_rfq_invitations_rfq_id", "rfq_invitations", ["rfq_id"])
    op.create_index("ix_rfq_invitations_partner_id", "rfq_invitations", ["partner_id"])

    op.create_table(
        "partner_bids",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rfq_id", UUID(as_uuid=True), sa.ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("lead_time_days", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("attachments_json", JSONB, nullable=True),
        sa.Column("ai_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ai_score_breakdown_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="submitted"),
        *_ts(),
    )
    op.create_index("ix_partner_bids_rfq_id", "partner_bids", ["rfq_id"])
    op.create_index("ix_partner_bids_partner_id", "partner_bids", ["partner_id"])
    op.create_index("ix_partner_bids_status", "partner_bids", ["status"])

    op.create_table(
        "partner_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=False, unique=True),
        sa.Column("response_hours_avg", sa.Numeric(8, 2), nullable=True),
        sa.Column("completion_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("cancellation_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("on_time_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("warranty_claim_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("customer_review_avg", sa.Numeric(3, 2), nullable=True),
        sa.Column("revenue_total", sa.Numeric(14, 2), nullable=True),
        sa.Column("ai_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("breakdown_json", JSONB, nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
    )
    op.create_index("ix_partner_metrics_composite_score", "partner_metrics", ["composite_score"])

    # ── Assets (digital-twin-ready hierarchy) ──────────────────
    op.create_table(
        "sites",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("contact_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("building_meta_json", JSONB, nullable=True),
        *_ts(),
    )

    op.create_table(
        "assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("parent_asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("floor", sa.String(50), nullable=True),
        sa.Column("room", sa.String(100), nullable=True),
        sa.Column("serial_no", sa.String(255), nullable=True),
        sa.Column("installed_at", sa.Date, nullable=True),
        sa.Column("customer_warranty_id", UUID(as_uuid=True), sa.ForeignKey("customer_warranties.id"), nullable=True),
        sa.Column("amc_contract_id", UUID(as_uuid=True), sa.ForeignKey("amc_contracts.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("meta_json", JSONB, nullable=True),
        *_ts(),
    )
    op.create_index("ix_assets_site_id", "assets", ["site_id"])
    op.create_index("ix_assets_project_id", "assets", ["project_id"])
    op.create_index("ix_assets_status", "assets", ["status"])

    op.add_column("tickets", sa.Column("asset_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_tickets_asset_id", "tickets", "assets", ["asset_id"], ["id"])
    op.create_index("ix_tickets_asset_id", "tickets", ["asset_id"])
    op.add_column("maintenance_schedules", sa.Column("asset_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_maintenance_schedules_asset_id", "maintenance_schedules", "assets", ["asset_id"], ["id"])
    op.create_index("ix_maintenance_schedules_asset_id", "maintenance_schedules", ["asset_id"])

    # ── Case library ───────────────────────────────────────────
    op.create_table(
        "cases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("property_type", sa.String(50), nullable=True),
        sa.Column("area_sqm", sa.Integer, nullable=True),
        sa.Column("budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("products_json", JSONB, nullable=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=True),
        sa.Column("duration_days", sa.Integer, nullable=True),
        sa.Column("gross_margin_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("photos_json", JSONB, nullable=True),
        sa.Column("customer_feedback", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("public_visible", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("embedding_document_id", UUID(as_uuid=True), sa.ForeignKey("ai.knowledge_documents.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_cases_property_type", "cases", ["property_type"])

    # ── AI memories ────────────────────────────────────────────
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), nullable=True),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("subject_id", UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_conversation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        *_ts(),
        sa.ForeignKeyConstraint(["region_id"], ["public.regions.id"]),
        sa.ForeignKeyConstraint(["source_conversation_id"], ["ai.conversations.id"]),
        schema="ai",
    )
    op.create_index("ix_ai_memories_subject", "memories", ["subject_type", "subject_id"], schema="ai")
    op.create_index("ix_ai_memories_status", "memories", ["status"], schema="ai")

    # ── Marketing assets + region profiles ─────────────────────
    op.create_table(
        "marketing_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("campaign_id", UUID(as_uuid=True), sa.ForeignKey("marketing_campaigns.id"), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("case_id", UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("media_minio_key", sa.String(500), nullable=True),
        sa.Column("ai_generated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("ai.ai_reviews.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("meta_json", JSONB, nullable=True),
        *_ts(),
    )
    op.create_index("ix_marketing_assets_status", "marketing_assets", ["status"])

    op.create_table(
        "region_marketing_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=False, unique=True),
        sa.Column("tone_json", JSONB, nullable=True),
        sa.Column("emphasis_json", JSONB, nullable=True),
        sa.Column("compliance_notes", sa.Text, nullable=True),
        *_ts(),
    )

    # ── Payments: ledger-first, money stays offline/PSP ────────
    op.create_table(
        "payment_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quotes.id"), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("retention_pct", sa.Numeric(4, 2), nullable=True),
        sa.Column("retention_release_days", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text, nullable=True),
        *_ts(),
    )
    op.create_index("ix_payment_plans_project_id", "payment_plans", ["project_id"])
    op.create_index("ix_payment_plans_status", "payment_plans", ["status"])

    op.create_table(
        "payment_milestones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("payment_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("trigger", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("funded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_ref", sa.String(255), nullable=True),
        *_ts(),
    )
    op.create_index("ix_payment_milestones_plan_id", "payment_milestones", ["plan_id"])
    op.create_index("ix_payment_milestones_status", "payment_milestones", ["status"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_group", UUID(as_uuid=True), nullable=False),
        sa.Column("account", sa.String(255), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("milestone_id", UUID(as_uuid=True), sa.ForeignKey("payment_milestones.id"), nullable=True),
        sa.Column("memo", sa.Text, nullable=True),
        *_ts(),
    )
    op.create_index("ix_ledger_entries_entry_group", "ledger_entries", ["entry_group"])
    op.create_index("ix_ledger_entries_account", "ledger_entries", ["account"])
    op.create_index("ix_ledger_entries_milestone_id", "ledger_entries", ["milestone_id"])

    op.create_table(
        "partner_deposits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("service_partners.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="requested"),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("forfeiture_log_json", JSONB, nullable=True),
        *_ts(),
    )
    op.create_index("ix_partner_deposits_partner_id", "partner_deposits", ["partner_id"])


def downgrade() -> None:
    op.drop_table("partner_deposits")
    op.drop_table("ledger_entries")
    op.drop_table("payment_milestones")
    op.drop_table("payment_plans")
    op.drop_table("region_marketing_profiles")
    op.drop_table("marketing_assets")
    op.drop_index("ix_ai_memories_status", table_name="memories", schema="ai")
    op.drop_index("ix_ai_memories_subject", table_name="memories", schema="ai")
    op.drop_table("memories", schema="ai")
    op.drop_table("cases")
    op.drop_index("ix_maintenance_schedules_asset_id", table_name="maintenance_schedules")
    op.drop_constraint("fk_maintenance_schedules_asset_id", "maintenance_schedules", type_="foreignkey")
    op.drop_column("maintenance_schedules", "asset_id")
    op.drop_index("ix_tickets_asset_id", table_name="tickets")
    op.drop_constraint("fk_tickets_asset_id", "tickets", type_="foreignkey")
    op.drop_column("tickets", "asset_id")
    op.drop_table("assets")
    op.drop_table("sites")
    op.drop_table("partner_metrics")
    op.drop_table("partner_bids")
    op.drop_table("rfq_invitations")
    op.drop_table("rfqs")
    op.drop_table("exchange_rates")
    op.drop_table("price_lists")
    op.drop_table("product_costs")

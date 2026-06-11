"""Lifecycle data foundation (FI.2.2 - FI.2.11)

Revision ID: 005
Revises: 004
Create Date: 2026-06-01

Adds recurring-revenue / lifecycle columns to products, leads, and tickets, the
solution_line taxonomy column to solutions, and the relational lifecycle tables:
supplier_warranties, customer_warranties, amc_contracts, monitoring_points,
inventory_items, stock_movements, maintenance_schedules, calibration_records.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FALSE = sa.text("false")


def upgrade() -> None:
    # --- FI.2.1 solution_line taxonomy on solutions -----------------------
    op.add_column("solutions", sa.Column("solution_line", sa.String(50), nullable=True))

    # --- FI.2.2 product recurring-revenue / lifecycle fields --------------
    op.add_column("products", sa.Column("solution_line", sa.String(50), nullable=True))
    op.add_column("products", sa.Column("public_name", sa.String(500), nullable=True))
    op.add_column("products", sa.Column("internal_model", sa.String(255), nullable=True))
    op.add_column("products", sa.Column("supplier_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_products_supplier_id_companies", "products", "companies", ["supplier_id"], ["id"]
    )
    op.add_column("products", sa.Column("recurring_revenue_types_json", JSONB, nullable=True))
    op.add_column("products", sa.Column("consumable_cycle_months", sa.Integer, nullable=True))
    op.add_column("products", sa.Column("calibration_cycle_months", sa.Integer, nullable=True))
    op.add_column("products", sa.Column("expected_lifetime_months", sa.Integer, nullable=True))
    op.add_column("products", sa.Column("replacement_margin_percent", sa.Float, nullable=True))
    op.add_column("products", sa.Column("required_for_compliance", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("products", sa.Column("report_template_available", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("products", sa.Column("amc_required", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("products", sa.Column("amc_recommended", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("products", sa.Column("service_dependency_level", sa.String(50), nullable=True))

    # --- FI.2.3 lead recurring-revenue qualification fields ---------------
    op.add_column("leads", sa.Column("solution_line", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("recurring_revenue_score", sa.Integer, nullable=True))
    op.add_column("leads", sa.Column("compliance_risk_level", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("consumable_potential", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("amc_potential", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("estimated_arr", sa.Float, nullable=True))
    op.add_column("leads", sa.Column("estimated_ltv", sa.Float, nullable=True))
    op.add_column("leads", sa.Column("is_multi_site", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("leads", sa.Column("monitoring_points_count", sa.Integer, nullable=True))

    # --- FI.2.5 supplier_warranties ---------------------------------------
    op.create_table(
        "supplier_warranties",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("warranty_years", sa.Integer, nullable=True),
        sa.Column("warranty_type", sa.String(50), nullable=True),
        sa.Column("shipping_responsibility", sa.String(50), nullable=True),
        sa.Column("response_time_days", sa.Integer, nullable=True),
        sa.Column("replacement_policy", sa.Text, nullable=True),
        sa.Column("spare_parts_available", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("firmware_support", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("remote_debug_support", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("api_protocol_support", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("warranty_region_limit", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.6 customer_warranties ---------------------------------------
    op.create_table(
        "customer_warranties",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("warranty_model", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("included_devices_json", JSONB, nullable=True),
        sa.Column("excluded_devices_json", JSONB, nullable=True),
        sa.Column("included_labor", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("included_remote_support", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("included_on_site_visits_per_year", sa.Integer, nullable=True),
        sa.Column("spare_parts_included", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("max_claims_per_year", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.7 amc_contracts ---------------------------------------------
    op.create_table(
        "amc_contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("package", sa.String(50), nullable=True),
        sa.Column("pricing_mode", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("renewal_status", sa.String(50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("coverage_json", JSONB, nullable=True),
        sa.Column("exclusions_json", JSONB, nullable=True),
        sa.Column("included_visits_per_year", sa.Integer, nullable=True),
        sa.Column("response_target_hours", sa.Integer, nullable=True),
        sa.Column("recurring_fee", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.8 monitoring_points (referenced by tickets / maintenance) ---
    op.create_table(
        "monitoring_points",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("solution_line", sa.String(50), nullable=True),
        sa.Column("site", sa.String(255), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("point_type", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("threshold_min", sa.Float, nullable=True),
        sa.Column("threshold_max", sa.Float, nullable=True),
        sa.Column("calibration_cycle_months", sa.Integer, nullable=True),
        sa.Column("last_calibrated_at", sa.Date, nullable=True),
        sa.Column("next_calibration_at", sa.Date, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.9 inventory_items + stock_movements -------------------------
    op.create_table(
        "inventory_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("reserved_for_project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("reserved_quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("min_stock_level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("reorder_level", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("last_checked_at", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("inventory_item_id", UUID(as_uuid=True), sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("movement_type", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("unit_cost", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.10 maintenance_schedules + calibration_records --------------
    op.create_table(
        "maintenance_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("monitoring_point_id", UUID(as_uuid=True), sa.ForeignKey("monitoring_points.id"), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("frequency_months", sa.Integer, nullable=True),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("covered_by_amc", sa.Boolean, nullable=False, server_default=_FALSE),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "calibration_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("monitoring_point_id", UUID(as_uuid=True), sa.ForeignKey("monitoring_points.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("calibration_date", sa.Date, nullable=True),
        sa.Column("next_due_date", sa.Date, nullable=True),
        sa.Column("calibration_method", sa.String(255), nullable=True),
        sa.Column("certificate_file_id", UUID(as_uuid=True), sa.ForeignKey("file_assets.id"), nullable=True),
        sa.Column("technician", sa.String(255), nullable=True),
        sa.Column("result", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- FI.2.4 ticket coverage fields (after monitoring_points exists) ---
    op.add_column("tickets", sa.Column("affected_device", sa.String(500), nullable=True))
    op.add_column("tickets", sa.Column("monitoring_point_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_tickets_monitoring_point_id", "tickets", "monitoring_points", ["monitoring_point_id"], ["id"]
    )
    op.add_column("tickets", sa.Column("warranty_related", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("tickets", sa.Column("amc_covered", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("tickets", sa.Column("is_paid_service", sa.Boolean, nullable=False, server_default=_FALSE))
    op.add_column("tickets", sa.Column("coverage_type", sa.String(50), nullable=True))
    op.add_column("tickets", sa.Column("estimated_cost", sa.Float, nullable=True))
    op.add_column("tickets", sa.Column("resolution", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "resolution")
    op.drop_column("tickets", "estimated_cost")
    op.drop_column("tickets", "coverage_type")
    op.drop_column("tickets", "is_paid_service")
    op.drop_column("tickets", "amc_covered")
    op.drop_column("tickets", "warranty_related")
    op.drop_constraint("fk_tickets_monitoring_point_id", "tickets", type_="foreignkey")
    op.drop_column("tickets", "monitoring_point_id")
    op.drop_column("tickets", "affected_device")

    op.drop_table("calibration_records")
    op.drop_table("maintenance_schedules")
    op.drop_table("stock_movements")
    op.drop_table("inventory_items")
    op.drop_table("monitoring_points")
    op.drop_table("amc_contracts")
    op.drop_table("customer_warranties")
    op.drop_table("supplier_warranties")

    for col in (
        "monitoring_points_count", "is_multi_site", "estimated_ltv", "estimated_arr",
        "amc_potential", "consumable_potential", "compliance_risk_level",
        "recurring_revenue_score", "solution_line",
    ):
        op.drop_column("leads", col)

    op.drop_constraint("fk_products_supplier_id_companies", "products", type_="foreignkey")
    for col in (
        "service_dependency_level", "amc_recommended", "amc_required",
        "report_template_available", "required_for_compliance", "replacement_margin_percent",
        "expected_lifetime_months", "calibration_cycle_months", "consumable_cycle_months",
        "recurring_revenue_types_json", "supplier_id", "internal_model", "public_name",
        "solution_line",
    ):
        op.drop_column("products", col)

    op.drop_column("solutions", "solution_line")

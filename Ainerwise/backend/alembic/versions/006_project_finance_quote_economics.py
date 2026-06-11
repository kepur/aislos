"""Project finance + quote economics (FI.4.1 - FI.4.5)

Revision ID: 006
Revises: 005
Create Date: 2026-06-01

Adds project_finances + platform_fee_rules tables, recurring-cost columns on
proposal_plans, and customer line-item / internal-economics columns on quotes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ZERO = sa.text("0")

_FINANCE_FLOAT_COLS = [
    "contract_total", "hardware_revenue", "design_fee", "installation_fee",
    "integration_fee", "platform_fee", "project_management_fee",
    "amc_fee_year_1", "amc_fee_annual", "consumable_revenue_estimate",
    "calibration_revenue_estimate", "report_revenue_estimate",
    "alarm_monitoring_revenue_estimate", "supplier_cost", "shipping_cost",
    "customs_cost", "local_installer_cost", "labor_cost", "travel_cost",
    "spare_parts_cost", "warranty_reserve_cost", "annual_service_cost",
    "direct_cost", "gross_profit", "gross_margin_percent", "first_year_revenue",
    "first_year_profit", "annual_recurring_revenue", "annual_recurring_profit",
    "ltv_3_year", "ltv_5_year", "ltv_8_year",
]


def upgrade() -> None:
    # FI.4.1 — project_finances
    cols = [
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("solution_line", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]
    cols += [sa.Column(c, sa.Float, nullable=False, server_default=_ZERO) for c in _FINANCE_FLOAT_COLS]
    op.create_table("project_finances", *cols)

    # FI.4.2 — platform_fee_rules
    op.create_table(
        "platform_fee_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("solution_line", sa.String(50), nullable=True),
        sa.Column("project_size_band", sa.String(20), nullable=False, server_default=sa.text("'any'")),
        sa.Column("fee_type", sa.String(20), nullable=False, server_default=sa.text("'percentage'")),
        sa.Column("percentage", sa.Float, nullable=True),
        sa.Column("fixed_fee", sa.Float, nullable=True),
        sa.Column("min_fee", sa.Float, nullable=True),
        sa.Column("max_fee", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FI.4.3 — proposal_plans recurring-cost fields
    for col in ("amc_fee", "consumable_fee", "calibration_fee", "reporting_fee",
                "alarm_monitoring_fee", "first_year_total", "annual_recurring_total"):
        op.add_column("proposal_plans", sa.Column(col, sa.Float, nullable=False, server_default=_ZERO))
    op.add_column("proposal_plans", sa.Column("recommended_contract_term_years", sa.Integer, nullable=True))

    # FI.4.4 / FI.4.5 — quote customer line items + internal economics
    op.add_column("quotes", sa.Column("customer_line_items_json", JSONB, nullable=True))
    op.add_column("quotes", sa.Column("internal_economics_json", JSONB, nullable=True))
    op.add_column("quotes", sa.Column("first_year_total", sa.Float, nullable=False, server_default=_ZERO))
    op.add_column("quotes", sa.Column("annual_recurring_total", sa.Float, nullable=False, server_default=_ZERO))


def downgrade() -> None:
    op.drop_column("quotes", "annual_recurring_total")
    op.drop_column("quotes", "first_year_total")
    op.drop_column("quotes", "internal_economics_json")
    op.drop_column("quotes", "customer_line_items_json")

    op.drop_column("proposal_plans", "recommended_contract_term_years")
    for col in ("annual_recurring_total", "first_year_total", "alarm_monitoring_fee",
                "reporting_fee", "calibration_fee", "consumable_fee", "amc_fee"):
        op.drop_column("proposal_plans", col)

    op.drop_table("platform_fee_rules")
    op.drop_table("project_finances")

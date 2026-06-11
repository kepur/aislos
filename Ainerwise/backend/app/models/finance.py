"""Project finance + platform fee models (FI.4.1, FI.4.2).

ProjectFinance is the per-project cost/revenue ledger; the derived margin and
LTV columns are recomputed by `services.finance.compute_finance` on every
create/update so they never go stale. PlatformFeeRule defines how AinerWise
takes a platform / project-management fee by solution line and project size.
"""
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class ProjectFinance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_finances"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    solution_line: Mapped[str | None] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), default="EUR")

    # --- one-time revenue ---
    contract_total: Mapped[float] = mapped_column(Float, default=0)
    hardware_revenue: Mapped[float] = mapped_column(Float, default=0)
    design_fee: Mapped[float] = mapped_column(Float, default=0)
    installation_fee: Mapped[float] = mapped_column(Float, default=0)
    integration_fee: Mapped[float] = mapped_column(Float, default=0)
    platform_fee: Mapped[float] = mapped_column(Float, default=0)
    project_management_fee: Mapped[float] = mapped_column(Float, default=0)

    # --- recurring revenue ---
    amc_fee_year_1: Mapped[float] = mapped_column(Float, default=0)
    amc_fee_annual: Mapped[float] = mapped_column(Float, default=0)
    consumable_revenue_estimate: Mapped[float] = mapped_column(Float, default=0)
    calibration_revenue_estimate: Mapped[float] = mapped_column(Float, default=0)
    report_revenue_estimate: Mapped[float] = mapped_column(Float, default=0)
    alarm_monitoring_revenue_estimate: Mapped[float] = mapped_column(Float, default=0)

    # --- direct costs ---
    supplier_cost: Mapped[float] = mapped_column(Float, default=0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0)
    customs_cost: Mapped[float] = mapped_column(Float, default=0)
    local_installer_cost: Mapped[float] = mapped_column(Float, default=0)
    labor_cost: Mapped[float] = mapped_column(Float, default=0)
    travel_cost: Mapped[float] = mapped_column(Float, default=0)
    spare_parts_cost: Mapped[float] = mapped_column(Float, default=0)
    warranty_reserve_cost: Mapped[float] = mapped_column(Float, default=0)
    annual_service_cost: Mapped[float] = mapped_column(Float, default=0)

    # --- derived (recomputed by services.finance.compute_finance) ---
    direct_cost: Mapped[float] = mapped_column(Float, default=0)
    gross_profit: Mapped[float] = mapped_column(Float, default=0)
    gross_margin_percent: Mapped[float] = mapped_column(Float, default=0)
    first_year_revenue: Mapped[float] = mapped_column(Float, default=0)
    first_year_profit: Mapped[float] = mapped_column(Float, default=0)
    annual_recurring_revenue: Mapped[float] = mapped_column(Float, default=0)
    annual_recurring_profit: Mapped[float] = mapped_column(Float, default=0)
    ltv_3_year: Mapped[float] = mapped_column(Float, default=0)
    ltv_5_year: Mapped[float] = mapped_column(Float, default=0)
    ltv_8_year: Mapped[float] = mapped_column(Float, default=0)

    notes: Mapped[str | None] = mapped_column(Text)


class PlatformFeeRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "platform_fee_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    solution_line: Mapped[str | None] = mapped_column(String(50))
    project_size_band: Mapped[str] = mapped_column(String(20), default="any")  # small|medium|large|any
    fee_type: Mapped[str] = mapped_column(String(20), default="percentage")  # fixed|percentage|hybrid
    percentage: Mapped[float | None] = mapped_column(Float)  # e.g. 0.08 for 8%
    fixed_fee: Mapped[float | None] = mapped_column(Float)
    min_fee: Mapped[float | None] = mapped_column(Float)
    max_fee: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

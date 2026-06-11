"""Schemas for project finance + platform fee rules (FI.4.1, FI.4.2, FI.4.6)."""
import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ProjectFinanceInput(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    solution_line: str | None = None
    currency: str = "EUR"
    contract_total: float = 0
    hardware_revenue: float = 0
    design_fee: float = 0
    installation_fee: float = 0
    integration_fee: float = 0
    platform_fee: float = 0
    project_management_fee: float = 0
    amc_fee_year_1: float = 0
    amc_fee_annual: float = 0
    consumable_revenue_estimate: float = 0
    calibration_revenue_estimate: float = 0
    report_revenue_estimate: float = 0
    alarm_monitoring_revenue_estimate: float = 0
    supplier_cost: float = 0
    shipping_cost: float = 0
    customs_cost: float = 0
    local_installer_cost: float = 0
    labor_cost: float = 0
    travel_cost: float = 0
    spare_parts_cost: float = 0
    warranty_reserve_cost: float = 0
    annual_service_cost: float = 0
    notes: str | None = None


class ProjectFinanceCreate(ProjectFinanceInput):
    pass


class ProjectFinanceUpdate(BaseSchema):
    project_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    solution_line: str | None = None
    currency: str | None = None
    contract_total: float | None = None
    hardware_revenue: float | None = None
    design_fee: float | None = None
    installation_fee: float | None = None
    integration_fee: float | None = None
    platform_fee: float | None = None
    project_management_fee: float | None = None
    amc_fee_year_1: float | None = None
    amc_fee_annual: float | None = None
    consumable_revenue_estimate: float | None = None
    calibration_revenue_estimate: float | None = None
    report_revenue_estimate: float | None = None
    alarm_monitoring_revenue_estimate: float | None = None
    supplier_cost: float | None = None
    shipping_cost: float | None = None
    customs_cost: float | None = None
    local_installer_cost: float | None = None
    labor_cost: float | None = None
    travel_cost: float | None = None
    spare_parts_cost: float | None = None
    warranty_reserve_cost: float | None = None
    annual_service_cost: float | None = None
    notes: str | None = None


class ProjectFinanceRead(ProjectFinanceInput):
    id: uuid.UUID
    # derived (read-only)
    direct_cost: float
    gross_profit: float
    gross_margin_percent: float
    first_year_revenue: float
    first_year_profit: float
    annual_recurring_revenue: float
    annual_recurring_profit: float
    ltv_3_year: float
    ltv_5_year: float
    ltv_8_year: float
    created_at: datetime


class PlatformFeeRuleBase(BaseSchema):
    name: str
    solution_line: str | None = None
    project_size_band: str = "any"
    fee_type: str = "percentage"
    percentage: float | None = None
    fixed_fee: float | None = None
    min_fee: float | None = None
    max_fee: float | None = None
    is_active: bool = True
    notes: str | None = None


class PlatformFeeRuleCreate(PlatformFeeRuleBase):
    pass


class PlatformFeeRuleUpdate(BaseSchema):
    name: str | None = None
    solution_line: str | None = None
    project_size_band: str | None = None
    fee_type: str | None = None
    percentage: float | None = None
    fixed_fee: float | None = None
    min_fee: float | None = None
    max_fee: float | None = None
    is_active: bool | None = None
    notes: str | None = None


class PlatformFeeRuleRead(PlatformFeeRuleBase):
    id: uuid.UUID
    created_at: datetime

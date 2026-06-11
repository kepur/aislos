import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ProposalPlanRead(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    tier: str
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    device_cost_estimate: float
    design_fee_estimate: float
    installation_fee_estimate: float
    platform_fee_estimate: float
    maintenance_fee_estimate: float
    spare_parts_reserve: float
    total_min: float
    total_max: float
    currency: str
    complexity: str | None = None
    risk_level: str | None = None
    recommended_next_step: str | None = None
    estimate_only: bool
    notes: str | None = None
    amc_fee: float = 0
    consumable_fee: float = 0
    calibration_fee: float = 0
    reporting_fee: float = 0
    alarm_monitoring_fee: float = 0
    first_year_total: float = 0
    annual_recurring_total: float = 0
    recommended_contract_term_years: int | None = None
    created_at: datetime
    updated_at: datetime


class ProposalPlanCreate(BaseSchema):
    lead_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    tier: str
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    device_cost_estimate: float = 0
    design_fee_estimate: float = 0
    installation_fee_estimate: float = 0
    platform_fee_estimate: float = 0
    maintenance_fee_estimate: float = 0
    spare_parts_reserve: float = 0
    total_min: float = 0
    total_max: float = 0
    currency: str = "EUR"
    complexity: str | None = None
    risk_level: str | None = None
    recommended_next_step: str | None = None
    estimate_only: bool = True
    notes: str | None = None
    amc_fee: float = 0
    consumable_fee: float = 0
    calibration_fee: float = 0
    reporting_fee: float = 0
    alarm_monitoring_fee: float = 0
    first_year_total: float = 0
    annual_recurring_total: float = 0
    recommended_contract_term_years: int | None = None


class ProposalPlanUpdate(BaseSchema):
    tier: str | None = None
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    device_cost_estimate: float | None = None
    design_fee_estimate: float | None = None
    installation_fee_estimate: float | None = None
    platform_fee_estimate: float | None = None
    maintenance_fee_estimate: float | None = None
    spare_parts_reserve: float | None = None
    total_min: float | None = None
    total_max: float | None = None
    currency: str | None = None
    complexity: str | None = None
    risk_level: str | None = None
    recommended_next_step: str | None = None
    notes: str | None = None
    amc_fee: float | None = None
    consumable_fee: float | None = None
    calibration_fee: float | None = None
    reporting_fee: float | None = None
    alarm_monitoring_fee: float | None = None
    first_year_total: float | None = None
    annual_recurring_total: float | None = None
    recommended_contract_term_years: int | None = None


class BOMItemRead(BaseSchema):
    id: uuid.UUID
    proposal_plan_id: uuid.UUID
    product_id: uuid.UUID | None = None
    category: str | None = None
    name: str
    brand: str | None = None
    qty: int
    unit_price: float
    device_cost: float
    installation_cost: float
    service_fee: float
    maintenance_years: int | None = None
    already_owned: bool
    need_ainerwise_supply: bool
    need_installation: bool
    design_only: bool
    total: float
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BOMItemCreate(BaseSchema):
    proposal_plan_id: uuid.UUID
    product_id: uuid.UUID | None = None
    category: str | None = None
    name: str
    brand: str | None = None
    qty: int = 1
    unit_price: float = 0
    device_cost: float = 0
    installation_cost: float = 0
    service_fee: float = 0
    maintenance_years: int | None = None
    already_owned: bool = False
    need_ainerwise_supply: bool = True
    need_installation: bool = True
    design_only: bool = False
    total: float = 0
    notes: str | None = None


class BOMItemUpdate(BaseSchema):
    product_id: uuid.UUID | None = None
    category: str | None = None
    name: str | None = None
    brand: str | None = None
    qty: int | None = None
    unit_price: float | None = None
    device_cost: float | None = None
    installation_cost: float | None = None
    service_fee: float | None = None
    maintenance_years: int | None = None
    already_owned: bool | None = None
    need_ainerwise_supply: bool | None = None
    need_installation: bool | None = None
    design_only: bool | None = None
    total: float | None = None
    notes: str | None = None

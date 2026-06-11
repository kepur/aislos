import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class ProductCategoryRead(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None = None
    icon: str | None = None
    sort_order: int


class ProductCategoryCreate(BaseSchema):
    name: str
    slug: str
    parent_id: uuid.UUID | None = None
    icon: str | None = None
    sort_order: int = 0


class ProductRead(BaseSchema):
    id: uuid.UUID
    owner_company_id: uuid.UUID | None = None
    source_type: str
    category_id: uuid.UUID | None = None
    name: str
    slug: str
    brand: str | None = None
    description: str | None = None
    specs_json: dict | None = None
    images_json: list | None = None
    list_price: float | None = None
    currency: str
    moq: int
    lead_time_days: int | None = None
    warranty_years: int | None = None
    spare_policy_json: dict | None = None
    service_available: bool
    service_term_years_json: list | None = None
    price_options_json: list | None = None
    lifecycle_pricing_json: list | None = None
    project_pricing_mode: str | None = None
    service_pricing_note: str | None = None
    supply_tier: str | None = None
    supplier_ecosystem_json: list | None = None
    supported_regions_json: list | None = None
    certifications_json: list | None = None
    protocol_json: list | None = None
    scenario_tags_json: list | None = None
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    feature_status: str | None = None
    risk_level: str | None = None
    status: str
    # FI.2.2 — public-safe lifecycle fields only. internal_model, supplier_id,
    # cost_price, and replacement_margin_percent stay out of the shared read
    # schema to preserve the public privacy boundary (FI.9.3).
    solution_line: str | None = None
    public_name: str | None = None
    recurring_revenue_types_json: list | None = None
    consumable_cycle_months: int | None = None
    calibration_cycle_months: int | None = None
    expected_lifetime_months: int | None = None
    required_for_compliance: bool | None = None
    report_template_available: bool | None = None
    amc_required: bool | None = None
    amc_recommended: bool | None = None
    service_dependency_level: str | None = None
    created_at: datetime


class ProductCreate(BaseSchema):
    name: str
    slug: str | None = None
    brand: str | None = None
    category_id: uuid.UUID | None = None
    source_type: str = "official"
    description: str | None = None
    specs_json: dict | None = None
    images_json: list | None = None
    cost_price: float | None = None
    list_price: float | None = None
    currency: str = "EUR"
    moq: int = 1
    lead_time_days: int | None = None
    warranty_years: int | None = None
    spare_policy_json: dict | None = None
    service_available: bool = False
    service_term_years_json: list | None = None
    price_options_json: list | None = None
    lifecycle_pricing_json: list | None = None
    project_pricing_mode: str | None = None
    service_pricing_note: str | None = None
    supply_tier: str | None = None
    supplier_ecosystem_json: list | None = None
    supported_regions_json: list | None = None
    certifications_json: list | None = None
    protocol_json: list | None = None
    scenario_tags_json: list | None = None
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    feature_status: str | None = None
    risk_level: str | None = None
    status: str = "draft"
    # FI.2.2 lifecycle fields (admin-managed, includes sensitive supplier/margin)
    solution_line: str | None = None
    public_name: str | None = None
    internal_model: str | None = None
    supplier_id: uuid.UUID | None = None
    recurring_revenue_types_json: list | None = None
    consumable_cycle_months: int | None = None
    calibration_cycle_months: int | None = None
    expected_lifetime_months: int | None = None
    replacement_margin_percent: float | None = None
    required_for_compliance: bool | None = None
    report_template_available: bool | None = None
    amc_required: bool | None = None
    amc_recommended: bool | None = None
    service_dependency_level: str | None = None


class ProductUpdate(BaseSchema):
    name: str | None = None
    brand: str | None = None
    category_id: uuid.UUID | None = None
    description: str | None = None
    specs_json: dict | None = None
    images_json: list | None = None
    cost_price: float | None = None
    list_price: float | None = None
    currency: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    warranty_years: int | None = None
    spare_policy_json: dict | None = None
    service_available: bool | None = None
    service_term_years_json: list | None = None
    price_options_json: list | None = None
    lifecycle_pricing_json: list | None = None
    project_pricing_mode: str | None = None
    service_pricing_note: str | None = None
    supply_tier: str | None = None
    supplier_ecosystem_json: list | None = None
    supported_regions_json: list | None = None
    certifications_json: list | None = None
    protocol_json: list | None = None
    scenario_tags_json: list | None = None
    intelligence_level_min: int | None = None
    intelligence_level_max: int | None = None
    feature_status: str | None = None
    risk_level: str | None = None
    # FI.2.2 lifecycle fields
    solution_line: str | None = None
    public_name: str | None = None
    internal_model: str | None = None
    supplier_id: uuid.UUID | None = None
    recurring_revenue_types_json: list | None = None
    consumable_cycle_months: int | None = None
    calibration_cycle_months: int | None = None
    expected_lifetime_months: int | None = None
    replacement_margin_percent: float | None = None
    required_for_compliance: bool | None = None
    report_template_available: bool | None = None
    amc_required: bool | None = None
    amc_recommended: bool | None = None
    service_dependency_level: str | None = None


class ProductStatusUpdate(BaseSchema):
    status: str

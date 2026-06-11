import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class LeadCreate(BaseSchema):
    project_type: str | None = None
    country: str | None = None
    city: str | None = None
    site_info_json: dict | None = None
    budget_range: str | None = None
    systems_needed_json: list | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    site_info_json: dict | None = None
    language: str = "en"
    solution_id: uuid.UUID | None = None
    lead_score: int | None = None
    lead_stage: str | None = None
    desired_intelligence_level: int | None = None
    conversation_json: list | None = None
    proposal_tiers_json: dict | None = None
    campaign_id: uuid.UUID | None = None
    source_channel: str | None = None
    source_detail: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    landing_page: str | None = None
    referrer: str | None = None


class LeadUpdate(BaseSchema):
    project_type: str | None = None
    country: str | None = None
    city: str | None = None
    budget_range: str | None = None
    systems_needed_json: list | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    site_info_json: dict | None = None
    notes: str | None = None
    lead_score: int | None = None
    lead_stage: str | None = None
    desired_intelligence_level: int | None = None
    conversation_json: list | None = None
    proposal_tiers_json: dict | None = None
    # FI.2.3 recurring-revenue qualification
    solution_line: str | None = None
    recurring_revenue_score: int | None = None
    compliance_risk_level: str | None = None
    consumable_potential: str | None = None
    amc_potential: str | None = None
    estimated_arr: float | None = None
    estimated_ltv: float | None = None
    is_multi_site: bool | None = None
    monitoring_points_count: int | None = None


class LeadRead(BaseSchema):
    id: uuid.UUID
    buyer_company_id: uuid.UUID | None = None
    buyer_user_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    project_type: str | None = None
    country: str | None = None
    city: str | None = None
    budget_range: str | None = None
    systems_needed_json: list | None = None
    description: str | None = None
    uploaded_files_json: list | None = None
    ai_analysis_json: dict | None = None
    status: str
    assigned_admin_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
    language: str
    notes: str | None = None
    lead_score: int | None = None
    lead_stage: str | None = None
    desired_intelligence_level: int | None = None
    conversation_json: list | None = None
    proposal_tiers_json: dict | None = None
    campaign_id: uuid.UUID | None = None
    source_channel: str | None = None
    source_detail: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    landing_page: str | None = None
    referrer: str | None = None
    # FI.2.3 recurring-revenue qualification
    solution_line: str | None = None
    recurring_revenue_score: int | None = None
    compliance_risk_level: str | None = None
    consumable_potential: str | None = None
    amc_potential: str | None = None
    estimated_arr: float | None = None
    estimated_ltv: float | None = None
    is_multi_site: bool | None = None
    monitoring_points_count: int | None = None
    created_at: datetime


class LeadStatusUpdate(BaseSchema):
    status: str


class LeadAssign(BaseSchema):
    assigned_admin_id: uuid.UUID


class LeadNotesUpdate(BaseSchema):
    notes: str

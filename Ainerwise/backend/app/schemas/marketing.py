import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class MarketingCampaignBase(BaseSchema):
    name: str
    channel: str
    objective: str | None = None
    status: str = "draft"
    landing_path: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str
    audience_json: dict | None = None
    offer_json: dict | None = None
    content_json: dict | None = None
    budget: float | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class MarketingCampaignCreate(MarketingCampaignBase):
    pass


class MarketingCampaignUpdate(BaseSchema):
    name: str | None = None
    channel: str | None = None
    objective: str | None = None
    status: str | None = None
    landing_path: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    audience_json: dict | None = None
    offer_json: dict | None = None
    content_json: dict | None = None
    budget: float | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class MarketingCampaignRead(MarketingCampaignBase):
    id: uuid.UUID
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class MarketingContactBase(BaseSchema):
    company_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    language: str = "en"
    segment: str | None = None
    source: str | None = None
    status: str = "prospect"
    consent_status: str = "unknown"
    tags_json: list | None = None
    notes: str | None = None
    lead_id: uuid.UUID | None = None
    last_contacted_at: datetime | None = None
    next_follow_up_at: datetime | None = None


class MarketingContactCreate(MarketingContactBase):
    pass


class MarketingContactUpdate(BaseSchema):
    company_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    language: str | None = None
    segment: str | None = None
    source: str | None = None
    status: str | None = None
    consent_status: str | None = None
    tags_json: list | None = None
    notes: str | None = None
    lead_id: uuid.UUID | None = None
    last_contacted_at: datetime | None = None
    next_follow_up_at: datetime | None = None


class MarketingContactRead(MarketingContactBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MarketingActivityBase(BaseSchema):
    campaign_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    inquiry_id: uuid.UUID | None = None
    activity_type: str
    channel: str
    direction: str = "outbound"
    status: str = "pending_approval"
    subject: str | None = None
    content: str | None = None
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict | None = None


class MarketingActivityCreate(MarketingActivityBase):
    pass


class MarketingActivityUpdate(BaseSchema):
    campaign_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    inquiry_id: uuid.UUID | None = None
    activity_type: str | None = None
    channel: str | None = None
    direction: str | None = None
    status: str | None = None
    subject: str | None = None
    content: str | None = None
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict | None = None


class MarketingActivityRead(MarketingActivityBase):
    id: uuid.UUID
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class DeliverableSpec(BaseSchema):
    key: str
    media_type: str
    channel: str
    language: str
    format: str
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    variant_count: int = 1
    required_text: list[str] | None = None
    notes: str | None = None


class CreativeBriefVersionContent(BaseSchema):
    copy_json: dict | None = None
    audience_json: dict | None = None
    brand_constraints_json: dict | None = None
    channel_specs_json: dict | None = None
    deliverables_json: list[DeliverableSpec] | None = None
    source_refs_json: dict | None = None
    compliance_json: dict | None = None


class CreativeBriefCreate(BaseSchema):
    title: str
    objective: str | None = None
    campaign_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    version: CreativeBriefVersionContent


class CreativeBriefVersionCreate(CreativeBriefVersionContent):
    pass


class CreativeBriefVersionUpdate(CreativeBriefVersionContent):
    pass


class CreativeBriefVersionRead(CreativeBriefVersionContent):
    id: uuid.UUID
    brief_id: uuid.UUID
    version: int
    status: str
    content_hash: str | None = None
    review_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class CreativeBriefRead(BaseSchema):
    id: uuid.UUID
    campaign_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    title: str
    objective: str | None = None
    status: str
    current_version_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    current_version: CreativeBriefVersionRead | None = None


class CreativeBriefExternalExport(BaseSchema):
    """Provider-neutral export view — no CRM, costs or internal review metadata."""

    brief_id: uuid.UUID
    title: str
    objective: str | None = None
    version: int
    copy_block: dict = Field(serialization_alias="copy")
    audience: dict
    brand_constraints: dict
    channel_specs: dict
    deliverables: list
    compliance: dict
    content_hash: str | None = None


class BriefReviewAction(BaseSchema):
    notes: str | None = None


class BriefRejectAction(BaseSchema):
    reason: str


class MediaRequestRead(BaseSchema):
    id: uuid.UUID
    brief_version_id: uuid.UUID
    deliverable_key: str
    status: str
    submitted_asset_count: int
    progress_percent: int | None = None
    progress_message: str | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    external_job_ref: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

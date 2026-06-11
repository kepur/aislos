import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.trust import TrustEntityType, TrustProfileStatus, TrustTier


class TrustProfileResponse(BaseModel):
    id: uuid.UUID
    entity_type: TrustEntityType
    entity_id: uuid.UUID
    trust_score: int
    trust_tier: TrustTier
    profile_completion_rate: int
    deal_completion_rate: int
    deposit_amount_minor: int
    deposit_currency: str
    verified_deposit_minor: int
    successful_deals_count: int
    canceled_deals_count: int
    dispute_rate: int
    refund_rate: int
    late_delivery_rate: int
    late_payment_rate: int
    score_breakdown_json: dict | None
    status: TrustProfileStatus
    last_calculated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrustMeResponse(BaseModel):
    user: TrustProfileResponse
    company: TrustProfileResponse | None = None


class TrustAdjustRequest(BaseModel):
    score_delta: int = Field(ge=-1000, le=1000)
    reason: str = Field(min_length=3, max_length=500)
    freeze: bool | None = None


class TrustSummaryResponse(BaseModel):
    entity_type: TrustEntityType
    entity_id: uuid.UUID
    trust_score: int
    trust_tier: TrustTier
    profile_completion_rate: int
    deal_completion_rate: int
    deposit_amount_minor: int
    deposit_currency: str
    successful_deals_count: int
    canceled_deals_count: int
    dispute_rate: int
    refund_rate: int
    status: TrustProfileStatus

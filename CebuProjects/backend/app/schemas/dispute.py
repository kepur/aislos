import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dispute import DisputeStatus


class DisputeCreate(BaseModel):
    reason: str
    evidence: list[dict] = []


class DisputeResolve(BaseModel):
    decision: str
    refund_amount_minor: int | None = None
    resolution: str | None = None


class DisputeResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    opened_by_user_id: uuid.UUID
    reason: str
    status: DisputeStatus
    evidence_json: list | None
    admin_notes: str | None
    resolution: str | None
    refund_amount_minor: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

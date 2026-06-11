import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.audit_log import RiskLevel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_role: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    before_json: dict | None
    after_json: dict | None
    ip_address: str | None
    risk_level: RiskLevel
    created_at: datetime

    model_config = {"from_attributes": True}

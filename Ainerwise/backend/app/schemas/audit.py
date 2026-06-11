import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class AuditLogRead(BaseSchema):
    id: uuid.UUID
    actor_type: str = "user"
    actor_user_id: uuid.UUID | None = None
    agent_slug: str | None = None
    portal_key: str | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    before_json: dict | None = None
    after_json: dict | None = None
    reason: str | None = None
    source: str | None = None
    correlation_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime

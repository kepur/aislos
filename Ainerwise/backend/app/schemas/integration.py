import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class IntegrationEventRead(BaseSchema):
    id: uuid.UUID
    event_type: str
    payload_json: dict | None = None
    target_channel: str | None = None
    status: str
    retry_count: int
    error_message: str | None = None
    aggregate_type: str | None = None
    aggregate_id: uuid.UUID | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AIRunRead(BaseSchema):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    workflow_name: str
    input_json: dict | None = None
    output_json: dict | None = None
    model_name: str | None = None
    tokens_used: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

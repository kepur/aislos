from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LegacyBridgeEventIn(BaseModel):
    event_type: str = Field(..., min_length=3, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)
    portal_key: str = Field(default="cebu", max_length=50)
    correlation_id: str | None = Field(default=None, max_length=64)


class LegacyBridgeEventOut(BaseModel):
    accepted: bool = True
    event_type: str
    idempotency_key: str
    correlation_id: str | None = None
    lead_id: UUID | None = None
    mapping_id: UUID | None = None
    core_event_id: UUID | None = None

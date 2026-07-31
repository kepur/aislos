import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrivacyRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    request_type: str
    status: str
    reviewed_by_user_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    review_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class PrivacyReview(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)

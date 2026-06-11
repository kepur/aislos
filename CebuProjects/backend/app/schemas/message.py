import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    body: str
    attachments: list[str] = []


class MessageResponse(BaseModel):
    id: uuid.UUID
    thread_type: str
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    attachments: list | None
    created_at: datetime

    model_config = {"from_attributes": True}

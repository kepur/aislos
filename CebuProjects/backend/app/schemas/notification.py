import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationStatus


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    channel: NotificationChannel
    notification_type: str
    subject: str | None
    body: str
    status: NotificationStatus
    created_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}

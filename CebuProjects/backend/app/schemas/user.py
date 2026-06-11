import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import AccountType, UserRole, UserStatus


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    role: UserRole
    status: UserStatus
    account_type: AccountType
    full_name: str
    avatar_url: str | None
    telegram_chat_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


class TelegramUpdate(BaseModel):
    telegram_chat_id: str | None = None


class NotificationChannelSettings(BaseModel):
    email: bool = True
    telegram: bool = False


class NotificationEventSettings(BaseModel):
    new_message: bool = True
    intent_match: bool = True
    offer_received: bool = True
    offer_awarded: bool = True
    order_update: bool = True
    delivery_update: bool = True


class NotificationPreferencesBase(BaseModel):
    channels: NotificationChannelSettings = Field(default_factory=NotificationChannelSettings)
    events: NotificationEventSettings = Field(default_factory=NotificationEventSettings)


class NotificationPreferencesResponse(NotificationPreferencesBase):
    email: str
    telegram_chat_id: str | None = None
    telegram_connected: bool


class NotificationPreferencesUpdate(BaseModel):
    channels: NotificationChannelSettings | None = None
    events: NotificationEventSettings | None = None

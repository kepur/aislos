"""Admin-configurable integration settings (SMTP / Telegram / AI agent)."""
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

# Categories + which config keys are secret (masked on read).
INTEGRATION_CATEGORIES = ("smtp", "telegram", "ai", "voice")
SECRET_KEYS = {
    "smtp": ("password",),
    "telegram": ("bot_token",),
    "ai": ("api_key",),
    "ai_media": ("api_key",),
    "social": ("api_key",),
    "stripe": ("secret_key", "webhook_secret"),
    "voice": ("api_key",),
}


class IntegrationSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "integration_settings"

    category: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

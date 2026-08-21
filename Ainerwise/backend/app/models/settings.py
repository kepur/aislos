"""Admin-configurable integration settings."""
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

# Categories + which config keys are secret (masked on read).
INTEGRATION_CATEGORIES = (
    "smtp", "telegram", "whatsapp", "ai", "voice", "social", "stripe", "source", "pricing"
)
SECRET_KEYS = {
    "smtp": ("password", "inbound_webhook_secret"),
    "telegram": ("bot_token",),
    "whatsapp": ("access_token", "app_secret", "verify_token"),
    "ai": ("api_key",),
    "social": ("api_key",),
    "stripe": ("secret_key", "webhook_secret"),
    "voice": ("api_key",),
    # Growth sourcing: source cookies / third-party data API keys.
    "source": ("api_key", "cookie", "access_token"),
    # Growth pricing: default markup/freight config (no secrets, listed for completeness).
    "pricing": (),
}


class IntegrationSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "integration_settings"

    category: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

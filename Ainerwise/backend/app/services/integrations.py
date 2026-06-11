"""Integration config access + secret masking (SMTP / Telegram / AI)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.settings import SECRET_KEYS, IntegrationSetting

# Non-secret defaults shown in the admin form when nothing is saved yet.
DEFAULTS: dict[str, dict[str, Any]] = {
    "smtp": {"host": "", "port": 587, "username": "", "from_email": "", "from_name": "AinerWise", "use_tls": True, "use_ssl": False},
    "telegram": {"admin_chat_id": "", "webhook_url": ""},
    "ai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "temperature": 0.3, "system_prompt": "", "embedding_model": "text-embedding-3-small"},
    # Image generation (OpenAI-compatible /images/generations endpoint).
    "ai_media": {"base_url": "https://api.openai.com/v1", "image_model": "gpt-image-1", "image_size": "1024x1024"},
    # Social publishing aggregator (Ayrshare-style REST: POST {base_url}/post).
    "social": {"base_url": "https://app.ayrshare.com/api", "default_platforms": ["linkedin", "facebook"]},
    # Stripe Connect (requires EU platform entity — see ARCHITECTURE_CONSTITUTION Art.3).
    "stripe": {"success_url": "", "cancel_url": ""},
    # Kiosk realtime voice (Experience Center). OpenAI-Realtime-compatible:
    # ephemeral client secrets are minted server-side; the key never reaches tablets.
    "voice": {
        "provider": "openai-realtime",
        "base_url": "https://api.openai.com/v1",
        "webrtc_url": "https://api.openai.com/v1/realtime/calls",
        "model": "gpt-realtime",
        "voice": "alloy",
        "transcription_model": "gpt-4o-mini-transcribe",
    },
}


async def get_setting(db: AsyncSession, category: str) -> IntegrationSetting | None:
    result = await db.execute(select(IntegrationSetting).where(IntegrationSetting.category == category))
    return result.scalar_one_or_none()


async def get_config(db: AsyncSession, category: str) -> dict[str, Any]:
    """Raw config (with secrets) for internal service use."""
    row = await get_setting(db, category)
    cfg = dict(DEFAULTS.get(category, {}))
    if row and row.config_json:
        cfg.update(row.config_json)
    cfg["_enabled"] = bool(row.is_enabled) if row else False
    # Env fallback for Telegram so existing deployments keep working.
    if category == "telegram":
        cfg.setdefault("bot_token", "") or None
        if not cfg.get("bot_token") and settings.TELEGRAM_BOT_TOKEN:
            cfg["bot_token"] = settings.TELEGRAM_BOT_TOKEN
        if not cfg.get("admin_chat_id") and settings.TELEGRAM_ADMIN_CHAT_ID:
            cfg["admin_chat_id"] = settings.TELEGRAM_ADMIN_CHAT_ID
        if (cfg.get("bot_token") and cfg.get("admin_chat_id")) and not row:
            cfg["_enabled"] = True
    return cfg


def mask_config(category: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Public/admin-safe view: secrets become `<field>_set` booleans, not values."""
    out: dict[str, Any] = {}
    secrets = SECRET_KEYS.get(category, ())
    for k, v in cfg.items():
        if k.startswith("_"):
            continue
        if k in secrets:
            out[f"{k}_set"] = bool(v)
        else:
            out[k] = v
    return out


async def upsert_config(db: AsyncSession, category: str, *, config: dict[str, Any], is_enabled: bool | None) -> IntegrationSetting:
    """Merge new config; empty secret fields keep the previously stored value."""
    row = await get_setting(db, category)
    existing = dict(row.config_json) if row and row.config_json else {}
    secrets = SECRET_KEYS.get(category, ())
    merged = dict(existing)
    for k, v in (config or {}).items():
        if k in secrets and (v is None or v == ""):
            continue  # don't overwrite a stored secret with blank
        merged[k] = v
    if row is None:
        row = IntegrationSetting(category=category, config_json=merged, is_enabled=bool(is_enabled))
        db.add(row)
    else:
        row.config_json = merged
        if is_enabled is not None:
            row.is_enabled = is_enabled
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def telegram_credentials(db: AsyncSession) -> tuple[str | None, str | None]:
    cfg = await get_config(db, "telegram")
    return cfg.get("bot_token") or None, cfg.get("admin_chat_id") or None

"""Admin integration settings (SMTP/Telegram/AI) + public AI assistant."""
from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import AdminUser, DB
from app.models.settings import INTEGRATION_CATEGORIES
from app.services import ai_agent, email
from app.services.integrations import (
    get_config,
    get_setting,
    mask_config,
    telegram_credentials,
    upsert_config,
)

router = APIRouter(tags=["integrations"])


# --- admin: read/update integration settings -------------------------------

@router.get("/admin/integrations")
async def list_integrations(db: DB, admin: AdminUser):
    out = []
    for cat in INTEGRATION_CATEGORIES:
        cfg = await get_config(db, cat)
        row = await get_setting(db, cat)
        out.append({
            "category": cat,
            "is_enabled": cfg.get("_enabled", False),
            "config": mask_config(cat, cfg),
            "configured_in_db": row is not None,
        })
    return {"items": out}


class IntegrationUpdate(BaseModel):
    is_enabled: bool | None = None
    config: dict[str, Any] = {}


@router.put("/admin/integrations/{category}")
async def update_integration(category: str, data: IntegrationUpdate, db: DB, admin: AdminUser):
    if category not in INTEGRATION_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown integration category")
    await upsert_config(db, category, config=data.config, is_enabled=data.is_enabled)
    cfg = await get_config(db, category)
    return {"category": category, "is_enabled": cfg.get("_enabled", False), "config": mask_config(category, cfg)}


# --- admin: test an integration --------------------------------------------

class SmtpTest(BaseModel):
    to: str


@router.post("/admin/integrations/smtp/test")
async def test_smtp(data: SmtpTest, db: DB, admin: AdminUser):
    return await email.send_email(
        db, to=data.to, subject="AinerWise SMTP test",
        body="This is a test email from your AinerWise admin integration settings.",
    )


@router.post("/admin/integrations/telegram/test")
async def test_telegram(db: DB, admin: AdminUser):
    token, chat_id = await telegram_credentials(db)
    if not token or not chat_id:
        return {"sent": False, "reason": "telegram_not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": "AinerWise Telegram test ✅"},
            )
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return {"sent": False, "reason": str(exc)}
    return {"sent": True}


@router.post("/admin/integrations/ai/test")
async def test_ai(db: DB, admin: AdminUser):
    reply = await ai_agent.chat(
        db,
        [{"role": "user", "content": "Reply with exactly: AinerWise AI OK"}],
        max_tokens=20,
    )
    if reply is None:
        return {"ok": False, "reason": "ai_not_configured_or_failed"}
    return {"ok": True, "reply": reply.strip()}


@router.post("/admin/integrations/voice/test")
async def test_voice(db: DB, admin: AdminUser):
    cfg = await get_config(db, "voice")
    if not (cfg.get("_enabled") and cfg.get("api_key") and cfg.get("base_url") and cfg.get("model")):
        return {"ok": False, "reason": "voice_not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                cfg["base_url"].rstrip("/") + "/models",
                headers={"Authorization": f"Bearer {cfg['api_key']}"},
            )
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}
    return {"ok": True, "provider": cfg.get("provider"), "model": cfg.get("model")}


# --- public: AI assistant for the facility assessment ----------------------

class AssistantRequest(BaseModel):
    category: str
    messages: list[dict[str, str]]
    collected: dict[str, Any] = {}


@router.post("/ai/assistant")
async def ai_assistant(data: AssistantRequest, db: DB):
    """Drive one assistant turn during the conversational intake.

    Returns {configured: false} when no AI is set up, so the frontend falls back
    to its scripted question flow with no regression.
    """
    return await ai_agent.run_assistant(
        db, category=data.category, messages=data.messages, collected=data.collected,
    )


@router.get("/ai/assistant/status")
async def ai_assistant_status(db: DB):
    return {"configured": await ai_agent.is_configured(db)}

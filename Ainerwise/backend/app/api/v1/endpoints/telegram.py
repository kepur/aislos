"""Telegram webhook endpoint (5.15).

Receives Telegram updates and dispatches admin bot commands. Telegram requires
a fast response; the standard secret-token header authenticates Telegram before
the configured admin chat id is checked inside the handler.
"""
import secrets

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import DB
from app.core.config import settings
from app.services.telegram_bot import handle_update

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request, db: DB):
    configured = settings.TELEGRAM_WEBHOOK_SECRET
    provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not configured or not secrets.compare_digest(provided, configured):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")
    try:
        update = await request.json()
    except Exception:
        return {"ok": True}
    return await handle_update(db, update)

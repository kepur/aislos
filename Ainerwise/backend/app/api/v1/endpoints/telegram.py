"""Telegram webhook endpoint (5.15).

Receives Telegram updates and dispatches admin bot commands. Telegram requires
a fast 200 response; auth is by matching the configured admin chat id inside the
handler (set the webhook with a secret path in production).
"""
from fastapi import APIRouter, Request

from app.api.deps import DB
from app.services.telegram_bot import handle_update

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request, db: DB):
    try:
        update = await request.json()
    except Exception:
        return {"ok": True}
    return await handle_update(db, update)

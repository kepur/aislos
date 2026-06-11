from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.integration import IntegrationEvent
from app.services.notification_templates import render_telegram


def _telegram_message(event_type: str, payload: dict) -> str:
    return render_telegram(event_type, payload)


async def create_integration_event(
    db: AsyncSession,
    *,
    event_type: str,
    payload: dict,
    target_channel: str = "telegram_admin",
    dispatch: bool = True,
) -> IntegrationEvent:
    event = IntegrationEvent(
        event_type=event_type,
        payload_json=payload,
        target_channel=target_channel,
        status="pending",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    if dispatch and target_channel == "telegram_admin":
        await dispatch_telegram_event(db, event)

    return event


async def dispatch_telegram_event(db: AsyncSession, event: IntegrationEvent) -> IntegrationEvent:
    # Admin-configured credentials (DB) take precedence over env.
    from app.services.integrations import telegram_credentials

    bot_token, admin_chat_id = await telegram_credentials(db)
    if not bot_token or not admin_chat_id:
        event.status = "skipped"
        event.error_message = "Telegram is not configured. Configure it in Admin → Integrations (or set TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_CHAT_ID)."
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    message = _telegram_message(event.event_type, event.payload_json or {})
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": admin_chat_id,
                    "text": message,
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()
    except Exception as exc:
        event.status = "failed"
        event.retry_count = (event.retry_count or 0) + 1
        event.error_message = str(exc)
    else:
        event.status = "sent"
        event.error_message = None

    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

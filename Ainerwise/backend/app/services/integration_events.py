from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.integration import IntegrationEvent
from app.services.event_bus import emit_event
from app.services.notification_templates import render_telegram


def _telegram_message(event_type: str, payload: dict) -> str:
    return render_telegram(event_type, payload)


async def queue_admin_telegram(
    db: AsyncSession,
    *,
    event_type: str,
    payload: dict,
    aggregate_type: str | None = None,
    aggregate_id=None,
) -> IntegrationEvent:
    """Enqueue admin Telegram delivery in the caller's transaction (no auto-dispatch)."""
    return await emit_event(
        db,
        event_type=event_type,
        payload=payload,
        target_channel="telegram_admin",
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
    )


async def create_integration_event(
    db: AsyncSession,
    *,
    event_type: str,
    payload: dict,
    target_channel: str = "telegram_admin",
    dispatch: bool = True,
) -> IntegrationEvent:
    """Legacy immediate-dispatch helper.

    New business flows must use ``emit_event`` or ``queue_admin_telegram`` so
    business state and the outbox row commit atomically.
    """
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
    """Legacy/admin retry entry point that owns the delivery transaction."""
    await deliver_telegram_event(db, event)
    await db.commit()
    await db.refresh(event)
    return event


async def deliver_telegram_event(db: AsyncSession, event: IntegrationEvent) -> IntegrationEvent:
    """Attempt one Telegram delivery without committing the caller's transaction."""
    # Admin-configured credentials (DB) take precedence over env.
    from app.services.integrations import telegram_credentials

    bot_token, admin_chat_id = await telegram_credentials(db)
    if not bot_token or not admin_chat_id:
        event.status = "skipped"
        event.error_message = "Telegram is not configured. Configure it in Admin → Integrations (or set TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_CHAT_ID)."
        db.add(event)
        await db.flush()
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
    await db.flush()
    return event


async def dispatch_pending_telegram_events(
    db: AsyncSession,
    *,
    batch_size: int = 50,
    max_retries: int = 5,
) -> int:
    """Deliver queued Telegram outbox rows with concurrent-worker locking."""
    result = await db.execute(
        select(IntegrationEvent)
        .where(
            IntegrationEvent.target_channel == "telegram_admin",
            IntegrationEvent.status.in_(("pending", "failed")),
            IntegrationEvent.retry_count < max_retries,
        )
        .order_by(IntegrationEvent.created_at)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    events = list(result.scalars().all())
    for event in events:
        await deliver_telegram_event(db, event)
    await db.commit()
    return len(events)

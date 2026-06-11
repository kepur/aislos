import uuid
from copy import deepcopy
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.user import User

DEFAULT_NOTIFICATION_PREFERENCES = {
    "channels": {
        "email": True,
        "telegram": False,
    },
    "events": {
        "new_message": True,
        "intent_match": True,
        "offer_received": True,
        "offer_awarded": True,
        "order_update": True,
        "delivery_update": True,
    },
}

NOTIFICATION_EVENT_MAP = {
    "MESSAGE_RECEIVED": "new_message",
    "NEW_INTENT_FOR_SUPPLIER": "intent_match",
    "NEW_OFFER_FOR_BUYER": "offer_received",
    "OFFER_AWARDED_SUPPLIER": "offer_awarded",
    "ORDER_UPDATED_BUYER": "order_update",
    "ORDER_UPDATED_SUPPLIER": "order_update",
    "DELIVERY_UPDATED_BUYER": "delivery_update",
    "DELIVERY_UPDATED_SUPPLIER": "delivery_update",
}


def get_merged_notification_preferences(raw: dict | None) -> dict:
    merged = deepcopy(DEFAULT_NOTIFICATION_PREFERENCES)
    if not raw:
        return merged
    for section in ("channels", "events"):
        section_values = raw.get(section) or {}
        if isinstance(section_values, dict):
            merged[section].update(section_values)
    return merged


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    channel: NotificationChannel,
    notification_type: str,
    subject: str | None = None,
    body: str,
) -> Notification:
    n = Notification(
        user_id=user_id,
        channel=channel,
        notification_type=notification_type,
        subject=subject,
        body=body,
    )
    db.add(n)
    await db.flush()

    if channel == NotificationChannel.IN_APP:
        n.status = NotificationStatus.SENT
        n.sent_at = datetime.now(timezone.utc)
    elif channel == NotificationChannel.TELEGRAM:
        await _send_telegram(db, n)
    elif channel == NotificationChannel.EMAIL:
        await _send_email(db, n)

    return n


async def notify_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: str,
    body: str,
    subject: str | None = None,
) -> None:
    await create_notification(
        db,
        user_id=user_id,
        channel=NotificationChannel.IN_APP,
        notification_type=notification_type,
        subject=subject,
        body=body,
    )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    prefs = get_merged_notification_preferences(user.notification_preferences)
    event_key = NOTIFICATION_EVENT_MAP.get(notification_type)
    if event_key and not prefs["events"].get(event_key, True):
        return

    if prefs["channels"].get("email") and user.email:
        await create_notification(
            db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            notification_type=notification_type,
            subject=subject,
            body=body,
        )

    if prefs["channels"].get("telegram") and user.telegram_chat_id:
        await create_notification(
            db,
            user_id=user_id,
            channel=NotificationChannel.TELEGRAM,
            notification_type=notification_type,
            subject=subject,
            body=body,
        )


async def _send_telegram(db: AsyncSession, n: Notification) -> None:
    if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        return
    try:
        result = await db.execute(select(User).where(User.id == n.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.telegram_chat_id:
            n.status = NotificationStatus.FAILED
            n.provider_response = "Telegram chat ID not configured"
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": user.telegram_chat_id, "text": n.body},
                timeout=10,
            )
            n.provider_response = resp.text
            n.status = NotificationStatus.SENT if resp.is_success else NotificationStatus.FAILED
            n.sent_at = datetime.now(timezone.utc)
    except Exception as e:
        n.status = NotificationStatus.FAILED
        n.provider_response = str(e)


async def _send_email(db: AsyncSession, n: Notification) -> None:
    if not settings.EMAIL_ENABLED:
        return
    try:
        import aiosmtplib
        from email.message import EmailMessage

        result = await db.execute(select(User).where(User.id == n.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.email:
            n.status = NotificationStatus.FAILED
            n.provider_response = "Email address not configured"
            return

        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = user.email
        msg["Subject"] = n.subject or n.notification_type
        msg.set_content(n.body)

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
        )
        n.status = NotificationStatus.SENT
        n.sent_at = datetime.now(timezone.utc)
    except Exception as e:
        n.status = NotificationStatus.FAILED
        n.provider_response = str(e)

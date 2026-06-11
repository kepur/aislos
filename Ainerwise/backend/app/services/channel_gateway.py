"""Internal client for the Phase D channel-gateway satellite process."""
from __future__ import annotations

import uuid

import httpx

from app.core.config import settings


async def send_channel_message(
    *,
    message_id: uuid.UUID,
    channel: str,
    external_thread_id: str,
    content: str,
    metadata: dict | None = None,
    account_name: str = "AinerWise",
) -> str:
    """Send once through channel-gateway and return its durable status."""
    if not settings.CHANNEL_GATEWAY_URL or not settings.SERVICE_TOKEN:
        return "unavailable"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{settings.CHANNEL_GATEWAY_URL.rstrip('/')}/internal/send",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
                json={
                    "message_id": str(message_id),
                    "channel": channel,
                    "account_name": account_name,
                    "external_thread_id": external_thread_id,
                    "content": content,
                    "metadata": metadata or {},
                },
            )
            response.raise_for_status()
            return str(response.json().get("status") or "unknown")
    except (httpx.HTTPError, ValueError):
        return "unavailable"

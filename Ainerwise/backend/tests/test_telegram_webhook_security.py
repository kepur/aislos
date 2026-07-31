"""Telegram webhook authentication must not trust forgeable request bodies."""
import asyncio

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.session import engine
from app.main import app


def test_telegram_webhook_requires_secret_header(monkeypatch):
    async def _run():
        await engine.dispose()
        monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "telegram-test-secret")
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            forged = await client.post(
                "/api/v1/telegram/webhook",
                json={"message": {"chat": {"id": settings.TELEGRAM_ADMIN_CHAT_ID}, "text": "/leads"}},
            )
            assert forged.status_code == 401, forged.text

            accepted = await client.post(
                "/api/v1/telegram/webhook",
                headers={"X-Telegram-Bot-Api-Secret-Token": "telegram-test-secret"},
                json={"message": {"chat": {"id": "-999"}, "text": "/leads"}},
            )
            assert accepted.status_code == 200, accepted.text
            assert accepted.json()["ignored"] == "unauthorized_chat"

    asyncio.run(_run())

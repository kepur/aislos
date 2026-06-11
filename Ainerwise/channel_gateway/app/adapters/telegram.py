from __future__ import annotations

import httpx

from app.adapters.base import ChannelAdapter, NormalizedMessage, SendResult
from app.backend import BackendClient
from app.config import Settings


class TelegramAdapter(ChannelAdapter):
    def __init__(self, settings: Settings, backend: BackendClient):
        self.settings = settings
        self.backend = backend

    async def _bot_token(self) -> str:
        if self.settings.TELEGRAM_BOT_TOKEN:
            return self.settings.TELEGRAM_BOT_TOKEN
        config = await self.backend.channel_config("telegram")
        token = config.get("bot_token")
        if not token:
            raise RuntimeError("Telegram bot token is not configured")
        return str(token)

    async def receive(self, payload: dict) -> NormalizedMessage | None:
        return self.normalize(payload)

    async def send(self, external_thread_id: str, content: str) -> SendResult:
        token = await self._bot_token()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": external_thread_id,
                    "text": content,
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result") or {}
        return SendResult(
            external_message_id=str(result.get("message_id")) if result.get("message_id") is not None else None,
            raw_payload=payload,
        )

    def normalize(self, payload: dict) -> NormalizedMessage | None:
        message = payload.get("message") or payload.get("edited_message")
        if not isinstance(message, dict) or not isinstance(message.get("chat"), dict):
            return None
        chat = message["chat"]
        sender = message.get("from") or {}
        contact_name = " ".join(
            part for part in (sender.get("first_name"), sender.get("last_name")) if part
        ) or sender.get("username") or chat.get("title")
        return NormalizedMessage(
            external_thread_id=str(chat["id"]),
            external_message_id=(
                str(message["message_id"]) if message.get("message_id") is not None else None
            ),
            content=message.get("text") or message.get("caption"),
            contact_name=contact_name,
            raw_payload=payload,
        )

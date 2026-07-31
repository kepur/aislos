from __future__ import annotations

import httpx

from app.adapters.base import ChannelAdapter, NormalizedMessage, SendResult
from app.backend import BackendClient
from app.config import Settings


class WhatsAppAdapter(ChannelAdapter):
    """Meta WhatsApp Cloud API adapter."""

    def __init__(self, settings: Settings, backend: BackendClient):
        self.settings = settings
        self.backend = backend

    async def _config(self) -> dict:
        config = await self.backend.channel_config("whatsapp")
        if not config.get("enabled"):
            raise RuntimeError("WhatsApp channel is disabled")
        return config

    async def credentials(self) -> tuple[str, str, str]:
        if self.settings.WHATSAPP_ACCESS_TOKEN and self.settings.WHATSAPP_PHONE_NUMBER_ID:
            return (
                self.settings.WHATSAPP_ACCESS_TOKEN,
                self.settings.WHATSAPP_PHONE_NUMBER_ID,
                self.settings.WHATSAPP_GRAPH_API_VERSION,
            )
        config = await self._config()
        access_token = str(config.get("access_token") or "")
        phone_number_id = str(config.get("phone_number_id") or "")
        version = str(config.get("graph_api_version") or "v23.0")
        if not access_token or not phone_number_id:
            raise RuntimeError("WhatsApp Cloud API is not configured")
        return access_token, phone_number_id, version

    async def app_secret(self) -> str:
        if self.settings.WHATSAPP_APP_SECRET:
            return self.settings.WHATSAPP_APP_SECRET
        config = await self.backend.channel_config("whatsapp")
        return str(config.get("app_secret") or "")

    async def verify_token(self) -> str:
        if self.settings.WHATSAPP_VERIFY_TOKEN:
            return self.settings.WHATSAPP_VERIFY_TOKEN
        config = await self.backend.channel_config("whatsapp")
        return str(config.get("verify_token") or "")

    async def receive(self, payload: dict) -> NormalizedMessage | None:
        return self.normalize(payload)

    async def send(
        self,
        external_thread_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> SendResult:
        access_token, phone_number_id, version = await self.credentials()
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://graph.facebook.com/{version}/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": external_thread_id,
                    "type": "text",
                    "text": {"preview_url": False, "body": content},
                },
            )
            response.raise_for_status()
            payload = response.json()
        messages = payload.get("messages") or []
        message_id = messages[0].get("id") if messages and isinstance(messages[0], dict) else None
        return SendResult(
            external_message_id=str(message_id) if message_id else None,
            raw_payload=payload,
        )

    def normalize(self, payload: dict) -> NormalizedMessage | None:
        for entry in payload.get("entry") or []:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                messages = value.get("messages") or []
                if not messages:
                    continue
                message = messages[0]
                sender = message.get("from")
                if not sender:
                    continue
                contacts = value.get("contacts") or []
                profile = contacts[0].get("profile") if contacts else {}
                content = self._content(message)
                return NormalizedMessage(
                    external_thread_id=str(sender),
                    external_message_id=str(message["id"]) if message.get("id") else None,
                    content=content,
                    contact_name=(profile or {}).get("name"),
                    raw_payload=payload,
                )
        return None

    @staticmethod
    def _content(message: dict) -> str | None:
        message_type = message.get("type")
        if message_type == "text":
            return (message.get("text") or {}).get("body")
        if message_type in {"image", "document", "video"}:
            media = message.get(message_type) or {}
            return media.get("caption") or f"[{message_type}:{media.get('id', 'unknown')}]"
        if message_type == "button":
            return (message.get("button") or {}).get("text")
        if message_type == "interactive":
            interactive = message.get("interactive") or {}
            reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
            return reply.get("title") or reply.get("id")
        return f"[{message_type}]" if message_type else None

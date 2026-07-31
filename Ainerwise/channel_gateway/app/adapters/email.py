from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any

from app.adapters.base import ChannelAdapter, NormalizedMessage, SendResult
from app.backend import BackendClient
from app.config import Settings


class EmailAdapter(ChannelAdapter):
    """Provider-neutral inbound email plus SMTP outbound delivery."""

    def __init__(self, settings: Settings, backend: BackendClient):
        self.settings = settings
        self.backend = backend

    async def _config(self) -> dict[str, Any]:
        config = await self.backend.channel_config("smtp")
        if not config.get("enabled"):
            raise RuntimeError("SMTP channel is disabled")
        return config

    async def webhook_secret(self) -> str:
        if self.settings.EMAIL_WEBHOOK_SECRET:
            return self.settings.EMAIL_WEBHOOK_SECRET
        config = await self.backend.channel_config("smtp")
        return str(config.get("inbound_webhook_secret") or "")

    async def receive(self, payload: dict) -> NormalizedMessage | None:
        return self.normalize(payload)

    async def send(
        self,
        external_thread_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> SendResult:
        config = await self._config()
        recipient = parseaddr(external_thread_id)[1]
        if not recipient or "@" not in recipient:
            raise ValueError("A valid recipient email is required")
        if not config.get("host") or not (config.get("from_email") or config.get("username")):
            raise RuntimeError("SMTP channel is not configured")
        await asyncio.to_thread(
            self._send_sync,
            config,
            recipient,
            content,
            metadata or {},
        )
        return SendResult(
            external_message_id=None,
            raw_payload={"accepted_recipient": recipient},
        )

    @staticmethod
    def _send_sync(
        config: dict[str, Any],
        recipient: str,
        content: str,
        metadata: dict,
    ) -> None:
        message = EmailMessage()
        from_email = str(config.get("from_email") or config.get("username"))
        from_name = str(config.get("from_name") or "AinerWise")
        message["From"] = f"{from_name} <{from_email}>"
        message["To"] = recipient
        message["Subject"] = str(metadata.get("subject") or "AinerWise notification")[:998]
        message.set_content(content)
        if metadata.get("html"):
            message.add_alternative(str(metadata["html"]), subtype="html")

        host = str(config["host"])
        port = int(config.get("port") or 587)
        server: smtplib.SMTP
        if config.get("use_ssl"):
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
        try:
            if not config.get("use_ssl") and config.get("use_tls", True):
                server.starttls()
            if config.get("username"):
                server.login(str(config["username"]), str(config.get("password") or ""))
            server.send_message(message)
        finally:
            server.quit()

    def normalize(self, payload: dict) -> NormalizedMessage | None:
        from_value = (
            payload.get("from_email")
            or payload.get("sender")
            or payload.get("from")
            or payload.get("From")
        )
        if isinstance(from_value, dict):
            contact_name = from_value.get("name")
            sender = str(from_value.get("email") or "")
        else:
            contact_name, sender = parseaddr(str(from_value or ""))
        sender = sender.strip().lower()
        if not sender or "@" not in sender:
            return None

        subject = str(payload.get("subject") or payload.get("Subject") or "").strip()
        body = str(
            payload.get("text")
            or payload.get("body")
            or payload.get("body-plain")
            or payload.get("stripped-text")
            or ""
        ).strip()
        content = "\n\n".join(part for part in (subject, body) if part) or None
        message_id = (
            payload.get("message_id")
            or payload.get("Message-Id")
            or payload.get("Message-ID")
            or payload.get("message-id")
        )
        return NormalizedMessage(
            external_thread_id=sender,
            external_message_id=str(message_id) if message_id else None,
            content=content,
            contact_name=str(contact_name).strip() or None,
            raw_payload=payload,
        )

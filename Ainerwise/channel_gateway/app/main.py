from __future__ import annotations

import hmac
import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from typing import Annotated
from urllib.parse import parse_qs

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse
from starlette.datastructures import UploadFile

from app.adapters import EmailAdapter, TelegramAdapter, WhatsAppAdapter
from app.backend import BackendClient
from app.config import settings
from app.database import ChannelDatabase

database = ChannelDatabase(settings.DATABASE_DSN)
backend = BackendClient(settings)
adapters = {
    "email": EmailAdapter(settings, backend),
    "telegram": TelegramAdapter(settings, backend),
    "whatsapp": WhatsAppAdapter(settings, backend),
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()
    yield
    await database.close()


app = FastAPI(title="AinerWise Channel Gateway", lifespan=lifespan)


async def verify_service_token(x_service_token: Annotated[str | None, Header()] = None) -> None:
    if not settings.SERVICE_TOKEN or not x_service_token or not hmac.compare_digest(
        x_service_token, settings.SERVICE_TOKEN
    ):
        raise HTTPException(status_code=401, detail="Invalid service token")


ServiceAuth = Depends(verify_service_token)


class SendRequest(BaseModel):
    message_id: uuid.UUID
    channel: str
    account_name: str = "AinerWise"
    external_thread_id: str
    content: str = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "channel-gateway", "channels": sorted(adapters)}


@app.post("/internal/send", dependencies=[ServiceAuth])
async def send_message(data: SendRequest):
    adapter = adapters.get(data.channel)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    prepared = await database.prepare_outbound(
        message_id=data.message_id,
        channel=data.channel,
        account_name=data.account_name,
        external_thread_id=data.external_thread_id,
        content=data.content,
        metadata=data.metadata,
    )
    if prepared["duplicate"]:
        return {
            "message_id": str(prepared["id"]),
            "status": prepared["status"],
            "external_message_id": prepared["external_message_id"],
            "duplicate": True,
        }
    try:
        result = await adapter.send(data.external_thread_id, data.content, data.metadata)
        await database.finish_outbound(
            data.message_id,
            status="sent",
            external_message_id=result.external_message_id,
        )
        return {
            "message_id": str(data.message_id),
            "status": "sent",
            "external_message_id": result.external_message_id,
            "duplicate": False,
        }
    except Exception as exc:  # noqa: BLE001 - failure is durably recorded for operators
        await database.finish_outbound(data.message_id, status="failed", error_message=str(exc)[:2000])
        return {
            "message_id": str(data.message_id),
            "status": "failed",
            "external_message_id": None,
            "duplicate": False,
        }


@app.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    hub_verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    hub_challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
):
    adapter = adapters["whatsapp"]
    expected = await adapter.verify_token()
    if (
        hub_mode != "subscribe"
        or not expected
        or not hub_verify_token
        or not hmac.compare_digest(hub_verify_token, expected)
        or hub_challenge is None
    ):
        raise HTTPException(status_code=401, detail="Invalid WhatsApp verification token")
    return PlainTextResponse(hub_challenge)


async def _webhook_payload(request: Request, raw_body: bytes) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = json.loads(raw_body or b"{}")
    elif "application/x-www-form-urlencoded" in content_type:
        payload = {key: values[-1] for key, values in parse_qs(raw_body.decode()).items()}
    elif "multipart/form-data" in content_type:
        form = await request.form()
        payload = {
            key: value.filename if isinstance(value, UploadFile) else str(value)
            for key, value in form.multi_items()
        }
    else:
        payload = json.loads(raw_body or b"{}")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be an object")
    return payload


@app.post("/webhooks/{channel}")
async def receive_webhook(
    channel: str,
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    x_email_webhook_secret: Annotated[str | None, Header()] = None,
):
    adapter = adapters.get(channel)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    if channel == "telegram" and settings.TELEGRAM_WEBHOOK_SECRET:
        if not x_telegram_bot_api_secret_token or not hmac.compare_digest(
            x_telegram_bot_api_secret_token, settings.TELEGRAM_WEBHOOK_SECRET
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    raw_body = await request.body()
    if channel == "whatsapp":
        secret = await adapter.app_secret()
        if not secret:
            raise HTTPException(status_code=503, detail="WhatsApp webhook signature is not configured")
        expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if (
            not x_hub_signature_256 or not hmac.compare_digest(x_hub_signature_256, expected)
        ):
            raise HTTPException(status_code=401, detail="Invalid WhatsApp signature")
    if channel == "email":
        secret = await adapter.webhook_secret()
        if not secret:
            raise HTTPException(status_code=503, detail="Email webhook secret is not configured")
        if (
            not x_email_webhook_secret or not hmac.compare_digest(x_email_webhook_secret, secret)
        ):
            raise HTTPException(status_code=401, detail="Invalid email webhook secret")
    payload = await _webhook_payload(request, raw_body)
    normalized = await adapter.receive(payload)
    if normalized is None:
        return {"ok": True, "ignored": True}
    message_id = await database.store_inbound(
        channel=channel,
        account_name=f"AinerWise {channel.title()}",
        external_thread_id=normalized.external_thread_id,
        external_message_id=normalized.external_message_id,
        content=normalized.content,
        contact_name=normalized.contact_name,
        raw_payload=normalized.raw_payload,
    )
    try:
        await backend.forward_inbound(
            {
                "channel": channel,
                "external_thread_id": normalized.external_thread_id,
                "external_message_id": normalized.external_message_id,
                "content": normalized.content,
                "contact_name": normalized.contact_name,
                "raw_payload": normalized.raw_payload,
            }
        )
    except httpx.HTTPError:
        pass
    return {"ok": True, "message_id": str(message_id)}

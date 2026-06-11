from __future__ import annotations

import hmac
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.adapters import TelegramAdapter
from app.backend import BackendClient
from app.config import settings
from app.database import ChannelDatabase

database = ChannelDatabase(settings.DATABASE_DSN)
backend = BackendClient(settings)
adapters = {"telegram": TelegramAdapter(settings, backend)}


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
        result = await adapter.send(data.external_thread_id, data.content)
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


@app.post("/webhooks/{channel}")
async def receive_webhook(
    channel: str,
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
):
    adapter = adapters.get(channel)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    if channel == "telegram" and settings.TELEGRAM_WEBHOOK_SECRET:
        if not x_telegram_bot_api_secret_token or not hmac.compare_digest(
            x_telegram_bot_api_secret_token, settings.TELEGRAM_WEBHOOK_SECRET
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    payload = await request.json()
    normalized = await adapter.receive(payload)
    if normalized is None:
        return {"ok": True, "ignored": True}
    message_id = await database.store_inbound(
        channel=channel,
        account_name="AinerWise Partner Bot",
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

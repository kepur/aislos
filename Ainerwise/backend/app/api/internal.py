"""Service-to-service API (/internal/v1/*), reachable only inside the docker
network and authenticated with X-Service-Token.

Per the architecture (ADR: orchestrator never writes business tables), the AI
orchestrator calls these endpoints to create business records; validation,
events, and audit stay in one place.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.api.deps import DB
from app.core.config import settings
from app.models.lead import Lead
from app.services.integrations import get_config
from app.services.integration_events import create_integration_event

router = APIRouter(prefix="/internal/v1", tags=["internal"])


async def verify_service_token(x_service_token: Annotated[str | None, Header()] = None) -> None:
    if not settings.SERVICE_TOKEN or x_service_token != settings.SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid service token")


ServiceAuth = Depends(verify_service_token)


class InternalLeadCreate(BaseModel):
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    project_type: str | None = None
    country: str | None = None
    city: str | None = None
    budget_range: str | None = None
    description: str | None = None
    language: str = "en"
    conversation_id: uuid.UUID | None = None
    transcript: list[dict] | None = None


@router.post("/leads", dependencies=[ServiceAuth])
async def create_lead_from_ai(data: InternalLeadCreate, db: DB):
    if not (data.contact_email or data.contact_phone or data.contact_name):
        raise HTTPException(status_code=400, detail="At least one contact field is required")
    lead = Lead(
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        project_type=data.project_type,
        country=data.country,
        city=data.city,
        budget_range=data.budget_range,
        description=data.description,
        language=data.language,
        status="new",
        source_channel="ai_chat",
        source_detail=str(data.conversation_id) if data.conversation_id else None,
        conversation_json=data.transcript,
    )
    db.add(lead)
    await db.flush()
    await create_integration_event(
        db,
        event_type="lead.created",
        payload={
            "lead_id": str(lead.id),
            "contact_name": lead.contact_name,
            "contact_email": lead.contact_email,
            "project_type": lead.project_type,
            "country": lead.country,
            "city": lead.city,
            "budget_range": lead.budget_range,
            "source": "ai_chat",
        },
    )
    return {"lead_id": str(lead.id)}


@router.get("/channel-config/{channel}", dependencies=[ServiceAuth])
async def get_channel_config(channel: str, db: DB):
    """Expose channel credentials only to trusted internal adapters."""
    if channel not in {"telegram"}:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    config = await get_config(db, channel)
    return {key: value for key, value in config.items() if not key.startswith("_")}


class InternalChannelInbound(BaseModel):
    channel: str
    external_thread_id: str
    external_message_id: str | None = None
    content: str | None = None
    contact_name: str | None = None
    raw_payload: dict | None = None


@router.post("/channels/inbound", dependencies=[ServiceAuth])
async def handle_channel_inbound(data: InternalChannelInbound, db: DB):
    """Keep existing Telegram admin commands working behind channel-gateway.

    Customer/partner conversational routing will attach here in later Phase D
    slices; the gateway already persists every inbound message.
    """
    if data.channel == "telegram" and data.raw_payload:
        from app.services.telegram_bot import handle_update

        return await handle_update(db, data.raw_payload)
    return {"ok": True}

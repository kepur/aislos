"""AinerWise AI orchestrator — internal-only service (no public exposure).

Auth: every agent endpoint requires X-Service-Token. The backend proxies the
public website chat through /api/v1/ai/chat with rate limiting; the channel
gateway (Phase D) will call the same /agent/chat.
"""
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.llm import get_ai_config, is_chat_configured
from app.workflows.consult import run_consult

app = FastAPI(title="AinerWise AI Orchestrator", docs_url="/docs")


async def verify_service_token(x_service_token: Annotated[str | None, Header()] = None) -> None:
    if not settings.SERVICE_TOKEN or x_service_token != settings.SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid service token")


DB = Annotated[AsyncSession, Depends(get_db)]


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    visitor_id: str | None = None
    lang: str | None = None
    channel: str = "web"
    agent_slug: str | None = None  # persona identity (kiosk personas etc.)


@app.post("/agent/chat", dependencies=[Depends(verify_service_token)])
async def agent_chat(data: AgentChatRequest, db: DB):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    payload = data.model_dump()
    payload["conversation_id"] = str(data.conversation_id) if data.conversation_id else None
    return await run_consult(db, payload)


class AgentGenerateRequest(BaseModel):
    agent_slug: str | None = None
    workflow: str
    context: dict = {}
    region_profile: dict | None = None
    channels: list[str] | None = None
    langs: list[str] | None = None
    lang: str | None = None


@app.post("/agent/generate", dependencies=[Depends(verify_service_token)])
async def agent_generate(data: AgentGenerateRequest, db: DB):
    from app.workflows.generate import run_generate

    try:
        return await run_generate(db, data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.post("/agent/briefing", dependencies=[Depends(verify_service_token)])
async def agent_briefing(db: DB):
    from app.workflows.briefing import run_briefing

    return await run_briefing(db)


@app.get("/health")
async def health(db: DB):
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    llm_configured = False
    if db_ok:
        try:
            llm_configured = is_chat_configured(await get_ai_config(db))
        except Exception:  # noqa: BLE001
            llm_configured = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.SERVICE_NAME,
        "db": db_ok,
        "llm_configured": llm_configured,
    }

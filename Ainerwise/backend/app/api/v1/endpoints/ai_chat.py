"""Public AI consultant endpoint: rate-limited proxy to the orchestrator.

The orchestrator is internal-only; the website talks to this endpoint, which
enforces per-IP rate limits (cost control on LLM tokens) and never exposes the
service token. Degrades gracefully when the orchestrator is down or AI is not
configured — the frontend then points visitors to the requirement form.
"""
import redis.asyncio as aioredis
import httpx
from fastapi import APIRouter, Request

from app.api.deps import DB
from app.core.config import settings
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.agent_runtime import AgentAuthorizationError, require_agent

router = APIRouter(prefix="/ai", tags=["ai-chat"])

RATE_LIMIT_PER_HOUR = 60
MAX_MESSAGE_CHARS = 2000

NOT_AVAILABLE = ChatResponse(
    configured=False,
    answer=None,
    disclaimer="AI consultant is not available right now. Please use the requirement form.",
)


async def _rate_limited(ip: str) -> bool:
    client = aioredis.from_url(settings.REDIS_URL)
    try:
        key = f"rate:chat:{ip}"
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, 3600)
        return count > RATE_LIMIT_PER_HOUR
    except Exception:  # noqa: BLE001 — redis down must not take the endpoint down
        return False
    finally:
        await client.aclose()


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, request: Request, db: DB):
    ip = request.client.host if request.client else "unknown"
    if await _rate_limited(ip):
        return ChatResponse(
            configured=True,
            answer=None,
            disclaimer="Rate limit reached. Please try again later or use the requirement form.",
        )
    message = data.message.strip()[:MAX_MESSAGE_CHARS]
    if not message:
        return NOT_AVAILABLE
    try:
        await require_agent(
            db,
            "sales-agent",
            scopes=("product_data", "customer_data"),
            workflow="consult",
        )
    except AgentAuthorizationError:
        return NOT_AVAILABLE

    payload = {
        "message": message,
        "conversation_id": str(data.conversation_id) if data.conversation_id else None,
        "visitor_id": data.visitor_id,
        "lang": data.lang,
        "channel": "web",
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/chat",
                json=payload,
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            return ChatResponse(**response.json())
    except Exception:  # noqa: BLE001 — orchestrator down => graceful degradation
        return NOT_AVAILABLE


@router.get("/chat/status")
async def chat_status(db: DB):
    try:
        await require_agent(
            db,
            "sales-agent",
            scopes=("product_data", "customer_data"),
            workflow="consult",
        )
    except AgentAuthorizationError:
        return {"available": False, "llm_configured": False}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/health")
            response.raise_for_status()
            body = response.json()
            return {"available": True, "llm_configured": bool(body.get("llm_configured"))}
    except Exception:  # noqa: BLE001
        return {"available": False, "llm_configured": False}

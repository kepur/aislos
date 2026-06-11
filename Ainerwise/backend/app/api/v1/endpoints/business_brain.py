"""AI Business Brain: read briefings (dashboard card) + manual trigger."""
import httpx
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DB, AdminUser
from app.core.config import settings
from app.models.ai import AgentRun
from app.services.agent_runtime import AgentAuthorizationError, require_agent

router = APIRouter(prefix="/admin/business-brain", tags=["business-brain"])


def _run_dict(run: AgentRun) -> dict:
    output = run.output_json or {}
    return {
        "id": str(run.id),
        "text": output.get("text"),
        "metrics": output.get("metrics"),
        "model": run.model_name,
        "status": run.status,
        "created_at": run.created_at.isoformat(),
    }


@router.get("/latest")
async def latest_briefing(db: DB, admin: AdminUser):
    run = (
        await db.execute(
            select(AgentRun)
            .where(AgentRun.workflow == "daily_briefing")
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if run is None:
        return {"briefing": None}
    return {"briefing": _run_dict(run)}


@router.get("/history")
async def briefing_history(db: DB, admin: AdminUser, limit: int = Query(14, ge=1, le=60)):
    runs = (
        await db.execute(
            select(AgentRun)
            .where(AgentRun.workflow == "daily_briefing")
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return {"items": [_run_dict(r) for r in runs]}


@router.post("/run")
async def run_briefing_now(db: DB, admin: AdminUser):
    try:
        await require_agent(
            db,
            "business-brain",
            scopes=("customer_data", "project_data", "partners"),
            workflow="daily_briefing",
        )
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/briefing",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Orchestrator unavailable: {exc}") from None

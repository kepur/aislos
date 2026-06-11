from app.tasks.celery_app import celery_app
from app.db.session import run_db_task


@celery_app.task(name="send_daily_briefing")
def send_daily_briefing():
    """AI Business Brain: fetch the briefing from the orchestrator, deliver to
    the admin Telegram channel, and leave it readable on the dashboard
    (ai.agent_runs is written by the orchestrator)."""
    import httpx

    from app.core.config import settings
    from app.services.agent_runtime import AgentAuthorizationError, require_agent
    from app.services.integration_events import create_integration_event

    async def _run(db):
        try:
            await require_agent(
                db,
                "business-brain",
                scopes=("customer_data", "project_data", "partners"),
                workflow="daily_briefing",
            )
        except AgentAuthorizationError as exc:
            return {"delivered": False, "skipped": True, "reason": str(exc)}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/briefing",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            briefing = response.json()
        await create_integration_event(
            db,
            event_type="briefing.daily",
            payload={"text": briefing.get("text"), "metrics": briefing.get("metrics")},
            target_channel="telegram_admin",
        )
        return {"delivered": True}

    return run_db_task(_run)

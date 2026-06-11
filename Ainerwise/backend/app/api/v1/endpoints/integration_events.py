import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import AdminUser, DB
from app.models.audit import AuditLog
from app.models.integration import AIRun, IntegrationEvent
from app.schemas.audit import AuditLogRead
from app.schemas.integration import AIRunRead, IntegrationEventRead
from app.services.ai_analysis import analyze_lead
from app.services.integration_events import dispatch_telegram_event

router = APIRouter(tags=["integrations"])


@router.get("/integration-events")
async def list_integration_events(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    event_type: str | None = None,
):
    from sqlalchemy import func

    filters = []
    if status:
        filters.append(IntegrationEvent.status == status)
    if event_type:
        filters.append(IntegrationEvent.event_type == event_type)

    query = select(IntegrationEvent).order_by(IntegrationEvent.created_at.desc())
    count_query = select(func.count()).select_from(IntegrationEvent)
    for item in filters:
        query = query.where(item)
        count_query = count_query.where(item)

    total_result = await db.execute(count_query)
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [IntegrationEventRead.model_validate(item) for item in result.scalars().all()],
        "total": total_result.scalar() or 0,
    }


@router.post("/integration-events/{id}/retry", response_model=IntegrationEventRead)
async def retry_integration_event(id: uuid.UUID, db: DB, admin: AdminUser):
    event = await db.get(IntegrationEvent, id)
    if event is None:
        raise HTTPException(status_code=404, detail="Integration event not found")
    if event.target_channel != "telegram_admin":
        raise HTTPException(status_code=400, detail="Only Telegram admin events can be retried")
    return await dispatch_telegram_event(db, event)


@router.get("/ai-runs")
async def list_ai_runs(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    entity_type: str | None = None,
):
    from sqlalchemy import func

    filters = []
    if status:
        filters.append(AIRun.status == status)
    if entity_type:
        filters.append(AIRun.entity_type == entity_type)

    query = select(AIRun).order_by(AIRun.created_at.desc())
    count_query = select(func.count()).select_from(AIRun)
    for item in filters:
        query = query.where(item)
        count_query = count_query.where(item)

    total_result = await db.execute(count_query)
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [AIRunRead.model_validate(item) for item in result.scalars().all()],
        "total": total_result.scalar() or 0,
    }


@router.post("/leads/{lead_id}/analyze", response_model=AIRunRead)
async def analyze_lead_endpoint(lead_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        return await analyze_lead(db, lead_id=lead_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lead not found") from None


# ── Audit Logs ──────────────────────────────────────────────


@router.get("/audit-logs")
async def list_audit_logs(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
    action: str | None = None,
    actor_user_id: uuid.UUID | None = None,
):
    from sqlalchemy import func

    filters = []
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if action:
        filters.append(AuditLog.action == action)
    if actor_user_id:
        filters.append(AuditLog.actor_user_id == actor_user_id)

    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    count_query = select(func.count()).select_from(AuditLog)
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    total_result = await db.execute(count_query)
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [AuditLogRead.model_validate(item) for item in result.scalars().all()],
        "total": total_result.scalar() or 0,
    }

"""Domain event consumers: read stream:events with a consumer group and run
automation. At-least-once delivery — handlers must be idempotent; entries are
acked only after successful handling, stale pending entries get reclaimed.

Phase C handlers:
  lead.created -> AI lead scoring (existing ai_analysis workflow), skipped if
                  the lead is already analyzed (idempotency).
"""
from app.tasks.celery_app import celery_app
from app.db.session import run_db_task

CONSUMER_GROUP = "automation"
CONSUMER_NAME = "celery-worker"
BATCH_SIZE = 50
RECLAIM_IDLE_MS = 5 * 60 * 1000


async def _handle_lead_created(db, payload: dict) -> None:
    import uuid

    from app.models.lead import Lead
    from app.services.ai_analysis import analyze_lead

    lead_id = payload.get("lead_id")
    if not lead_id:
        return
    lead = await db.get(Lead, uuid.UUID(lead_id))
    if lead is None or lead.ai_analysis_json:
        return  # gone or already analyzed — idempotent skip
    await analyze_lead(db, lead_id=uuid.UUID(lead_id))


async def _handle_rfq_awarded(db, payload: dict) -> None:
    """Auto-dispatch: award -> installation task for the winning partner.
    Skips gracefully when the partner has no linked user account."""
    import uuid
    from datetime import date, timedelta

    from sqlalchemy import select

    from app.models.lifecycle import MaintenanceSchedule
    from app.models.project import Project
    from app.models.rfq import RFQ
    from app.models.service import ServicePartner
    from app.services.partner_dispatch import dispatch_partner_task

    rfq_id = payload.get("rfq_id")
    partner_id = payload.get("partner_id")
    project_id = payload.get("project_id")
    if not (rfq_id and partner_id and project_id):
        return
    existing = (
        await db.execute(
            select(MaintenanceSchedule).where(
                MaintenanceSchedule.project_id == uuid.UUID(project_id),
                MaintenanceSchedule.task_type == "installation",
            )
        )
    ).scalars().first()
    if existing is not None:
        return  # idempotent: already dispatched
    rfq = await db.get(RFQ, uuid.UUID(rfq_id))
    project = await db.get(Project, uuid.UUID(project_id))
    partner = await db.get(ServicePartner, uuid.UUID(partner_id))
    if not (rfq and project and partner):
        return
    if partner.user_id is None:
        return  # partner not onboarded to the portal — admin schedules manually
    await dispatch_partner_task(
        db,
        project=project,
        partner=partner,
        task_type="installation",
        due_date=date.today() + timedelta(days=14),
        device_name=rfq.title,
        notes="Auto-dispatched from RFQ award",
        covered_by_amc=False,
    )


async def _handle_document_signed(db, payload: dict) -> None:
    """Acceptance reports close the delivery loop when the customer signs."""
    import uuid

    from app.models.content import GeneratedDocument
    from app.services.acceptance import handle_acceptance_signed

    document_id = payload.get("document_id")
    if not document_id:
        return
    document = await db.get(GeneratedDocument, uuid.UUID(document_id))
    if document is None or document.kind != "acceptance_report":
        return
    return await handle_acceptance_signed(db, document)


HANDLERS = {
    "lead.created": _handle_lead_created,
    "rfq.awarded": _handle_rfq_awarded,
    "document.signed": _handle_document_signed,
}


@celery_app.task(name="consume_domain_events")
def consume_domain_events():
    """Poll the event stream and dispatch handlers (beat, every 30s)."""
    import json

    import redis.asyncio as aioredis

    from app.core.config import settings
    from app.services.event_bus import EVENT_STREAM_KEY

    async def _run(db):
        client = aioredis.from_url(settings.REDIS_URL)
        processed = 0
        try:
            try:
                await client.xgroup_create(EVENT_STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
            except aioredis.ResponseError as exc:
                if "BUSYGROUP" not in str(exc):
                    raise

            entries = []
            # reclaim entries a crashed worker left pending
            try:
                _, claimed, _ = await client.xautoclaim(
                    EVENT_STREAM_KEY, CONSUMER_GROUP, CONSUMER_NAME,
                    min_idle_time=RECLAIM_IDLE_MS, start_id="0", count=BATCH_SIZE,
                )
                entries.extend(claimed)
            except aioredis.ResponseError:
                pass
            fresh = await client.xreadgroup(
                CONSUMER_GROUP, CONSUMER_NAME, {EVENT_STREAM_KEY: ">"}, count=BATCH_SIZE
            )
            for _, stream_entries in fresh or []:
                entries.extend(stream_entries)

            for entry_id, fields in entries:
                event_type = (fields.get(b"type") or b"").decode()
                handler = HANDLERS.get(event_type)
                try:
                    if handler is not None:
                        payload = json.loads((fields.get(b"payload") or b"{}").decode())
                        result = await handler(db, payload)
                        await db.commit()
                        if result and result.get("embedding_document_id"):
                            celery_app.send_task(
                                "ingest_knowledge_document",
                                args=[result["embedding_document_id"]],
                            )
                    await client.xack(EVENT_STREAM_KEY, CONSUMER_GROUP, entry_id)
                    processed += 1
                except Exception:  # noqa: BLE001 — leave unacked for retry/reclaim
                    await db.rollback()
            return processed
        finally:
            await client.aclose()

    return run_db_task(_run)


@celery_app.task(name="recompute_partner_metrics")
def recompute_partner_metrics_task():
    """Daily partner composite score recomputation."""
    from app.services.partner_score import recompute_partner_metrics

    return run_db_task(recompute_partner_metrics)


@celery_app.task(name="release_due_retentions")
def release_due_retentions_task():
    """Daily check: release retention milestones past their hold period."""
    from app.services.payments import release_due_retentions

    return run_db_task(release_due_retentions)

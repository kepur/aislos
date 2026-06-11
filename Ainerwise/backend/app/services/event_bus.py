"""Domain event bus: transactional outbox + Redis Stream relay.

Producers call `emit_event` inside their own transaction; the row commits
atomically with the business change. A periodic Celery task
(`relay_outbox_events`) pushes unpublished rows to the `stream:events`
Redis Stream, where future consumers (orchestrator, channel gateway,
automation workers) read with consumer groups.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.integration import IntegrationEvent

EVENT_STREAM_KEY = "ainerwise:stream:events"
EVENT_STREAM_MAXLEN = 10_000
RELAY_BATCH_SIZE = 100


class EventType:
    LEAD_CREATED = "lead.created"
    LEAD_SCORED = "lead.scored"
    QUOTE_SENT = "quote.sent"
    QUOTE_ACCEPTED = "quote.accepted"
    PROJECT_COMPLETED = "project.completed"
    TICKET_OPENED = "ticket.opened"
    DEVICE_WARRANTY_EXPIRING = "device.warranty_expiring"
    KNOWLEDGE_UPLOADED = "knowledge.uploaded"
    AI_DRAFT_READY = "ai.draft_ready"
    # Procurement Phase 1 (C03+)
    PROCUREMENT_PROJECT_CREATED = "procurement.project.created"
    PROCUREMENT_PROJECT_PORTAL_TRANSFERRED = "procurement.project.portal_transferred"
    PROCUREMENT_FILE_ATTACHED = "procurement.file.attached"
    PROCUREMENT_FACT_UPDATED = "procurement.fact.updated"
    PROCUREMENT_FACT_CONFIRMED = "procurement.fact.confirmed"
    PROCUREMENT_BOQ_GENERATED = "procurement.boq.generated"
    PROCUREMENT_BOQ_REVIEWED = "procurement.boq.reviewed"
    PROCUREMENT_BOQ_FROZEN = "procurement.boq.frozen"
    PROCUREMENT_AI_STARTED = "procurement.ai.started"
    PROCUREMENT_AI_COMPLETED = "procurement.ai.completed"
    PROCUREMENT_AI_FAILED = "procurement.ai.failed"
    PROCUREMENT_PACKAGES_GENERATED = "procurement.packages.generated"
    PROCUREMENT_PACKAGE_UPDATED = "procurement.package.updated"
    PROCUREMENT_COMMERCIAL_SNAPSHOT_CREATED = "procurement.commercial_snapshot.created"
    PROCUREMENT_RFQ_PUBLISHED = "procurement.rfq.published"


ALL_EVENT_TYPES = frozenset(
    value for name, value in vars(EventType).items() if not name.startswith("_")
)


async def emit_event(
    db: AsyncSession,
    event_type: str,
    payload: dict,
    *,
    aggregate_type: str | None = None,
    aggregate_id: uuid.UUID | None = None,
    target_channel: str | None = None,
) -> IntegrationEvent:
    """Write an outbox row in the caller's transaction. Does NOT commit —
    the event becomes durable exactly when the business change does.

    `target_channel` keeps the legacy notification path: events with
    "telegram_admin" still show up in Admin → Integrations for delivery
    retry; pure domain events use status "internal" and skip that view.
    """
    event = IntegrationEvent(
        event_type=event_type,
        payload_json=payload,
        target_channel=target_channel,
        status="pending" if target_channel else "internal",
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
    )
    db.add(event)
    await db.flush()
    return event


async def publish_pending_events(
    db: AsyncSession,
    redis_client: aioredis.Redis | None = None,
    batch_size: int = RELAY_BATCH_SIZE,
) -> int:
    """Relay unpublished outbox rows to the Redis Stream. Returns the count.

    SELECT ... FOR UPDATE SKIP LOCKED makes concurrent relays safe; delivery
    is at-least-once, so stream consumers must dedupe on the event id.
    """
    owns_client = redis_client is None
    if owns_client:
        redis_client = aioredis.from_url(settings.REDIS_URL)
    try:
        result = await db.execute(
            select(IntegrationEvent)
            .where(IntegrationEvent.published_at.is_(None))
            .order_by(IntegrationEvent.created_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()
        for event in events:
            await redis_client.xadd(
                EVENT_STREAM_KEY,
                {
                    "id": str(event.id),
                    "type": event.event_type,
                    "payload": json.dumps(event.payload_json or {}),
                    "aggregate_type": event.aggregate_type or "",
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else "",
                    "occurred_at": event.created_at.isoformat() if event.created_at else "",
                },
                maxlen=EVENT_STREAM_MAXLEN,
                approximate=True,
            )
            event.published_at = datetime.now(timezone.utc)
            db.add(event)
        await db.commit()
        return len(events)
    finally:
        if owns_client:
            await redis_client.aclose()

"""Project the existing outbox into the analytics spine.

The platform's own flows (Market, procurement, commerce) already write
`integration_events` inside their transactions. Rather than editing any of
those producers, this reads that outbox past a watermark and translates the
events it recognises into analytics rows.

That keeps the original system completely untouched while still getting its
activity into the same funnel as 2Hands and syndication — and moving the
cursor back is all a backfill takes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsProjectionCursor
from app.models.integration import IntegrationEvent
from app.services.analytics import record_event

CURSOR_NAME = "integration_events"
BATCH_SIZE = 500

# Outbox event type -> analytics event type. Anything not listed is skipped,
# so a new domain event never silently pollutes the funnel.
EVENT_MAP: dict[str, str] = {
    "commerce.order.awarded": "deal.reserved",
    "commerce.order.completed": "deal.completed",
    "procurement.offer.submitted": "contact.requested",
    "procurement.offer.awarded": "deal.reserved",
    "procurement.rfq.published": "listing.published",
    "lead.created": "contact.requested",
    "quote.accepted": "deal.completed",
}

# Which aggregate a value can be resolved from, when the payload is thin.
ORDER_AGGREGATES = ("commerce_order",)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_or_none(value) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


async def _resolve_order_dimensions(db: AsyncSession, order_id: uuid.UUID | None) -> dict:
    """Older outbox payloads are thin (just an id), so look up what is missing."""
    if order_id is None:
        return {}
    from app.models.commerce import CommerceOrder, ProcurementRequest

    order = await db.get(CommerceOrder, order_id)
    if order is None:
        return {}
    listing_id = None
    if order.winning_offer_id:
        from app.models.commerce import SupplierOffer

        offer = await db.get(SupplierOffer, order.winning_offer_id)
        listing_id = getattr(offer, "supplier_listing_id", None)
    region_id = None
    if order.procurement_request_id:
        request = await db.get(ProcurementRequest, order.procurement_request_id)
        region_id = getattr(request, "region_id", None)
    return {
        "listing_id": listing_id,
        "region_id": region_id,
        "value_minor": order.total_minor,
        "currency": order.currency,
    }


async def project_outbox_events(db: AsyncSession, *, batch_size: int = BATCH_SIZE) -> int:
    """Translate one batch of outbox rows into analytics events.

    Idempotent on the outbox row id, so re-running or overlapping schedules
    cannot double-count.
    """
    cursor = (
        await db.execute(
            select(AnalyticsProjectionCursor).where(AnalyticsProjectionCursor.name == CURSOR_NAME)
        )
    ).scalar_one_or_none()
    if cursor is None:
        cursor = AnalyticsProjectionCursor(name=CURSOR_NAME, processed_count=0)
        db.add(cursor)
        await db.flush()

    stmt = select(IntegrationEvent).order_by(IntegrationEvent.created_at, IntegrationEvent.id)
    if cursor.last_event_created_at is not None:
        stmt = stmt.where(IntegrationEvent.created_at > cursor.last_event_created_at)
    rows = list((await db.execute(stmt.limit(batch_size))).scalars())
    if not rows:
        return 0

    projected = 0
    for row in rows:
        mapped = EVENT_MAP.get(row.event_type)
        if mapped:
            payload = row.payload_json if isinstance(row.payload_json, dict) else {}
            dimensions: dict = {}
            if row.aggregate_type in ORDER_AGGREGATES:
                dimensions = await _resolve_order_dimensions(db, row.aggregate_id)
            if not dimensions.get("listing_id"):
                dimensions["listing_id"] = _uuid_or_none(
                    payload.get("listing_id") or payload.get("supplier_listing_id")
                )

            created = await record_event(
                db,
                mapped,
                listing_id=dimensions.get("listing_id"),
                region_id=dimensions.get("region_id"),
                value_minor=dimensions.get("value_minor"),
                currency=dimensions.get("currency"),
                portal_key=payload.get("portal_key"),
                source_app="core",
                occurred_at=row.created_at,
                # One analytics row per outbox row, forever.
                idempotency_key=f"outbox:{row.id}",
                meta={"outbox_event_type": row.event_type, "aggregate_type": row.aggregate_type},
            )
            if created is not None:
                projected += 1

        cursor.last_event_created_at = row.created_at
        cursor.last_event_id = row.id

    cursor.processed_count = (cursor.processed_count or 0) + len(rows)
    await db.commit()
    return projected

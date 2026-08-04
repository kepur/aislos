"""Recording and reading the analytics event spine.

Two rules keep this trustworthy:

  * **Never break the business call.** Recording is best-effort — a listing
    must still publish and a pickup must still confirm if analytics is down.
  * **Never store raw visitor PII.** Actors are salted hashes; a session id is
    an opaque client token. Neither can be reversed to a person, which is what
    lets us keep the data indefinitely under GDPR.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.analytics import AnalyticsEvent

# Funnel order used by the read API. Each step is a strict subset of the one
# before it, which is what makes the drop-off percentages meaningful.
FUNNEL_STEPS = (
    "listing.impression",
    "listing.view",
    "contact.requested",
    "deal.reserved",
    "deal.completed",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def hash_actor(value: str | uuid.UUID | None) -> str | None:
    """Salted, one-way actor identifier.

    Salted with the app secret so the same person cannot be correlated across
    a leaked dump and an external dataset.
    """
    if not value:
        return None
    salt = str(getattr(settings, "SECRET_KEY", "") or "aislos")
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


async def record_event(
    db: AsyncSession,
    event_type: str,
    *,
    listing_id: uuid.UUID | None = None,
    channel_account_id: uuid.UUID | None = None,
    creative_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    region_id: uuid.UUID | None = None,
    portal_key: str | None = None,
    actor_id: uuid.UUID | str | None = None,
    session_id: str | None = None,
    value_minor: int | None = None,
    currency: str | None = None,
    source_app: str | None = None,
    idempotency_key: str | None = None,
    occurred_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
    commit: bool = False,
) -> AnalyticsEvent | None:
    """Append one event. Returns None when it was a duplicate or failed.

    Does not commit by default so the caller can keep it in their transaction.
    """
    if idempotency_key:
        existing = (
            await db.execute(
                select(AnalyticsEvent.id).where(AnalyticsEvent.idempotency_key == idempotency_key)
            )
        ).scalar_one_or_none()
        if existing is not None:
            return None

    event = AnalyticsEvent(
        occurred_at=occurred_at or _now(),
        event_type=event_type,
        portal_key=portal_key,
        region_id=region_id,
        channel_account_id=channel_account_id,
        listing_id=listing_id,
        creative_id=creative_id,
        campaign_id=campaign_id,
        session_id=session_id,
        actor_hash=hash_actor(actor_id),
        value_minor=value_minor,
        currency=currency,
        source_app=source_app,
        idempotency_key=idempotency_key,
        meta_json=meta,
    )
    db.add(event)
    await db.flush()
    if commit:
        await db.commit()
    return event


async def record_event_safe(db: AsyncSession, event_type: str, **kwargs: Any) -> None:
    """Fire-and-forget wrapper for business endpoints.

    Analytics is never worth failing a sale over, so every error is swallowed.
    """
    try:
        await record_event(db, event_type, **kwargs)
    except Exception:  # noqa: BLE001 - telemetry must not break the caller
        pass


# ───────────────────────────── read side ────────────────────────────
#
# Aggregated on read rather than materialised. At this volume Postgres answers
# in milliseconds off the composite indexes, and a live query cannot go stale
# or drift from the events. Materialise only when a dashboard actually gets
# slow — the event grain stays the same either way.


def _window(since: datetime | None, until: datetime | None):
    conditions = []
    if since:
        conditions.append(AnalyticsEvent.occurred_at >= since)
    if until:
        conditions.append(AnalyticsEvent.occurred_at <= until)
    return conditions


async def funnel_counts(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    portal_key: str | None = None,
    channel_account_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """Impression -> view -> lead -> reserved -> sold, with drop-off."""
    stmt = select(AnalyticsEvent.event_type, func.count()).where(
        AnalyticsEvent.event_type.in_(FUNNEL_STEPS)
    )
    for condition in _window(since, until):
        stmt = stmt.where(condition)
    if portal_key:
        stmt = stmt.where(AnalyticsEvent.portal_key == portal_key)
    if channel_account_id:
        stmt = stmt.where(AnalyticsEvent.channel_account_id == channel_account_id)

    counts = dict((await db.execute(stmt.group_by(AnalyticsEvent.event_type))).all())

    out: list[dict[str, Any]] = []
    previous: int | None = None
    for step in FUNNEL_STEPS:
        count = int(counts.get(step, 0))
        conversion = round(count / previous * 100, 1) if previous else None
        out.append(
            {
                "step": step,
                "count": count,
                # Conversion from the previous step, not from the top: that is
                # the number that tells you which stage to fix.
                "conversion_from_previous": conversion,
                # Over 100% is real, not a bug: a sale on an external channel
                # never passes through our view/reserve steps. Flagged so a
                # dashboard can say "includes activity we don't see upstream"
                # instead of showing what looks like broken arithmetic.
                "exceeds_previous_step": bool(conversion and conversion > 100),
            }
        )
        previous = count if count else previous
    return out


async def sku_performance(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Which SKUs actually sell — views, leads and revenue per listing."""
    stmt = select(
        AnalyticsEvent.listing_id,
        AnalyticsEvent.event_type,
        func.count().label("n"),
        func.sum(AnalyticsEvent.value_minor).label("value_minor"),
    ).where(AnalyticsEvent.listing_id.isnot(None))
    for condition in _window(since, until):
        stmt = stmt.where(condition)

    rows = (await db.execute(stmt.group_by(AnalyticsEvent.listing_id, AnalyticsEvent.event_type))).all()

    by_listing: dict[uuid.UUID, dict[str, Any]] = {}
    for listing_id, event_type, n, value_minor in rows:
        bucket = by_listing.setdefault(
            listing_id,
            {"listing_id": listing_id, "impressions": 0, "views": 0, "leads": 0,
             "reserved": 0, "sold": 0, "revenue_minor": 0},
        )
        if event_type == "listing.impression":
            bucket["impressions"] += n
        elif event_type == "listing.view":
            bucket["views"] += n
        elif event_type == "contact.requested":
            bucket["leads"] += n
        elif event_type == "deal.reserved":
            bucket["reserved"] += n
        elif event_type == "deal.completed":
            bucket["sold"] += n
            bucket["revenue_minor"] += int(value_minor or 0)

    for bucket in by_listing.values():
        bucket["view_to_lead_pct"] = (
            round(bucket["leads"] / bucket["views"] * 100, 1) if bucket["views"] else None
        )
        bucket["lead_to_sale_pct"] = (
            round(bucket["sold"] / bucket["leads"] * 100, 1) if bucket["leads"] else None
        )

    return sorted(
        by_listing.values(),
        key=lambda b: (b["revenue_minor"], b["sold"], b["leads"]),
        reverse=True,
    )[:limit]


async def channel_performance(
    db: AsyncSession, *, since: datetime | None = None, until: datetime | None = None
) -> list[dict[str, Any]]:
    """Which channel converts. A NULL channel is our own storefront."""
    stmt = select(
        AnalyticsEvent.channel_account_id,
        AnalyticsEvent.event_type,
        func.count().label("n"),
        func.sum(AnalyticsEvent.value_minor).label("value_minor"),
    )
    for condition in _window(since, until):
        stmt = stmt.where(condition)

    rows = (
        await db.execute(stmt.group_by(AnalyticsEvent.channel_account_id, AnalyticsEvent.event_type))
    ).all()

    by_channel: dict[Any, dict[str, Any]] = {}
    for channel_id, event_type, n, value_minor in rows:
        bucket = by_channel.setdefault(
            channel_id,
            {"channel_account_id": channel_id, "onsite": channel_id is None,
             "impressions": 0, "views": 0, "leads": 0, "sold": 0, "revenue_minor": 0},
        )
        if event_type == "listing.impression":
            bucket["impressions"] += n
        elif event_type == "listing.view":
            bucket["views"] += n
        elif event_type == "contact.requested":
            bucket["leads"] += n
        elif event_type == "deal.completed":
            bucket["sold"] += n
            bucket["revenue_minor"] += int(value_minor or 0)

    for bucket in by_channel.values():
        bucket["lead_conversion_pct"] = (
            round(bucket["leads"] / bucket["views"] * 100, 1) if bucket["views"] else None
        )
        bucket["sale_conversion_pct"] = (
            round(bucket["sold"] / bucket["leads"] * 100, 1) if bucket["leads"] else None
        )

    return sorted(by_channel.values(), key=lambda b: b["revenue_minor"], reverse=True)


async def creative_performance(
    db: AsyncSession, *, since: datetime | None = None, until: datetime | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Click-through per ad image/copy variant — the question aggregate
    campaign counters can never answer."""
    stmt = select(
        AnalyticsEvent.creative_id,
        AnalyticsEvent.event_type,
        func.count().label("n"),
    ).where(
        AnalyticsEvent.creative_id.isnot(None),
        AnalyticsEvent.event_type.in_(("creative.impression", "creative.click")),
    )
    for condition in _window(since, until):
        stmt = stmt.where(condition)

    rows = (await db.execute(stmt.group_by(AnalyticsEvent.creative_id, AnalyticsEvent.event_type))).all()

    by_creative: dict[uuid.UUID, dict[str, Any]] = {}
    for creative_id, event_type, n in rows:
        bucket = by_creative.setdefault(
            creative_id, {"creative_id": creative_id, "impressions": 0, "clicks": 0}
        )
        if event_type == "creative.impression":
            bucket["impressions"] += n
        else:
            bucket["clicks"] += n

    for bucket in by_creative.values():
        bucket["ctr_pct"] = (
            round(bucket["clicks"] / bucket["impressions"] * 100, 2) if bucket["impressions"] else None
        )

    return sorted(
        by_creative.values(), key=lambda b: (b["ctr_pct"] or 0, b["clicks"]), reverse=True
    )[:limit]

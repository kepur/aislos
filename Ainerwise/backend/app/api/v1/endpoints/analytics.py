"""Analytics API (P2): ingest events, read the numbers that drive decisions.

Purely additive — reads the analytics spine, writes only analytics rows.

The read endpoints exist to answer three specific business questions:
  * which SKUs actually sell            -> /analytics/sku
  * which channel converts              -> /analytics/channel
  * which ad image gets clicked         -> /analytics/creative
plus the funnel that shows where buyers drop off.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DB, AdminUser, CurrentUser
from app.models.analytics import EVENT_TYPES, AnalyticsEvent, Creative
from app.models.commerce import SupplierListing
from app.services.analytics import (
    channel_performance,
    creative_performance,
    funnel_counts,
    record_event,
    sku_performance,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _window(days: int | None, since: datetime | None, until: datetime | None):
    if since or until:
        return since, until
    if days:
        return datetime.now(timezone.utc) - timedelta(days=days), None
    return None, None


# ───────────────────────────── ingest ───────────────────────────────


class EventIn(BaseModel):
    event_type: str
    occurred_at: datetime | None = None
    listing_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    creative_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    portal_key: str | None = None
    session_id: str | None = Field(default=None, max_length=64)
    value_minor: int | None = None
    currency: str | None = Field(default=None, max_length=3)
    idempotency_key: str | None = Field(default=None, max_length=128)
    meta: dict | None = None


class EventBatchIn(BaseModel):
    events: list[EventIn] = Field(min_length=1, max_length=500)
    # Required: without it every externally ingested event lands as "unknown"
    # and cross-project attribution — the reason this API exists — is lost.
    source_app: str = Field(min_length=2, max_length=64)


@router.post("/events", status_code=202)
async def ingest_events(data: EventBatchIn, db: DB, user: CurrentUser):
    """Record a batch of events.

    Send an `idempotency_key` for anything a client may retry — duplicates are
    dropped rather than double-counted. Never send raw personal data: identify
    visitors with an opaque `session_id` only.
    """
    unknown = {e.event_type for e in data.events} - set(EVENT_TYPES)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown event_type(s): {sorted(unknown)}. Allowed: {sorted(EVENT_TYPES)}",
        )

    accepted = 0
    for item in data.events:
        created = await record_event(
            db,
            item.event_type,
            listing_id=item.listing_id,
            channel_account_id=item.channel_account_id,
            creative_id=item.creative_id,
            campaign_id=item.campaign_id,
            region_id=item.region_id,
            portal_key=item.portal_key,
            session_id=item.session_id,
            value_minor=item.value_minor,
            currency=item.currency,
            source_app=data.source_app,
            idempotency_key=item.idempotency_key,
            occurred_at=item.occurred_at,
            meta=item.meta,
        )
        if created is not None:
            accepted += 1
    await db.commit()
    return {"received": len(data.events), "accepted": accepted, "duplicates": len(data.events) - accepted}


# ───────────────────────────── creatives ────────────────────────────


class CreativeIn(BaseModel):
    listing_id: uuid.UUID | None = None
    channel_account_id: uuid.UUID | None = None
    variant_label: str = Field(default="default", max_length=80)
    image_url: str | None = None
    copy_text: str | None = None
    generated_by: str = "human"


@router.post("/creatives", status_code=201)
async def create_creative(data: CreativeIn, db: DB, user: CurrentUser):
    """Register an ad image/copy variant so its click-through can be measured."""
    if data.generated_by not in ("human", "ai"):
        raise HTTPException(status_code=422, detail="generated_by must be 'human' or 'ai'")
    row = Creative(
        listing_id=data.listing_id,
        channel_account_id=data.channel_account_id,
        variant_label=data.variant_label,
        image_url=data.image_url,
        copy_text=data.copy_text,
        generated_by=data.generated_by,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {
        "id": row.id,
        "listing_id": row.listing_id,
        "variant_label": row.variant_label,
        "image_url": row.image_url,
        "generated_by": row.generated_by,
        "status": row.status,
    }


@router.get("/creatives")
async def list_creatives(db: DB, user: CurrentUser, listing_id: uuid.UUID | None = None):
    stmt = select(Creative).order_by(Creative.created_at.desc()).limit(200)
    if listing_id:
        stmt = stmt.where(Creative.listing_id == listing_id)
    rows = list((await db.execute(stmt)).scalars())
    return {
        "items": [
            {
                "id": r.id,
                "listing_id": r.listing_id,
                "variant_label": r.variant_label,
                "image_url": r.image_url,
                "copy_text": r.copy_text,
                "generated_by": r.generated_by,
                "status": r.status,
            }
            for r in rows
        ]
    }


# ───────────────────────────── read side ────────────────────────────


@router.get("/funnel")
async def read_funnel(
    db: DB,
    user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    since: datetime | None = None,
    until: datetime | None = None,
    portal_key: str | None = None,
    channel_account_id: uuid.UUID | None = None,
):
    """Impression -> view -> lead -> reserved -> sold, with step conversion."""
    start, end = _window(days, since, until)
    return {
        "window_days": days if not (since or until) else None,
        "steps": await funnel_counts(
            db, since=start, until=end, portal_key=portal_key, channel_account_id=channel_account_id
        ),
    }


@router.get("/sku")
async def read_sku_performance(
    db: DB,
    user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    """Which SKUs sell — ranked by revenue, then units, then leads."""
    start, end = _window(days, since, until)
    rows = await sku_performance(db, since=start, until=end, limit=limit)

    titles: dict[uuid.UUID, str] = {}
    ids = [r["listing_id"] for r in rows if r["listing_id"]]
    if ids:
        titles = dict(
            (await db.execute(select(SupplierListing.id, SupplierListing.title).where(SupplierListing.id.in_(ids)))).all()
        )
    for row in rows:
        row["title"] = titles.get(row["listing_id"])
    return {"items": rows}


@router.get("/channel")
async def read_channel_performance(
    db: DB,
    user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    since: datetime | None = None,
    until: datetime | None = None,
):
    """Which channel converts. `onsite: true` is our own storefront."""
    from app.models.channels import ChannelAccount

    start, end = _window(days, since, until)
    rows = await channel_performance(db, since=start, until=end)

    names: dict[uuid.UUID, tuple[str, str]] = {}
    ids = [r["channel_account_id"] for r in rows if r["channel_account_id"]]
    if ids:
        names = {
            row.id: (row.channel, row.name)
            for row in (await db.execute(select(ChannelAccount).where(ChannelAccount.id.in_(ids)))).scalars()
        }
    for row in rows:
        channel, name = names.get(row["channel_account_id"], (None, None))
        row["channel"] = channel or ("onsite" if row["onsite"] else None)
        row["channel_name"] = name or ("Our storefront" if row["onsite"] else None)
    return {"items": rows}


@router.get("/creative")
async def read_creative_performance(
    db: DB,
    user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    """Click-through per ad image/copy variant, best first."""
    start, end = _window(days, since, until)
    rows = await creative_performance(db, since=start, until=end, limit=limit)

    assets: dict[uuid.UUID, Creative] = {}
    ids = [r["creative_id"] for r in rows if r["creative_id"]]
    if ids:
        assets = {
            c.id: c for c in (await db.execute(select(Creative).where(Creative.id.in_(ids)))).scalars()
        }
    for row in rows:
        asset = assets.get(row["creative_id"])
        row["variant_label"] = getattr(asset, "variant_label", None)
        row["image_url"] = getattr(asset, "image_url", None)
        row["generated_by"] = getattr(asset, "generated_by", None)
    return {"items": rows}


@router.get("/health")
async def spine_health(db: DB, admin: AdminUser):
    """Is the spine actually receiving data, and from where."""
    from sqlalchemy import func

    total = (await db.execute(select(func.count()).select_from(AnalyticsEvent))).scalar() or 0
    by_source = (
        await db.execute(
            select(AnalyticsEvent.source_app, func.count()).group_by(AnalyticsEvent.source_app)
        )
    ).all()
    latest = (
        await db.execute(select(func.max(AnalyticsEvent.occurred_at)))
    ).scalar()
    return {
        "total_events": total,
        "by_source_app": {(s or "unknown"): n for s, n in by_source},
        "latest_event_at": latest,
    }

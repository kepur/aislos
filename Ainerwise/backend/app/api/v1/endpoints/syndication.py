"""Channel syndication API (P1).

Purely additive. No existing endpoint or flow is modified: syndication reads
listings and writes only to the new `channels.channel_listings` /
`channels.channel_category_maps` tables.

A syndication channel is a `channels.channel_accounts` row tagged
`meta_json.kind = "syndication"`, so the messaging channels already stored
there are untouched and invisible to these routes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DB, AdminUser, CurrentUser
from app.models.channels import ChannelAccount
from app.models.commerce import SupplierListing, TradeCategorySchema
from app.models.secondhand import SecondhandListing
from app.models.syndication import (
    ACTION_REQUIRED_STATUSES,
    DRIVER_KINDS,
    LIVE_STATUSES,
    ChannelCategoryMap,
    ChannelListing,
)
from app.models.user import Company
from app.services.analytics import record_event_safe
from app.services.syndication import (
    get_driver,
    map_listing_to_payload,
    render_feed_document,
    render_feed_item,
)

router = APIRouter(prefix="/syndication", tags=["syndication"])

SYNDICATION_KIND = "syndication"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _account_kind(account: ChannelAccount) -> str:
    meta = account.meta_json if isinstance(account.meta_json, dict) else {}
    return str(meta.get("driver_kind") or "assisted")


def _is_syndication(account: ChannelAccount) -> bool:
    meta = account.meta_json if isinstance(account.meta_json, dict) else {}
    return meta.get("kind") == SYNDICATION_KIND


def _account_as_dict(account: ChannelAccount) -> dict:
    meta = account.meta_json if isinstance(account.meta_json, dict) else {}
    return {
        "id": account.id,
        "channel": account.channel,
        "name": account.name,
        "status": account.status,
        "region_id": account.region_id,
        "driver_kind": _account_kind(account),
        "feed_slug": meta.get("feed_slug"),
        "notes": meta.get("notes"),
        # Credentials are never returned — only whether they are configured.
        "credentials_set": bool(account.credentials_json),
    }


def _channel_listing_as_dict(row: ChannelListing) -> dict:
    return {
        "id": row.id,
        "listing_id": row.supplier_listing_id,
        "account_id": row.account_id,
        "status": row.status,
        "external_id": row.external_id,
        "external_url": row.external_url,
        "content_hash": row.content_hash,
        "last_synced_at": row.last_synced_at,
        "last_error": row.last_error,
        "published_at": row.published_at,
        "delisted_at": row.delisted_at,
    }


async def _load_syndication_account(db: DB, account_id: uuid.UUID) -> ChannelAccount:
    account = await db.get(ChannelAccount, account_id)
    if account is None or not _is_syndication(account):
        raise HTTPException(status_code=404, detail="Syndication channel not found")
    return account


async def _load_listing_bundle(db: DB, listing_id: uuid.UUID):
    listing = await db.get(SupplierListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    secondhand = (
        await db.execute(
            select(SecondhandListing).where(SecondhandListing.supplier_listing_id == listing.id)
        )
    ).scalar_one_or_none()
    company_name = (
        await db.execute(select(Company.name).where(Company.id == listing.company_id))
    ).scalar_one_or_none()
    return listing, secondhand, company_name


async def _load_category_map(db: DB, account_id: uuid.UUID, category_id: uuid.UUID | None):
    if category_id is None:
        return None
    return (
        await db.execute(
            select(ChannelCategoryMap).where(
                ChannelCategoryMap.account_id == account_id,
                ChannelCategoryMap.category_schema_id == category_id,
            )
        )
    ).scalar_one_or_none()


# ───────────────────────────── payloads ─────────────────────────────


class ChannelCreate(BaseModel):
    channel: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    driver_kind: str = "assisted"
    region_id: uuid.UUID | None = None
    feed_slug: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class ChannelUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    driver_kind: str | None = None
    feed_slug: str | None = None
    notes: str | None = None


class CategoryMapUpsert(BaseModel):
    category_schema_id: uuid.UUID
    external_category_code: str = Field(min_length=1, max_length=120)
    external_category_path: str | None = None
    field_map: dict | None = None
    defaults: dict | None = None


class PublishRequest(BaseModel):
    account_ids: list[uuid.UUID] = Field(default_factory=list)
    force: bool = False


class ExternalRefUpdate(BaseModel):
    """Operator records the channel's own post id after an assisted publish."""

    external_id: str | None = None
    external_url: str | None = None
    mark_published: bool = True


# ───────────────────────────── channels ─────────────────────────────


@router.get("/channels")
async def list_channels(db: DB, user: CurrentUser):
    rows = list((await db.execute(select(ChannelAccount).order_by(ChannelAccount.created_at.desc()))).scalars())
    return {"items": [_account_as_dict(a) for a in rows if _is_syndication(a)]}


@router.post("/channels", status_code=201)
async def create_channel(data: ChannelCreate, db: DB, admin: AdminUser):
    if data.driver_kind not in DRIVER_KINDS:
        raise HTTPException(status_code=422, detail=f"driver_kind must be one of {DRIVER_KINDS}")
    account = ChannelAccount(
        channel=data.channel.strip().lower(),
        name=data.name.strip(),
        region_id=data.region_id,
        status="active",
        meta_json={
            "kind": SYNDICATION_KIND,
            "driver_kind": data.driver_kind,
            "feed_slug": data.feed_slug,
            "notes": data.notes,
        },
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return _account_as_dict(account)


@router.patch("/channels/{account_id}")
async def update_channel(account_id: uuid.UUID, data: ChannelUpdate, db: DB, admin: AdminUser):
    account = await _load_syndication_account(db, account_id)
    if data.driver_kind is not None and data.driver_kind not in DRIVER_KINDS:
        raise HTTPException(status_code=422, detail=f"driver_kind must be one of {DRIVER_KINDS}")

    if data.name is not None:
        account.name = data.name.strip()
    if data.status is not None:
        account.status = data.status
    meta = dict(account.meta_json or {})
    for key, value in (
        ("driver_kind", data.driver_kind),
        ("feed_slug", data.feed_slug),
        ("notes", data.notes),
    ):
        if value is not None:
            meta[key] = value
    meta["kind"] = SYNDICATION_KIND
    account.meta_json = meta

    await db.commit()
    await db.refresh(account)
    return _account_as_dict(account)


# ───────────────────────── category mapping ─────────────────────────


@router.get("/channels/{account_id}/category-maps")
async def list_category_maps(account_id: uuid.UUID, db: DB, user: CurrentUser):
    await _load_syndication_account(db, account_id)
    rows = list(
        (
            await db.execute(
                select(ChannelCategoryMap, TradeCategorySchema.name)
                .join(TradeCategorySchema, TradeCategorySchema.id == ChannelCategoryMap.category_schema_id)
                .where(ChannelCategoryMap.account_id == account_id)
            )
        ).all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "category_schema_id": row.category_schema_id,
                "category_name": name,
                "external_category_code": row.external_category_code,
                "external_category_path": row.external_category_path,
                "field_map": row.field_map_json or {},
                "defaults": row.defaults_json or {},
            }
            for row, name in rows
        ]
    }


@router.put("/channels/{account_id}/category-maps")
async def upsert_category_map(
    account_id: uuid.UUID, data: CategoryMapUpsert, db: DB, admin: AdminUser
):
    await _load_syndication_account(db, account_id)
    row = (
        await db.execute(
            select(ChannelCategoryMap).where(
                ChannelCategoryMap.account_id == account_id,
                ChannelCategoryMap.category_schema_id == data.category_schema_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = ChannelCategoryMap(account_id=account_id, category_schema_id=data.category_schema_id)
        db.add(row)
    row.external_category_code = data.external_category_code
    row.external_category_path = data.external_category_path
    row.field_map_json = data.field_map
    row.defaults_json = data.defaults
    await db.commit()
    await db.refresh(row)
    return {
        "id": row.id,
        "category_schema_id": row.category_schema_id,
        "external_category_code": row.external_category_code,
        "external_category_path": row.external_category_path,
    }


# ───────────────────────────── publish ──────────────────────────────


@router.get("/listings/{listing_id}/status")
async def listing_syndication_status(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    rows = list(
        (
            await db.execute(
                select(ChannelListing, ChannelAccount)
                .join(ChannelAccount, ChannelAccount.id == ChannelListing.account_id)
                .where(ChannelListing.supplier_listing_id == listing_id)
            )
        ).all()
    )
    return {
        "items": [
            {**_channel_listing_as_dict(row), "channel": account.channel, "channel_name": account.name}
            for row, account in rows
        ]
    }


@router.post("/listings/{listing_id}/publish")
async def publish_listing(
    listing_id: uuid.UUID, data: PublishRequest, db: DB, user: CurrentUser
):
    """Map a listing for each requested channel and run its driver.

    No third-party request is made by the shipped drivers: `feed` marks the row
    as part of the pull feed, `assisted` returns a pack for a human to post.
    """
    listing, secondhand, company_name = await _load_listing_bundle(db, listing_id)
    if listing.status != "active":
        raise HTTPException(status_code=409, detail="Only active listings can be syndicated")

    if data.account_ids:
        accounts = [await _load_syndication_account(db, aid) for aid in data.account_ids]
    else:
        accounts = [
            a
            for a in (await db.execute(select(ChannelAccount).where(ChannelAccount.status == "active"))).scalars()
            if _is_syndication(a)
        ]
    if not accounts:
        raise HTTPException(status_code=409, detail="No active syndication channels configured")

    results = []
    for account in accounts:
        category_map = await _load_category_map(db, account.id, listing.category_schema_id)
        payload = map_listing_to_payload(
            listing=listing,
            secondhand=secondhand,
            category_map=category_map,
            company_name=company_name,
        )
        content_hash = payload.content_hash()

        row = (
            await db.execute(
                select(ChannelListing).where(
                    ChannelListing.supplier_listing_id == listing.id,
                    ChannelListing.account_id == account.id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = ChannelListing(supplier_listing_id=listing.id, account_id=account.id, status="draft")
            db.add(row)
            await db.flush()

        # Identical content is not re-sent: repeated identical posts are what
        # gets marketplace accounts flagged.
        if row.content_hash == content_hash and row.status == "published" and not data.force:
            results.append(
                {**_channel_listing_as_dict(row), "channel": account.channel, "skipped": True,
                 "message": "Unchanged since the last publish"}
            )
            continue

        driver = get_driver(_account_kind(account), account.channel)
        try:
            outcome = (
                driver.update(payload, account=account, external_id=row.external_id)
                if row.external_id
                else driver.publish(payload, account=account)
            )
            row.status = outcome.status
            row.external_id = outcome.external_id or row.external_id
            row.external_url = outcome.external_url or row.external_url
            row.last_error = None
            if outcome.status == "published":
                row.published_at = row.published_at or _now()
        except Exception as exc:  # noqa: BLE001 - a driver failure must not abort the batch
            outcome = None
            row.status = "failed"
            row.last_error = str(exc)[:2000]

        row.content_hash = content_hash
        row.payload_json = payload.as_dict()
        row.last_synced_at = _now()

        if row.status == "published":
            # Channel attribution starts here: everything that later happens
            # to this listing can be compared against where it was published.
            await record_event_safe(
                db,
                "channel.published",
                listing_id=listing.id,
                channel_account_id=account.id,
                region_id=account.region_id,
                source_app="syndication",
                idempotency_key=f"channel.published:{row.id}:{content_hash}",
                meta={"channel": account.channel},
            )

        results.append(
            {
                **_channel_listing_as_dict(row),
                "channel": account.channel,
                "driver_kind": _account_kind(account),
                "artifact": outcome.artifact if outcome else None,
                "artifact_kind": outcome.artifact_kind if outcome else None,
                "message": outcome.message if outcome else row.last_error,
            }
        )

    await db.commit()
    return {"items": results}


@router.get("/queue")
async def action_queue(db: DB, user: CurrentUser, limit: int = Query(default=100, ge=1, le=500)):
    """Everything a human still has to do, and which action it is.

    `pending_review` → go post it. `pending_takedown` → go remove it (the item
    sold). `failed` → the last attempt errored. Without this the assisted
    channels quietly accumulate work nobody can see.
    """
    rows = list(
        (
            await db.execute(
                select(ChannelListing, ChannelAccount, SupplierListing.title)
                .join(ChannelAccount, ChannelAccount.id == ChannelListing.account_id)
                .join(SupplierListing, SupplierListing.id == ChannelListing.supplier_listing_id)
                .where(ChannelListing.status.in_(ACTION_REQUIRED_STATUSES))
                .order_by(ChannelListing.last_synced_at.desc())
                .limit(limit)
            )
        ).all()
    )
    action_for = {
        "pending_review": "post",
        "pending_takedown": "take_down",
        "failed": "retry",
    }
    return {
        "items": [
            {
                **_channel_listing_as_dict(row),
                "channel": account.channel,
                "channel_name": account.name,
                "listing_title": title,
                "action": action_for.get(row.status, "review"),
            }
            for row, account, title in rows
        ]
    }


@router.post("/channel-listings/{channel_listing_id}/confirm-takedown")
async def confirm_takedown(channel_listing_id: uuid.UUID, db: DB, user: CurrentUser):
    """Operator confirms they removed the post on a channel we cannot automate."""
    row = await db.get(ChannelListing, channel_listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Channel listing not found")
    row.status = "delisted"
    row.delisted_at = row.delisted_at or _now()
    row.last_synced_at = _now()
    await db.commit()
    await db.refresh(row)
    return _channel_listing_as_dict(row)


@router.post("/channel-listings/{channel_listing_id}/external-ref")
async def record_external_ref(
    channel_listing_id: uuid.UUID, data: ExternalRefUpdate, db: DB, user: CurrentUser
):
    """After an assisted publish, record the channel's own post id."""
    row = await db.get(ChannelListing, channel_listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Channel listing not found")
    row.external_id = data.external_id
    row.external_url = data.external_url
    if data.mark_published:
        row.status = "published"
        row.published_at = row.published_at or _now()
    row.last_synced_at = _now()
    await db.commit()
    await db.refresh(row)
    return _channel_listing_as_dict(row)


@router.post("/listings/{listing_id}/delist")
async def delist_listing(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    """Take a listing down everywhere it was published.

    Second-hand stock is unique, so a sale has to remove every live copy.
    """
    rows = list(
        (
            await db.execute(
                select(ChannelListing, ChannelAccount)
                .join(ChannelAccount, ChannelAccount.id == ChannelListing.account_id)
                .where(
                    ChannelListing.supplier_listing_id == listing_id,
                    ChannelListing.status.in_(LIVE_STATUSES),
                )
            )
        ).all()
    )
    results = []
    for row, account in rows:
        driver = get_driver(_account_kind(account), account.channel)
        try:
            outcome = driver.delist(account=account, external_id=row.external_id)
            row.status = outcome.status
            row.last_error = None
        except Exception as exc:  # noqa: BLE001
            outcome = None
            row.status = "failed"
            row.last_error = str(exc)[:2000]
        row.delisted_at = _now()
        row.last_synced_at = _now()
        await record_event_safe(
            db,
            "channel.delisted",
            listing_id=listing_id,
            channel_account_id=account.id,
            region_id=account.region_id,
            source_app="syndication",
            meta={"channel": account.channel, "status": row.status},
        )
        results.append(
            {
                **_channel_listing_as_dict(row),
                "channel": account.channel,
                "artifact": outcome.artifact if outcome else None,
                "message": outcome.message if outcome else row.last_error,
            }
        )
    await db.commit()
    return {"items": results, "delisted": len(results)}


# ───────────────────────────── feed export ──────────────────────────


@router.get("/feed/{feed_slug}.xml")
async def export_feed(feed_slug: str, db: DB, limit: int = Query(default=500, ge=1, le=2000)):
    """Public merchant feed a channel pulls on its own schedule.

    Only listings explicitly published to this channel appear, and only coarse
    location is included — pickup addresses are never syndicated.
    """
    accounts = [
        a
        for a in (await db.execute(select(ChannelAccount).where(ChannelAccount.status == "active"))).scalars()
        if _is_syndication(a) and (a.meta_json or {}).get("feed_slug") == feed_slug
    ]
    if not accounts:
        raise HTTPException(status_code=404, detail="Feed not found")
    account = accounts[0]

    rows = list(
        (
            await db.execute(
                select(ChannelListing, SupplierListing)
                .join(SupplierListing, SupplierListing.id == ChannelListing.supplier_listing_id)
                .where(
                    ChannelListing.account_id == account.id,
                    ChannelListing.status == "published",
                    SupplierListing.status == "active",
                )
                .limit(limit)
            )
        ).all()
    )

    items: list[str] = []
    for channel_listing, listing in rows:
        payload_dict = channel_listing.payload_json or {}
        if not payload_dict:
            continue
        from app.services.syndication import ChannelPayload

        items.append(
            render_feed_item(
                ChannelPayload(
                    title=payload_dict.get("title") or listing.title,
                    description=payload_dict.get("description") or "",
                    price_minor=payload_dict.get("price_minor") or 0,
                    currency=payload_dict.get("currency") or listing.currency,
                    category_code=payload_dict.get("category_code"),
                    category_path=payload_dict.get("category_path"),
                    condition=payload_dict.get("condition"),
                    images=payload_dict.get("images") or [],
                    location=payload_dict.get("location") or {},
                    attributes=payload_dict.get("attributes") or {},
                )
            )
        )

    xml = render_feed_document(items, title=account.name)
    return Response(content=xml, media_type="application/rss+xml")

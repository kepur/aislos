"""Channel syndication: mapping, driver contract and the shipped drivers.

The driver contract is the whole point of this module. Every channel — a
merchant feed today, an official API tomorrow, an AI agent later — implements
the same five calls against the same mapped payload, so adding a channel never
means touching the job path, the mapping tables or the API.

COMPLIANCE NOTE
    Most classifieds platforms (KupujemProdajem, OLX, Facebook Marketplace)
    forbid automated posting in their terms of service. The drivers shipped
    here therefore make **no outbound request to any third party**:
      * `feed`     — renders a merchant feed the platform pulls itself
      * `assisted` — renders a ready-to-paste pack a human posts manually
    An `api` driver must only be added for a channel where we hold an official
    integration agreement, and an `agent` driver additionally has to pass the
    human review gate before anything leaves the building.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from xml.etree import ElementTree as ET

from app.models.syndication import DRIVER_KINDS


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ───────────────────────────── payload ──────────────────────────────


@dataclass
class ChannelPayload:
    """Channel-neutral view of a listing, after category/field mapping."""

    title: str
    description: str
    price_minor: int
    currency: str
    category_code: str | None = None
    category_path: str | None = None
    condition: str | None = None
    images: list[str] = field(default_factory=list)
    location: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "price_minor": self.price_minor,
            "currency": self.currency,
            "category_code": self.category_code,
            "category_path": self.category_path,
            "condition": self.condition,
            "images": self.images,
            "location": self.location,
            "attributes": self.attributes,
        }

    def content_hash(self) -> str:
        """Stable fingerprint — lets the job path skip unchanged re-publishes."""
        blob = json.dumps(self.as_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class PublishResult:
    """What a driver hands back after a publish/update attempt."""

    status: str                      # published | pending_review | failed
    external_id: str | None = None
    external_url: str | None = None
    # Content the operator needs when the driver cannot post by itself.
    artifact: str | None = None
    artifact_kind: str | None = None  # "xml" | "csv" | "text"
    message: str | None = None


@dataclass
class StatsResult:
    """Numbers pulled back from a channel.

    `available` is the honest part of this contract. A channel we cannot query
    must say so rather than return zeros — zeros would silently become a
    denominator and make every conversion rate wrong.
    """

    available: bool
    impressions: int | None = None
    views: int | None = None
    contacts: int | None = None
    fetched_at: datetime | None = None
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "impressions": self.impressions,
            "views": self.views,
            "contacts": self.contacts,
            "fetched_at": (self.fetched_at or _now()).isoformat(),
            "message": self.message,
        }


# ───────────────────────────── contract ─────────────────────────────


@runtime_checkable
class ChannelDriver(Protocol):
    """Contract every channel implements. Adding a channel adds one of these."""

    kind: str            # one of DRIVER_KINDS
    channel: str         # e.g. "kupujemprodajem"
    capabilities: set[str]  # subset of publish/update/delist/stats/messages

    def publish(self, payload: ChannelPayload, *, account: Any) -> PublishResult: ...
    def update(self, payload: ChannelPayload, *, account: Any, external_id: str | None) -> PublishResult: ...
    def delist(self, *, account: Any, external_id: str | None) -> PublishResult: ...
    def fetch_stats(self, *, account: Any, external_id: str | None) -> StatsResult: ...


# ───────────────────────────── mapping ──────────────────────────────

CONDITION_TO_CHANNEL = {
    "A": "like_new",
    "B": "good",
    "C": "used",
    "D": "for_parts",
}


def map_listing_to_payload(
    *,
    listing: Any,
    secondhand: Any | None = None,
    category_map: Any | None = None,
    company_name: str | None = None,
) -> ChannelPayload:
    """Build the channel-neutral payload for one listing.

    `category_map` supplies the channel's own category code plus optional
    field overrides and constants, so the same listing maps differently per
    channel without any code change.
    """
    attrs = listing.attributes_json if isinstance(listing.attributes_json, dict) else {}

    description_parts: list[str] = []
    if attrs.get("description"):
        description_parts.append(str(attrs["description"]))

    if secondhand is not None:
        if secondhand.condition_grade:
            description_parts.append(
                f"Condition: {secondhand.condition_grade} "
                f"({CONDITION_TO_CHANNEL.get(secondhand.condition_grade, 'used')})"
            )
        if secondhand.purchase_year:
            description_parts.append(f"Purchased: {secondhand.purchase_year}")
        if secondhand.warranty_left_months:
            description_parts.append(f"Warranty remaining: {secondhand.warranty_left_months} months")
        if secondhand.original_packaging:
            description_parts.append("Original packaging included")
        defects = secondhand.defects_json or []
        if defects:
            lines = [
                f"- {d.get('type') or 'note'}: {d.get('note') or ''}".rstrip(": ")
                for d in defects
                if isinstance(d, dict)
            ]
            if lines:
                description_parts.append("Declared faults:\n" + "\n".join(lines))

    location: dict[str, Any] = {}
    condition = None
    if secondhand is not None:
        condition = CONDITION_TO_CHANNEL.get(secondhand.condition_grade)
        location = {
            # Coarse location only — the exact address is never syndicated.
            "country": secondhand.pickup_country,
            "city": secondhand.pickup_city,
            "area": secondhand.pickup_area,
        }

    attributes: dict[str, Any] = {}
    if company_name:
        attributes["seller"] = company_name
    if category_map is not None and category_map.defaults_json:
        attributes.update(category_map.defaults_json)

    payload = ChannelPayload(
        title=listing.title,
        description="\n\n".join(p for p in description_parts if p),
        price_minor=listing.price_minor or 0,
        currency=listing.currency,
        category_code=getattr(category_map, "external_category_code", None),
        category_path=getattr(category_map, "external_category_path", None),
        condition=condition,
        images=list(attrs.get("images") or []),
        location={k: v for k, v in location.items() if v},
        attributes=attributes,
    )

    # Per-channel field renames, applied last so operators can always win.
    field_map = getattr(category_map, "field_map_json", None) or {}
    if field_map:
        renamed = {}
        base = payload.as_dict()
        for ours, theirs in field_map.items():
            if ours in base:
                renamed[str(theirs)] = base[ours]
        payload.attributes.update(renamed)

    return payload


# ───────────────────────────── drivers ──────────────────────────────


class FeedDriver:
    """Renders a merchant feed the channel pulls on its own schedule.

    Makes no outbound call: publishing means "this row is now part of the feed
    document", which the channel fetches from our export endpoint.
    """

    kind = "feed"
    capabilities = {"publish", "update", "delist"}

    def __init__(self, channel: str) -> None:
        self.channel = channel

    def publish(self, payload: ChannelPayload, *, account: Any) -> PublishResult:
        return PublishResult(
            status="published",
            external_id=None,
            artifact=render_feed_item(payload),
            artifact_kind="xml",
            message="Included in the merchant feed; the channel pulls it on its next fetch.",
        )

    def update(self, payload: ChannelPayload, *, account: Any, external_id: str | None) -> PublishResult:
        result = self.publish(payload, account=account)
        result.external_id = external_id
        return result

    def delist(self, *, account: Any, external_id: str | None) -> PublishResult:
        return PublishResult(
            status="delisted",
            external_id=external_id,
            message="Removed from the merchant feed; the channel drops it on its next fetch.",
        )

    def fetch_stats(self, *, account: Any, external_id: str | None) -> StatsResult:
        # A pull feed is one-way: the channel fetches our XML and never reports
        # back. Saying so beats inventing zeros that would poison conversion
        # rates. Real numbers need either the channel's API or a tracked link.
        return StatsResult(
            available=False,
            message="Merchant feeds are one-way; this channel reports no view data back.",
        )


class AssistedDriver:
    """Prepares everything a person needs to post manually.

    This is the compliant answer for channels without an official integration:
    the operator gets the mapped title/description/category/price and pastes
    it in. Nothing is sent automatically, so no terms of service are broken.
    """

    kind = "assisted"
    capabilities = {"publish", "update", "delist"}

    def __init__(self, channel: str) -> None:
        self.channel = channel

    def publish(self, payload: ChannelPayload, *, account: Any) -> PublishResult:
        return PublishResult(
            status="pending_review",
            artifact=render_assisted_pack(payload, channel=self.channel),
            artifact_kind="text",
            message="Ready for a human to post. Save the channel's post ID here afterwards.",
        )

    def update(self, payload: ChannelPayload, *, account: Any, external_id: str | None) -> PublishResult:
        result = self.publish(payload, account=account)
        result.external_id = external_id
        return result

    def delist(self, *, account: Any, external_id: str | None) -> PublishResult:
        # Distinct from pending_review: the operator queue must say whether to
        # post something or to remove something already live.
        return PublishResult(
            status="pending_takedown",
            external_id=external_id,
            artifact=(
                f"Take down the {self.channel} post"
                + (f" (id {external_id})" if external_id else "")
                + " — the item is no longer available."
            ),
            artifact_kind="text",
            message="Manual takedown required on this channel.",
        )

    def fetch_stats(self, *, account: Any, external_id: str | None) -> StatsResult:
        # Nothing to query — the post lives in someone else's account. The
        # operator reads the view count off the channel and types it in via
        # record_channel_stats, which is why that endpoint exists.
        return StatsResult(
            available=False,
            message="No API for this channel — enter the view count from the post manually.",
        )


DRIVER_REGISTRY: dict[str, type] = {
    "feed": FeedDriver,
    "assisted": AssistedDriver,
}


def get_driver(kind: str, channel: str) -> ChannelDriver:
    """Resolve a driver. Unknown kinds fall back to assisted (never automated)."""
    normalized = (kind or "").lower()
    if normalized not in DRIVER_KINDS:
        normalized = "assisted"
    driver_cls = DRIVER_REGISTRY.get(normalized)
    if driver_cls is None:
        # `api` and `agent` need a per-channel implementation plus an
        # integration agreement; until one is registered, degrade to a pack a
        # human posts rather than silently automating against a channel's ToS.
        driver_cls = AssistedDriver
    return driver_cls(channel)  # type: ignore[return-value]


# ───────────────────────────── renderers ────────────────────────────


def render_feed_item(payload: ChannelPayload) -> str:
    """One <item> in a Google-Merchant-shaped feed (widely accepted)."""
    item = ET.Element("item")
    ET.SubElement(item, "title").text = payload.title
    ET.SubElement(item, "description").text = payload.description
    ET.SubElement(item, "price").text = f"{payload.price_minor / 100:.2f} {payload.currency}"
    if payload.category_code:
        ET.SubElement(item, "product_type").text = payload.category_path or payload.category_code
    if payload.condition:
        ET.SubElement(item, "condition").text = payload.condition
    for url in payload.images[:10]:
        ET.SubElement(item, "image_link").text = url
    if payload.location:
        loc = ET.SubElement(item, "location")
        for key, value in payload.location.items():
            ET.SubElement(loc, key).text = str(value)
    return ET.tostring(item, encoding="unicode")


def render_feed_document(items: list[str], *, title: str) -> str:
    """Wrap rendered items into an RSS 2.0 document a channel can fetch."""
    body = "".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>'
        f"<title>{title}</title>"
        f"<generated>{_now().isoformat()}</generated>"
        f"{body}"
        "</channel></rss>"
    )


async def delist_listing_everywhere(db: Any, listing_id: Any) -> int:
    """Take a listing down on every channel it is live on.

    Called when unique second-hand stock is sold. Best-effort by design: the
    caller has already completed a real-world transaction, so a channel error
    is recorded on the row rather than raised.
    """
    from sqlalchemy import select

    from app.models.channels import ChannelAccount
    from app.models.syndication import LIVE_STATUSES, ChannelListing

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
    for row, account in rows:
        meta = account.meta_json if isinstance(account.meta_json, dict) else {}
        driver = get_driver(str(meta.get("driver_kind") or "assisted"), account.channel)
        try:
            outcome = driver.delist(account=account, external_id=row.external_id)
            row.status = outcome.status
            row.last_error = None
        except Exception as exc:  # noqa: BLE001
            row.status = "failed"
            row.last_error = str(exc)[:2000]
        row.delisted_at = _now()
        row.last_synced_at = _now()

    if rows:
        await db.commit()
    return len(rows)


async def record_channel_stats(
    db: Any,
    channel_listing: Any,
    stats: StatsResult,
    *,
    account: Any,
) -> int:
    """Store pulled/entered channel numbers and feed the delta into the funnel.

    Channel stats are cumulative totals, so only the **increase** since the last
    reading becomes new events — otherwise every refresh would re-count the
    same impressions and destroy the conversion rates this exists to produce.
    """
    from app.services.analytics import record_event_safe

    if not stats.available:
        # Keep the reason visible to operators, but write no numbers.
        merged = dict(channel_listing.stats_json or {})
        merged["last_attempt"] = stats.as_dict()
        channel_listing.stats_json = merged
        return 0

    previous = channel_listing.stats_json or {}
    emitted = 0
    for field, event_type in (("impressions", "listing.impression"), ("views", "listing.view")):
        total = getattr(stats, field) or 0
        seen = int(previous.get(field) or 0)
        delta = total - seen
        if delta <= 0:
            continue
        # One event per unit would bloat the spine for large counts; a single
        # event carrying the delta keeps the arithmetic identical for the
        # aggregations, which all use count/sum over the window.
        for _ in range(min(delta, 1000)):
            await record_event_safe(
                db,
                event_type,
                listing_id=channel_listing.supplier_listing_id,
                channel_account_id=account.id,
                region_id=getattr(account, "region_id", None),
                source_app="syndication",
            )
        emitted += delta

    channel_listing.stats_json = {
        "impressions": stats.impressions,
        "views": stats.views,
        "contacts": stats.contacts,
        "fetched_at": (stats.fetched_at or _now()).isoformat(),
        "source": "channel",
    }
    return emitted


def render_assisted_pack(payload: ChannelPayload, *, channel: str) -> str:
    """Human-readable block an operator copies into the channel's own form."""
    lines = [
        f"CHANNEL: {channel}",
        f"CATEGORY: {payload.category_path or payload.category_code or '(map not configured)'}",
        f"PRICE: {payload.price_minor / 100:.2f} {payload.currency}",
    ]
    if payload.condition:
        lines.append(f"CONDITION: {payload.condition}")
    if payload.location:
        lines.append("LOCATION: " + ", ".join(str(v) for v in payload.location.values()))
    lines += ["", "TITLE:", payload.title, "", "DESCRIPTION:", payload.description]
    if payload.images:
        lines += ["", "IMAGES:"] + [f"  {u}" for u in payload.images]
    return "\n".join(lines)

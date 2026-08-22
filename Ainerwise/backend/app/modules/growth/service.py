"""Growth orchestration: import → translate → price → draft.

Persists into ``growth_sourced_listings`` / ``growth_price_rules`` and, for the
draft step, into the existing ``marketing_assets`` (kind='post', status='draft')
so the rest of the marketing/publishing backbone can pick it up unchanged.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import PublishJob
from app.models.costing import ExchangeRate
from app.models.marketing import MarketingAsset

from .adapters.reprice_default import DefaultRepricer
from .adapters.source_manual import ManualSourceAdapter
from .adapters.translate_llm import LLMTextTranslator
from .contracts import Money, PriceInputs, SourcedItem, TranslateRequest
from .models import PriceRule, SourcedListing


# --------------------------------------------------------------------------- #
# Import
# --------------------------------------------------------------------------- #
async def normalize_and_upsert(
    db: AsyncSession,
    payload: dict,
    *,
    workspace_id: uuid.UUID | None = None,
    source: str = "manual",
) -> SourcedListing:
    item: SourcedItem = ManualSourceAdapter.normalize(payload, source=source)
    existing = (
        await db.execute(
            select(SourcedListing).where(
                SourcedListing.source == item.source,
                SourcedListing.external_id == item.external_id,
            )
        )
    ).scalar_one_or_none()

    listing = existing or SourcedListing(source=item.source, external_id=item.external_id)
    listing.workspace_id = workspace_id if workspace_id is not None else listing.workspace_id
    listing.source_url = item.url
    listing.seller_ref = item.seller_ref
    listing.title = item.title
    listing.description = item.description
    listing.source_lang = payload.get("source_lang") or listing.source_lang
    listing.images_json = item.images
    listing.attributes_json = item.attributes
    listing.raw_json = item.raw
    if item.price is not None:
        listing.source_price_minor = item.price.minor
        listing.source_currency = item.price.currency
    if existing is None:
        listing.status = "imported"
        db.add(listing)
    await db.flush()
    return listing


# --------------------------------------------------------------------------- #
# Translate
# --------------------------------------------------------------------------- #
async def translate_listing(
    db: AsyncSession,
    listing: SourcedListing,
    *,
    target_lang: str,
    source_lang: str | None = None,
    glossary: dict[str, str] | None = None,
) -> SourcedListing:
    translator = LLMTextTranslator(db)
    texts = [listing.title or "", listing.description or ""]
    result = await translator.translate(
        TranslateRequest(
            texts=texts,
            target_lang=target_lang,
            source_lang=source_lang or listing.source_lang,
            glossary=glossary or {},
            context="smart-building / e-commerce product listing",
        )
    )
    listing.translated_title = result.texts[0] if result.texts else listing.title
    listing.translated_description = result.texts[1] if len(result.texts) > 1 else listing.description
    listing.target_lang = target_lang
    if listing.status in ("imported", "failed"):
        listing.status = "translated"
    await db.flush()
    return listing


# --------------------------------------------------------------------------- #
# Price
# --------------------------------------------------------------------------- #
async def resolve_fx(db: AsyncSession, base: str, quote: str) -> Decimal | None:
    if not base or not quote:
        return None
    if base == quote:
        return Decimal(1)
    row = (
        await db.execute(
            select(ExchangeRate)
            .where(ExchangeRate.base == base, ExchangeRate.quote == quote)
            .order_by(ExchangeRate.as_of.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return Decimal(row.rate) if row else None


def price_inputs_from(listing: SourcedListing, rule: PriceRule, fx_rate: Decimal) -> PriceInputs:
    purchase = Money(
        minor=int(listing.source_price_minor or 0),
        currency=listing.source_currency or "CNY",
    )
    freight_fixed = (
        Money(minor=int(rule.freight_fixed_minor), currency=rule.freight_currency or rule.sell_currency)
        if rule.freight_fixed_minor is not None
        else None
    )
    return PriceInputs(
        purchase_cost=purchase,
        fx_rate=fx_rate,
        sell_currency=rule.sell_currency,
        freight_pct=Decimal(rule.freight_pct),
        freight_fixed=freight_fixed,
        duties_pct=Decimal(rule.duties_pct),
        target_margin_pct=Decimal(rule.target_margin_pct),
        platform_fee_pct=Decimal(rule.platform_fee_pct),
        min_price=Money(minor=int(rule.min_price_minor), currency=rule.sell_currency)
        if rule.min_price_minor is not None
        else None,
        max_price=Money(minor=int(rule.max_price_minor), currency=rule.sell_currency)
        if rule.max_price_minor is not None
        else None,
        round_to_minor=int(rule.round_to_minor or 0),
    )


async def price_listing(
    db: AsyncSession,
    listing: SourcedListing,
    rule: PriceRule,
    *,
    fx_rate: Decimal | None = None,
) -> SourcedListing:
    if fx_rate is None:
        fx_rate = await resolve_fx(db, listing.source_currency or "", rule.sell_currency)
    if fx_rate is None:
        raise ValueError(
            f"No exchange rate for {listing.source_currency}->{rule.sell_currency}; "
            "pass fx_rate explicitly or seed an ExchangeRate."
        )
    inputs = price_inputs_from(listing, rule, Decimal(fx_rate))
    quote = DefaultRepricer().price(inputs)
    listing.price_rule_id = rule.id
    listing.sell_price_minor = quote.sell.minor
    listing.sell_currency = quote.sell.currency
    listing.price_quote_json = quote.model_dump(mode="json")
    if listing.status in ("imported", "translated", "failed"):
        listing.status = "priced"
    await db.flush()
    return listing


# --------------------------------------------------------------------------- #
# Draft (into marketing_assets)
# --------------------------------------------------------------------------- #
async def draft_listing(
    db: AsyncSession,
    listing: SourcedListing,
    *,
    channel: str = "instagram",
    lang: str | None = None,
) -> MarketingAsset:
    title = listing.translated_title or listing.title
    body = listing.translated_description or listing.description or ""
    price_line = ""
    if listing.sell_price_minor is not None:
        price_line = f"\n\n{(listing.sell_price_minor / 100):.2f} {listing.sell_currency}"
    asset = MarketingAsset(
        workspace_id=listing.workspace_id,
        product_id=listing.product_id,
        kind="post",
        channel=channel,
        lang=lang or listing.target_lang or "en",
        title=(title or "")[:500],
        content=(body + price_line).strip(),
        ai_generated=True,
        status="draft",
        source_metadata_json={
            "growth_sourced_listing_id": str(listing.id),
            "source": listing.source,
            "external_id": listing.external_id,
            "sell_price_minor": listing.sell_price_minor,
            "sell_currency": listing.sell_currency,
        },
    )
    db.add(asset)
    listing.status = "drafted"
    await db.flush()
    return asset


# --------------------------------------------------------------------------- #
# Publish (schedule PublishJob rows the existing dispatcher picks up)
# --------------------------------------------------------------------------- #
async def schedule_publish(
    db: AsyncSession,
    asset: MarketingAsset,
    *,
    platforms: list[str],
    scheduled_at: datetime | None = None,
    account_ref: str | None = None,
) -> list[PublishJob]:
    when = scheduled_at or datetime.now(timezone.utc)
    jobs: list[PublishJob] = []
    for platform in platforms:
        job = PublishJob(
            workspace_id=asset.workspace_id,
            asset_id=asset.id,
            platform=platform,
            account_ref=account_ref,
            scheduled_at=when,
            status="scheduled",
        )
        db.add(job)
        jobs.append(job)
    # The dispatcher only publishes assets in approved/scheduled/published state.
    if asset.status == "draft":
        asset.status = "scheduled"
    await db.flush()
    return jobs


# --------------------------------------------------------------------------- #
# Reprice (re-run compute_sell_price for a rule's listings; used by beat/manual)
# --------------------------------------------------------------------------- #
async def reprice_rule(
    db: AsyncSession,
    rule: PriceRule,
    *,
    fx_rate: Decimal | None = None,
) -> dict:
    """Re-price every listing bound to ``rule``. Only writes a new sell price
    when the relative change exceeds ``rule.reprice_threshold_pct`` (avoids
    churn). Returns a small summary."""
    listings = (
        await db.execute(select(SourcedListing).where(SourcedListing.price_rule_id == rule.id))
    ).scalars().all()
    changed = 0
    skipped = 0
    for listing in listings:
        rate = fx_rate or await resolve_fx(db, listing.source_currency or "", rule.sell_currency)
        if rate is None or not listing.source_price_minor:
            skipped += 1
            continue
        quote = DefaultRepricer().price(price_inputs_from(listing, rule, Decimal(rate)))
        old = listing.sell_price_minor
        new = quote.sell.minor
        if old and old > 0:
            delta = abs(new - old) / old
            if Decimal(delta) < Decimal(rule.reprice_threshold_pct):
                skipped += 1
                continue
        listing.sell_price_minor = new
        listing.sell_currency = quote.sell.currency
        listing.price_quote_json = quote.model_dump(mode="json")
        changed += 1
    await db.flush()
    return {"rule_id": str(rule.id), "listings": len(listings), "changed": changed, "skipped": skipped}


# --------------------------------------------------------------------------- #
# Full pipeline
# --------------------------------------------------------------------------- #
async def run_pipeline(
    db: AsyncSession,
    payload: dict,
    *,
    target_lang: str,
    rule: PriceRule,
    fx_rate: Decimal | None = None,
    channel: str = "instagram",
    workspace_id: uuid.UUID | None = None,
    source: str = "manual",
) -> tuple[SourcedListing, MarketingAsset]:
    listing = await normalize_and_upsert(db, payload, workspace_id=workspace_id, source=source)
    await translate_listing(db, listing, target_lang=target_lang)
    await price_listing(db, listing, rule, fx_rate=fx_rate)
    asset = await draft_listing(db, listing, channel=channel, lang=target_lang)
    return listing, asset

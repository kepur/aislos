"""Admin Growth API: sourcing → translate → price → draft.

Guarded by the ``admin.growth.read`` portal grant (or admin/super_admin role),
mirroring the marketing surface. Money is minor units + currency throughout.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.permissions import UserRole
from app.db.session import get_db
from app.models.user import User
from app.modules.growth import registry_boot as _registry_boot  # noqa: F401 (populates registry)
from app.modules.growth import service
from app.modules.growth.contracts import PriceInputs, PriceQuote, compute_sell_price, registry
from app.modules.growth.models import PriceRule, SourcedListing
from app.modules.growth.schemas import (
    DraftIn,
    ImportListingIn,
    ListingOut,
    PipelineIn,
    PriceIn,
    PriceRuleIn,
    PriceRuleOut,
    TranslateIn,
)
from app.services.portal_access import user_has_grant_in_any_workspace

router = APIRouter(prefix="/growth", tags=["growth"])

DB = Annotated[AsyncSession, Depends(get_db)]


async def require_growth_user(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DB,
) -> User:
    if current_user.role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        return current_user
    if await user_has_grant_in_any_workspace(
        db, current_user.id, "admin.growth.read", portal_key="admin_growth"
    ):
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Growth portal grant required")


GrowthUser = Annotated[User, Depends(require_growth_user)]


async def _get_listing(db: AsyncSession, listing_id: uuid.UUID) -> SourcedListing:
    obj = (
        await db.execute(select(SourcedListing).where(SourcedListing.id == listing_id))
    ).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Sourced listing not found")
    return obj


async def _get_rule(db: AsyncSession, rule_id: uuid.UUID) -> PriceRule:
    obj = (await db.execute(select(PriceRule).where(PriceRule.id == rule_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Price rule not found")
    return obj


# --------------------------------------------------------------------------- #
# Discovery + stateless pricing
# --------------------------------------------------------------------------- #
@router.get("/providers")
async def list_providers(_: GrowthUser) -> dict:
    return {
        "providers": [
            {
                "key": s.key,
                "label": s.label,
                "capabilities": sorted(c.value for c in s.capabilities),
                "settings_category": s.settings_category,
            }
            for s in registry.all()
        ]
    }


@router.post("/price/preview", response_model=PriceQuote)
async def price_preview(inputs: PriceInputs, _: GrowthUser) -> PriceQuote:
    return compute_sell_price(inputs)


# --------------------------------------------------------------------------- #
# Price rules
# --------------------------------------------------------------------------- #
@router.post("/price-rules", response_model=PriceRuleOut, status_code=201)
async def create_price_rule(body: PriceRuleIn, db: DB, _: GrowthUser) -> PriceRule:
    rule = PriceRule(**body.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/price-rules", response_model=list[PriceRuleOut])
async def list_price_rules(db: DB, _: GrowthUser) -> list[PriceRule]:
    rows = (
        await db.execute(select(PriceRule).order_by(PriceRule.created_at.desc()))
    ).scalars().all()
    return list(rows)


# --------------------------------------------------------------------------- #
# Listings
# --------------------------------------------------------------------------- #
@router.post("/listings", response_model=ListingOut, status_code=201)
async def import_listing(body: ImportListingIn, db: DB, _: GrowthUser) -> SourcedListing:
    listing = await service.normalize_and_upsert(
        db, body.model_dump(), workspace_id=body.workspace_id, source=body.source
    )
    await db.commit()
    await db.refresh(listing)
    return listing


@router.get("/listings", response_model=list[ListingOut])
async def list_listings(db: DB, _: GrowthUser, status_filter: str | None = None) -> list[SourcedListing]:
    stmt = select(SourcedListing).order_by(SourcedListing.created_at.desc())
    if status_filter:
        stmt = stmt.where(SourcedListing.status == status_filter)
    rows = (await db.execute(stmt.limit(200))).scalars().all()
    return list(rows)


@router.get("/listings/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: uuid.UUID, db: DB, _: GrowthUser) -> SourcedListing:
    return await _get_listing(db, listing_id)


@router.post("/listings/{listing_id}/translate", response_model=ListingOut)
async def translate_listing(listing_id: uuid.UUID, body: TranslateIn, db: DB, _: GrowthUser) -> SourcedListing:
    listing = await _get_listing(db, listing_id)
    await service.translate_listing(
        db, listing, target_lang=body.target_lang, source_lang=body.source_lang, glossary=body.glossary
    )
    await db.commit()
    await db.refresh(listing)
    return listing


@router.post("/listings/{listing_id}/price", response_model=ListingOut)
async def price_listing(listing_id: uuid.UUID, body: PriceIn, db: DB, _: GrowthUser) -> SourcedListing:
    listing = await _get_listing(db, listing_id)
    rule = await _get_rule(db, body.price_rule_id)
    try:
        await service.price_listing(db, listing, rule, fx_rate=body.fx_rate)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await db.commit()
    await db.refresh(listing)
    return listing


@router.post("/listings/{listing_id}/draft")
async def draft_listing(listing_id: uuid.UUID, body: DraftIn, db: DB, _: GrowthUser) -> dict:
    listing = await _get_listing(db, listing_id)
    asset = await service.draft_listing(db, listing, channel=body.channel, lang=body.lang)
    await db.commit()
    return {"marketing_asset_id": str(asset.id), "listing_status": listing.status}


@router.post("/pipeline")
async def run_pipeline(body: PipelineIn, db: DB, _: GrowthUser) -> dict:
    rule = await _get_rule(db, body.price_rule_id)
    payload = body.model_dump(exclude={"target_lang", "price_rule_id", "fx_rate", "channel"})
    try:
        listing, asset = await service.run_pipeline(
            db,
            payload,
            target_lang=body.target_lang,
            rule=rule,
            fx_rate=body.fx_rate,
            channel=body.channel,
            workspace_id=body.workspace_id,
            source=body.source,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await db.commit()
    await db.refresh(listing)
    return {
        "listing": ListingOut.model_validate(listing).model_dump(mode="json"),
        "marketing_asset_id": str(asset.id),
    }

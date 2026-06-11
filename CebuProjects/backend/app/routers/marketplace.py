"""Marketplace feed, ad campaigns, and ranking endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.ad_campaign import AdCampaign, AdCampaignStatus, AdPlacementType
from app.models.catalog import CatalogItem, CatalogItemStatus, MarketMode
from app.models.category import Category
from app.models.user import User, UserRole

require_admin = require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)
from app.models.company import Company
from app.schemas.marketplace import (
    AdCampaignCreate,
    AdCampaignMetricsResponse,
    AdCampaignResponse,
    AdCampaignUpdate,
    AdminAdCampaignAction,
    FeedFiltersResponse,
    FeedItemResponse,
    FeedResponse,
)
from app.services.marketplace_service import get_feed

router = APIRouter(tags=["marketplace"])


# ──────────────── Public Feed ────────────────

@router.get("/marketplace/feed", response_model=FeedResponse)
async def marketplace_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: UUID | None = None,
    market_mode: MarketMode | None = None,
    keyword: str | None = None,
    origin_country: str | None = None,
    currency: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    sort: str = Query("rank", pattern="^(rank|price_asc|price_desc|newest|orders)$"),
    account_type: str | None = None,
    verified_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Public marketplace feed with ranking and sponsored injection."""
    from app.models.user import AccountType
    acct = AccountType(account_type) if account_type in ("INDIVIDUAL", "BUSINESS") else None
    items, total = await get_feed(
        db,
        page=page,
        page_size=page_size,
        category_id=category_id,
        market_mode=market_mode,
        keyword=keyword,
        origin_country=origin_country,
        currency=currency,
        price_min=price_min,
        price_max=price_max,
        sort=sort,
        account_type=acct,
        verified_only=verified_only,
    )
    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/marketplace/categories/{category_id}/feed", response_model=FeedResponse)
async def category_feed(
    category_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    market_mode: MarketMode | None = None,
    sort: str = Query("rank", pattern="^(rank|price_asc|price_desc|newest|orders)$"),
    db: AsyncSession = Depends(get_db),
):
    """Category-specific feed."""
    items, total = await get_feed(
        db,
        page=page,
        page_size=page_size,
        category_id=category_id,
        market_mode=market_mode,
        sort=sort,
    )
    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/marketplace/filters", response_model=FeedFiltersResponse)
async def marketplace_filters(db: AsyncSession = Depends(get_db)):
    """Get available filter options for the marketplace feed."""
    # Categories with active items
    cat_rows = (await db.execute(
        select(Category.id, Category.name, Category.name_zh, Category.icon, func.count(CatalogItem.id).label("item_count"))
        .join(CatalogItem, CatalogItem.category_id == Category.id)
        .where(CatalogItem.status == CatalogItemStatus.ACTIVE)
        .group_by(Category.id, Category.name, Category.name_zh, Category.icon)
        .order_by(func.count(CatalogItem.id).desc())
    )).all()

    # Price range
    price_row = (await db.execute(
        select(func.min(CatalogItem.price_minor), func.max(CatalogItem.price_minor))
        .where(CatalogItem.status == CatalogItemStatus.ACTIVE)
    )).first()

    # Distinct currencies
    currency_rows = (await db.execute(
        select(CatalogItem.currency).where(CatalogItem.status == CatalogItemStatus.ACTIVE).distinct()
    )).scalars().all()

    # Distinct origin countries
    country_rows = (await db.execute(
        select(CatalogItem.origin_country)
        .where(CatalogItem.status == CatalogItemStatus.ACTIVE, CatalogItem.origin_country != None)  # noqa: E711
        .distinct()
    )).scalars().all()

    return FeedFiltersResponse(
        categories=[
            {"id": str(r.id), "name": r.name, "name_zh": r.name_zh, "icon": r.icon, "item_count": r.item_count}
            for r in cat_rows
        ],
        market_modes=[m.value for m in MarketMode],
        currencies=list(currency_rows),
        origin_countries=[c for c in country_rows if c],
        price_range={
            "min": price_row[0] or 0,
            "max": price_row[1] or 0,
        } if price_row else {"min": 0, "max": 0},
    )


# ──────────────── Item Detail ────────────────

@router.get("/marketplace/items/{item_id}", response_model=FeedItemResponse)
async def get_item_detail(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public product detail page data."""
    row = (await db.execute(
        select(CatalogItem, Category.name.label("category_name"), Company.name.label("company_name"))
        .join(Category, Category.id == CatalogItem.category_id, isouter=True)
        .join(Company, Company.id == CatalogItem.company_id, isouter=True)
        .where(CatalogItem.id == item_id, CatalogItem.status == CatalogItemStatus.ACTIVE)
    )).first()

    if not row:
        raise HTTPException(404, "Product not found")

    item = row.CatalogItem

    # Increment view count
    await db.execute(
        update(CatalogItem)
        .where(CatalogItem.id == item_id)
        .values(view_count=CatalogItem.view_count + 1)
    )
    await db.commit()

    # Get trust score
    from app.models.trust import TrustProfile
    trust = (await db.execute(
        select(TrustProfile.trust_score).where(TrustProfile.entity_id == item.company_id)
    )).scalar()

    return FeedItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        price_minor=item.price_minor,
        currency=item.currency,
        unit=item.unit,
        stock_qty=item.stock_qty,
        images=item.images,
        tags=item.tags,
        market_mode=item.market_mode,
        min_order_qty=item.min_order_qty,
        origin_country=item.origin_country,
        view_count=item.view_count,
        order_count=item.order_count,
        status=item.status,
        category_id=item.category_id,
        category_name=row.category_name,
        company_id=item.company_id,
        company_name=row.company_name,
        company_trust_score=trust,
        is_sponsored=False,
        created_at=item.created_at,
    )


# ──────────────── Merchant: Ad Campaigns ────────────────

@router.get("/merchant/ad-campaigns", response_model=list[AdCampaignResponse])
async def list_my_campaigns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(
        select(Company).where(Company.owner_user_id == user.id)
    )).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found")

    campaigns = (await db.execute(
        select(AdCampaign).where(AdCampaign.company_id == company.id)
        .order_by(AdCampaign.created_at.desc())
    )).scalars().all()

    return [_enrich_campaign(c) for c in campaigns]


@router.post("/merchant/ad-campaigns", response_model=AdCampaignResponse, status_code=201)
async def create_campaign(
    body: AdCampaignCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(
        select(Company).where(Company.owner_user_id == user.id)
    )).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found. Create a company first.")

    campaign = AdCampaign(
        company_id=company.id,
        **body.model_dump(),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.patch("/merchant/ad-campaigns/{campaign_id}", response_model=AdCampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    body: AdCampaignUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found")

    campaign = (await db.execute(
        select(AdCampaign).where(AdCampaign.id == campaign_id, AdCampaign.company_id == company.id)
    )).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status == AdCampaignStatus.ACTIVE:
        raise HTTPException(400, "Cannot edit active campaign. Pause it first.")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(campaign, k, v)
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.post("/merchant/ad-campaigns/{campaign_id}/submit", response_model=AdCampaignResponse)
async def submit_campaign_for_review(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found")

    campaign = (await db.execute(
        select(AdCampaign).where(AdCampaign.id == campaign_id, AdCampaign.company_id == company.id)
    )).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != AdCampaignStatus.DRAFT:
        raise HTTPException(400, f"Cannot submit campaign in status {campaign.status}")

    campaign.status = AdCampaignStatus.PENDING_REVIEW
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.post("/merchant/ad-campaigns/{campaign_id}/pause", response_model=AdCampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found")

    campaign = (await db.execute(
        select(AdCampaign).where(AdCampaign.id == campaign_id, AdCampaign.company_id == company.id)
    )).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != AdCampaignStatus.ACTIVE:
        raise HTTPException(400, "Campaign is not active")

    campaign.status = AdCampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.get("/merchant/ad-campaigns/{campaign_id}/metrics", response_model=AdCampaignMetricsResponse)
async def campaign_metrics(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalars().first()
    if not company:
        raise HTTPException(404, "Company not found")

    campaign = (await db.execute(
        select(AdCampaign).where(AdCampaign.id == campaign_id, AdCampaign.company_id == company.id)
    )).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    ctr = campaign.clicks / max(campaign.impressions, 1)
    cvr = campaign.conversions / max(campaign.clicks, 1)
    avg_cpc = campaign.spent_minor / max(campaign.clicks, 1)

    return AdCampaignMetricsResponse(
        campaign_id=campaign.id,
        impressions=campaign.impressions,
        clicks=campaign.clicks,
        conversions=campaign.conversions,
        ctr=round(ctr, 4),
        cvr=round(cvr, 4),
        spent_minor=campaign.spent_minor,
        remaining_budget_minor=campaign.budget_minor - campaign.spent_minor,
        avg_cpc_minor=round(avg_cpc, 2),
        currency=campaign.currency,
    )


# ──────────────── Admin: Ad Campaign Management ────────────────

@router.get("/admin/ad-campaigns", response_model=list[AdCampaignResponse])
async def admin_list_campaigns(
    status: AdCampaignStatus | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(AdCampaign).order_by(AdCampaign.created_at.desc())
    if status:
        q = q.where(AdCampaign.status == status)
    campaigns = (await db.execute(q)).scalars().all()
    return [_enrich_campaign(c) for c in campaigns]


@router.post("/admin/ad-campaigns/{campaign_id}/approve", response_model=AdCampaignResponse)
async def admin_approve_campaign(
    campaign_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    campaign = (await db.execute(select(AdCampaign).where(AdCampaign.id == campaign_id))).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != AdCampaignStatus.PENDING_REVIEW:
        raise HTTPException(400, f"Campaign is not pending review (status: {campaign.status})")
    campaign.status = AdCampaignStatus.ACTIVE
    campaign.rejection_reason = None
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.post("/admin/ad-campaigns/{campaign_id}/reject", response_model=AdCampaignResponse)
async def admin_reject_campaign(
    campaign_id: UUID,
    body: AdminAdCampaignAction,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    campaign = (await db.execute(select(AdCampaign).where(AdCampaign.id == campaign_id))).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.status = AdCampaignStatus.REJECTED
    campaign.rejection_reason = body.reason
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


@router.post("/admin/ad-campaigns/{campaign_id}/pause", response_model=AdCampaignResponse)
async def admin_pause_campaign(
    campaign_id: UUID,
    body: AdminAdCampaignAction,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    campaign = (await db.execute(select(AdCampaign).where(AdCampaign.id == campaign_id))).scalars().first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.status = AdCampaignStatus.PAUSED
    if body.reason:
        campaign.rejection_reason = body.reason
    await db.commit()
    await db.refresh(campaign)
    return _enrich_campaign(campaign)


# ──────────────── Helper ────────────────

def _enrich_campaign(campaign: AdCampaign) -> AdCampaignResponse:
    ctr = campaign.clicks / max(campaign.impressions, 1) if campaign.impressions else 0.0
    return AdCampaignResponse(
        **{k: getattr(campaign, k) for k in AdCampaignResponse.model_fields if hasattr(campaign, k)},
        remaining_budget_minor=campaign.budget_minor - campaign.spent_minor,
        ctr=round(ctr, 4),
    )

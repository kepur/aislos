"""Marketplace feed service with ranking logic."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad_campaign import AdCampaign, AdCampaignStatus, AdPlacementType
from app.models.catalog import CatalogItem, CatalogItemStatus, MarketMode
from app.models.category import Category
from app.models.company import Company, VerificationLevel
from app.models.trust import TrustProfile
from app.models.user import AccountType
from app.schemas.marketplace import FeedItemResponse


async def get_feed(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    category_id: UUID | None = None,
    market_mode: MarketMode | None = None,
    keyword: str | None = None,
    origin_country: str | None = None,
    currency: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    sort: str = "rank",  # rank | price_asc | price_desc | newest | orders
    account_type: AccountType | None = None,
    verified_only: bool = False,
) -> tuple[list[FeedItemResponse], int]:
    """Fetch ranked marketplace feed with optional sponsored injection."""

    # Base query: active catalog items
    q = (
        select(
            CatalogItem,
            Category.name.label("category_name"),
            Company.name.label("company_name"),
        )
        .join(Category, Category.id == CatalogItem.category_id, isouter=True)
        .join(Company, Company.id == CatalogItem.company_id, isouter=True)
        .where(CatalogItem.status == CatalogItemStatus.ACTIVE)
    )

    # Filters
    if category_id:
        q = q.where(CatalogItem.category_id == category_id)
    if market_mode:
        q = q.where(
            (CatalogItem.market_mode == market_mode) |
            (CatalogItem.market_mode == MarketMode.BOTH)
        )
    if keyword:
        q = q.where(CatalogItem.title.ilike(f"%{keyword}%"))
    if origin_country:
        q = q.where(CatalogItem.origin_country == origin_country.upper())
    if currency:
        q = q.where(CatalogItem.currency == currency.upper())
    if price_min is not None:
        q = q.where(CatalogItem.price_minor >= price_min)
    if price_max is not None:
        q = q.where(CatalogItem.price_minor <= price_max)
    # AccountType filter (join to company's owner user)
    if account_type is not None:
        from app.models.user import User
        q = q.join(User, User.id == Company.owner_user_id, isouter=True)
        q = q.where(User.account_type == account_type)
    if verified_only:
        q = q.where(Company.verification_level.in_([
            VerificationLevel.BUSINESS,
            VerificationLevel.TRUSTED,
        ]))

    # Count total
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sorting
    if sort == "price_asc":
        q = q.order_by(CatalogItem.price_minor.asc())
    elif sort == "price_desc":
        q = q.order_by(CatalogItem.price_minor.desc())
    elif sort == "newest":
        q = q.order_by(CatalogItem.created_at.desc())
    elif sort == "orders":
        q = q.order_by(CatalogItem.order_count.desc(), CatalogItem.view_count.desc())
    else:
        # Default ranking: order_count * 0.4 + view_count * 0.1 (simplified; full ranking applied below)
        q = q.order_by(
            (CatalogItem.order_count * 4 + CatalogItem.view_count).desc(),
            CatalogItem.created_at.desc()
        )

    # Pagination
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).all()

    # Fetch trust scores for companies
    company_ids = list({row.CatalogItem.company_id for row in rows})
    trust_map: dict[UUID, float] = {}
    if company_ids:
        trust_rows = (await db.execute(
            select(TrustProfile.entity_id, TrustProfile.trust_score)
            .where(TrustProfile.entity_id.in_(company_ids))
        )).all()
        trust_map = {row.entity_id: row.trust_score for row in trust_rows}

    # Build feed items
    items: list[FeedItemResponse] = []
    for row in rows:
        item = row.CatalogItem
        trust_score = trust_map.get(item.company_id)

        # Simple rank score
        rank_score = (
            (item.order_count * 0.4) +
            (item.view_count * 0.01) +
            ((trust_score or 50) * 0.3) / 100
        )

        items.append(FeedItemResponse(
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
            company_trust_score=trust_score,
            is_sponsored=False,
            ad_placement=None,
            created_at=item.created_at,
            rank_score=round(rank_score, 4),
        ))

    # Inject sponsored items at top (if feed page 1)
    if page == 1 and sort == "rank":
        sponsored = await _get_sponsored_items(db, category_id, market_mode)
        # Prepend sponsored (max 3) with dedup
        existing_ids = {i.id for i in items}
        injected = 0
        for sp in sponsored:
            if injected >= 3:
                break
            if sp.id not in existing_ids:
                items.insert(injected, sp)
                injected += 1

    return items, total


async def _get_sponsored_items(
    db: AsyncSession,
    category_id: UUID | None,
    market_mode: MarketMode | None,
) -> list[FeedItemResponse]:
    """Get active sponsored catalog items for injection into feed."""
    now = datetime.now(timezone.utc)

    q = (
        select(AdCampaign, CatalogItem, Category.name.label("category_name"), Company.name.label("company_name"))
        .join(CatalogItem, CatalogItem.id == AdCampaign.catalog_item_id)
        .join(Category, Category.id == CatalogItem.category_id, isouter=True)
        .join(Company, Company.id == CatalogItem.company_id, isouter=True)
        .where(
            AdCampaign.status == AdCampaignStatus.ACTIVE,
            AdCampaign.placement.in_([AdPlacementType.FEED_TOP, AdPlacementType.FEED_INLINE]),
            AdCampaign.spent_minor < AdCampaign.budget_minor,
            CatalogItem.status == CatalogItemStatus.ACTIVE,
        )
        .where(
            (AdCampaign.starts_at == None) | (AdCampaign.starts_at <= now)  # noqa: E711
        )
        .where(
            (AdCampaign.ends_at == None) | (AdCampaign.ends_at >= now)  # noqa: E711
        )
    )

    if category_id:
        q = q.where(
            (AdCampaign.target_category_id == None) |  # noqa: E711
            (AdCampaign.target_category_id == category_id)
        )

    # Sort by bid descending (highest bidder gets top slot)
    q = q.order_by(AdCampaign.bid_per_click_minor.desc()).limit(5)

    rows = (await db.execute(q)).all()

    items = []
    for row in rows:
        ad = row.AdCampaign
        item = row.CatalogItem
        items.append(FeedItemResponse(
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
            company_trust_score=None,
            is_sponsored=True,
            ad_placement=ad.placement.value,
            created_at=item.created_at,
            rank_score=float(ad.bid_per_click_minor),
        ))

    return items

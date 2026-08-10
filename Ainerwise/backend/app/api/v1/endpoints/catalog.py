"""Unified catalog feed.

The platform keeps official products and supplier listings in two unrelated
tables (`products` / `supplier_listings`) with separate category trees. The
storefront used to expose them as two menu entries, which forced buyers to
know which table a thing lived in before they could look for it.

This endpoint normalises both into one shape and lets the caller filter by
`source` instead. Neither table is migrated and neither existing endpoint
changes, so this is additive and reversible.

Row counts are small (a few hundred per table), so the merge happens in memory
after both sides are filtered. That keeps the ranking and pagination rules in
one readable place instead of a UNION whose two halves must stay in lockstep.
"""

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.api.deps import DB
from app.core.product_catalog import PUBLIC_PRODUCT_STATUSES
from app.models.commerce import SupplierListing, TradeCategorySchema, TrustProfile
from app.models.product import Product, ProductCategory
from app.models.user import Company

router = APIRouter(prefix="/catalog", tags=["catalog"])

SourceKey = Literal["official", "supplier", "secondhand"]

# A listing is second-hand when it sits under this category tree; everything
# else from the supplier side is a normal supplier listing.
SECONDHAND_CATEGORY_SLUGS = {"2hands", "second-hand", "secondhand"}

# products.source_type values that mean "resold / refurbished stock".
RECYCLED_PRODUCT_SOURCE_TYPES = {
    "enterprise_recycled",
    "official_recycled",
    "recycled_official",
    "refurbished",
    "secondhand",
}


def _product_source(row: Product) -> SourceKey:
    if str(row.source_type or "").lower() in RECYCLED_PRODUCT_SOURCE_TYPES:
        return "secondhand"
    if str(row.source_type or "").lower() == "supplier":
        return "supplier"
    return "official"


def _listing_source(category_slug: str | None) -> SourceKey:
    if (category_slug or "").lower() in SECONDHAND_CATEGORY_SLUGS:
        return "secondhand"
    return "supplier"


def _first_image(images: Any) -> str | None:
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url") or first.get("src")
    return None


def _product_to_item(row: Product, category_name: str | None) -> dict:
    # Official products are quoted per project, so their price is a reference
    # figure rather than a checkout price.
    price = row.list_price
    return {
        "id": str(row.id),
        "source": _product_source(row),
        "title": row.public_name or row.name,
        "brand": row.brand,
        "vendor_name": None,
        "price_minor": int(round(price * 100)) if price is not None else None,
        "currency": row.currency or "EUR",
        "price_is_reference": True,
        "market_mode": "B2B",
        "category_id": str(row.category_id) if row.category_id else None,
        "category_name": category_name,
        "image": _first_image(row.images_json),
        "verified": True,
        "trust_score": None,
        "detail_path": f"/products/{row.slug}",
        "created_at": row.created_at,
    }


def _listing_to_item(
    row: SupplierListing,
    company_name: str | None,
    category: TradeCategorySchema | None,
    verification: str | None = None,
    trust_score: int | None = None,
) -> dict:
    attributes = row.attributes_json or {}
    return {
        "id": str(row.id),
        "source": _listing_source(category.slug if category else None),
        "title": row.title,
        "brand": attributes.get("brand"),
        "vendor_name": company_name,
        "price_minor": row.price_minor,
        "currency": row.currency or "EUR",
        "price_is_reference": False,
        "market_mode": str(attributes.get("market_mode") or "B2B").upper(),
        "category_id": str(row.category_schema_id) if row.category_schema_id else None,
        "category_name": category.name if category else None,
        "image": _first_image(attributes.get("images")),
        "verified": str(verification or "").lower() in {"verified", "approved"},
        "trust_score": trust_score,
        "detail_path": f"/market/marketplace/{row.id}",
        "created_at": row.created_at,
    }


@router.get("/unified")
async def unified_catalog(
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    source: str | None = Query(default=None, description="official | supplier | secondhand"),
    market_mode: str | None = Query(default=None, description="B2B | B2C"),
    keyword: str | None = None,
    category_id: uuid.UUID | None = Query(default=None, description="matches either category tree"),
    verified_only: bool = False,
    sort: str = Query(default="newest", description="newest | price_asc | price_desc | trust"),
):
    wanted_sources = {s.strip().lower() for s in (source or "").split(",") if s.strip()}
    normalized_mode = (market_mode or "").strip().upper()

    items: list[dict] = []

    # --- Official product side -------------------------------------------
    if not wanted_sources or wanted_sources & {"official", "secondhand", "supplier"}:
        stmt = (
            select(Product, ProductCategory.name)
            .join(ProductCategory, ProductCategory.id == Product.category_id, isouter=True)
            .where(Product.status.in_(PUBLIC_PRODUCT_STATUSES))
        )
        if keyword:
            term = f"%{keyword.strip()}%"
            stmt = stmt.where(or_(Product.name.ilike(term), Product.brand.ilike(term)))
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        for row, category_name in (await db.execute(stmt)).all():
            item = _product_to_item(row, category_name)
            if wanted_sources and item["source"] not in wanted_sources:
                continue
            # Official products are project-grade B2B supply; a B2C filter
            # should not surface them.
            if normalized_mode and normalized_mode != "B2B":
                continue
            items.append(item)

    # --- Supplier listing side -------------------------------------------
    if not wanted_sources or wanted_sources & {"supplier", "secondhand"}:
        stmt = (
            select(SupplierListing, Company.name, TradeCategorySchema, Company.verification_status, TrustProfile.trust_score)
            .join(Company, Company.id == SupplierListing.company_id, isouter=True)
            .join(
                TradeCategorySchema,
                TradeCategorySchema.id == SupplierListing.category_schema_id,
                isouter=True,
            )
            .join(TrustProfile, TrustProfile.company_id == SupplierListing.company_id, isouter=True)
            .where(SupplierListing.status == "active")
        )
        if category_id:
            stmt = stmt.where(SupplierListing.category_schema_id == category_id)
        if verified_only:
            stmt = stmt.where(func.lower(Company.verification_status).in_(["verified", "approved"]))
        if keyword:
            term = f"%{keyword.strip()}%"
            stmt = stmt.where(or_(SupplierListing.title.ilike(term), Company.name.ilike(term)))
        if normalized_mode in {"B2B", "B2C"}:
            mode_expr = func.upper(
                func.coalesce(SupplierListing.attributes_json["market_mode"].astext, "B2B")
            )
            stmt = stmt.where(mode_expr.in_([normalized_mode, "BOTH"]))
        for row, company_name, category, verification, trust_score in (await db.execute(stmt)).all():
            item = _listing_to_item(row, company_name, category, verification, trust_score)
            if wanted_sources and item["source"] not in wanted_sources:
                continue
            items.append(item)

    # --- Merge, sort, paginate -------------------------------------------
    if sort == "price_asc":
        items.sort(key=lambda i: (i["price_minor"] is None, i["price_minor"] or 0))
    elif sort == "price_desc":
        items.sort(key=lambda i: (i["price_minor"] is None, -(i["price_minor"] or 0)))
    elif sort == "trust":
        items.sort(key=lambda i: -(i.get("trust_score") or 0))
    else:
        items.sort(key=lambda i: i["created_at"] or "", reverse=True)

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    for item in page_items:
        item["created_at"] = item["created_at"].isoformat() if item["created_at"] else None

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "facets": {"source": _source_counts(items)},
    }


def _source_counts(items: list[dict]) -> dict[str, int]:
    counts = {"official": 0, "supplier": 0, "secondhand": 0}
    for item in items:
        counts[item["source"]] = counts.get(item["source"], 0) + 1
    return counts


@router.get("/categories")
async def unified_categories(db: DB):
    """Both category trees side by side, tagged with which source they filter."""
    product_categories = list(
        (await db.execute(select(ProductCategory).order_by(ProductCategory.sort_order))).scalars()
    )
    trade_categories = list(
        (
            await db.execute(
                select(TradeCategorySchema)
                .where(TradeCategorySchema.status == "active")
                .order_by(TradeCategorySchema.name)
            )
        ).scalars()
    )
    return {
        "official": [
            {"id": str(row.id), "name": row.name, "slug": row.slug} for row in product_categories
        ],
        "supplier": [
            {"id": str(row.id), "name": row.name, "slug": row.slug} for row in trade_categories
        ],
    }

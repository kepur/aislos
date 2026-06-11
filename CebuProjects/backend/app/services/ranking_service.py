"""Supplier candidate ranking for buyer intents.

Scores candidates on up to 10 dimensions and returns a ranked list
with score breakdowns (why_recommended).
"""
import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogItem, CatalogItemStatus
from app.models.company import Branch, Company, CompanyStatus, VerificationLevel
from app.models.intent import Intent
from app.models.trust import TrustProfile


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


SORT_WEIGHTS = {
    "comprehensive": {
        "category": 0.25,
        "trust": 0.20,
        "distance": 0.20,
        "deal_rate": 0.15,
        "stock": 0.10,
        "verification": 0.10,
    },
    "cost": {
        "category": 0.15,
        "trust": 0.10,
        "distance": 0.10,
        "deal_rate": 0.10,
        "stock": 0.10,
        "verification": 0.05,
        "price": 0.40,  # lower price wins
    },
    "trust": {
        "category": 0.20,
        "trust": 0.50,
        "distance": 0.10,
        "deal_rate": 0.15,
        "stock": 0.05,
    },
    "distance": {
        "category": 0.20,
        "trust": 0.10,
        "distance": 0.50,
        "deal_rate": 0.10,
        "stock": 0.10,
    },
    "delivery": {
        "category": 0.15,
        "trust": 0.15,
        "distance": 0.30,
        "deal_rate": 0.20,
        "stock": 0.20,
    },
}


async def rank_supplier_candidates(
    db: AsyncSession,
    intent: Intent,
    sort: str = "comprehensive",
    limit: int = 20,
) -> list[dict]:
    """Return ranked supplier candidates with score breakdowns."""
    weights = SORT_WEIGHTS.get(sort, SORT_WEIGHTS["comprehensive"])

    result = await db.execute(
        select(CatalogItem, Company, Branch)
        .join(Company, CatalogItem.company_id == Company.id)
        .outerjoin(Branch, CatalogItem.branch_id == Branch.id)
        .where(
            CatalogItem.category_id == intent.category_id,
            CatalogItem.status == CatalogItemStatus.ACTIVE,
            Company.status == CompanyStatus.ACTIVE,
        )
    )
    rows = result.all()
    bound_catalog_item_id = None
    bound_supplier_company_id = None
    if isinstance(intent.attrs_jsonb, dict):
        bound_catalog_item_id = str(intent.attrs_jsonb.get("catalog_item_id") or "")
        bound_supplier_company_id = str(intent.attrs_jsonb.get("supplier_company_id") or "")

    # Fetch trust profiles for all companies
    company_ids = list({company.id for _, company, _ in rows})
    trust_map: dict = {}
    if company_ids:
        trust_res = await db.execute(
            select(TrustProfile).where(
                TrustProfile.entity_type == "COMPANY",
                TrustProfile.entity_id.in_(company_ids),
            )
        )
        for tp in trust_res.scalars().all():
            trust_map[tp.entity_id] = tp

    candidates: list[dict] = []
    for item, company, branch in rows:
        breakdown: dict = {}

        # 1. Category match score (0-100)
        cat_score = 60.0
        if intent.attrs_jsonb and item.attrs_jsonb:
            overlap = len(set(intent.attrs_jsonb.keys()) & set(item.attrs_jsonb.keys()))
            cat_score = min(60 + overlap * 10, 100)
        breakdown["category_match"] = round(cat_score)

        # 2. Trust score (0-100)
        tp = trust_map.get(company.id)
        trust_raw = tp.trust_score if tp else 0
        trust_norm = min(trust_raw / 10.0, 100)
        breakdown["trust_score"] = trust_raw
        breakdown["trust_tier"] = tp.trust_tier if tp else "BRONZE"
        breakdown["deal_completion_rate"] = round(tp.deal_completion_rate, 2) if tp else 0.0

        # 3. Distance score (0-100) — closer is better
        distance_km: Optional[float] = None
        distance_score = 50.0
        if intent.lat and intent.lng and branch and branch.lat and branch.lng:
            distance_km = round(_haversine_km(intent.lat, intent.lng, branch.lat, branch.lng), 1)
            within = distance_km <= (branch.radius_km or 50)
            if within:
                distance_score = max(100 - distance_km * 2, 20)
            else:
                distance_score = max(10 - distance_km * 0.5, 0)
        breakdown["distance_km"] = distance_km

        # 4. Deal completion rate score (0-100)
        deal_score = (tp.deal_completion_rate * 100) if tp else 50.0

        # 5. Stock score
        stock_ok = (item.stock_qty or 0) >= (intent.qty or 1)
        stock_score = 100.0 if stock_ok else 30.0
        breakdown["has_stock"] = stock_ok
        breakdown["stock_qty"] = item.stock_qty or 0

        # 6. Verification score (0-100)
        ver_map = {
            VerificationLevel.TRUSTED: 100,
            VerificationLevel.BUSINESS: 75,
            VerificationLevel.BASIC: 50,
            VerificationLevel.UNVERIFIED: 10,
        }
        ver_score = ver_map.get(company.verification_level, 10)
        breakdown["verification_level"] = company.verification_level.value

        # 7. Price score (inverse — lower price is better), optional
        price_score = 50.0
        if item.price_minor and intent.budget_max_minor:
            ratio = item.price_minor / max(intent.budget_max_minor, 1)
            price_score = max(0, 100 - ratio * 50)
        breakdown["price_minor"] = item.price_minor

        # Composite weighted score
        composite = (
            weights.get("category", 0) * cat_score
            + weights.get("trust", 0) * trust_norm
            + weights.get("distance", 0) * distance_score
            + weights.get("deal_rate", 0) * deal_score
            + weights.get("stock", 0) * stock_score
            + weights.get("verification", 0) * ver_score
            + weights.get("price", 0) * price_score
        )
        is_bound_catalog_item = bool(bound_catalog_item_id and str(item.id) == bound_catalog_item_id)
        is_bound_supplier = bool(bound_supplier_company_id and str(company.id) == bound_supplier_company_id)
        if is_bound_catalog_item:
            composite += 25
        elif is_bound_supplier:
            composite += 12
        breakdown["bound_catalog_item"] = is_bound_catalog_item
        breakdown["bound_supplier"] = is_bound_supplier

        # Build human-readable why_recommended
        reasons = []
        if is_bound_catalog_item:
            reasons.append("selected catalog item")
        elif is_bound_supplier:
            reasons.append("selected supplier")
        if distance_km is not None and distance_km <= 10:
            reasons.append(f"{distance_km}km away")
        if deal_score >= 80:
            reasons.append(f"{round(deal_score)}% deal rate")
        if stock_ok:
            reasons.append("in stock")
        if company.verification_level in (VerificationLevel.BUSINESS, VerificationLevel.TRUSTED):
            reasons.append("verified business")
        if breakdown["trust_tier"] in ("GOLD", "PLATINUM", "DIAMOND"):
            reasons.append(f"{breakdown['trust_tier'].title()} tier")
        why = " · ".join(reasons) if reasons else "Matching category"

        candidates.append(
            {
                "supplier_id": str(company.owner_user_id),
                "company_id": str(company.id),
                "company_name": company.name,
                "catalog_item_id": str(item.id),
                "catalog_item_title": item.title,
                "unit_price_minor": item.price_minor,
                "currency": item.currency,
                "unit": item.unit,
                "market_mode": item.market_mode.value,
                "origin_country": item.origin_country,
                "ranking_score": round(composite, 1),
                "score_breakdown": breakdown,
                "why_recommended": why,
            }
        )

    candidates.sort(key=lambda x: x["ranking_score"], reverse=True)
    return candidates[:limit]

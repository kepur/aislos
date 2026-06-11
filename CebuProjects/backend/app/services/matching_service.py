import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogItem, CatalogItemStatus
from app.models.company import Branch, Company, CompanyStatus, VerificationLevel
from app.models.intent import Intent


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def find_matching_suppliers(db: AsyncSession, intent: Intent, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(CatalogItem, Company, Branch)
        .join(Company, CatalogItem.company_id == Company.id)
        .outerjoin(Branch, CatalogItem.branch_id == Branch.id)
        .where(
            CatalogItem.category_id == intent.category_id,
            CatalogItem.status == CatalogItemStatus.ACTIVE,
            Company.status == CompanyStatus.ACTIVE,
            Company.verification_level.in_([
                VerificationLevel.BASIC,
                VerificationLevel.BUSINESS,
                VerificationLevel.TRUSTED,
            ]),
        )
    )

    scored: list[dict] = []
    for item, company, branch in result.all():
        score = 40  # category match

        if intent.attrs_jsonb and item.attrs_jsonb:
            overlap = len(set(intent.attrs_jsonb.keys()) & set(item.attrs_jsonb.keys()))
            score += min(overlap * 10, 30)

        within_radius = True
        if intent.lat and intent.lng and branch and branch.lat and branch.lng:
            dist = _haversine_km(intent.lat, intent.lng, branch.lat, branch.lng)
            if dist <= (branch.radius_km or 30):
                score += 20
            else:
                within_radius = False

        if company.verification_level == VerificationLevel.TRUSTED:
            score += 10
        elif company.verification_level == VerificationLevel.BUSINESS:
            score += 7
        elif company.verification_level == VerificationLevel.BASIC:
            score += 5

        if score >= 50:
            scored.append({
                "company_id": company.id,
                "owner_user_id": company.owner_user_id,
                "catalog_item_id": item.id,
                "score": score,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]

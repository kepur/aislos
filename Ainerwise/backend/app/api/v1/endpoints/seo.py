"""SEO Engine v1: generate keyword landing pages from the knowledge base,
review, publish; frontend-pc renders published pages at /insights/{slug}."""
import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.core.config import settings
from app.models.ai import AIReview
from app.models.content import SeoPage
from app.services.agent_runtime import AgentAuthorizationError, require_agent

router = APIRouter(tags=["seo"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^\w]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:200]


class SeoGenerateRequest(BaseModel):
    target_keyword: str
    lang: str = "en"
    region_id: uuid.UUID | None = None
    context_hint: str | None = None


class SeoPageUpdate(BaseModel):
    title: str | None = None
    meta_description: str | None = None
    content_md: str | None = None


def _page_dict(p: SeoPage, *, internal: bool) -> dict:
    data = {
        "id": str(p.id), "slug": p.slug, "lang": p.lang, "title": p.title,
        "meta_description": p.meta_description, "content_md": p.content_md,
        "ai_generated": p.ai_generated,
        "published_at": p.published_at.isoformat() if p.published_at else None,
    }
    if internal:
        data["status"] = p.status
        data["target_keyword"] = p.target_keyword
        data["created_at"] = p.created_at.isoformat()
    return data


@router.post("/admin/seo/pages/generate")
async def generate_seo_page(data: SeoGenerateRequest, db: DB, admin: AdminUser):
    try:
        await require_agent(db, "marketing-agent", workflow="content_gen")
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    slug = _slugify(data.target_keyword)
    existing = (await db.execute(select(SeoPage).where(SeoPage.slug == slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Page for slug '{slug}' already exists")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/generate",
                json={
                    "agent_slug": "marketing-agent",
                    "workflow": "content_gen",
                    "context": {"title": data.target_keyword,
                                "summary": data.context_hint or f"SEO landing page targeting: {data.target_keyword}"},
                    "channels": ["blog"], "langs": [data.lang],
                },
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            items = response.json().get("data", {}).get("items", [])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Orchestrator unavailable: {exc}") from None

    item = items[0] if items else {"title": data.target_keyword, "content": ""}
    review = AIReview(target_type="seo_page", draft_json=item, status="preliminary")
    db.add(review)
    await db.flush()
    page = SeoPage(
        region_id=data.region_id, lang=data.lang, slug=slug,
        target_keyword=data.target_keyword,
        title=item.get("title") or data.target_keyword,
        meta_description=(item.get("content") or "")[:300],
        content_md=item.get("content"),
        ai_generated=True, review_id=review.id, status="in_review",
    )
    db.add(page)
    await db.flush()
    review.target_id = page.id
    db.add(review)
    await db.commit()
    await db.refresh(page)
    return _page_dict(page, internal=True)


@router.get("/admin/seo/pages")
async def list_seo_pages_admin(
    db: DB, admin: AdminUser,
    status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(SeoPage).order_by(SeoPage.created_at.desc())
    count_query = select(func.count()).select_from(SeoPage)
    if status:
        query = query.where(SeoPage.status == status)
        count_query = count_query.where(SeoPage.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_page_dict(p, internal=True) for p in rows], "total": total}


@router.patch("/admin/seo/pages/{id}")
async def update_seo_page(id: uuid.UUID, data: SeoPageUpdate, db: DB, admin: AdminUser):
    page = await db.get(SeoPage, id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(page, key, value)
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return _page_dict(page, internal=True)


@router.post("/admin/seo/pages/{id}/publish")
async def publish_seo_page(id: uuid.UUID, db: DB, admin: AdminUser):
    page = await db.get(SeoPage, id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    page.status = "published"
    page.published_at = datetime.now(timezone.utc)
    db.add(page)
    if page.review_id:
        review = await db.get(AIReview, page.review_id)
        if review and review.status == "preliminary":
            review.status = "approved"
            review.reviewed_by = admin.id
            review.reviewed_at = datetime.now(timezone.utc)
            db.add(review)
    await db.commit()
    return {"id": str(page.id), "status": page.status, "url": f"/insights/{page.slug}"}


# ── public (website) ───────────────────────────────────────────


@router.get("/seo/pages")
async def list_seo_pages_public(db: DB, lang: str | None = None, limit: int = Query(20, ge=1, le=50)):
    query = select(SeoPage).where(SeoPage.status == "published").order_by(SeoPage.published_at.desc())
    if lang:
        query = query.where(SeoPage.lang == lang)
    rows = (await db.execute(query.limit(limit))).scalars().all()
    return {"items": [_page_dict(p, internal=False) for p in rows]}


@router.get("/seo/pages/{slug}")
async def get_seo_page_public(slug: str, db: DB):
    page = (
        await db.execute(select(SeoPage).where(SeoPage.slug == slug, SeoPage.status == "published"))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return _page_dict(page, internal=False)

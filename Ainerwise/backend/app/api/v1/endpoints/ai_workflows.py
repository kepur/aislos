"""AI workflow triggers: marketing content generation and quote drafts.

The backend assembles business context and calls the orchestrator's
/agent/generate; drafts land in ai_reviews (+ marketing_assets) as
preliminary — humans approve, then publish manually in Phase C.
"""
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.core.config import settings
from app.models.ai import AIMemory, AgentRun, AIReview
from app.models.case_library import CaseStudy
from app.models.lead import Lead
from app.models.marketing import MarketingAsset, RegionMarketingProfile
from app.models.product import Product
from app.models.region import Region
from app.services.agent_runtime import AgentAuthorizationError, require_agent
from app.services.marketing_reporting import generate_weekly_marketing_report

router = APIRouter(prefix="/admin", tags=["ai-workflows"])


async def _require_agent(db: DB, slug: str, workflow: str, *scopes: str) -> None:
    try:
        await require_agent(db, slug, scopes=scopes, workflow=workflow)
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


async def _call_orchestrator_generate(payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/generate",
                json=payload,
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Orchestrator unavailable: {exc}") from None


class MarketingGenerateRequest(BaseModel):
    product_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    channels: list[str] = ["linkedin", "blog"]
    langs: list[str] = ["en"]


@router.post("/marketing/generate")
async def generate_marketing_content(data: MarketingGenerateRequest, db: DB, admin: AdminUser):
    context: dict = {}
    if data.product_id:
        await _require_agent(db, "marketing-agent", "content_gen", "product_data")
        product = await db.get(Product, data.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        context = {"product_name": product.name, "brand": product.brand,
                   "description": product.description, "specs": product.specs_json}
    elif data.case_id:
        await _require_agent(db, "marketing-agent", "content_gen", "project_data")
        case = await db.get(CaseStudy, data.case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")
        context = {"title": case.title, "summary": case.summary,
                   "property_type": case.property_type, "area_sqm": case.area_sqm,
                   "country": case.country, "customer_feedback": case.customer_feedback}
    else:
        raise HTTPException(status_code=400, detail="product_id or case_id required")

    region_profile = None
    if data.region_id:
        profile = (
            await db.execute(
                select(RegionMarketingProfile).where(RegionMarketingProfile.region_id == data.region_id)
            )
        ).scalar_one_or_none()
        if profile:
            region_profile = {"tone": profile.tone_json, "emphasis": profile.emphasis_json,
                              "compliance": profile.compliance_notes}

    result = await _call_orchestrator_generate(
        {"agent_slug": "marketing-agent", "workflow": "content_gen",
         "context": context, "region_profile": region_profile,
         "channels": data.channels, "langs": data.langs}
    )
    items = result.get("data", {}).get("items", [])
    created = []
    for item in items:
        review = AIReview(target_type="marketing_content", draft_json=item, status="preliminary")
        db.add(review)
        await db.flush()
        asset = MarketingAsset(
            region_id=data.region_id, product_id=data.product_id, case_id=data.case_id,
            kind="post" if item.get("channel") != "blog" else "article",
            channel=item.get("channel"), lang=item.get("lang") or "en",
            title=item.get("title"), content=item.get("content"),
            ai_generated=True, review_id=review.id, status="in_review",
        )
        db.add(asset)
        await db.flush()
        review.target_id = asset.id
        db.add(review)
        created.append(str(asset.id))
    await db.commit()
    return {"created_assets": created, "llm_used": result.get("llm_used", False)}


@router.get("/marketing/assets")
async def list_marketing_assets(
    db: DB, admin: AdminUser,
    status: str | None = None, channel: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(MarketingAsset).order_by(MarketingAsset.created_at.desc())
    count_query = select(func.count()).select_from(MarketingAsset)
    if status:
        query = query.where(MarketingAsset.status == status)
        count_query = count_query.where(MarketingAsset.status == status)
    if channel:
        query = query.where(MarketingAsset.channel == channel)
        count_query = count_query.where(MarketingAsset.channel == channel)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {
        "items": [
            {"id": str(a.id), "kind": a.kind, "channel": a.channel, "lang": a.lang,
             "title": a.title, "content": a.content, "status": a.status,
             "ai_generated": a.ai_generated, "created_at": a.created_at.isoformat()}
            for a in rows
        ],
        "total": total,
    }


class AssetDecision(BaseModel):
    notes: str | None = None


@router.post("/marketing/assets/{id}/approve")
async def approve_marketing_asset(id: uuid.UUID, data: AssetDecision, db: DB, admin: AdminUser):
    from datetime import datetime, timezone

    from app.services.event_bus import emit_event

    asset = await db.get(MarketingAsset, id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status != "in_review":
        raise HTTPException(status_code=409, detail="Only in_review assets can be approved")
    asset.status = "approved"
    db.add(asset)
    if asset.review_id:
        review = await db.get(AIReview, asset.review_id)
        if review and review.status == "preliminary":
            review.status = "approved"
            review.reviewed_by = admin.id
            review.reviewed_at = datetime.now(timezone.utc)
            review.review_notes = data.notes
            db.add(review)
    await emit_event(
        db,
        "marketing.media_asset.approved",
        {"asset_id": str(asset.id)},
        aggregate_type="marketing_asset",
        aggregate_id=asset.id,
    )
    await db.commit()
    return {"id": str(asset.id), "status": asset.status}


@router.post("/marketing/assets/{id}/reject")
async def reject_marketing_asset(id: uuid.UUID, data: AssetDecision, db: DB, admin: AdminUser):
    from datetime import datetime, timezone

    from app.services.event_bus import emit_event

    if not data.notes or not data.notes.strip():
        raise HTTPException(status_code=422, detail="Rejection notes are required")
    asset = await db.get(MarketingAsset, id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status != "in_review":
        raise HTTPException(status_code=409, detail="Only in_review assets can be rejected")
    asset.status = "rejected"
    db.add(asset)
    if asset.review_id:
        review = await db.get(AIReview, asset.review_id)
        if review and review.status == "preliminary":
            review.status = "rejected"
            review.reviewed_by = admin.id
            review.reviewed_at = datetime.now(timezone.utc)
            review.review_notes = data.notes
            db.add(review)
    await emit_event(
        db,
        "marketing.media_asset.rejected",
        {"asset_id": str(asset.id), "reason": data.notes},
        aggregate_type="marketing_asset",
        aggregate_id=asset.id,
    )
    await db.commit()
    return {"id": str(asset.id), "status": asset.status}


class PublishScheduleRequest(BaseModel):
    platform: str
    scheduled_at: str  # ISO datetime


@router.post("/marketing/assets/{id}/schedule")
async def schedule_marketing_asset(id: uuid.UUID, data: PublishScheduleRequest, db: DB, admin: AdminUser):
    from datetime import datetime

    from app.models.content import PublishJob

    asset = await db.get(MarketingAsset, id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.status not in ("approved", "scheduled", "published"):
        raise HTTPException(status_code=409, detail="Only approved assets can be scheduled")
    job = PublishJob(
        asset_id=asset.id, platform=data.platform,
        scheduled_at=datetime.fromisoformat(data.scheduled_at), status="scheduled",
    )
    asset.status = "scheduled"
    db.add_all([job, asset])
    await db.commit()
    await db.refresh(job)
    return {"job_id": str(job.id), "status": job.status, "scheduled_at": job.scheduled_at.isoformat()}


@router.get("/marketing/publish-jobs")
async def list_publish_jobs(
    db: DB, admin: AdminUser,
    status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    from app.models.content import PublishJob

    query = select(PublishJob).order_by(PublishJob.scheduled_at.desc())
    count_query = select(func.count()).select_from(PublishJob)
    if status:
        query = query.where(PublishJob.status == status)
        count_query = count_query.where(PublishJob.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {
        "items": [
            {"id": str(j.id), "asset_id": str(j.asset_id), "platform": j.platform,
             "scheduled_at": j.scheduled_at.isoformat(), "status": j.status,
             "published_at": j.published_at.isoformat() if j.published_at else None,
             "error_message": j.error_message}
            for j in rows
        ],
        "total": total,
    }


class ImageGenerateRequest(BaseModel):
    prompt: str
    region_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None


@router.post("/marketing/generate-image")
async def generate_marketing_image(data: ImageGenerateRequest, db: DB, admin: AdminUser):
    """Image Studio: OpenAI-compatible /images/generations -> MinIO -> asset."""
    import base64
    import io

    from app.services.integrations import get_config
    from app.services.knowledge import get_minio_client

    cfg = await get_config(db, "ai_media")
    if not (cfg.get("_enabled") and cfg.get("api_key") and cfg.get("base_url")):
        raise HTTPException(
            status_code=503,
            detail="Image generation not configured (Admin → Integrations → ai_media)",
        )
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                cfg["base_url"].rstrip("/") + "/images/generations",
                headers={"Authorization": f"Bearer {cfg['api_key']}"},
                json={"model": cfg.get("image_model", "gpt-image-1"), "prompt": data.prompt,
                      "size": cfg.get("image_size", "1024x1024"), "n": 1},
            )
            response.raise_for_status()
            payload = response.json()["data"][0]
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Image API error: {exc}") from None

    if payload.get("b64_json"):
        image_bytes = base64.b64decode(payload["b64_json"])
    elif payload.get("url"):
        async with httpx.AsyncClient(timeout=60) as client:
            image_bytes = (await client.get(payload["url"])).content
    else:
        raise HTTPException(status_code=502, detail="Image API returned no image")

    bucket = "marketing-assets"
    minio = get_minio_client()
    if not minio.bucket_exists(bucket):
        minio.make_bucket(bucket)
    object_name = f"images/{uuid.uuid4()}.png"
    minio.put_object(bucket, object_name, io.BytesIO(image_bytes), len(image_bytes), content_type="image/png")

    review = AIReview(target_type="marketing_image", draft_json={"prompt": data.prompt}, status="preliminary")
    db.add(review)
    await db.flush()
    asset = MarketingAsset(
        region_id=data.region_id, product_id=data.product_id, case_id=data.case_id,
        kind="image", lang="en", title=data.prompt[:200],
        media_minio_key=f"{bucket}/{object_name}",
        ai_generated=True, review_id=review.id, status="in_review",
    )
    db.add(asset)
    await db.flush()
    review.target_id = asset.id
    db.add(review)
    await db.commit()
    return {"asset_id": str(asset.id), "media_key": asset.media_minio_key}


@router.post("/leads/{lead_id}/quote-draft")
async def generate_quote_draft(lead_id: uuid.UUID, db: DB, admin: AdminUser):
    await _require_agent(db, "sales-agent", "quote_draft", "customer_data", "quotes")
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lines: list[dict] = []
    region = None
    if lead.country:
        region = (
            await db.execute(select(Region).where(Region.name.ilike(lead.country)))
        ).scalar_one_or_none()
    analysis = lead.ai_analysis_json or {}
    for solution in (analysis.get("matched_solutions") or [])[:3]:
        lines.append({"name": solution.get("title") or solution.get("name"), "type": "solution"})

    context = {
        "project_type": lead.project_type,
        "country": lead.country, "city": lead.city,
        "budget_range": lead.budget_range,
        "systems_needed": lead.systems_needed_json,
        "description": lead.description,
        "lines": lines,
        "region": region.code if region else None,
    }
    result = await _call_orchestrator_generate(
        {"agent_slug": "sales-agent", "workflow": "quote_draft",
         "context": context, "lang": lead.language or "en"}
    )
    review = AIReview(
        target_type="quote_draft", target_id=lead.id,
        draft_json=result.get("data"), status="preliminary",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return {"review_id": str(review.id), "draft": review.draft_json, "llm_used": result.get("llm_used", False)}


@router.get("/memories")
async def list_memories(
    db: DB, admin: AdminUser,
    subject_type: str | None = None, subject_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    query = select(AIMemory).where(AIMemory.status == "active").order_by(AIMemory.created_at.desc())
    if subject_type:
        query = query.where(AIMemory.subject_type == subject_type)
    if subject_id:
        query = query.where(AIMemory.subject_id == subject_id)
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {
        "items": [
            {"id": str(m.id), "subject_type": m.subject_type, "subject_id": str(m.subject_id),
             "kind": m.kind, "content": m.content,
             "confidence": float(m.confidence) if m.confidence is not None else None,
             "created_at": m.created_at.isoformat()}
            for m in rows
        ]
    }


@router.get("/marketing/weekly-report/latest")
async def latest_marketing_weekly_report(db: DB, admin: AdminUser):
    run = (
        await db.execute(
            select(AgentRun)
            .where(
                AgentRun.agent_slug == "marketing-agent",
                AgentRun.workflow == "marketing_weekly_report",
            )
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    return {
        "report": None
        if run is None
        else {
            "id": str(run.id),
            "status": run.status,
            "output": run.output_json,
            "created_at": run.created_at.isoformat(),
        }
    }


@router.post("/marketing/weekly-report/run")
async def run_marketing_weekly_report(db: DB, admin: AdminUser):
    try:
        run = await generate_weekly_marketing_report(db)
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(run)
    return {"id": str(run.id), "status": run.status, "output": run.output_json}

import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.case_library import CaseStudy
from app.services.cases import embed_case
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["cases"])


class CaseUpsert(BaseModel):
    title: str
    region_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    country: str | None = None
    city: str | None = None
    property_type: str | None = None
    area_sqm: int | None = None
    budget: float | None = None
    currency: str = "EUR"
    products_json: list | None = None
    partner_id: uuid.UUID | None = None
    duration_days: int | None = None
    gross_margin_pct: float | None = None
    rework_count: int | None = None
    satisfaction_score: float | None = None
    photos_json: list | None = None
    customer_feedback: str | None = None
    summary: str | None = None
    public_visible: bool = False


def _case_dict(c: CaseStudy, *, internal: bool) -> dict:
    data = {
        "id": str(c.id), "title": c.title, "country": c.country, "city": c.city,
        "property_type": c.property_type, "area_sqm": c.area_sqm,
        "budget": float(c.budget) if c.budget is not None else None,
        "currency": c.currency, "products_json": c.products_json,
        "duration_days": c.duration_days, "photos_json": c.photos_json,
        "customer_feedback": c.customer_feedback, "summary": c.summary,
        "public_visible": c.public_visible, "created_at": c.created_at.isoformat(),
    }
    if internal:
        data["gross_margin_pct"] = float(c.gross_margin_pct) if c.gross_margin_pct is not None else None
        data["rework_count"] = c.rework_count
        data["satisfaction_score"] = float(c.satisfaction_score) if c.satisfaction_score is not None else None
        data["ai_summary"] = c.ai_summary
        data["partner_id"] = str(c.partner_id) if c.partner_id else None
        data["project_id"] = str(c.project_id) if c.project_id else None
        data["embedding_document_id"] = str(c.embedding_document_id) if c.embedding_document_id else None
    return data


@router.post("/admin/cases")
async def create_case(data: CaseUpsert, db: DB, admin: AdminUser):
    case = CaseStudy(**data.model_dump())
    db.add(case)
    await db.flush()
    document = await embed_case(db, case)
    await db.commit()
    celery_app.send_task("ingest_knowledge_document", args=[str(document.id)])
    await db.refresh(case)
    return _case_dict(case, internal=True)


@router.patch("/admin/cases/{id}")
async def update_case(id: uuid.UUID, data: CaseUpsert, db: DB, admin: AdminUser):
    case = await db.get(CaseStudy, id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    db.add(case)
    await db.flush()
    document = await embed_case(db, case)  # re-embed on content change
    await db.commit()
    celery_app.send_task("ingest_knowledge_document", args=[str(document.id)])
    await db.refresh(case)
    return _case_dict(case, internal=True)


@router.get("/admin/cases")
async def list_cases_admin(
    db: DB, admin: AdminUser,
    property_type: str | None = None, country: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(CaseStudy).order_by(CaseStudy.created_at.desc())
    count_query = select(func.count()).select_from(CaseStudy)
    if property_type:
        query = query.where(CaseStudy.property_type == property_type)
        count_query = count_query.where(CaseStudy.property_type == property_type)
    if country:
        query = query.where(CaseStudy.country.ilike(country))
        count_query = count_query.where(CaseStudy.country.ilike(country))
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_case_dict(c, internal=True) for c in rows], "total": total}


@router.delete("/admin/cases/{id}")
async def delete_case(id: uuid.UUID, db: DB, admin: AdminUser):
    case = await db.get(CaseStudy, id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.embedding_document_id:
        from app.models.ai import KnowledgeDocument

        doc = await db.get(KnowledgeDocument, case.embedding_document_id)
        if doc:
            await db.delete(doc)
    await db.delete(case)
    await db.commit()
    return {"deleted": True}


@router.get("/admin/cases/similar")
async def find_similar_cases_admin(
    db: DB, admin: AdminUser,
    query: str,
    country: str | None = None,
    property_type: str | None = None,
    area_sqm: int | None = None,
    limit: int = Query(3, ge=1, le=10),
):
    """Living Case Dataset lookup for admins (same engine the AI consultant uses)."""
    from sqlalchemy import text as sql_text

    from app.services.embeddings import embed_texts

    vectors, _ = await embed_texts(db, [query])
    qvec = "[" + ",".join(f"{v:.8f}" for v in vectors[0]) + "]"
    rows = (
        await db.execute(
            sql_text(
                """
                SELECT c.id, c.title, c.country, c.city, c.property_type, c.area_sqm,
                       c.budget, c.currency, c.duration_days, c.gross_margin_pct,
                       min(ch.embedding <=> CAST(:qvec AS vector)) AS distance
                FROM cases c
                JOIN ai.document_chunks ch ON ch.document_id = c.embedding_document_id
                WHERE ch.embedding IS NOT NULL
                  AND (CAST(:country AS text) IS NULL OR c.country ILIKE :country)
                  AND (CAST(:property_type AS text) IS NULL OR c.property_type = :property_type)
                  AND (CAST(:area_sqm AS int) IS NULL
                       OR c.area_sqm BETWEEN CAST(:area_sqm AS int) * 0.7 AND CAST(:area_sqm AS int) * 1.3)
                GROUP BY c.id
                ORDER BY distance
                LIMIT :top_k
                """
            ),
            {"qvec": qvec, "country": country, "property_type": property_type,
             "area_sqm": area_sqm, "top_k": limit},
        )
    ).mappings().all()
    return {
        "items": [
            {
                "case_id": str(r["id"]), "title": r["title"], "country": r["country"],
                "city": r["city"], "property_type": r["property_type"], "area_sqm": r["area_sqm"],
                "budget": float(r["budget"]) if r["budget"] is not None else None,
                "currency": r["currency"], "duration_days": r["duration_days"],
                "gross_margin_pct": float(r["gross_margin_pct"]) if r["gross_margin_pct"] is not None else None,
                "similarity": round(1 - float(r["distance"]), 4),
            }
            for r in rows
        ]
    }


# Public: website case wall (no margin/partner/internal fields).
@router.get("/cases")
async def list_cases_public(
    db: DB,
    property_type: str | None = None, country: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(12, ge=1, le=50),
):
    query = select(CaseStudy).where(CaseStudy.public_visible.is_(True)).order_by(CaseStudy.created_at.desc())
    count_query = select(func.count()).select_from(CaseStudy).where(CaseStudy.public_visible.is_(True))
    if property_type:
        query = query.where(CaseStudy.property_type == property_type)
        count_query = count_query.where(CaseStudy.property_type == property_type)
    if country:
        query = query.where(CaseStudy.country.ilike(country))
        count_query = count_query.where(CaseStudy.country.ilike(country))
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_case_dict(c, internal=False) for c in rows], "total": total}

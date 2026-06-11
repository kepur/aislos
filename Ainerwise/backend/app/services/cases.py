"""Case library: structured cases embed into the knowledge base so the AI
consultant can cite similar delivered projects. Margin stays internal."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import KnowledgeDocument
from app.models.case_library import CaseStudy
def build_case_summary(case: CaseStudy) -> str:
    parts = [f"Case study: {case.title}."]
    if case.property_type or case.area_sqm:
        parts.append(f"Property: {case.property_type or 'n/a'}, {case.area_sqm or '?'} sqm.")
    if case.city or case.country:
        parts.append(f"Location: {', '.join(p for p in [case.city, case.country] if p)}.")
    if case.budget:
        parts.append(f"Budget: {case.budget} {case.currency}.")
    if case.products_json:
        names = [p.get("name") or str(p) for p in case.products_json if p]
        if names:
            parts.append(f"Installed: {', '.join(names[:10])}.")
    if case.duration_days:
        parts.append(f"Delivery time: {case.duration_days} days.")
    if case.summary:
        parts.append(case.summary)
    if case.customer_feedback:
        parts.append(f"Customer feedback: {case.customer_feedback}")
    return "\n".join(parts)


async def embed_case(db: AsyncSession, case: CaseStudy) -> KnowledgeDocument:
    """Prepare the knowledge document for a case.

    The caller must enqueue ingestion only after its transaction commits.
    Queueing here races the worker against an uncommitted document and can
    leave a Celery task marked successful with a failed ingestion result.

    Intentionally excludes gross_margin_pct — internal economics never enter
    the customer-facing knowledge base."""
    summary = build_case_summary(case)
    doc = None
    if case.embedding_document_id:
        doc = await db.get(KnowledgeDocument, case.embedding_document_id)
    if doc is None:
        doc = KnowledgeDocument(source_type="case_study", title=case.title, lang=None, status="pending")
        db.add(doc)
        await db.flush()
        case.embedding_document_id = doc.id
        db.add(case)
    doc.title = case.title
    doc.status = "pending"
    doc.meta_json = {**(doc.meta_json or {}), "inline_text": summary, "case_id": str(case.id)}
    db.add(doc)
    await db.flush()
    return doc

"""Document Center: templates ({{variable}}) -> rendered documents -> PDF.
AI-polished drafts pass ai_reviews; finalize renders the PDF into MinIO."""
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.content import DocumentTemplate, GeneratedDocument
from app.services.documents import pdf_download_url, render_template, store_pdf

router = APIRouter(prefix="/admin/documents", tags=["documents"])


class TemplateUpsert(BaseModel):
    kind: str
    name: str
    body_md: str
    lang: str = "en"
    region_id: uuid.UUID | None = None
    variables_json: list | None = None
    is_active: bool = True


class DocumentGenerate(BaseModel):
    template_id: uuid.UUID
    title: str
    variables: dict = {}
    subject_type: str | None = None
    subject_id: uuid.UUID | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    body_md: str | None = None


def _template_dict(t: DocumentTemplate) -> dict:
    return {
        "id": str(t.id), "kind": t.kind, "name": t.name, "lang": t.lang,
        "body_md": t.body_md, "variables_json": t.variables_json,
        "is_active": t.is_active, "created_at": t.created_at.isoformat(),
    }


def _document_dict(d: GeneratedDocument) -> dict:
    return {
        "id": str(d.id), "kind": d.kind, "title": d.title, "body_md": d.body_md,
        "subject_type": d.subject_type,
        "subject_id": str(d.subject_id) if d.subject_id else None,
        "status": d.status, "pdf_minio_key": d.pdf_minio_key,
        "ai_generated": d.ai_generated, "created_at": d.created_at.isoformat(),
    }


@router.post("/templates")
async def create_template(data: TemplateUpsert, db: DB, admin: AdminUser):
    template = DocumentTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return _template_dict(template)


@router.get("/templates")
async def list_templates(db: DB, admin: AdminUser, kind: str | None = None):
    query = select(DocumentTemplate).where(DocumentTemplate.is_active.is_(True)).order_by(DocumentTemplate.kind)
    if kind:
        query = query.where(DocumentTemplate.kind == kind)
    rows = (await db.execute(query)).scalars().all()
    return {"items": [_template_dict(t) for t in rows]}


@router.patch("/templates/{id}")
async def update_template(id: uuid.UUID, data: TemplateUpsert, db: DB, admin: AdminUser):
    template = await db.get(DocumentTemplate, id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return _template_dict(template)


@router.post("/generate")
async def generate_document(data: DocumentGenerate, db: DB, admin: AdminUser):
    template = await db.get(DocumentTemplate, data.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    body, missing = render_template(template.body_md, data.variables)
    document = GeneratedDocument(
        template_id=template.id, kind=template.kind, title=data.title,
        body_md=body, subject_type=data.subject_type, subject_id=data.subject_id,
        ai_generated=False, status="draft",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return {**_document_dict(document), "missing_variables": missing}


@router.get("")
async def list_documents(
    db: DB, admin: AdminUser,
    kind: str | None = None, status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(GeneratedDocument).order_by(GeneratedDocument.created_at.desc())
    count_query = select(func.count()).select_from(GeneratedDocument)
    if kind:
        query = query.where(GeneratedDocument.kind == kind)
        count_query = count_query.where(GeneratedDocument.kind == kind)
    if status:
        query = query.where(GeneratedDocument.status == status)
        count_query = count_query.where(GeneratedDocument.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_document_dict(d) for d in rows], "total": total}


@router.patch("/{id}")
async def update_document(id: uuid.UUID, data: DocumentUpdate, db: DB, admin: AdminUser):
    document = await db.get(GeneratedDocument, id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "final":
        raise HTTPException(status_code=409, detail="Final documents are immutable")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(document, key, value)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return _document_dict(document)


@router.post("/{id}/finalize")
async def finalize_document(id: uuid.UUID, db: DB, admin: AdminUser):
    document = await db.get(GeneratedDocument, id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.body_md:
        raise HTTPException(status_code=400, detail="Document body is empty")
    document.pdf_minio_key = store_pdf(document.title, document.body_md)
    document.status = "final"
    db.add(document)
    await db.commit()
    return {**_document_dict(document), "pdf_url": pdf_download_url(document.pdf_minio_key)}


@router.get("/{id}/pdf-url")
async def get_document_pdf_url(id: uuid.UUID, db: DB, admin: AdminUser):
    document = await db.get(GeneratedDocument, id)
    if document is None or not document.pdf_minio_key:
        raise HTTPException(status_code=404, detail="PDF not available")
    return {"pdf_url": pdf_download_url(document.pdf_minio_key)}

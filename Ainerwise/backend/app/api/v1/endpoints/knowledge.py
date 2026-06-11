import uuid

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.ai import DocumentChunk, KnowledgeDocument
from app.schemas.ai import DocumentChunkRead, KnowledgeDocumentRead, KnowledgeTextCreate
from app.services.event_bus import EventType, emit_event
from app.services.knowledge import KNOWLEDGE_BUCKET, chunk_counts, ensure_bucket, get_minio_client
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/admin/knowledge", tags=["knowledge"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _enqueue_ingest(document_id: uuid.UUID) -> None:
    celery_app.send_task("ingest_knowledge_document", args=[str(document_id)])


@router.post("/documents", response_model=KnowledgeDocumentRead)
async def upload_document(
    db: DB,
    admin: AdminUser,
    file: UploadFile = File(...),
    title: str = Form(""),
    source_type: str = Form("manual"),
    lang: str = Form(""),
    product_id: str = Form(""),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    client = get_minio_client()
    ensure_bucket(client)
    object_name = f"{uuid.uuid4()}/{file.filename}"
    import io

    client.put_object(
        KNOWLEDGE_BUCKET, object_name, io.BytesIO(data), len(data),
        content_type=file.content_type or "application/octet-stream",
    )

    doc = KnowledgeDocument(
        source_type=source_type or "manual",
        title=title or file.filename or "Untitled",
        lang=lang or None,
        minio_key=object_name,
        product_id=uuid.UUID(product_id) if product_id else None,
        status="pending",
        meta_json={"filename": file.filename, "size_bytes": len(data)},
    )
    db.add(doc)
    await db.flush()
    await emit_event(
        db, EventType.KNOWLEDGE_UPLOADED,
        {"document_id": str(doc.id), "title": doc.title, "source_type": doc.source_type},
        aggregate_type="knowledge_document", aggregate_id=doc.id,
    )
    await db.commit()
    await db.refresh(doc)
    _enqueue_ingest(doc.id)
    return KnowledgeDocumentRead.model_validate(doc)


@router.post("/documents/text", response_model=KnowledgeDocumentRead)
async def create_text_document(data: KnowledgeTextCreate, db: DB, admin: AdminUser):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Empty content")
    doc = KnowledgeDocument(
        source_type=data.source_type,
        title=data.title,
        lang=data.lang,
        product_id=data.product_id,
        status="pending",
        meta_json={"inline_text": data.content},
    )
    db.add(doc)
    await db.flush()
    await emit_event(
        db, EventType.KNOWLEDGE_UPLOADED,
        {"document_id": str(doc.id), "title": doc.title, "source_type": doc.source_type},
        aggregate_type="knowledge_document", aggregate_id=doc.id,
    )
    await db.commit()
    await db.refresh(doc)
    _enqueue_ingest(doc.id)
    return KnowledgeDocumentRead.model_validate(doc)


@router.get("/documents")
async def list_documents(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    source_type: str | None = None,
):
    filters = []
    if status:
        filters.append(KnowledgeDocument.status == status)
    if source_type:
        filters.append(KnowledgeDocument.source_type == source_type)

    query = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    count_query = select(func.count()).select_from(KnowledgeDocument)
    for item in filters:
        query = query.where(item)
        count_query = count_query.where(item)

    total = (await db.execute(count_query)).scalar() or 0
    docs = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    counts = await chunk_counts(db, [d.id for d in docs])
    items = []
    for doc in docs:
        read = KnowledgeDocumentRead.model_validate(doc)
        read.chunk_count = counts.get(doc.id, 0)
        items.append(read)
    return {"items": items, "total": total}


@router.get("/documents/{id}", response_model=KnowledgeDocumentRead)
async def get_document(id: uuid.UUID, db: DB, admin: AdminUser):
    doc = await db.get(KnowledgeDocument, id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    read = KnowledgeDocumentRead.model_validate(doc)
    read.chunk_count = (await chunk_counts(db, [doc.id])).get(doc.id, 0)
    return read


@router.get("/documents/{id}/chunks")
async def get_document_chunks(
    id: uuid.UUID, db: DB, admin: AdminUser,
    skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50),
):
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == id)
        .order_by(DocumentChunk.chunk_index)
        .offset(skip).limit(limit)
    )
    return {"items": [DocumentChunkRead.model_validate(c) for c in result.scalars().all()]}


@router.post("/documents/{id}/reingest", response_model=KnowledgeDocumentRead)
async def reingest_document(id: uuid.UUID, db: DB, admin: AdminUser):
    doc = await db.get(KnowledgeDocument, id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "pending"
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    _enqueue_ingest(doc.id)
    return KnowledgeDocumentRead.model_validate(doc)


@router.delete("/documents/{id}")
async def delete_document(id: uuid.UUID, db: DB, admin: AdminUser):
    doc = await db.get(KnowledgeDocument, id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    minio_key = doc.minio_key
    await db.delete(doc)  # chunks cascade
    await db.commit()
    if minio_key:
        try:
            get_minio_client().remove_object(KNOWLEDGE_BUCKET, minio_key)
        except Exception:  # noqa: BLE001 — DB row is gone; orphan object is acceptable
            pass
    return {"deleted": True}

"""Knowledge ingestion pipeline: extract -> chunk -> embed -> ai.document_chunks.

Runs on the `ai_ingestion` Celery queue. Source bytes live in MinIO
(`knowledge-source` bucket); small text sources (FAQ entries) may instead
carry their body in meta_json["inline_text"] and skip MinIO entirely.
"""
from __future__ import annotations

import io
import re
import uuid

from minio import Minio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import DocumentChunk, KnowledgeDocument
from app.services.embeddings import embed_texts

KNOWLEDGE_BUCKET = "knowledge-source"
CHUNK_MAX_CHARS = 1800
CHUNK_OVERLAP_CHARS = 200
EMBED_BATCH_SIZE = 64


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_USE_SSL,
    )


def ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(KNOWLEDGE_BUCKET):
        client.make_bucket(KNOWLEDGE_BUCKET)


# --- extraction ---------------------------------------------------------------

def extract_text(data: bytes, filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf") or data[:5] == b"%PDF-":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    text = data.decode("utf-8", errors="replace")
    if name.endswith((".html", ".htm")):
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    return text


# --- chunking -----------------------------------------------------------------

def chunk_text(
    text: str,
    max_chars: int = CHUNK_MAX_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """Paragraph-aware splitting with a sliding-window fallback for long blocks."""
    normalized = re.sub(r"\n{3,}", "\n\n", text.replace("\r\n", "\n")).strip()
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    blocks: list[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            blocks.append(para)
            continue
        start = 0
        while start < len(para):
            blocks.append(para[start : start + max_chars])
            start += max_chars - overlap

    chunks: list[str] = []
    current = ""
    for block in blocks:
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = block
    if current:
        chunks.append(current)
    return chunks


# --- ingestion ----------------------------------------------------------------

async def ingest_document(db: AsyncSession, document_id: uuid.UUID) -> dict:
    doc = await db.get(KnowledgeDocument, document_id)
    if doc is None:
        return {"status": "not_found", "document_id": str(document_id)}

    try:
        meta = dict(doc.meta_json or {})
        if meta.get("inline_text"):
            text = meta["inline_text"]
        elif doc.minio_key:
            client = get_minio_client()
            response = client.get_object(KNOWLEDGE_BUCKET, doc.minio_key)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
            text = extract_text(data, meta.get("filename") or doc.minio_key)
        else:
            raise ValueError("document has neither minio_key nor inline_text")

        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("no text could be extracted")

        vectors: list[list[float]] = []
        provider = None
        for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
            batch_vectors, provider = await embed_texts(db, batch)
            vectors.extend(batch_vectors)

        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        for index, (content, embedding) in enumerate(zip(chunks, vectors)):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )

        meta["embedding_provider"] = provider
        meta["chunk_count"] = len(chunks)
        doc.meta_json = meta
        doc.status = "embedded"
        db.add(doc)
        await db.commit()
        return {"status": "embedded", "document_id": str(doc.id), "chunks": len(chunks)}
    except Exception as exc:  # noqa: BLE001 — status machine must capture any failure
        await db.rollback()
        doc = await db.get(KnowledgeDocument, document_id)
        if doc is not None:
            meta = dict(doc.meta_json or {})
            meta["last_error"] = str(exc)[:500]
            doc.meta_json = meta
            doc.status = "failed"
            db.add(doc)
            await db.commit()
        return {"status": "failed", "document_id": str(document_id), "error": str(exc)[:200]}


async def chunk_counts(db: AsyncSession, document_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not document_ids:
        return {}
    from sqlalchemy import func

    result = await db.execute(
        select(DocumentChunk.document_id, func.count())
        .where(DocumentChunk.document_id.in_(document_ids))
        .group_by(DocumentChunk.document_id)
    )
    return dict(result.all())

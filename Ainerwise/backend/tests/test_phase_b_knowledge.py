"""Phase B tests: knowledge ingestion pipeline, AI chat surface, internal API.

Ingestion runs with the hash embedding fallback (no AI configured), so the
whole pipeline is exercised without external credentials.
"""
import asyncio
import math
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.ai import DocumentChunk, KnowledgeDocument
from app.models.lead import Lead
from app.services.embeddings import EMBEDDING_DIM, hash_embed
from app.services.knowledge import chunk_text, ingest_document


def test_phase_b_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/knowledge/documents",
        "/api/v1/admin/knowledge/documents/text",
        "/api/v1/admin/knowledge/documents/{id}/reingest",
        "/api/v1/admin/ai-reviews",
        "/api/v1/admin/ai-reviews/{id}/approve",
        "/api/v1/admin/ai-conversations",
        "/api/v1/ai/chat",
        "/api/v1/ai/chat/status",
        "/internal/v1/leads",
    ):
        assert p in paths, p


# --- chunker -------------------------------------------------------------------

def test_chunk_text_paragraph_packing():
    text = "\n\n".join(f"Paragraph {i} " + "x" * 300 for i in range(10))
    chunks = chunk_text(text, max_chars=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    assert chunks[0].startswith("Paragraph 0")


def test_chunk_text_long_block_sliding_window():
    text = "y" * 5000
    chunks = chunk_text(text, max_chars=1000, overlap=100)
    assert all(len(c) <= 1000 for c in chunks)
    assert sum(len(c) for c in chunks) >= 5000  # overlap duplicates some chars


def test_chunk_text_empty():
    assert chunk_text("   \n\n  ") == []


# --- hash embedding fallback ----------------------------------------------------

def test_hash_embed_deterministic_and_normalized():
    a = hash_embed("KNX actuator installation on DIN rail")
    b = hash_embed("KNX actuator installation on DIN rail")
    assert a == b
    assert len(a) == EMBEDDING_DIM
    norm = math.sqrt(sum(v * v for v in a))
    assert abs(norm - 1.0) < 1e-6


def test_hash_embed_similarity_orders_correctly():
    query = hash_embed("solar inverter warranty")
    similar = hash_embed("warranty terms for the solar inverter")
    unrelated = hash_embed("kitchen gas alarm maintenance")
    dot_similar = sum(x * y for x, y in zip(query, similar))
    dot_unrelated = sum(x * y for x, y in zip(query, unrelated))
    assert dot_similar > dot_unrelated


# --- ingestion pipeline (inline text, hash provider) ------------------------------

def test_ingest_inline_text_document():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            doc = KnowledgeDocument(
                source_type="faq",
                title="Test FAQ — KNX vs Matter",
                meta_json={"inline_text": "KNX is a wired bus standard for building automation. "
                                          "Matter is a new IP-based smart home standard.\n\n"
                                          "AinerWise integrates both depending on project scale."},
                status="pending",
            )
            db.add(doc)
            await db.commit()
            doc_id = doc.id

        async with async_session_factory() as db:
            result = await ingest_document(db, doc_id)
            assert result["status"] == "embedded", result
            assert result["chunks"] >= 1

            refreshed = await db.get(KnowledgeDocument, doc_id)
            assert refreshed.status == "embedded"
            assert refreshed.meta_json["embedding_provider"] == "hash-v1"

            from sqlalchemy import select

            chunks = (
                await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            ).scalars().all()
            assert chunks and chunks[0].embedding is not None
            await db.refresh(chunks[0], ["tsv"])
            assert chunks[0].tsv is not None

            # cleanup
            await db.delete(refreshed)
            await db.commit()

    asyncio.run(_run())


def test_ingest_missing_source_marks_failed():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            doc = KnowledgeDocument(source_type="manual", title="No source", status="pending")
            db.add(doc)
            await db.commit()
            doc_id = doc.id

        async with async_session_factory() as db:
            result = await ingest_document(db, doc_id)
            assert result["status"] == "failed"
            refreshed = await db.get(KnowledgeDocument, doc_id)
            assert refreshed.status == "failed"
            assert "last_error" in (refreshed.meta_json or {})
            await db.delete(refreshed)
            await db.commit()

    asyncio.run(_run())


# --- internal service API ---------------------------------------------------------

def test_internal_leads_requires_service_token():
    async def _run():
        await engine.dispose()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/internal/v1/leads", json={"contact_email": "a@b.c"})
            assert r.status_code in (401, 403)
            r = await client.post(
                "/internal/v1/leads",
                json={"contact_email": "a@b.c"},
                headers={"X-Service-Token": "wrong"},
            )
            assert r.status_code == 401

    asyncio.run(_run())


def test_internal_leads_creates_lead_with_event():
    async def _run():
        await engine.dispose()
        marker = f"ai-e2e-{uuid.uuid4().hex[:8]}@test.local"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/internal/v1/leads",
                json={
                    "contact_email": marker,
                    "description": "300sqm villa, smart lighting + solar",
                    "language": "en",
                },
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            assert r.status_code == 200, r.text
            lead_id = r.json()["lead_id"]

        async with async_session_factory() as db:
            lead = await db.get(Lead, uuid.UUID(lead_id))
            assert lead is not None
            assert lead.source_channel == "ai_chat"
            assert lead.contact_email == marker

            from sqlalchemy import select

            from app.models.integration import IntegrationEvent

            events = (
                await db.execute(
                    select(IntegrationEvent).where(
                        IntegrationEvent.event_type == "lead.created",
                        IntegrationEvent.payload_json["lead_id"].astext == lead_id,
                    )
                )
            ).scalars().all()
            assert len(events) == 1

            # cleanup
            for event in events:
                await db.delete(event)
            await db.delete(lead)
            await db.commit()

    asyncio.run(_run())

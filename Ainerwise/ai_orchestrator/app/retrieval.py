"""Hybrid retrieval over ai.document_chunks: pgvector cosine + tsv full text,
fused with reciprocal rank fusion. One SQL statement — this JOIN-ability with
business filters is the reason pgvector won over a separate vector DB (ADR-4).
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

HYBRID_SQL = text(
    """
WITH vec AS (
    SELECT c.id, c.document_id, c.content,
           row_number() OVER (ORDER BY c.embedding <=> CAST(:qvec AS vector)) AS rank
    FROM ai.document_chunks c
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> CAST(:qvec AS vector)
    LIMIT 20
),
txt AS (
    SELECT c.id, c.document_id, c.content,
           row_number() OVER (
               ORDER BY ts_rank(c.tsv, plainto_tsquery('simple', :query)) DESC
           ) AS rank
    FROM ai.document_chunks c
    WHERE c.tsv @@ plainto_tsquery('simple', :query)
    LIMIT 20
)
SELECT COALESCE(v.id, t.id) AS chunk_id,
       COALESCE(v.document_id, t.document_id) AS document_id,
       COALESCE(v.content, t.content) AS content,
       COALESCE(1.0 / (60 + v.rank), 0) + COALESCE(1.0 / (60 + t.rank), 0) AS score,
       d.title AS document_title,
       d.source_type AS source_type
FROM vec v
FULL OUTER JOIN txt t ON v.id = t.id
JOIN ai.knowledge_documents d ON d.id = COALESCE(v.document_id, t.document_id)
WHERE d.status = 'embedded'
ORDER BY score DESC
LIMIT :top_k
"""
)


async def search_chunks(
    db: AsyncSession, query: str, query_vector: list[float], top_k: int | None = None
) -> list[dict[str, Any]]:
    qvec = "[" + ",".join(f"{v:.8f}" for v in query_vector) + "]"
    rows = (
        await db.execute(
            HYBRID_SQL,
            {"qvec": qvec, "query": query, "top_k": top_k or settings.RETRIEVAL_TOP_K},
        )
    ).mappings().all()
    return [
        {
            "chunk_id": str(row["chunk_id"]),
            "document_id": str(row["document_id"]),
            "title": row["document_title"],
            "source_type": row["source_type"],
            "content": row["content"],
            "score": float(row["score"]),
        }
        for row in rows
    ]


SIMILAR_CASES_SQL = text(
    """
SELECT c.id, c.title, c.country, c.city, c.property_type, c.area_sqm,
       c.budget, c.currency, c.duration_days,
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
)


async def find_similar_cases(
    db: AsyncSession,
    query_vector: list[float],
    *,
    country: str | None = None,
    property_type: str | None = None,
    area_sqm: int | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Living Case Dataset lookup: structured filters + vector similarity.
    Never returns margin/partner internals — safe for customer-facing answers."""
    qvec = "[" + ",".join(f"{v:.8f}" for v in query_vector) + "]"
    rows = (
        await db.execute(
            SIMILAR_CASES_SQL,
            {"qvec": qvec, "country": country, "property_type": property_type,
             "area_sqm": area_sqm, "top_k": top_k},
        )
    ).mappings().all()
    return [
        {
            "case_id": str(row["id"]),
            "title": row["title"],
            "country": row["country"],
            "city": row["city"],
            "property_type": row["property_type"],
            "area_sqm": row["area_sqm"],
            "budget": float(row["budget"]) if row["budget"] is not None else None,
            "currency": row["currency"],
            "duration_days": row["duration_days"],
            "similarity": round(1 - float(row["distance"]), 4),
        }
        for row in rows
    ]


_WORD_RE = re.compile(r"[\w一-鿿]{3,}", re.UNICODE)

PRODUCT_SQL = text(
    """
SELECT id, name, brand, slug, list_price, currency
FROM products
WHERE name ILIKE :pattern OR brand ILIKE :pattern OR description ILIKE :pattern
ORDER BY updated_at DESC
LIMIT 3
"""
)


async def match_products(db: AsyncSession, query: str) -> list[dict[str, Any]]:
    """Cheap keyword product matching; vector product search can replace this later."""
    seen: dict[str, dict[str, Any]] = {}
    for token in _WORD_RE.findall(query)[:6]:
        rows = (
            await db.execute(PRODUCT_SQL, {"pattern": f"%{token}%"})
        ).mappings().all()
        for row in rows:
            product_id = str(row["id"])
            if product_id not in seen:
                seen[product_id] = {
                    "id": product_id,
                    "name": row["name"],
                    "brand": row["brand"],
                    "slug": row["slug"],
                    "list_price": float(row["list_price"]) if row["list_price"] is not None else None,
                    "currency": row["currency"],
                }
        if len(seen) >= 3:
            break
    return list(seen.values())[:3]

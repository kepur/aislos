"""Embedding provider with graceful degradation.

Uses the admin-configured OpenAI-compatible endpoint ("ai" integration
settings, same credentials as chat). When no provider is configured the
deterministic feature-hashing fallback keeps the whole pipeline (ingest,
hybrid search, tests) runnable in dev — recall quality then comes from the
full-text half of the hybrid search, not the vectors.

The provider name is recorded on each ingested document; mixing providers
in one corpus breaks cosine distances, so re-ingest everything after
switching (the admin knowledge page exposes re-ingest per document).
"""
from __future__ import annotations

import hashlib
import math
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import EMBEDDING_DIM
from app.services.integrations import get_config

HASH_PROVIDER = "hash-v1"
_TOKEN_RE = re.compile(r"[\w一-鿿]+", re.UNICODE)


def hash_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic feature-hashing bag-of-words vector (dev fallback)."""
    vec = [0.0] * dim
    for token in _TOKEN_RE.findall(text.lower()):
        digest = hashlib.md5(token.encode()).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[index] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


async def embedding_config(db: AsyncSession) -> dict | None:
    """Return the remote embedding config, or None to use the hash fallback."""
    cfg = await get_config(db, "ai")
    if cfg.get("_enabled") and cfg.get("base_url") and cfg.get("api_key") and cfg.get("embedding_model"):
        return cfg
    return None


async def embed_texts(db: AsyncSession, texts: list[str]) -> tuple[list[list[float]], str]:
    """Embed a batch of texts. Returns (vectors, provider_label)."""
    if not texts:
        return [], HASH_PROVIDER
    cfg = await embedding_config(db)
    if cfg is None:
        return [hash_embed(t) for t in texts], HASH_PROVIDER

    url = cfg["base_url"].rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    payload = {
        "model": cfg["embedding_model"],
        "input": texts,
        "dimensions": EMBEDDING_DIM,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    rows = sorted(data["data"], key=lambda item: item["index"])
    return [row["embedding"] for row in rows], str(cfg["embedding_model"])

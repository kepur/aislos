"""LLM + embedding access for the orchestrator.

Reads the admin-configured OpenAI-compatible settings from
public.integration_settings (category "ai") — the same config the backend
uses, so there is exactly one place to configure AI. Degrades gracefully:
`chat` returns None when unconfigured and the consult workflow falls back to
extractive answers.

`hash_embed` MUST stay identical to backend `app/services/embeddings.py` —
query vectors and chunk vectors have to live in the same space when the
hash fallback provider is active.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

HASH_PROVIDER = "hash-v1"
_TOKEN_RE = re.compile(r"[\w一-鿿]+", re.UNICODE)

AI_DEFAULTS = {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "temperature": 0.3}


async def get_ai_config(db: AsyncSession) -> dict[str, Any]:
    row = (
        await db.execute(
            text("SELECT config_json, is_enabled FROM integration_settings WHERE category = 'ai'")
        )
    ).first()
    cfg = dict(AI_DEFAULTS)
    if row and row.config_json:
        cfg.update(row.config_json)
    cfg["_enabled"] = bool(row.is_enabled) if row else False
    return cfg


def is_chat_configured(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("_enabled") and cfg.get("base_url") and cfg.get("api_key") and cfg.get("model"))


async def chat(
    cfg: dict[str, Any],
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 800,
    response_json: bool = False,
) -> dict[str, Any] | None:
    """One chat-completions call. Returns {content, tokens_in, tokens_out, model} or None."""
    if not is_chat_configured(cfg):
        return None
    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            cfg["base_url"].rstrip("/") + "/chat/completions", json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
    usage = data.get("usage") or {}
    return {
        "content": data["choices"][0]["message"]["content"],
        "tokens_in": usage.get("prompt_tokens"),
        "tokens_out": usage.get("completion_tokens"),
        "model": data.get("model") or cfg["model"],
    }


def hash_embed(text_value: str, dim: int | None = None) -> list[float]:
    """Deterministic feature-hashing vector — keep in sync with the backend."""
    dim = dim or settings.EMBEDDING_DIM
    vec = [0.0] * dim
    for token in _TOKEN_RE.findall(text_value.lower()):
        digest = hashlib.md5(token.encode()).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[index] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


async def embed_query(cfg: dict[str, Any], query: str) -> list[float]:
    if cfg.get("_enabled") and cfg.get("base_url") and cfg.get("api_key") and cfg.get("embedding_model"):
        headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
        payload = {
            "model": cfg["embedding_model"],
            "input": [query],
            "dimensions": settings.EMBEDDING_DIM,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                cfg["base_url"].rstrip("/") + "/embeddings", json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
    return hash_embed(query)

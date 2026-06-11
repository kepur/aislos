"""AI service for KYC document analysis, fraud detection, and content moderation.

Reads configuration from platform_settings (ai_provider, ai_api_key, ai_model, etc.)
Supports OpenAI, Anthropic, and OpenAI-compatible (Azure, local) providers.
Gracefully degrades if AI is not configured or disabled.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_setting import PlatformSetting

logger = logging.getLogger(__name__)


KYC_ANALYSIS_PROMPT = """You are a KYC compliance assistant. Analyze the provided document and respond ONLY with valid JSON matching this schema:

{
  "doc_type_detected": "BUSINESS_PERMIT|DTI|SEC|BIR|ID|PASSPORT|UTILITY_BILL|OTHER",
  "extracted_fields": {
    "business_name": "string or null",
    "registration_number": "string or null",
    "issued_date": "YYYY-MM-DD or null",
    "expiry_date": "YYYY-MM-DD or null",
    "issuer": "string or null",
    "address": "string or null",
    "owner_name": "string or null"
  },
  "authenticity": "AUTHENTIC|SUSPICIOUS|FAKE",
  "confidence": 0.0-1.0,
  "concerns": ["list of specific issues found"],
  "summary": "1-sentence assessment"
}

Be strict. If the document looks tampered, blurry, or expired, mark as SUSPICIOUS or FAKE. Do not invent fields you cannot read."""


async def get_ai_config(db: AsyncSession) -> dict[str, Any]:
    """Load AI configuration from platform_settings.

    Admin platform_settings is the product source of truth. Env vars are only
    accepted as local development fallback when settings are empty.
    """
    from app.core.config import settings as app_settings

    keys = [
        "ai_enabled",
        "ai_provider",  # openai | openai_compatible | deepseek | anthropic | azure
        "ai_api_key",
        "ai_model",
        "ai_base_url",
        "ai_kyc_enabled",
        "ai_fraud_enabled",
        "ai_moderation_enabled",
        "ai_confidence_threshold",
    ]
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key.in_(keys)))
    settings = {s.key: s.value for s in result.scalars().all()}

    # Resolve API key with env fallback
    api_key = settings.get("ai_api_key", "")
    if not api_key or api_key.startswith("sk-test"):
        api_key = app_settings.OPENAI_API_KEY or ""

    provider = settings.get("ai_provider") or app_settings.AI_PROVIDER or "openai"
    base_url = (settings.get("ai_base_url", "") or "").strip()
    if "api.deepseek.com" in base_url:
        provider = "deepseek"
    elif provider == "deepseek" and not base_url:
        base_url = "https://api.deepseek.com"
    base_url = base_url.rstrip("/")

    model = settings.get("ai_model") or app_settings.AI_MODEL or "gpt-4o-mini"
    if provider == "deepseek" and (not model or model == "gpt-4o-mini"):
        model = "deepseek-v4-pro"

    return {
        "enabled": settings.get("ai_enabled") == "true",
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "kyc_enabled": settings.get("ai_kyc_enabled") == "true",
        "fraud_enabled": settings.get("ai_fraud_enabled") == "true",
        "moderation_enabled": settings.get("ai_moderation_enabled") == "true",
        "confidence_threshold": float(settings.get("ai_confidence_threshold") or 0.7),
    }


async def test_ai_connection(db: AsyncSession) -> dict[str, Any]:
    """Test the configured AI connection by sending a minimal prompt."""
    cfg = await get_ai_config(db)
    if not cfg["enabled"]:
        return {"ok": False, "error": "AI not enabled"}
    if not cfg["api_key"]:
        return {"ok": False, "error": "API key not configured"}

    try:
        result = await _call_ai(cfg, [{"role": "user", "content": "Reply with only: OK"}], max_tokens=10)
        return {"ok": True, "model": cfg["model"], "response": (result or "").strip()[:50]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


async def analyze_kyc_document(
    db: AsyncSession,
    image_url: str | None = None,
    document_text: str | None = None,
    doc_type_hint: str | None = None,
) -> dict[str, Any]:
    """Analyze a KYC document for authenticity and extract structured fields."""
    cfg = await get_ai_config(db)
    if not cfg["enabled"] or not cfg["kyc_enabled"]:
        return {"ok": False, "error": "AI KYC analysis is disabled"}
    if not cfg["api_key"]:
        return {"ok": False, "error": "AI API key not configured"}

    user_content: Any
    if image_url:
        # Vision-style request
        user_content = [
            {"type": "text", "text": f"Document type hint: {doc_type_hint or 'unknown'}\n\n{KYC_ANALYSIS_PROMPT}"},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    elif document_text:
        user_content = f"{KYC_ANALYSIS_PROMPT}\n\nDocument text (OCR):\n{document_text[:8000]}"
    else:
        return {"ok": False, "error": "Must provide image_url or document_text"}

    try:
        raw = await _call_ai(
            cfg,
            [{"role": "user", "content": user_content}],
            max_tokens=800,
            json_mode=True,
        )
        parsed = _extract_json(raw)
        if not parsed:
            return {"ok": False, "error": "AI returned non-JSON output", "raw": raw[:300]}
        passes_threshold = parsed.get("confidence", 0) >= cfg["confidence_threshold"]
        return {
            "ok": True,
            "analysis": parsed,
            "meets_threshold": passes_threshold,
            "threshold": cfg["confidence_threshold"],
            "model": cfg["model"],
        }
    except Exception as e:
        logger.exception("AI KYC analysis failed")
        return {"ok": False, "error": str(e)[:200]}


async def moderate_content(db: AsyncSession, text: str) -> dict[str, Any]:
    """Check if content violates platform policy."""
    cfg = await get_ai_config(db)
    if not cfg["enabled"] or not cfg["moderation_enabled"] or not cfg["api_key"]:
        return {"ok": False, "skipped": True}
    prompt = (
        "You are a content moderator. Respond ONLY with valid JSON: "
        '{"flagged": true|false, "categories": [...], "severity": "LOW|MEDIUM|HIGH", "reason": "..."}\n\n'
        "Flag content that contains: spam, scams, off-platform deal attempts, illegal goods, "
        "personal contact info shared too early, abusive language.\n\n"
        f"Content:\n{text[:4000]}"
    )
    try:
        raw = await _call_ai(cfg, [{"role": "user", "content": prompt}], max_tokens=300, json_mode=True)
        parsed = _extract_json(raw)
        return {"ok": True, "result": parsed or {"flagged": False}}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ---------- Provider implementations ----------

async def _call_ai(
    cfg: dict[str, Any],
    messages: list[dict],
    max_tokens: int = 500,
    json_mode: bool = False,
) -> str:
    """Dispatch to the configured provider."""
    provider = (cfg.get("provider") or "openai").lower()
    if provider == "anthropic":
        return await _call_anthropic(cfg, messages, max_tokens)
    return await _call_openai_compatible(cfg, messages, max_tokens, json_mode)


async def _call_openai_compatible(cfg, messages, max_tokens, json_mode):
    import httpx

    provider = (cfg.get("provider") or "").lower()
    base_url = (cfg.get("base_url") or "").strip()
    if provider == "deepseek" and not base_url:
        base_url = "https://api.deepseek.com"
    elif not base_url:
        base_url = "https://api.openai.com/v1"
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
        )
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = (r.text or "").strip()
            if len(detail) > 600:
                detail = f"{detail[:600]}..."
            raise RuntimeError(f"AI provider request failed ({r.status_code}): {detail}") from exc
        data = r.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(cfg, messages, max_tokens):
    import httpx

    base_url = cfg.get("base_url") or "https://api.anthropic.com/v1"
    url = f"{base_url.rstrip('/')}/messages"
    payload = {
        "model": cfg["model"],
        "max_tokens": max_tokens,
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            url,
            json=payload,
            headers={
                "x-api-key": cfg["api_key"],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        data = r.json()
        # Anthropic returns content as list of blocks
        blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from raw model output."""
    if not text:
        return None
    # Try direct
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try fenced code block
    import re
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try first {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None

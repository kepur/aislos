"""LLM text translator — reuses the platform's configured LLM (``ai_agent``).

Degrades gracefully: if the LLM is not configured or the response can't be
parsed, it returns the input texts unchanged so the pipeline still completes
(the listing is simply left in the source language). Swap in a dedicated MT
provider later by adding another TextTranslator adapter.
"""
from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import ai_agent

from ..contracts import TranslateRequest, TranslateResult


class LLMTextTranslator:
    key = "llm"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def translate(self, req: TranslateRequest) -> TranslateResult:
        if not req.texts:
            return TranslateResult(texts=[], provider_ref=self.key)

        if not await ai_agent.is_configured(self.db):
            # No LLM configured — pass through unchanged.
            return TranslateResult(texts=list(req.texts), provider_ref="passthrough")

        glossary = ""
        if req.glossary:
            pairs = "; ".join(f"{k} -> {v}" for k, v in req.glossary.items())
            glossary = f"\nKeep these terms fixed: {pairs}."
        context = f"\nContext: {req.context}." if req.context else ""
        payload = {"items": list(req.texts)}
        system = (
            "You are a professional e-commerce localisation engine. Translate each "
            f"string in the input JSON 'items' array into {req.target_lang}. Preserve "
            "meaning, marketing tone and any measurements/specs. Return ONLY a JSON "
            "object of the form {\"items\": [...]} with the same number of items in "
            f"the same order.{glossary}{context}"
        )
        try:
            raw = await ai_agent.chat(
                self.db,
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.2,
                max_tokens=1500,
                response_json=True,
            )
            data = json.loads(raw) if raw else {}
            out = data.get("items")
            if isinstance(out, list) and len(out) == len(req.texts):
                return TranslateResult(
                    texts=[str(x) for x in out],
                    detected_source_lang=req.source_lang,
                    provider_ref=self.key,
                )
        except Exception:
            pass
        # Any failure -> safe passthrough.
        return TranslateResult(texts=list(req.texts), provider_ref="passthrough")

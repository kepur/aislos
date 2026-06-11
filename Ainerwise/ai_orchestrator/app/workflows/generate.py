"""Generation workflows: marketing content + quote drafts.

The backend gathers all business context (products, prices, region profile)
and calls /agent/generate; this module only does the language work. Without a
configured LLM it falls back to deterministic templates so the pipeline stays
testable. Every run is logged to ai.agent_runs; drafts are persisted by the
backend into ai_reviews/marketing_assets — nothing publishes from here.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import chat, get_ai_config, is_chat_configured

CONTENT_SYSTEM = """You are the marketing writer for AinerWise, a European AI \
general contractor platform for smart building, KNX, solar, security and EV \
charging. Write in the requested language. Ground every claim in the provided \
context; never invent prices or certifications. Respect the regional messaging \
profile (tone, selling points). Output strict JSON:
{"items": [{"channel": "...", "lang": "...", "title": "...", "content": "..."}]}"""

QUOTE_SYSTEM = """You are the solution consultant for AinerWise. From the lead \
context, matched solution and product/price lines, draft a customer-friendly \
quotation summary in the requested language. Never invent prices — use only \
the provided lines. Mark everything as preliminary. Output strict JSON:
{"intro": "...", "scope_summary": "...", "line_comments": {"<product>": "..."},
 "next_steps": "...", "validity_note": "..."}"""


def _fallback_content(context: dict, channels: list[str], langs: list[str]) -> list[dict]:
    name = context.get("title") or context.get("product_name") or "our smart building solutions"
    summary = (context.get("summary") or context.get("description") or "")[:400]
    items = []
    for lang in langs:
        for channel in channels:
            items.append(
                {
                    "channel": channel,
                    "lang": lang,
                    "title": f"{name}",
                    "content": (
                        f"{name} — {summary}\n\n"
                        "Contact AinerWise for a tailored solution with certified local installation. "
                        "[template draft — configure the LLM in Admin → Integrations for generated copy]"
                    ),
                }
            )
    return items


def _fallback_quote(context: dict) -> dict:
    lines = context.get("lines", [])
    return {
        "intro": f"Thank you for your interest. Based on your {context.get('project_type') or 'project'} "
                 "we prepared a preliminary proposal.",
        "scope_summary": "; ".join(line.get("name", "") for line in lines)[:500],
        "line_comments": {},
        "next_steps": "Our specialist will confirm the scope and schedule a site survey.",
        "validity_note": "Preliminary draft — prices subject to specialist review.",
    }


async def run_generate(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    workflow = payload.get("workflow")
    agent_slug = payload.get("agent_slug")
    context = payload.get("context") or {}
    langs = payload.get("langs") or ["en"]
    channels = payload.get("channels") or ["blog"]

    cfg = await get_ai_config(db)
    model_used = None
    tokens_in = tokens_out = None
    error = None

    if workflow == "content_gen":
        result_data: dict[str, Any] = {"items": _fallback_content(context, channels, langs)}
        if is_chat_configured(cfg):
            prompt = (
                f"Context:\n{json.dumps(context, ensure_ascii=False)[:4000]}\n\n"
                f"Regional profile:\n{json.dumps(payload.get('region_profile') or {}, ensure_ascii=False)[:1000]}\n\n"
                f"Generate one item per channel x language. Channels: {channels}. Languages: {langs}."
            )
            try:
                llm = await chat(cfg, [{"role": "system", "content": CONTENT_SYSTEM},
                                       {"role": "user", "content": prompt}],
                                 max_tokens=2000, response_json=True)
                if llm:
                    parsed = json.loads(llm["content"])
                    if isinstance(parsed.get("items"), list) and parsed["items"]:
                        result_data = {"items": parsed["items"]}
                    model_used, tokens_in, tokens_out = llm["model"], llm["tokens_in"], llm["tokens_out"]
            except Exception as exc:  # noqa: BLE001 — fallback already in place
                error = str(exc)[:300]
    elif workflow == "procurement_analyze":
        from app.workflows.procurement_analyze import run_procurement_analyze

        return await run_procurement_analyze(db, payload)
    elif workflow == "quote_draft":
        result_data = _fallback_quote(context)
        if is_chat_configured(cfg):
            prompt = (
                f"Lead and pricing context:\n{json.dumps(context, ensure_ascii=False)[:5000]}\n\n"
                f"Language: {payload.get('lang') or 'en'}."
            )
            try:
                llm = await chat(cfg, [{"role": "system", "content": QUOTE_SYSTEM},
                                       {"role": "user", "content": prompt}],
                                 max_tokens=1500, response_json=True)
                if llm:
                    result_data = json.loads(llm["content"])
                    model_used, tokens_in, tokens_out = llm["model"], llm["tokens_in"], llm["tokens_out"]
            except Exception as exc:  # noqa: BLE001
                error = str(exc)[:300]
    else:
        raise ValueError(f"Unknown generate workflow: {workflow}")

    latency_ms = int((time.monotonic() - started) * 1000)
    await db.execute(
        text(
            "INSERT INTO ai.agent_runs (id, agent_slug, workflow, model_name, tokens_in, tokens_out, "
            "latency_ms, status, input_json, output_json, error_message) "
            "VALUES (:id, :agent_slug, :workflow, :model, :tin, :tout, :latency, :status, "
            "CAST(:input AS jsonb), CAST(:output AS jsonb), :error)"
        ),
        {
            "id": uuid.uuid4(), "agent_slug": agent_slug, "workflow": workflow, "model": model_used,
            "tin": tokens_in, "tout": tokens_out, "latency": latency_ms,
            "status": "failed" if error else "completed",
            "input": json.dumps({k: v for k, v in payload.items() if k != "context"}),
            "output": json.dumps(result_data)[:20000],
            "error": error,
        },
    )
    await db.commit()
    return {"workflow": workflow, "llm_used": model_used is not None, "data": result_data}

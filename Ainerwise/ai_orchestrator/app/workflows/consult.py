"""Consult workflow: retrieve -> match products -> generate -> capture lead.

Linear graph, explicit steps (same in-process graph style as the backend's
ai_graph.py). All writes go to the ai schema; business writes (leads) go
through the backend internal API — the orchestrator DB role cannot write
public tables even if this code tried.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm import chat, embed_query, get_ai_config, is_chat_configured
from app.prompts.consult import DISCLAIMER, SYSTEM_PROMPT, build_user_prompt
from app.retrieval import find_similar_cases, match_products, search_chunks

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


async def _load_or_create_conversation(
    db: AsyncSession, conversation_id: str | None, visitor_id: str | None, channel: str, lang: str | None
) -> uuid.UUID:
    if conversation_id:
        row = (
            await db.execute(
                text("SELECT id FROM ai.conversations WHERE id = :id"), {"id": conversation_id}
            )
        ).first()
        if row:
            return row.id
    new_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO ai.conversations (id, channel, visitor_id, status, lang) "
            "VALUES (:id, :channel, :visitor_id, 'active', :lang)"
        ),
        {"id": new_id, "channel": channel, "visitor_id": visitor_id, "lang": lang},
    )
    return new_id


async def _save_message(db: AsyncSession, conversation_id: uuid.UUID, role: str, content: str, tokens: int | None = None) -> None:
    await db.execute(
        text(
            "INSERT INTO ai.messages (id, conversation_id, role, content, tokens) "
            "VALUES (:id, :cid, :role, :content, :tokens)"
        ),
        {"id": uuid.uuid4(), "cid": conversation_id, "role": role, "content": content, "tokens": tokens},
    )


async def _load_memories(db: AsyncSession, conversation_id: uuid.UUID) -> list[str]:
    """Active memories for the lead linked to this conversation (if any)."""
    rows = (
        await db.execute(
            text(
                "SELECT m.content FROM ai.memories m "
                "JOIN ai.conversations c ON c.lead_id = m.subject_id "
                "WHERE c.id = :cid AND m.subject_type = 'lead' AND m.status = 'active' "
                "AND (m.expires_at IS NULL OR m.expires_at > now()) "
                "ORDER BY m.created_at DESC LIMIT 10"
            ),
            {"cid": conversation_id},
        )
    ).all()
    return [row.content for row in rows]


MEMORY_EXTRACT_PROMPT = """From this conversation turn, extract up to 3 durable \
facts about the customer worth remembering for future conversations (preferences, \
budget, plans, constraints). Skip small talk. Output strict JSON: \
{"memories": [{"kind": "preference|fact|constraint|plan", "content": "...", "confidence": 0.0-1.0}]}"""


async def _extract_memories(
    db: AsyncSession, cfg: dict, conversation_id: uuid.UUID, user_message: str, answer: str
) -> None:
    """Best-effort, LLM-only; anonymous conversations (no lead) are skipped."""
    row = (
        await db.execute(
            text("SELECT lead_id FROM ai.conversations WHERE id = :cid"), {"cid": conversation_id}
        )
    ).first()
    if not row or row.lead_id is None:
        return
    try:
        result = await chat(
            cfg,
            [{"role": "system", "content": MEMORY_EXTRACT_PROMPT},
             {"role": "user", "content": f"User: {user_message}\nAssistant: {answer}"}],
            max_tokens=400, response_json=True,
        )
        if not result:
            return
        memories = json.loads(result["content"]).get("memories") or []
        for memory in memories[:3]:
            content = str(memory.get("content") or "").strip()
            if not content:
                continue
            await db.execute(
                text(
                    "INSERT INTO ai.memories (id, subject_type, subject_id, kind, content, "
                    "source_conversation_id, confidence, status) "
                    "VALUES (:id, 'lead', :subject_id, :kind, :content, :cid, :confidence, 'active')"
                ),
                {
                    "id": uuid.uuid4(), "subject_id": row.lead_id,
                    "kind": memory.get("kind") or "fact", "content": content[:1000],
                    "cid": conversation_id,
                    "confidence": min(max(float(memory.get("confidence") or 0.7), 0), 1),
                },
            )
    except Exception:  # noqa: BLE001 — memory extraction must never break the chat
        return


async def _history(db: AsyncSession, conversation_id: uuid.UUID) -> list[dict[str, str]]:
    rows = (
        await db.execute(
            text(
                "SELECT role, content FROM ai.messages WHERE conversation_id = :cid "
                "ORDER BY created_at DESC LIMIT :n"
            ),
            {"cid": conversation_id, "n": settings.HISTORY_MAX_MESSAGES},
        )
    ).all()
    return [{"role": row.role, "content": row.content or ""} for row in reversed(rows)]


def _fallback_answer(message: str, chunks: list[dict], products: list[dict]) -> tuple[str, dict | None]:
    """No LLM configured: extractive answer + regex lead capture."""
    parts: list[str] = []
    if chunks:
        parts.append("Here is what our knowledge base says:")
        for chunk in chunks[:2]:
            snippet = chunk["content"][:400].strip()
            parts.append(f"• {snippet} (source: {chunk['title']})")
    if products:
        names = ", ".join(p["name"] for p in products)
        parts.append(f"Possibly relevant products: {names}.")
    if not parts:
        parts.append(
            "I could not find this in our knowledge base yet. Please leave your "
            "contact details or use the requirement form, and our team will follow up."
        )
    email = EMAIL_RE.search(message)
    phone = PHONE_RE.search(message)
    lead = None
    if email or phone:
        lead = {
            "contact_email": email.group(0) if email else None,
            "contact_phone": phone.group(0) if phone else None,
            "description": message[:500],
        }
    return "\n\n".join(parts), lead


def _parse_llm_json(content: str) -> tuple[str, dict | None]:
    try:
        data = json.loads(content)
        answer = str(data.get("answer") or "").strip()
        lead = data.get("lead") if isinstance(data.get("lead"), dict) else None
        if answer:
            return answer, lead
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return content.strip(), None


async def _create_lead(
    db: AsyncSession, conversation_id: uuid.UUID, lead: dict, lang: str | None, history: list[dict]
) -> bool:
    if not (lead.get("contact_email") or lead.get("contact_phone")):
        return False
    payload = {
        "contact_name": lead.get("contact_name"),
        "contact_email": lead.get("contact_email"),
        "contact_phone": lead.get("contact_phone"),
        "project_type": lead.get("project_type"),
        "country": lead.get("country"),
        "city": lead.get("city"),
        "budget_range": lead.get("budget_range"),
        "description": lead.get("description"),
        "language": lang or "en",
        "conversation_id": str(conversation_id),
        "transcript": history[-6:],
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                settings.BACKEND_INTERNAL_URL.rstrip("/") + "/internal/v1/leads",
                json=payload,
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            lead_id = response.json().get("lead_id")
    except Exception:  # noqa: BLE001 — lead loss is logged on the run, chat continues
        return False
    await db.execute(
        text("UPDATE ai.conversations SET lead_id = :lead_id WHERE id = :cid"),
        {"lead_id": lead_id, "cid": conversation_id},
    )
    return True


async def _log_run(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    *,
    status: str,
    model: str | None,
    tokens_in: int | None,
    tokens_out: int | None,
    latency_ms: int,
    output: dict | None = None,
    error: str | None = None,
    agent_slug: str = "sales-agent",
) -> None:
    await db.execute(
        text(
            "INSERT INTO ai.agent_runs (id, conversation_id, agent_slug, workflow, model_name, "
            "tokens_in, tokens_out, latency_ms, status, output_json, error_message) "
            "VALUES (:id, :cid, :agent_slug, 'consult', :model, :tin, :tout, :latency, :status, "
            "CAST(:output AS jsonb), :error)"
        ),
        {
            "id": uuid.uuid4(),
            "cid": conversation_id,
            "agent_slug": agent_slug,
            "model": model,
            "tin": tokens_in,
            "tout": tokens_out,
            "latency": latency_ms,
            "status": status,
            "output": json.dumps(output) if output is not None else None,
            "error": error,
        },
    )


# AI Act Art.50 — prepended server-side for showroom personas; persona config
# cannot remove or override it.
AI_DISCLOSURE_LINE = (
    "You MUST open your first reply by clearly stating you are an AI assistant. "
    "Never claim to be human."
)


async def _load_persona(db: AsyncSession, agent_slug: str | None) -> tuple[str, str | None]:
    """Resolve the acting agent. Returns (effective_slug, persona_block).
    Unknown/paused slugs fall back to the default sales-agent identity."""
    if not agent_slug:
        return "sales-agent", None
    row = (
        await db.execute(
            text(
                "SELECT slug, name, role_title, config_json FROM agents "
                "WHERE slug = :slug AND status = 'active'"
            ),
            {"slug": agent_slug},
        )
    ).first()
    if row is None:
        return "sales-agent", None
    config = row.config_json or {}
    lines = [
        f"You are '{row.name}' ({row.role_title or 'consultant'}), an in-store AI persona.",
        AI_DISCLOSURE_LINE,
    ]
    if config.get("voice"):
        lines.append(f"Personality/tone: {config['voice']}.")
    if config.get("brand_voice"):
        lines.append(f"Brand voice: {config['brand_voice']}.")
    if config.get("audience"):
        lines.append(f"Primary audience: {config['audience']}.")
    if config.get("forbidden"):
        lines.append(f"Never do: {config['forbidden']}.")
    return row.slug, "\n".join(lines)


async def run_consult(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    message: str = payload["message"]
    lang = payload.get("lang")
    acting_slug, persona_block = await _load_persona(db, payload.get("agent_slug"))

    conversation_id = await _load_or_create_conversation(
        db, payload.get("conversation_id"), payload.get("visitor_id"), payload.get("channel") or "web", lang
    )
    await _save_message(db, conversation_id, "user", message)

    cfg = await get_ai_config(db)
    query_vector = await embed_query(cfg, message)
    chunks = await search_chunks(db, message, query_vector)
    products = await match_products(db, message)
    similar_cases = await find_similar_cases(db, query_vector)

    model_used = None
    tokens_in = tokens_out = None
    error = None
    lead_created = False

    if is_chat_configured(cfg):
        history = await _history(db, conversation_id)
        system_prompt = SYSTEM_PROMPT
        if persona_block:
            system_prompt = persona_block + "\n\n" + system_prompt
        memories = await _load_memories(db, conversation_id)
        if memories:
            system_prompt += "\n\nKnown about this customer (use naturally, do not recite):\n- " + "\n- ".join(memories)
        if similar_cases:
            case_lines = "\n".join(
                f"- {c['title']} ({c['property_type']}, {c['area_sqm']}sqm, "
                f"{c['budget']} {c['currency']}, {c['duration_days']} days, similarity {c['similarity']:.0%})"
                for c in similar_cases
            )
            system_prompt += (
                "\n\nSimilar delivered projects (cite them to build trust, budgets are indicative):\n"
                + case_lines
            )
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[:-1])
        messages.append({"role": "user", "content": build_user_prompt(message, chunks, products)})
        try:
            result = await chat(cfg, messages, response_json=True)
        except Exception as exc:  # noqa: BLE001 — LLM failure degrades to fallback
            result = None
            error = str(exc)[:300]
        if result:
            answer, lead = _parse_llm_json(result["content"])
            model_used = result["model"]
            tokens_in, tokens_out = result["tokens_in"], result["tokens_out"]
        else:
            answer, lead = _fallback_answer(message, chunks, products)
    else:
        answer, lead = _fallback_answer(message, chunks, products)

    if lead:
        history = await _history(db, conversation_id)
        lead_created = await _create_lead(db, conversation_id, lead, lang, history)

    await _save_message(db, conversation_id, "assistant", answer, tokens=tokens_out)
    if model_used:
        await _extract_memories(db, cfg, conversation_id, message, answer)

    latency_ms = int((time.monotonic() - started) * 1000)
    sources = [
        {"title": c["title"], "source_type": c["source_type"], "score": round(c["score"], 4)}
        for c in chunks
    ]
    await _log_run(
        db,
        conversation_id,
        status="failed" if error else "completed",
        model=model_used,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        output={"sources": sources, "lead_created": lead_created},
        error=error,
        agent_slug=acting_slug,
    )
    await db.commit()

    return {
        "configured": True,
        "conversation_id": str(conversation_id),
        "agent_slug": acting_slug,
        "answer": answer,
        "sources": sources,
        "products": products,
        "similar_cases": similar_cases,
        "lead_created": lead_created,
        "disclaimer": DISCLAIMER,
    }

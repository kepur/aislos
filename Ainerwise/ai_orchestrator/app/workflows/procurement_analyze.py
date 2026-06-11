"""Procurement project analysis — structured facts, BOQ draft and confidence."""
from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import chat, get_ai_config, is_chat_configured

PROCUREMENT_SYSTEM = """You are the procurement analyst for AISLOS smart building projects.
Given project context and fact definitions, output STRICT JSON with keys:
project_summary, extracted_facts (list of {key, value, source, confidence, assumption}),
missing_questions (list of {key, importance, reason}),
boq_items (list with category, name, qty, unit, quantity_basis, confidence, assumptions,
  critical, weight, included, options: [{tier, capability, unit_price_min, unit_price_max, currency}]),
risks, exclusions.
tiers must be budget, standard, premium for each included item. confidence 0-1."""


def _tier_options(base: int) -> list[dict]:
    return [
        {
            "tier": "budget",
            "capability": "Entry package",
            "unit_price_min": base,
            "unit_price_max": base + 50,
            "currency": "USD",
        },
        {
            "tier": "standard",
            "capability": "Standard package",
            "unit_price_min": base + 100,
            "unit_price_max": base + 150,
            "currency": "USD",
        },
        {
            "tier": "premium",
            "capability": "Premium package",
            "unit_price_min": base + 200,
            "unit_price_max": base + 300,
            "currency": "USD",
        },
    ]


def _scenario_confidence(scenario: str | None) -> Decimal:
    mapping = {
        "low": Decimal("0.550"),
        "edge_600": Decimal("0.600"),
        "edge_800": Decimal("0.800"),
        "edge_801": Decimal("0.801"),
        "high": Decimal("0.850"),
    }
    return mapping.get(scenario or "high", Decimal("0.850"))


def _fallback_analyze(context: dict) -> dict:
    scenario = context.get("test_scenario")
    conf = float(_scenario_confidence(scenario))
    project_type = context.get("project_type") or "villa_smart_home"
    title = context.get("title") or "Smart project"

    fact_keys = (
        ["property_area_sqm", "room_count", "target_budget", "installation_timeline"]
        if project_type == "villa_smart_home"
        else ["room_count", "property_area_sqm", "star_rating", "target_budget"]
    )

    extracted = [
        {
            "key": key,
            "value": context.get("facts", {}).get(key, "TBD"),
            "source": "ai",
            "confidence": conf if scenario != "low" else 0.4,
            "assumption": None,
        }
        for key in fact_keys
    ]
    missing = []
    if scenario == "low" or conf < 0.6:
        missing = [
            {
                "key": "target_budget",
                "importance": "critical",
                "reason": "Budget required for accurate BOQ",
            }
        ]

    boq_items = [
        {
            "category": "lighting",
            "name": "Smart lighting",
            "qty": "2",
            "unit": "lot",
            "quantity_basis": "2 floors",
            "confidence": conf,
            "assumptions": "Based on typical villa layout",
            "critical": False,
            "weight": "1",
            "included": True,
            "options": _tier_options(100),
        }
    ]

    return {
        "project_summary": f"Preliminary analysis for {title} ({project_type}).",
        "extracted_facts": extracted,
        "missing_questions": missing,
        "boq_items": boq_items if conf >= 0.6 else [],
        "risks": ["Site survey not yet completed"],
        "exclusions": ["Civil works", "Permits"],
    }


def validate_analyze_output(data: dict) -> list[str]:
    problems: list[str] = []
    for key in (
        "project_summary",
        "extracted_facts",
        "missing_questions",
        "boq_items",
        "risks",
        "exclusions",
    ):
        if key not in data:
            problems.append(f"missing key: {key}")
    if not isinstance(data.get("extracted_facts"), list):
        problems.append("extracted_facts must be a list")
    if not isinstance(data.get("boq_items"), list):
        problems.append("boq_items must be a list")
    for item in data.get("boq_items") or []:
        if not item.get("quantity_basis"):
            problems.append(f"boq item missing quantity_basis: {item.get('name')}")
        opts = item.get("options") or []
        tiers = {o.get("tier") for o in opts}
        if item.get("included", True) and tiers != {"budget", "standard", "premium"}:
            problems.append(f"included item missing tier options: {item.get('name')}")
    return problems


async def run_procurement_analyze(db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    context = payload.get("context") or {}
    agent_slug = payload.get("agent_slug") or "procurement-agent"
    workflow = "procurement_analyze"

    cfg = await get_ai_config(db)
    result_data = _fallback_analyze(context)
    model_used = None
    tokens_in = tokens_out = None
    error = None

    if is_chat_configured(cfg):
        prompt = f"Analyze this procurement project:\n{json.dumps(context, ensure_ascii=False)[:6000]}"
        try:
            llm = await chat(
                cfg,
                [
                    {"role": "system", "content": PROCUREMENT_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
                response_json=True,
            )
            if llm:
                parsed = json.loads(llm["content"])
                problems = validate_analyze_output(parsed)
                if problems:
                    error = "; ".join(problems)
                else:
                    result_data = parsed
                model_used, tokens_in, tokens_out = llm["model"], llm["tokens_in"], llm["tokens_out"]
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:300]

    latency_ms = int((time.monotonic() - started) * 1000)
    status = "failed" if error else "completed"
    await db.execute(
        text(
            "INSERT INTO ai.agent_runs (id, agent_slug, workflow, model_name, tokens_in, tokens_out, "
            "latency_ms, status, input_json, output_json, error_message) "
            "VALUES (:id, :agent_slug, :workflow, :model, :tin, :tout, :latency, :status, "
            "CAST(:input AS jsonb), CAST(:output AS jsonb), :error)"
        ),
        {
            "id": uuid.uuid4(),
            "agent_slug": agent_slug,
            "workflow": workflow,
            "model": model_used,
            "tin": tokens_in,
            "tout": tokens_out,
            "latency": latency_ms,
            "status": status,
            "input": json.dumps({k: v for k, v in payload.items() if k != "context"}),
            "output": json.dumps(result_data)[:20000],
            "error": error,
        },
    )
    await db.commit()
    if error:
        return {"workflow": workflow, "status": "failed", "error": error, "data": None}
    return {"workflow": workflow, "status": "completed", "llm_used": model_used is not None, "data": result_data}

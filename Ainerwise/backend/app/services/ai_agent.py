"""OpenAI-compatible AI agent for the conversational facility assessment.

Calls a configured chat-completions endpoint (OpenAI / Azure / local LLM / any
OpenAI-protocol gateway). Always degrades gracefully: if the AI is not
configured, `run_assistant` returns {configured: False} and the frontend keeps
its scripted question flow. All AI output is tagged preliminary.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integrations import get_config

PRELIMINARY = "Preliminary AI assistant output — admin review required before any quotation."

# What the assistant must collect per facility category (drives extraction).
CATEGORY_FIELDS = {
    "storage": ["storage_type", "temperature_humidity", "compliance_use", "monitoring_points", "alert_channels", "calibration_cycle"],
    "kitchen": ["kitchen_count", "gas_type", "alarm_contacts", "service_term"],
    "water": ["water_system", "parameters", "reporting", "service_term"],
    "energy": ["assets", "loads", "goals", "service_term"],
    "factory": ["production_machines", "industrial_protocols", "energy_solar", "safety_requirements"],
    "asset": ["asset_count", "goals", "monitoring_points"],
}
COMMON_FIELDS = ["location", "budget_and_service", "contact"]


async def is_configured(db: AsyncSession) -> bool:
    cfg = await get_config(db, "ai")
    return bool(cfg.get("_enabled") and cfg.get("base_url") and cfg.get("api_key") and cfg.get("model"))


async def chat(db: AsyncSession, messages: list[dict[str, str]], *, temperature: float | None = None, max_tokens: int = 700, response_json: bool = False) -> str | None:
    cfg = await get_config(db, "ai")
    if not (cfg.get("base_url") and cfg.get("api_key") and cfg.get("model")):
        return None
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3) if temperature is None else temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001
        return None


def _system_prompt(category: str, custom: str | None) -> str:
    fields = COMMON_FIELDS + CATEGORY_FIELDS.get(category, [])
    base = (
        "You are AinerWise's AI Facility Assessment assistant. AinerWise is an AI Facility "
        "Intelligence platform (smart buildings, cold chain, kitchen safety, water compliance, "
        "energy, assets, industrial). You collect a B2B customer's requirement through a short, "
        "friendly conversation, asking ONE concise question at a time about the missing item.\n"
        f"Facility type: {category}. Fields to collect: {', '.join(fields)}.\n"
        "Rules: never expose supplier cost, internal model, or commodity device prices. Speak about "
        "monitored outcomes and service packages. Tag everything as a preliminary estimate requiring "
        "admin review and a site survey.\n"
        'Respond ONLY as compact JSON: {"reply": "<next question or summary>", '
        '"extracted": {<field>: <value>, ...}, "complete": <true|false>}. '
        "Set complete=true once the key fields are collected; then reply with a short summary."
    )
    return base + (f"\nExtra guidance: {custom}" if custom else "")


async def run_assistant(db: AsyncSession, *, category: str, messages: list[dict[str, str]], collected: dict[str, Any] | None = None) -> dict[str, Any]:
    """Drive one assistant turn. Returns {configured, reply, extracted, complete}."""
    cfg = await get_config(db, "ai")
    if not await is_configured(db):
        return {"configured": False, "disclaimer": PRELIMINARY}

    sys = _system_prompt(category, cfg.get("system_prompt"))
    convo = [{"role": "system", "content": sys}]
    if collected:
        convo.append({"role": "system", "content": "Already collected: " + json.dumps(collected, ensure_ascii=False)})
    convo.extend(messages[-20:])

    raw = await chat(db, convo, response_json=True)
    if raw is None:
        return {"configured": True, "error": "ai_call_failed", "disclaimer": PRELIMINARY}
    try:
        parsed = json.loads(raw)
    except Exception:  # noqa: BLE001
        parsed = {"reply": raw, "extracted": {}, "complete": False}
    return {
        "configured": True,
        "reply": parsed.get("reply", ""),
        "extracted": parsed.get("extracted", {}) or {},
        "complete": bool(parsed.get("complete")),
        "disclaimer": PRELIMINARY,
    }

"""Procurement AI analyze — orchestrator call, validation, BOQ draft and gate."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import AgentRun, AIReview
from app.models.procurement import ProcurementProject, ProcurementProjectFact
from app.models.user import User
from app.services.procurement_boq import create_draft_boq
from app.services.procurement_confidence import (
    classify_project_status,
    compute_boq_score,
    compute_facts_score,
    compute_overall_confidence,
)

WORKFLOW = "procurement_analyze"
AGENT_SLUG = "procurement-agent"


class ProcurementAIError(ValueError):
    pass


def validate_analyze_payload(data: dict) -> list[str]:
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
        if item.get("included", True):
            tiers = {o.get("tier") for o in (item.get("options") or [])}
            if tiers != {"budget", "standard", "premium"}:
                problems.append(f"included item missing tier options: {item.get('name')}")
    return problems


async def _call_orchestrator(context: dict) -> dict:
    payload = {
        "workflow": WORKFLOW,
        "agent_slug": AGENT_SLUG,
        "context": context,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/generate",
            json=payload,
            headers={"X-Service-Token": settings.SERVICE_TOKEN},
        )
        response.raise_for_status()
        return response.json()


async def _active_analyze_run(db: AsyncSession, project_id: uuid.UUID) -> AgentRun | None:
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.workflow == WORKFLOW,
            AgentRun.status == "running",
            AgentRun.input_json["project_id"].astext == str(project_id),
        )
    )
    return result.scalar_one_or_none()


async def run_project_analyze(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    user: User,
    portal_key: str,
    test_scenario: str | None = None,
) -> dict[str, Any]:
    if project.status == "analyzing":
        raise ProcurementAIError("analysis already in progress for this project")
    if await _active_analyze_run(db, project.id):
        raise ProcurementAIError("analysis already in progress for this project")

    facts_result = await db.execute(
        select(ProcurementProjectFact).where(ProcurementProjectFact.project_id == project.id)
    )
    facts = list(facts_result.scalars().all())
    fact_values = {
        f.template_key: f.value_json for f in facts if f.value_json is not None
    }

    run = AgentRun(
        agent_slug=AGENT_SLUG,
        workflow=WORKFLOW,
        status="running",
        input_json={
            "project_id": str(project.id),
            "portal_key": portal_key,
            "project_type": project.project_type,
            "test_scenario": test_scenario,
        },
    )
    db.add(run)
    project.status = "analyzing"
    await db.flush()

    context = {
        "project_id": str(project.id),
        "project_type": project.project_type,
        "title": project.title,
        "description": project.description,
        "facts": fact_values,
        "test_scenario": test_scenario,
    }

    try:
        orch = await _call_orchestrator(context)
    except httpx.HTTPError as exc:
        run.status = "failed"
        run.error_message = str(exc)[:500]
        project.status = "collecting"
        await db.flush()
        raise ProcurementAIError(f"orchestrator unavailable: {exc}") from exc

    if orch.get("status") == "failed" or not orch.get("data"):
        run.status = "failed"
        run.error_message = (orch.get("error") or "invalid orchestrator response")[:500]
        project.status = "collecting"
        await db.flush()
        raise ProcurementAIError(run.error_message)

    data = orch["data"]
    problems = validate_analyze_payload(data)
    if problems:
        run.status = "failed"
        run.error_message = "; ".join(problems)[:500]
        run.output_json = data
        project.status = "collecting"
        await db.flush()
        raise ProcurementAIError("AI output validation failed: " + run.error_message)

    run.output_json = data
    run.status = "completed"

    for extracted in data.get("extracted_facts") or []:
        key = extracted.get("key")
        if not key:
            continue
        for fact in facts:
            if fact.template_key == key:
                if extracted.get("value") is not None:
                    fact.value_json = extracted["value"]
                fact.source = extracted.get("source") or "ai"
                fact.confidence = Decimal(str(extracted.get("confidence", 0)))
                fact.assumption = extracted.get("assumption")
                break

    boq_version = None
    boq_items = []
    plans = []
    if data.get("boq_items"):
        boq_version, boq_items, _, plans = await create_draft_boq(
            db,
            project=project,
            facts=facts,
            items_payload=data["boq_items"],
            disclaimer="Preliminary AI estimate — subject to specialist review.",
            source_run_id=run.id,
        )

    facts_score = compute_facts_score(facts)
    boq_score = compute_boq_score(boq_items) if boq_items else Decimal("0")
    overall = compute_overall_confidence(facts_score, boq_score)
    project.facts_score = facts_score
    project.boq_score = boq_score
    project.overall_confidence = overall
    if boq_version:
        boq_version.facts_score = facts_score
        boq_version.boq_score = boq_score
        boq_version.overall_confidence = overall

    project.status = classify_project_status(overall)
    review = None
    if project.status == "review_ready" and boq_version:
        review = AIReview(
            run_id=run.id,
            target_type="boq_version",
            target_id=boq_version.id,
            draft_json={
                "project_summary": data.get("project_summary"),
                "boq_version_id": str(boq_version.id),
                "overall_confidence": str(overall),
            },
            status="preliminary",
        )
        db.add(review)
        await db.flush()
        boq_version.review_id = review.id
        boq_version.status = "in_review"

    await db.flush()
    return {
        "run_id": str(run.id),
        "status": project.status,
        "facts_score": str(facts_score),
        "boq_score": str(boq_score),
        "overall_confidence": str(overall),
        "missing_questions": data.get("missing_questions") or [],
        "boq_version_id": str(boq_version.id) if boq_version else None,
        "review_id": str(review.id) if review else None,
        "solution_plans": [
            {"tier": p.tier, "total_min": str(p.total_min), "total_max": str(p.total_max)}
            for p in plans
        ],
        "disclaimer": boq_version.disclaimer if boq_version else None,
    }

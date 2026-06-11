"""Lead-intake graph orchestrator (5.14).

Re-expresses the rule-based analysis pipeline as an explicit node graph
(Normalize -> Completeness -> Classify -> Risk -> Match -> Recommend -> Compat
-> Draft -> Summarize), the same workflow described for the LangGraph service.

This is an in-process executor (LangGraph-style: shared state, named nodes,
ordered edges) so it runs inside the API/worker without a separate service or a
heavy dependency. It reuses the existing node functions in `ai_analysis`, so the
output is equivalent to `build_lead_analysis` plus a `graph_trace`. The
rule-based MVP path is left intact; callers opt in via `use_graph=True`.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.services import ai_analysis as aa
from app.services import factorypulse, recurring_revenue, storageguard

NodeFn = Callable[[dict[str, Any]], Awaitable[None]]


# --- nodes ------------------------------------------------------------------

async def node_normalize(s: dict[str, Any]) -> None:
    lead: Lead = s["lead"]
    s["systems"] = lead.systems_needed_json or []
    s["site_info"] = lead.site_info_json or {}
    s["category_key"] = aa._clean_text(s["site_info"].get("category_key")).lower() or None
    s["text"] = aa._lead_text(lead)


async def node_classify(s: dict[str, Any]) -> None:
    s["classification"], s["complexity"] = aa._classify(s["text"], s["systems"], s["category_key"])
    s["solution_line"] = aa._solution_line(s["category_key"], s["text"])


async def node_completeness(s: dict[str, Any]) -> None:
    missing = aa._missing_fields(s["lead"])
    s["missing"] = missing
    s["completeness_score"] = max(0, round(((10 - len(missing)) / 10) * 100))


async def node_risk(s: dict[str, Any]) -> None:
    s["risks"] = aa._risk_items(s["lead"], s["missing"], s["classification"])


async def node_match(s: dict[str, Any]) -> None:
    db: AsyncSession = s["db"]
    s["matched_solutions"] = await aa._match_solutions(db, s["classification"], s["text"])
    s["matched_packages"] = await aa._match_packages(db, s["classification"], s["text"])


async def node_recommend(s: dict[str, Any]) -> None:
    s["lead_score"], s["lead_stage"] = aa._lead_score(s["lead"], s["completeness_score"])
    s["proposal_tiers"] = aa._proposal_tiers(s["lead"], s["complexity"])
    s["recurring"] = recurring_revenue.score_lead(s["lead"])


async def node_compat(s: dict[str, Any]) -> None:
    # Solution-line lifecycle templates (StorageGuard / FactoryPulse).
    s["lifecycle_proposal"] = None
    s["bom_template"] = None
    if storageguard.is_storageguard(s["category_key"], s["text"]):
        s["lifecycle_proposal"] = storageguard.build_storageguard_proposal(s["site_info"])
        s["bom_template"] = storageguard.build_storageguard_bom(s["site_info"])
    elif factorypulse.CLASSIFICATION_MATCH in s["classification"]:
        s["lifecycle_proposal"] = factorypulse.build_factorypulse_proposal(s["site_info"])
        s["bom_template"] = factorypulse.build_factorypulse_bom(s["site_info"])


async def node_draft(s: dict[str, Any]) -> None:
    if s["completeness_score"] < 60:
        s["next_action"] = "Request missing information before quoting."
        s["recommended_status"] = "need_more_info"
    elif any(r["level"] == "high" for r in s["risks"]):
        s["next_action"] = "Schedule professional site assessment before drafting scope."
        s["recommended_status"] = "need_more_info"
    else:
        s["next_action"] = "Admin can review matched solution and prepare a first consultation response."
        s["recommended_status"] = "matched"


async def node_summarize(s: dict[str, Any]) -> None:
    lead: Lead = s["lead"]
    s["output"] = {
        "disclaimer": aa.PRELIMINARY_NOTICE,
        "classification": {
            "project_class": s["classification"],
            "estimated_complexity": s["complexity"],
            "systems_detected": s["systems"],
        },
        "completeness": {
            "score": s["completeness_score"],
            "missing_fields": s["missing"],
            "questions": aa._questions_for(s["missing"]),
        },
        "risks": s["risks"],
        "matched_solutions": s["matched_solutions"],
        "matched_service_packages": s["matched_packages"],
        "lead_score": {"score": s["lead_score"], "stage": s["lead_stage"]},
        "proposal_tiers": s["proposal_tiers"],
        "solution_line": s["solution_line"],
        "recurring_revenue": s["recurring"],
        "lifecycle_proposal": s["lifecycle_proposal"],
        "bom_template": s["bom_template"],
        "phase1_requested": bool(s["site_info"].get("phase1_requested")),
        "recommended_next_action": s["next_action"],
        "recommended_status": s["recommended_status"],
        "customer_draft": (
            f"Based on the submitted information, this looks like a {s['classification']} request. "
            f"The next step is: {s['next_action']} {aa.PRELIMINARY_NOTICE}"
        ),
        "admin_summary": {
            "location": " ".join(p for p in [lead.country, lead.city] if p) or None,
            "budget_range": lead.budget_range,
            "contact": lead.contact_email or lead.contact_phone,
            "priority": "review_now" if s["completeness_score"] >= 60 else "collect_info",
        },
        "graph_trace": s["trace"],
    }


# Ordered graph (linear edges; matches the documented workflow).
GRAPH: list[tuple[str, NodeFn]] = [
    ("normalize", node_normalize),
    ("completeness", node_completeness),
    ("classify", node_classify),
    ("risk", node_risk),
    ("match", node_match),
    ("recommend", node_recommend),
    ("compat", node_compat),
    ("draft", node_draft),
    ("summarize", node_summarize),
]


async def run_lead_graph(db: AsyncSession, lead: Lead) -> dict[str, Any]:
    """Execute the lead-intake graph and return the analysis output."""
    state: dict[str, Any] = {"db": db, "lead": lead, "trace": []}
    for name, fn in GRAPH:
        await fn(state)
        state["trace"].append(name)
    return state["output"]

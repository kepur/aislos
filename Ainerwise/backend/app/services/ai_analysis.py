from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import AIRun
from app.models.lead import Lead
from app.models.solution import Solution, SolutionPackage
from app.services import factorypulse, lifecycle_lines, recurring_revenue, storageguard
from app.services.integration_events import create_integration_event

# Map AI Facility Assessment category keys to solution-line taxonomy.
SOLUTION_LINE_BY_CATEGORY = {
    "storage": "storageguard",
    "factory": "factorypulse",
    "energy": "energyguard",
    "kitchen": "kitchenguard",
    "water": "aquaguard",
    "asset": "assetpulse",
    "agri": "agribrain",
    "villa": "buildingbrain",
    "hotel": "buildingbrain",
    "office": "buildingbrain",
    "school": "buildingbrain",
    "apartment": "buildingbrain",
    "retrofit": "buildingbrain",
}


def _solution_line(category_key: str | None, text: str) -> str | None:
    if storageguard.is_storageguard(category_key, text):
        return "storageguard"
    mapped = SOLUTION_LINE_BY_CATEGORY.get((category_key or "").lower())
    if mapped:
        return mapped
    return lifecycle_lines.detect(category_key, text)

PRELIMINARY_NOTICE = (
    "Preliminary recommendation. Final solution requires engineering review and site verification."
)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values())
    return str(value)


def _lead_text(lead: Lead) -> str:
    parts = [
        lead.project_type,
        lead.country,
        lead.city,
        lead.budget_range,
        lead.description,
        lead.systems_needed_json,
        lead.site_info_json,
    ]
    return " ".join(_clean_text(part).lower() for part in parts)


def _classify(text: str, systems: list[str], category_key: str | None = None) -> tuple[str, str]:
    tokens = text + " " + " ".join(s.lower() for s in systems)
    # StorageGuard takes precedence: cold-chain / compliance storage is its own
    # vertical even when it sits inside a "warehouse" that would otherwise look
    # industrial.
    if storageguard.is_storageguard(category_key, tokens):
        return storageguard.CLASSIFICATION, "medium"
    # KitchenGuard / AquaGuard take precedence over generic factory/solar matching.
    for _line in ("kitchenguard", "aquaguard"):
        _spec = lifecycle_lines.SPECS[_line]
        if (category_key or "") in _spec["category_keys"] or any(kw in tokens for kw in _spec["keywords"]):
            return _spec["classification"], "medium"
    if any(word in tokens for word in [
        "factory", "plant", "manufacturing", "production", "assembly", "warehouse",
        "industrial", "machine", "machinery", "equipment", "plc", "scada", "mes",
        "opc-ua", "opcua", "conveyor", "compressor", "chiller", "motor", "vfd",
        "robotic arm", "cnc", "pump", "boiler", "compressed air",
    ]):
        return "Industrial Factory Automation & Energy", "high"
    if any(word in tokens for word in ["hotel", "guest", "room card", "room control"]):
        return "Smart Hotel / Hospitality", "medium"
    if any(word in tokens for word in ["cctv", "camera", "access", "nvr", "onvif"]):
        return "CCTV & Access Control", "low"
    if (category_key or "") in lifecycle_lines.SPECS["energyguard"]["category_keys"] or any(word in tokens for word in ["solar", "pv", "inverter", "battery", "energy"]):
        return lifecycle_lines.SPECS["energyguard"]["classification"], "medium"
    if any(word in tokens for word in ["knx", "lighting", "scene", "dali"]):
        return "KNX Lighting & Scene Control", "medium"
    if any(word in tokens for word in ["maintenance", "remote", "support", "backup"]):
        return "Remote Maintenance", "low"
    if any(word in tokens for word in ["villa", "apartment", "retrofit", "home assistant"]):
        return "Smart Starter Retrofit", "low"
    return "Smart Building Requirement", "medium"


def _missing_fields(lead: Lead) -> list[str]:
    missing = []
    required = {
        "project_type": lead.project_type,
        "country": lead.country,
        "budget_range": lead.budget_range,
        "systems_needed": lead.systems_needed_json,
        "description": lead.description,
        "contact_email": lead.contact_email,
    }
    for field, value in required.items():
        if not value:
            missing.append(field)

    site_info = lead.site_info_json or {}
    for field in ["area", "rooms", "floors", "existing_systems"]:
        if not site_info.get(field):
            missing.append(f"site_info.{field}")
    category = _clean_text(site_info.get("category_key")).lower()
    combined = _lead_text(lead)
    if storageguard.is_storageguard(category, combined):
        missing.extend(storageguard.storageguard_missing_fields(site_info))
        return missing
    _ll = lifecycle_lines.detect(category, combined)
    if _ll:
        missing.extend(lifecycle_lines.missing_fields(_ll, site_info))
        return missing
    is_factory = category == "factory" or any(token in combined for token in ["factory", "industrial", "plc", "scada", "production line", "machinery"])
    if is_factory:
        factory_required = {
            "production_machines": site_info.get("production_machines") or site_info.get("production"),
            "energy_solar": site_info.get("energy_solar") or site_info.get("energy"),
            "industrial_protocols": site_info.get("industrial_protocols") or site_info.get("existing_systems"),
            "safety_requirements": site_info.get("safety_requirements") or site_info.get("identity_access"),
        }
        for field, value in factory_required.items():
            if not value:
                missing.append(f"site_info.{field}")
    return missing


def _questions_for(missing: list[str]) -> list[str]:
    question_map = {
        "project_type": "What type of building or site is this project for?",
        "country": "Which country and city is the site located in?",
        "budget_range": "What budget range should we design around?",
        "systems_needed": "Which systems are required: lighting, HVAC, CCTV, access control, energy monitoring, KNX, or other?",
        "description": "What business goal or problem should the solution solve?",
        "contact_email": "Which email should the project team use for follow-up?",
        "site_info.area": "What is the approximate site area in square meters?",
        "site_info.rooms": "How many rooms, zones, or controlled areas are involved?",
        "site_info.floors": "How many floors does the site have?",
        "site_info.existing_systems": "What existing wiring, network, HVAC, CCTV, access, solar, or automation systems are already installed?",
        "site_info.production_machines": "Which production lines, machines, compressors, chillers, motors, pumps, robots, or mechanical systems should be monitored or linked?",
        "site_info.energy_solar": "What are the major energy loads, PV/battery assets, tariffs, and peak-demand constraints?",
        "site_info.industrial_protocols": "Which industrial protocols or platforms are available: PLC, SCADA, MES, Modbus, BACnet, MQTT, OPC-UA, or vendor APIs?",
        "site_info.safety_requirements": "What safety boundaries, restricted machine zones, OT network isolation, and downtime constraints must be respected?",
        **storageguard.STORAGEGUARD_QUESTIONS,
    }
    for _line in lifecycle_lines.SPECS:
        question_map.update(lifecycle_lines.questions(_line))
    return [question_map[field] for field in missing if field in question_map]


def _lead_score(lead: Lead, completeness_score: int) -> tuple[int, str]:
    site_info = lead.site_info_json or {}
    score = 0

    if completeness_score >= 70:
        score += 20
    elif completeness_score >= 40:
        score += 10

    budget = _clean_text(lead.budget_range).lower() + " " + _clean_text(site_info.get("budget_and_service")).lower()
    if any(token in budget for token in ["50", "100", "over", "enterprise", "premium"]):
        score += 20
    elif any(token in budget for token in ["15", "20", "30"]):
        score += 12
    elif budget:
        score += 6

    if any(token in budget for token in ["3-year", "3 year", "5-year", "5 year", "8-year", "10-year", "lifecycle"]):
        score += 15

    if lead.contact_email and "unknown@" not in lead.contact_email:
        score += 10
    if lead.contact_phone and any(token in lead.contact_phone.lower() for token in ["telegram", "whatsapp", "@", "+"]):
        score += 10

    transcript_text = _clean_text(site_info.get("transcript")).lower()
    if any(token in transcript_text for token in ["drawing", "photo", "floor plan", "blueprint"]):
        score += 20
    if site_info.get("phase1_requested"):
        score += 25
    if site_info.get("target_intelligence_level") in ["L4", "L5"]:
        score += 10

    score = min(score, 100)
    if score >= 85:
        return score, "Phase-1 Ready"
    if score >= 70:
        return score, "Qualified Lead"
    if score >= 45:
        return score, "Warm Lead"
    return score, "Cold Lead"


def _proposal_tiers(lead: Lead, complexity: str) -> list[dict[str, Any]]:
    site_info = lead.site_info_json or {}
    target_level = site_info.get("target_intelligence_level") or "L3"
    category = site_info.get("category_key") or "smart_building"
    base_ranges = {
        "budget": (5000, 15000),
        "standard": (15000, 50000),
        "premium_ai": (50000, 120000),
    }
    if category in {"school", "office", "hotel"}:
        base_ranges = {
            "budget": (15000, 50000),
            "standard": (50000, 100000),
            "premium_ai": (100000, 250000),
        }
    if category == "factory":
        base_ranges = {
            "budget": (30000, 100000),
            "standard": (100000, 300000),
            "premium_ai": (300000, 800000),
        }

    tiers = [
        {
            "tier": "budget",
            "name": "Budget Plan",
            "intelligence_level": "L1-L2",
            "device_cost_estimate": base_ranges["budget"],
            "design_fee_estimate": "800-2500 EUR",
            "installation_fee_estimate": "project dependent",
            "platform_fee_estimate": "5-8%",
            "maintenance_fee_estimate": "1-3 years optional",
            "spare_parts_reserve": "5-8%",
            "complexity": "low",
            "risk_level": "medium" if complexity == "medium" else "low",
            "next_step": "Use only for constrained scope or starter retrofit.",
            "estimate_only": True,
        },
        {
            "tier": "standard",
            "name": "Standard Plan",
            "intelligence_level": "L2-L3",
            "device_cost_estimate": base_ranges["standard"],
            "design_fee_estimate": "2500-8000 EUR",
            "installation_fee_estimate": "site survey required",
            "platform_fee_estimate": "8-12%",
            "maintenance_fee_estimate": "3-5 years recommended",
            "spare_parts_reserve": "8-12%",
            "complexity": complexity,
            "risk_level": "medium",
            "next_step": "Recommended default path for a practical AinerWise delivery.",
            "estimate_only": True,
        },
        {
            "tier": "premium_ai",
            "name": "Premium AI Plan",
            "intelligence_level": "L4-L5" if target_level in ["L4", "L5"] else "L3-L4",
            "device_cost_estimate": base_ranges["premium_ai"],
            "design_fee_estimate": "8000-25000 EUR",
            "installation_fee_estimate": "manual engineering review required",
            "platform_fee_estimate": "10-15%",
            "maintenance_fee_estimate": "5-10 years recommended",
            "spare_parts_reserve": "10-15%",
            "complexity": "high",
            "risk_level": "high",
            "next_step": "Request Phase-1 Proposal before committing scope or price.",
            "estimate_only": True,
        },
        {
            "tier": "future_autonomous",
            "name": "Future Autonomous Plan",
            "intelligence_level": "L5-L6",
            "device_cost_estimate": "custom engineering required",
            "design_fee_estimate": "paid discovery required",
            "installation_fee_estimate": "not fixed",
            "platform_fee_estimate": "custom",
            "maintenance_fee_estimate": "8-10 years or custom SLA",
            "spare_parts_reserve": "custom",
            "complexity": "advanced custom",
            "risk_level": "requires review",
            "next_step": "Concept demo only until engineering review, site verification, supplier confirmation, and contract.",
            "estimate_only": True,
        },
    ]
    return tiers


def _risk_items(lead: Lead, missing: list[str], classification: str) -> list[dict[str, str]]:
    risks = []
    if len(missing) >= 5:
        risks.append({
            "level": "high",
            "area": "requirements",
            "note": "The requirement is too incomplete for a reliable scope or budget estimate.",
        })
    if not lead.budget_range:
        risks.append({
            "level": "medium",
            "area": "budget",
            "note": "Budget range is missing, so solution tier and product grade cannot be narrowed yet.",
        })
    if "KNX" in classification and "site_info.existing_systems" in missing:
        risks.append({
            "level": "medium",
            "area": "site",
            "note": "KNX feasibility depends on wiring routes, panel access, bus topology, and renovation stage.",
        })
    if "CCTV" in classification:
        risks.append({
            "level": "medium",
            "area": "network",
            "note": "Camera placement, PoE budget, storage retention, and remote access policy must be verified.",
        })
    if "Solar" in classification:
        risks.append({
            "level": "medium",
            "area": "compatibility",
            "note": "Inverter protocol, meter access, and data export capability must be confirmed.",
        })
    if "Industrial Factory" in classification:
        risks.extend([
            {
                "level": "high",
                "area": "safety",
                "note": "Machine control, safety interlocks, and production downtime constraints require engineering review before any control recommendation.",
            },
            {
                "level": "medium",
                "area": "ot_network",
                "note": "PLC/SCADA access, OT/IT network isolation, protocol availability, and vendor permissions must be confirmed.",
            },
            {
                "level": "medium",
                "area": "energy",
                "note": "Machine-level metering, compressor/chiller loads, power quality, and peak demand data are needed for reliable industrial energy optimization.",
            },
        ])
    if not risks:
        risks.append({
            "level": "low",
            "area": "scope",
            "note": "No major red flags from the quick intake. A detailed site survey is still required.",
        })
    return risks


async def _match_solutions(db: AsyncSession, classification: str, text: str) -> list[dict[str, Any]]:
    result = await db.execute(
        select(Solution)
        .where(Solution.public_visible == True)
        .order_by(Solution.sort_order, Solution.created_at.desc())
    )
    solutions = list(result.scalars().all())

    classification_terms = set(classification.lower().replace("&", " ").replace("/", " ").split())
    matches = []
    for solution in solutions:
        haystack = " ".join([
            solution.title or "",
            solution.category or "",
            solution.description or "",
            _clean_text(solution.target_scenarios_json),
            _clean_text(solution.pain_points_json),
        ]).lower()
        score = sum(1 for term in classification_terms if term in haystack)
        if solution.title and any(word in text for word in solution.title.lower().split()):
            score += 2
        if score:
            matches.append({
                "id": str(solution.id),
                "title": solution.title,
                "slug": solution.slug,
                "score": score,
            })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:3]


async def _match_packages(db: AsyncSession, classification: str, text: str) -> list[dict[str, Any]]:
    result = await db.execute(
        select(SolutionPackage)
        .where(SolutionPackage.public_visible == True)
        .order_by(SolutionPackage.sort_order, SolutionPackage.created_at.desc())
    )
    packages = list(result.scalars().all())

    terms = set(classification.lower().replace("&", " ").replace("/", " ").split())
    matches = []
    for package in packages:
        haystack = " ".join([
            package.title or "",
            package.target_customer_type or "",
            package.description or "",
            _clean_text(package.included_systems_json),
        ]).lower()
        score = sum(1 for term in terms if term in haystack)
        if package.title and any(word in text for word in package.title.lower().split()):
            score += 2
        if score:
            matches.append({
                "id": str(package.id),
                "title": package.title,
                "slug": package.slug,
                "score": score,
                "estimated_timeline_days": package.estimated_timeline_days,
            })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:3]


async def build_lead_analysis(db: AsyncSession, lead: Lead) -> dict[str, Any]:
    systems = lead.systems_needed_json or []
    site_info = lead.site_info_json or {}
    category_key = _clean_text(site_info.get("category_key")).lower() or None
    text = _lead_text(lead)
    classification, complexity = _classify(text, systems, category_key)
    missing = _missing_fields(lead)
    total_fields = 10
    completeness_score = max(0, round(((total_fields - len(missing)) / total_fields) * 100))
    risks = _risk_items(lead, missing, classification)
    matched_solutions = await _match_solutions(db, classification, text)
    matched_packages = await _match_packages(db, classification, text)
    lead_score, lead_stage = _lead_score(lead, completeness_score)
    proposal_tiers = _proposal_tiers(lead, complexity)
    recurring = recurring_revenue.score_lead(lead)
    solution_line = _solution_line(category_key, text)

    # Solution-line lifecycle templates (StorageGuard sellable slice). These are
    # estimate-only and surfaced for admin review alongside the generic tiers.
    lifecycle_proposal = None
    bom_template = None
    if storageguard.is_storageguard(category_key, text):
        lifecycle_proposal = storageguard.build_storageguard_proposal(site_info)
        bom_template = storageguard.build_storageguard_bom(site_info)
    elif factorypulse.CLASSIFICATION_MATCH in classification:
        # IND.9 — industrial BOM + proposal template for FactoryPulse leads.
        lifecycle_proposal = factorypulse.build_factorypulse_proposal(site_info)
        bom_template = factorypulse.build_factorypulse_bom(site_info)
    else:
        # FI.7 — KitchenGuard / AquaGuard / EnergyGuard lifecycle templates.
        _ll = lifecycle_lines.detect(category_key, text)
        if _ll:
            lifecycle_proposal = lifecycle_lines.build_proposal(_ll, site_info)
            bom_template = lifecycle_lines.build_bom(_ll, site_info)

    if completeness_score < 60:
        next_action = "Request missing information before quoting."
        recommended_status = "need_more_info"
    elif any(risk["level"] == "high" for risk in risks):
        next_action = "Schedule professional site assessment before drafting scope."
        recommended_status = "need_more_info"
    else:
        next_action = "Admin can review matched solution and prepare a first consultation response."
        recommended_status = "matched"

    return {
        "disclaimer": PRELIMINARY_NOTICE,
        "classification": {
            "project_class": classification,
            "estimated_complexity": complexity,
            "systems_detected": systems,
        },
        "completeness": {
            "score": completeness_score,
            "missing_fields": missing,
            "questions": _questions_for(missing),
        },
        "risks": risks,
        "matched_solutions": matched_solutions,
        "matched_service_packages": matched_packages,
        "lead_score": {
            "score": lead_score,
            "stage": lead_stage,
        },
        "proposal_tiers": proposal_tiers,
        "solution_line": solution_line,
        "recurring_revenue": recurring,
        "lifecycle_proposal": lifecycle_proposal,
        "bom_template": bom_template,
        "phase1_requested": bool((lead.site_info_json or {}).get("phase1_requested")),
        "recommended_next_action": next_action,
        "recommended_status": recommended_status,
        "customer_draft": (
            f"Based on the submitted information, this looks like a {classification} request. "
            f"The next step is: {next_action} {PRELIMINARY_NOTICE}"
        ),
        "admin_summary": {
            "location": " ".join(part for part in [lead.country, lead.city] if part) or None,
            "budget_range": lead.budget_range,
            "contact": lead.contact_email or lead.contact_phone,
            "priority": "review_now" if completeness_score >= 60 else "collect_info",
        },
    }


async def analyze_lead(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID,
    workflow_name: str | None = None,
    use_graph: bool = False,
) -> AIRun:
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")

    workflow_name = workflow_name or ("lead_intake_graph" if use_graph else "lead_intake_mvp")
    lead.status = "ai_analyzing"
    ai_run = AIRun(
        entity_type="lead",
        entity_id=lead.id,
        workflow_name=workflow_name,
        input_json={
            "lead_id": str(lead.id),
            "project_type": lead.project_type,
            "country": lead.country,
            "city": lead.city,
            "budget_range": lead.budget_range,
            "systems_needed_json": lead.systems_needed_json,
            "site_info_json": lead.site_info_json,
        },
        model_name="rule-based-graph" if use_graph else "rule-based-mvp",
        status="running",
    )
    db.add(lead)
    db.add(ai_run)
    await db.commit()
    await db.refresh(ai_run)
    await db.refresh(lead)

    try:
        if use_graph:
            from app.services.ai_graph import run_lead_graph
            output = await run_lead_graph(db, lead)
        else:
            output = await build_lead_analysis(db, lead)
        lead.ai_analysis_json = output
        lead.status = output["recommended_status"]

        # Persist recurring-revenue qualification to queryable columns (FI.6.1).
        rr = output["recurring_revenue"]
        arr_avg = round((rr["estimated_arr_min"] + rr["estimated_arr_max"]) / 2)
        lead.solution_line = output["solution_line"]
        lead.recurring_revenue_score = rr["recurring_revenue_score"]
        lead.compliance_risk_level = rr["compliance_risk_level"]
        lead.consumable_potential = rr["consumable_potential"]
        lead.amc_potential = rr["amc_potential"]
        lead.estimated_arr = arr_avg
        lead.estimated_ltv = arr_avg * 3
        lead.is_multi_site = rr["is_multi_site"]
        lead.monitoring_points_count = rr["monitoring_points_count"]
        ai_run.output_json = output
        ai_run.status = "completed"
        db.add(lead)
        db.add(ai_run)
        await db.commit()
        await db.refresh(ai_run)
        await db.refresh(lead)

        await create_integration_event(
            db,
            event_type="ai.completed",
            payload={
                "lead_id": str(lead.id),
                "ai_run_id": str(ai_run.id),
                "classification": output["classification"]["project_class"],
                "completeness_score": output["completeness"]["score"],
                "recommended_status": output["recommended_status"],
            },
        )
    except Exception as exc:
        lead.status = "new"
        ai_run.status = "failed"
        ai_run.error_message = str(exc)
        db.add(lead)
        db.add(ai_run)
        await db.commit()
        await db.refresh(ai_run)
        raise

    return ai_run

"""Spare-kit calculator and fast-replacement plan rules.

FI.3.3 — Recommended spare-kit calculator by product criticality / category.
FI.3.4 — Fast-replacement plan rules (eligible devices, cap, response, exclusions).
"""
from __future__ import annotations

import math
from typing import Any

# Recommended spare ratio (as a fraction) per device category, from the
# lifecycle finance plan. Used for "customer-owned kit" and "shared pool".
SPARE_RATIO = {
    "critical_gateway": (0.05, 0.10),
    "controller": (0.05, 0.10),
    "temperature": (0.10, 0.15),
    "humidity": (0.10, 0.15),
    "water_probe": (0.15, 0.25),
    "ph": (0.15, 0.25),
    "kitchen_safety": (0.10, 0.20),
    "gas": (0.10, 0.20),
    "tag": (0.10, 0.20),
    "asset_tag": (0.10, 0.20),
    "panel": (0.03, 0.08),
    "switch": (0.03, 0.08),
    "camera": (0.05, 0.10),
    "battery": (0.20, 0.30),
    "consumable": (0.20, 0.30),
    "calibration_fluid": (0.20, 0.30),
    "default": (0.05, 0.12),
}

SPARE_PLANS = ("customer_owned", "shared_pool", "fast_replacement")


def recommend_spare_kit(items: list[dict[str, Any]], plan: str = "customer_owned") -> dict[str, Any]:
    """FI.3.3 — Recommend spare quantities for a list of BOM-style items.

    Each item: {category, qty, unit_cost?}. Returns per-line spare recommendation
    and an overall reserve-cost percentage band.
    """
    lines = []
    total_low = total_high = 0
    cost_total = 0.0
    spare_cost_low = spare_cost_high = 0.0

    for item in items:
        category = (item.get("category") or "default").lower()
        qty = int(item.get("qty") or 0)
        unit_cost = float(item.get("unit_cost") or 0)
        ratio_low, ratio_high = SPARE_RATIO.get(category, SPARE_RATIO["default"])
        spares_low = max(1, math.ceil(qty * ratio_low)) if qty else 0
        spares_high = max(1, math.ceil(qty * ratio_high)) if qty else 0
        lines.append({
            "category": category,
            "qty": qty,
            "ratio_min_pct": round(ratio_low * 100, 1),
            "ratio_max_pct": round(ratio_high * 100, 1),
            "recommended_spares_min": spares_low,
            "recommended_spares_max": spares_high,
        })
        total_low += spares_low
        total_high += spares_high
        cost_total += qty * unit_cost
        spare_cost_low += spares_low * unit_cost
        spare_cost_high += spares_high * unit_cost

    reserve_pct_min = round((spare_cost_low / cost_total) * 100, 1) if cost_total else None
    reserve_pct_max = round((spare_cost_high / cost_total) * 100, 1) if cost_total else None

    return {
        "plan": plan if plan in SPARE_PLANS else "customer_owned",
        "lines": lines,
        "total_spares_min": total_low,
        "total_spares_max": total_high,
        "reserve_cost_pct_min": reserve_pct_min,
        "reserve_cost_pct_max": reserve_pct_max,
        "plan_note": _plan_note(plan),
        "estimate_only": True,
    }


def _plan_note(plan: str) -> str:
    return {
        "customer_owned": "Spares purchased by and owned by the customer; managed by AinerWise.",
        "shared_pool": "AinerWise maintains a shared spare pool across similar projects.",
        "fast_replacement": "Spares covered under a paid Fast Replacement Plan; see fast-replacement rules.",
    }.get(plan, "Spares purchased by and owned by the customer; managed by AinerWise.")


# FI.3.4 — Fast-replacement plan rules.
FAST_REPLACEMENT_PLAN = {
    "name": "Fast Replacement Plan",
    "billing": "paid_annual_addon",
    "eligible_categories": [
        "temperature", "humidity", "door", "gas", "kitchen_safety",
        "water_probe", "ph", "tag", "asset_tag", "battery", "consumable",
    ],
    "ineligible_categories": ["critical_gateway", "controller", "camera", "panel"],
    "annual_cap_per_100_points": 6,
    "response_promise": "Replacement unit dispatched within 2 business days of confirmed fault.",
    "refurbished_stock_consent_required": True,
    "exclusions": [
        "Physical / accidental damage", "Water ingress beyond rating", "Lightning / surge",
        "Unauthorized modification", "Use beyond device lifecycle", "Lapsed plan",
    ],
    "estimate_only": True,
}


def fast_replacement_eligible(category: str | None) -> bool:
    """FI.3.4 — Whether a device category is eligible for fast replacement."""
    cat = (category or "").lower()
    if cat in FAST_REPLACEMENT_PLAN["ineligible_categories"]:
        return False
    return cat in FAST_REPLACEMENT_PLAN["eligible_categories"]

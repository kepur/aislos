"""AMC catalog, pricing formulas, and contract-boundary template.

FI.3.1 — AMC catalog (Basic / Compliance / Commercial / Premium / Enterprise),
         keeping the included 3-year remote assurance as a separate baseline.
FI.3.2 — AMC pricing formulas: percentage, point-based, site-based, service-level.
FI.3.7 — Contract-boundary template separating supply / integration / platform /
         warranty coordination / on-site service / exclusions / third-party.

All figures are estimate-only and require admin review before quoting.
"""
from __future__ import annotations

from typing import Any

ESTIMATE_NOTICE = "Estimate only. Final AMC scope and price require admin review and a signed contract."

# Included baseline that ships with qualifying delivered projects — NOT an AMC.
BASELINE_REMOTE_ASSURANCE = {
    "name": "Included Remote Assurance",
    "years": 3,
    "billing": "included_with_qualifying_project",
    "includes": [
        "Remote diagnosis and technical consultation",
        "Handover documentation and configuration records",
        "Supplier warranty coordination",
    ],
    "note": "Baseline support included with delivery. On-site visits are quoted separately. AMC tiers below are optional paid plans.",
}

# FI.3.1 — AMC catalog.
AMC_CATALOG = [
    {
        "tier": "basic",
        "name": "Basic AMC",
        "suitable_for": ["Small cold room", "Small restaurant", "Small office", "Small villa"],
        "includes": ["Remote support", "Basic alarm watch", "One annual system check", "Basic reports"],
        "excludes": ["Consumables", "On-site emergency service", "Calibration"],
        "default_pricing_mode": "service_level",
        "service_level_fee_range": [300, 900],
    },
    {
        "tier": "compliance",
        "name": "Compliance AMC",
        "suitable_for": ["Cold chain", "Water compliance", "Commercial kitchen safety"],
        "includes": [
            "Compliance reports", "Annual calibration", "Probe checks",
            "Alarm contact maintenance", "Electronic maintenance record", "Consumable discount",
        ],
        "excludes": ["Unscheduled on-site emergency (quoted separately)"],
        "default_pricing_mode": "point_based",
        "service_level_fee_range": [900, 3500],
    },
    {
        "tier": "commercial",
        "name": "Commercial AMC",
        "suitable_for": ["Hotels", "Apartments", "Factories", "Warehouses"],
        "includes": [
            "Remote monitoring", "Multi-point management", "Annual on-site inspection",
            "Firmware upgrades", "Minor logic changes", "Priority spare supply", "Quarterly report",
        ],
        "excludes": ["Major reconfiguration", "New points (quoted separately)"],
        "default_pricing_mode": "percentage",
        "service_level_fee_range": [3000, 12000],
    },
    {
        "tier": "premium",
        "name": "Premium AMC",
        "suitable_for": ["High-end villas", "Key accounts", "Multi-site customers"],
        "includes": [
            "Priority response", "Dedicated support", "2-4 on-site visits/year",
            "Critical spare pool", "System optimization", "Energy/AI reports",
        ],
        "excludes": ["Damage from misuse, water, lightning, tampering"],
        "default_pricing_mode": "service_level",
        "service_level_fee_range": [8000, 25000],
    },
    {
        "tier": "enterprise",
        "name": "Enterprise AMC",
        "suitable_for": ["Multi-site enterprises"],
        "includes": ["SLA", "Spare parts pool", "Dedicated account support", "Custom reporting"],
        "excludes": ["Out-of-scope projects"],
        "default_pricing_mode": "site_based",
        "service_level_fee_range": [20000, 80000],
    },
]

# FI.3.2 — percentage-of-project-value bands by solution line.
AMC_PERCENT_RANGE = {
    "buildingbrain": (0.05, 0.10),
    "energyguard": (0.05, 0.12),
    "storageguard": (0.08, 0.18),
    "aquaguard": (0.12, 0.25),
    "kitchenguard": (0.08, 0.18),
    "factorypulse": (0.08, 0.15),
    "assetpulse": (0.10, 0.20),
    "agribrain": (0.08, 0.15),
}

# Per-point annual fee bands (EUR) for point-based pricing.
POINT_FEE_RANGE = {
    "gateway": (50, 200),
    "temperature": (30, 80),
    "humidity": (30, 80),
    "door": (20, 60),
    "water_probe": (150, 500),
    "ph": (150, 500),
    "kitchen_node": (50, 150),
    "gas": (50, 150),
    "asset_tag": (5, 30),
    "default": (30, 100),
}

DEFAULT_BASE_FEE = 300


def _catalog_tier(tier: str | None) -> dict[str, Any] | None:
    return next((t for t in AMC_CATALOG if t["tier"] == tier), None)


def amc_annual_fee(
    *,
    mode: str,
    solution_line: str | None = None,
    project_value: float | None = None,
    points: dict[str, int] | None = None,
    sites: int | None = None,
    site_fee: float | None = None,
    base_fee: float | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    """FI.3.2 — Compute an estimate-only annual AMC fee range.

    mode: percentage | point_based | site_based | service_level
    """
    currency = "EUR"
    base = DEFAULT_BASE_FEE if base_fee is None else base_fee

    if mode == "percentage":
        low, high = AMC_PERCENT_RANGE.get(solution_line or "", (0.05, 0.12))
        value = project_value or 0
        return {
            "mode": mode,
            "amount_min": round(value * low),
            "amount_max": round(value * high),
            "currency": currency,
            "basis": f"{int(low * 100)}-{int(high * 100)}% of project value {value:.0f}",
            "estimate_only": True,
            "disclaimer": ESTIMATE_NOTICE,
        }

    if mode == "point_based":
        low_total = base
        high_total = base
        breakdown = []
        for point_type, qty in (points or {}).items():
            plow, phigh = POINT_FEE_RANGE.get(point_type, POINT_FEE_RANGE["default"])
            low_total += plow * qty
            high_total += phigh * qty
            breakdown.append({"point_type": point_type, "qty": qty, "fee_min": plow, "fee_max": phigh})
        return {
            "mode": mode,
            "amount_min": round(low_total),
            "amount_max": round(high_total),
            "currency": currency,
            "base_fee": base,
            "breakdown": breakdown,
            "estimate_only": True,
            "disclaimer": ESTIMATE_NOTICE,
        }

    if mode == "site_based":
        sfee = site_fee if site_fee is not None else 1200
        n = sites or 1
        point_low = point_high = 0
        for point_type, qty in (points or {}).items():
            plow, phigh = POINT_FEE_RANGE.get(point_type, POINT_FEE_RANGE["default"])
            point_low += plow * qty
            point_high += phigh * qty
        return {
            "mode": mode,
            "amount_min": round(sfee * n + point_low),
            "amount_max": round(sfee * n * 1.5 + point_high),
            "currency": currency,
            "basis": f"{n} sites x site fee {sfee:.0f} + point fees",
            "estimate_only": True,
            "disclaimer": ESTIMATE_NOTICE,
        }

    # service_level: flat band from the catalog tier
    catalog = _catalog_tier(tier) or _catalog_tier("basic")
    low, high = catalog["service_level_fee_range"]
    return {
        "mode": "service_level",
        "tier": catalog["tier"],
        "amount_min": low,
        "amount_max": high,
        "currency": currency,
        "estimate_only": True,
        "disclaimer": ESTIMATE_NOTICE,
    }


# FI.3.7 — Contract-boundary template.
CONTRACT_BOUNDARY_TEMPLATE = {
    "title": "AinerWise Service & Liability Boundary",
    "summary": (
        "AinerWise provides system integration, monitoring, support coordination, and "
        "lifecycle service. Hardware warranty follows the original supplier warranty unless "
        "the customer purchases AinerWise Managed Warranty or a Fast Replacement Plan."
    ),
    "sections": [
        {"key": "equipment_supply", "title": "Equipment Supply", "scope": "Supply of specified devices; hardware defects follow supplier warranty terms."},
        {"key": "integration", "title": "Integration & Commissioning", "scope": "System design, installation coordination, configuration, and commissioning."},
        {"key": "platform", "title": "Platform Service", "scope": "Monitoring platform, dashboards, alert routing, and report generation."},
        {"key": "warranty_coordination", "title": "Warranty Coordination", "scope": "AinerWise diagnoses faults and coordinates supplier warranty claims on the customer's behalf."},
        {"key": "on_site_service", "title": "On-site Service", "scope": "On-site visits are quoted separately unless included in a purchased AMC tier."},
        {"key": "exclusions", "title": "Exclusions", "scope": "Misuse, water ingress, lightning, customer modification, third-party damage, lapsed payment, end-of-life devices."},
        {"key": "third_party", "title": "Third-party Dependencies", "scope": "Power, ISP/network, and cloud-provider outages are outside AinerWise control."},
    ],
    "exclusions": [
        "Physical / accidental damage", "Water ingress", "Lightning / power surge",
        "Unauthorized modification", "Third-party construction damage",
        "Network / power / ISP outages", "Lapsed contract or unpaid service",
        "Use beyond device lifecycle",
    ],
    "note": ESTIMATE_NOTICE,
}

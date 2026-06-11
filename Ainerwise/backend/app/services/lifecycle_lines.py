"""Data-driven lifecycle solution lines (FI.7.1 KitchenGuard, FI.7.2 AquaGuard,
FI.7.3 EnergyGuard).

A spec registry + generic proposal / BOM builders so new verticals reuse the
StorageGuard pattern without per-file duplication. StorageGuard and FactoryPulse
keep their dedicated modules. All output is estimate-only and public-safe (no
supplier cost / internal model).
"""
from __future__ import annotations

import re
from typing import Any

PRELIMINARY = "Preliminary estimate. Points, scope, and pricing require admin review and a site survey before quotation."

# Each spec: classification, detection keywords/category keys, required intake
# fields + questions, per-point pricing band, and BOM rows.
SPECS: dict[str, dict[str, Any]] = {
    "kitchenguard": {
        "classification": "Commercial Kitchen Safety (KitchenGuard)",
        "category_keys": {"kitchen", "kitchenguard"},
        "keywords": (
            "kitchen", "gas leak", "carbon monoxide", " co ", "cooktop", "stove",
            "extraction hood", "grease", "cutoff valve", "fire suppression", "restaurant",
        ),
        "required_fields": ("kitchen_count", "gas_type", "alarm_contacts", "service_term"),
        "questions": {
            "kitchen_count": "How many kitchens / cooking lines, and is there an automatic gas cut-off valve?",
            "gas_type": "What gas type is used (natural gas, LPG), and do you need CO and water-leak monitoring?",
            "alarm_contacts": "Who should receive alarms (store manager, property, maintenance) and via which channels?",
            "service_term": "Do you need annual safety inspection certificates, and over how many years?",
        },
        "point_low": 90, "point_high": 220, "gateway_low": 450, "gateway_high": 700,
        "amc_pct": (0.08, 0.18),
        "default_points": 6,
        "bom": [
            ("gateway", "KitchenGuard Safety Gateway", 1, "Edge gateway with alarm relay and backup power."),
            ("gas_sensor", "Combustible Gas + CO Sensor", "points", "Gas leak and carbon monoxide monitoring per cooking zone."),
            ("water_leak", "Water Leak Sensor", "third", "Leak detection under sinks and appliances."),
            ("cutoff_valve", "Gas Cut-off Valve Integration", 1, "Auto cut-off interlock on alarm (where a valve exists)."),
            ("annual_inspection", "Annual Safety Inspection & Certificate", 1, "Recurring annual inspection with maintenance certificate.", True),
        ],
        "recurring_carriers": ["annual_inspection", "alarm_monitoring", "calibration", "amc"],
    },
    "aquaguard": {
        "classification": "Water & Effluent Compliance (AquaGuard)",
        "category_keys": {"water", "aquaguard", "effluent"},
        "keywords": (
            "effluent", "wastewater", "waste water", "water quality", "ph ", "conductivity",
            "turbidity", "cod", "discharge", "pool water", "process water", "environmental compliance",
        ),
        "required_fields": ("water_system", "parameters", "reporting", "service_term"),
        "questions": {
            "water_system": "What water system is this (effluent, pool, cooling, process water) and how many discharge/sample points?",
            "parameters": "Which parameters must be monitored: pH, conductivity, turbidity, COD, temperature?",
            "reporting": "Do you need government / environmental compliance reports, and how often?",
            "service_term": "How often must probes be calibrated/replaced, and over how many years of service?",
        },
        "point_low": 200, "point_high": 600, "gateway_low": 700, "gateway_high": 1100,
        "amc_pct": (0.12, 0.25),
        "default_points": 4,
        "professional_partner_required": True,
        "bom": [
            ("gateway", "AquaGuard Monitoring Gateway", 1, "Industrial gateway with analog/RS-485 probe inputs."),
            ("probe", "Water Quality Probe (pH / EC / Turbidity / COD)", "points", "Certified probes per monitored parameter."),
            ("sampler", "Auto-sampling / Flow Module (optional)", 1, "Optional auto-sampler for regulated discharge points.", False, True),
            ("consumable", "Calibration Fluid & Probe Spare Kit", "third", "Recurring calibration fluid and probe replacement.", True),
            ("compliance_report", "Environmental Compliance Reporting (per year)", 1, "Recurring regulated reporting service.", True),
        ],
        "recurring_carriers": ["calibration", "consumable", "compliance_report", "alarm_monitoring", "amc"],
    },
    "energyguard": {
        "classification": "Solar & Energy Monitoring (EnergyGuard)",
        "category_keys": {"energy", "energyguard", "solar"},
        "keywords": (
            "solar", "pv ", "inverter", "battery storage", "peak tariff", "energy monitoring",
            "ev charging", "vpp", "demand charge", "battery health",
        ),
        "required_fields": ("assets", "loads", "goals", "service_term"),
        "questions": {
            "assets": "What energy assets exist: PV, inverter brand, battery, EV chargers, meters?",
            "loads": "What are the key loads and tariff problem (peak demand, time-of-use)?",
            "goals": "What to optimize: self-consumption, peak shaving, EV coordination, battery health, reports?",
            "service_term": "Do you need monthly energy reports and remote operations, and over how many years?",
        },
        "point_low": 120, "point_high": 350, "gateway_low": 600, "gateway_high": 950,
        "amc_pct": (0.05, 0.12),
        "default_points": 6,
        "bom": [
            ("gateway", "Energy Gateway (inverter/meter/EV)", 1, "Gateway for inverter, meters, battery, and EV chargers."),
            ("meter", "Energy / Load Meter", "points", "Per-circuit and key-load energy metering."),
            ("edge_box", "Local Energy Edge Box (optional)", 1, "Optional on-prem analytics and control logic.", False, True),
            ("report", "Monthly Energy Report + Remote Ops (per year)", 1, "Recurring reporting, optimization, and remote operations.", True),
        ],
        "recurring_carriers": ["saas", "report_export", "algorithm_subscription", "amc"],
    },
}


def detect(category_key: str | None, text: str) -> str | None:
    ck = (category_key or "").lower()
    text = (text or "").lower()
    for key, spec in SPECS.items():
        if ck in spec["category_keys"]:
            return key
        if any(kw in text for kw in spec["keywords"]):
            return key
    return None


def _points(site_info: dict[str, Any], spec: dict[str, Any]) -> int:
    raw = site_info.get("monitoring_points") or site_info.get("points")
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    if raw:
        m = re.search(r"\d+", str(raw))
        if m:
            return max(1, int(m.group()))
    return spec["default_points"]


def missing_fields(spec_key: str, site_info: dict[str, Any]) -> list[str]:
    spec = SPECS[spec_key]
    return [f"site_info.{f}" for f in spec["required_fields"] if not site_info.get(f)]


def questions(spec_key: str) -> dict[str, str]:
    return {f"site_info.{k}": v for k, v in SPECS[spec_key]["questions"].items()}


def build_proposal(spec_key: str, site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = SPECS[spec_key]
    site_info = site_info or {}
    points = _points(site_info, spec)
    hw_low = spec["gateway_low"] + points * spec["point_low"]
    hw_high = spec["gateway_high"] + points * spec["point_high"]
    install_low, install_high = 600 + points * 40, 1400 + points * 90
    platform_low, platform_high = 400, 1000
    amc_lo, amc_hi = spec["amc_pct"]
    project_mid = (hw_low + hw_high) / 2
    return {
        "solution_line": spec_key,
        "name": f"{spec['classification']} Package",
        "estimated_points": points,
        "currency": "EUR",
        "estimate_only": True,
        "disclaimer": PRELIMINARY,
        "professional_partner_required": spec.get("professional_partner_required", False),
        "one_time": [
            {"label": "Initial Hardware & Gateway", "amount_min": round(hw_low), "amount_max": round(hw_high), "currency": "EUR"},
            {"label": "Installation & Commissioning", "amount_min": round(install_low), "amount_max": round(install_high), "currency": "EUR"},
            {"label": "Platform Setup", "amount_min": platform_low, "amount_max": platform_high, "currency": "EUR"},
            {"label": "First-Year Support", "amount_min": 0, "amount_max": 0, "currency": "EUR", "included": True},
        ],
        "recurring_annual": [
            {"label": "Annual Maintenance Contract", "amount_min": round(project_mid * amc_lo), "amount_max": round(project_mid * amc_hi), "currency": "EUR"},
        ],
        "recommended_contract_length_years": 3,
        "recurring_revenue_carriers": spec["recurring_carriers"],
    }


def build_bom(spec_key: str, site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = SPECS[spec_key]
    site_info = site_info or {}
    points = _points(site_info, spec)

    def qty_for(q: Any) -> int:
        if q == "points":
            return points
        if q == "third":
            return max(1, points // 3)
        return int(q)

    items = []
    for row in spec["bom"]:
        category, name, q = row[0], row[1], row[2]
        notes = row[3] if len(row) > 3 else ""
        recurring = row[4] if len(row) > 4 else False
        optional = row[5] if len(row) > 5 else False
        items.append({
            "category": category, "name": name, "qty": qty_for(q),
            "need_ainerwise_supply": True, "need_installation": not recurring,
            "recurring": recurring, "optional": optional, "notes": notes,
        })
    return {"solution_line": spec_key, "estimated_points": points, "estimate_only": True, "disclaimer": PRELIMINARY, "items": items}

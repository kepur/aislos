"""Recurring-revenue scoring + lead classification (FI.6.1, FI.6.2).

Turns a lead's intake into an LTV signal the admin CRM can prioritise:
- recurring_revenue_score (0-100)
- classification (Low/Medium/High LTV, Compliance Cashflow, Consumable Cashflow,
  Enterprise Expansion)
- estimated ARR band, consumable / AMC potential, compliance risk, multi-site,
  and monitoring-point count.

Scoring weights (from the rebuild plan §13):
  reports +25, calibration +20, consumables +20, multi-site +15, 3+ years +15,
  alarm monitoring +15, strategic vertical +10, 20+ points +10, device-only -30.
"""
from __future__ import annotations

import re
from typing import Any

STRATEGIC_VERTICAL_TOKENS = (
    "pharma", "pharmaceutical", "vaccine", "medic", "food", "cold", "factory",
    "industrial", "hotel", "hospital", "lab",
)
DEVICE_ONLY_TOKENS = (
    "just buy", "only buy", "buy device", "device only", "hardware only",
    "one-time", "one time", "no service", "no maintenance", "without service",
)


def _text(lead: Any) -> str:
    site = lead.site_info_json or {}
    parts = [
        lead.project_type, lead.description, lead.budget_range,
        " ".join(lead.systems_needed_json or []),
        " ".join(str(v) for v in site.values()),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _points_count(lead: Any) -> int | None:
    site = lead.site_info_json or {}
    raw = site.get("monitoring_points")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    m = re.search(r"\d+", str(raw))
    return int(m.group()) if m else None


def score_lead(lead: Any) -> dict[str, Any]:
    """FI.6.1 + FI.6.2 — compute recurring-revenue score and classification."""
    text = _text(lead)
    site = lead.site_info_json or {}

    needs_reports = any(t in text for t in ("report", "audit", "compliance", "haccp", "gdp"))
    needs_calibration = "calibrat" in text
    has_consumables = any(t in text for t in ("consumable", "probe", "battery", "tag", "cartridge", "reagent"))
    multi_site = any(t in text for t in ("multi-site", "multi site", "sites", "branches", "locations", "stores", "outlets")) \
        or bool(site.get("multi_site"))
    long_term = bool(re.search(r"\b(3|4|5|6|7|8|10)[ -]?(year|yr)", text)) or "lifecycle" in text
    alarm_monitoring = any(t in text for t in ("alarm", "alert", "monitoring", "watch", "24/7", "outage"))
    strategic = any(t in text for t in STRATEGIC_VERTICAL_TOKENS)
    points = _points_count(lead)
    device_only = any(t in text for t in DEVICE_ONLY_TOKENS)

    score = 0
    if needs_reports:
        score += 25
    if needs_calibration:
        score += 20
    if has_consumables:
        score += 20
    if multi_site:
        score += 15
    if long_term:
        score += 15
    if alarm_monitoring:
        score += 15
    if strategic:
        score += 10
    if points and points >= 20:
        score += 10
    if device_only:
        score -= 30

    score = max(0, min(score, 100))

    classification = _classify(
        score=score, needs_reports=needs_reports, has_consumables=has_consumables,
        multi_site=multi_site, needs_calibration=needs_calibration,
    )
    compliance_risk = "high" if needs_reports and strategic else "medium" if needs_reports else "low"
    consumable_potential = "high" if has_consumables and needs_calibration else "medium" if has_consumables else "low"
    amc_potential = "high" if score >= 70 else "medium" if score >= 40 else "low"
    arr_min, arr_max = _arr_band(points, score)

    return {
        "recurring_revenue_score": score,
        "classification": classification,
        "compliance_risk_level": compliance_risk,
        "consumable_potential": consumable_potential,
        "amc_potential": amc_potential,
        "estimated_arr_min": arr_min,
        "estimated_arr_max": arr_max,
        "is_multi_site": multi_site,
        "monitoring_points_count": points,
        "signals": {
            "reports": needs_reports, "calibration": needs_calibration,
            "consumables": has_consumables, "multi_site": multi_site,
            "long_term": long_term, "alarm_monitoring": alarm_monitoring,
            "strategic_vertical": strategic, "device_only": device_only,
        },
    }


def _classify(*, score: int, needs_reports: bool, has_consumables: bool, multi_site: bool, needs_calibration: bool) -> str:
    if multi_site and score >= 60:
        return "Enterprise Expansion"
    if needs_reports and (needs_calibration or score >= 50):
        return "Compliance Cashflow"
    if has_consumables and score >= 40:
        return "Consumable Cashflow"
    if score >= 70:
        return "High LTV"
    if score >= 40:
        return "Medium LTV"
    return "Low LTV"


def _arr_band(points: int | None, score: int) -> tuple[int, int]:
    """Rough ARR band (EUR) from point count and score; estimate-only."""
    p = points or 8
    per_point_low, per_point_high = 60, 180
    base = 300
    low = base + p * per_point_low
    high = base + p * per_point_high
    if score >= 70:
        high = int(high * 1.3)
    return round(low), round(high)

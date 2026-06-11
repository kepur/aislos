"""StorageGuard (cold chain & precision storage compliance) templates.

This module keeps the StorageGuard sellable slice self-contained:

- classification keywords + missing-info questions (consumed by ai_analysis)
- a proposal template (FI.1.5) with first-year + recurring lifecycle economics
- a BOM template (FI.1.6) with monitoring points, door sensors, outage alert,
  optional local display, spare kit, and calibration line

All output is preliminary and estimate-only. Final scope, points, and pricing
require admin review, a site survey, supplier confirmation, and a signed
contract. The public site only ever shows packages / monitoring points, never
supplier cost or internal model.
"""
from __future__ import annotations

import re
from typing import Any

PRELIMINARY_NOTICE = (
    "Preliminary StorageGuard estimate. Monitoring points, calibration scope, and "
    "pricing require admin review and a site survey before any quotation."
)

CLASSIFICATION = "Cold Chain & Storage Compliance (StorageGuard)"

# Keywords that route a lead into the StorageGuard vertical.
STORAGEGUARD_KEYWORDS = (
    "storageguard",
    "cold chain",
    "cold-chain",
    "cold room",
    "cold storage",
    "coldroom",
    "refrigerat",
    "refrigerator",
    "freezer",
    "chiller room",
    "walk-in",
    "blast freezer",
    "pharma",
    "pharmaceutical",
    "vaccine",
    "medicine warehouse",
    "food storage",
    "food warehouse",
    "temperature monitoring",
    "temperature and humidity",
    "temp/humidity",
    "humidity compliance",
    "haccp",
    "gdp compliance",
    "audit report",
)

# Site-info fields StorageGuard needs before a reliable estimate.
STORAGEGUARD_REQUIRED_FIELDS = (
    "storage_type",
    "temperature_humidity",
    "compliance_use",
    "monitoring_points",
    "alert_channels",
    "calibration_cycle",
)

STORAGEGUARD_QUESTIONS = {
    "site_info.storage_type": (
        "What type of storage is this: walk-in cold room, freezer, pharmacy fridge, "
        "ambient warehouse, or laboratory storage, and how many rooms or zones?"
    ),
    "site_info.temperature_humidity": (
        "What temperature and humidity ranges must each room stay within "
        "(for example 2-8°C, -18°C, or 15-25°C with <60% RH)?"
    ),
    "site_info.compliance_use": (
        "Is this for food (HACCP) or pharmaceutical/medical (GDP) goods, and do you "
        "need audit-ready compliance reports for inspectors?"
    ),
    "site_info.monitoring_points": (
        "How many monitoring points do you need in total across all rooms, doors, and "
        "sensors?"
    ),
    "site_info.alert_channels": (
        "How should outage and out-of-range alerts reach you: SMS, Telegram, email, "
        "phone call, or in-app?"
    ),
    "site_info.calibration_cycle": (
        "How often must sensors be calibrated (for example every 12 months) and do you "
        "need power-failure / door-open alerting?"
    ),
}


def is_storageguard(category_key: str | None, text: str) -> bool:
    """Return True when a lead should be handled as StorageGuard."""
    if (category_key or "").lower() in {"storage", "storageguard", "cold_chain", "coldchain"}:
        return True
    haystack = (text or "").lower()
    return any(keyword in haystack for keyword in STORAGEGUARD_KEYWORDS)


def storageguard_missing_fields(site_info: dict[str, Any]) -> list[str]:
    """Return missing StorageGuard site-info fields, prefixed for the question map."""
    missing = []
    for field in STORAGEGUARD_REQUIRED_FIELDS:
        if not site_info.get(field):
            missing.append(f"site_info.{field}")
    return missing


def _estimate_points(site_info: dict[str, Any]) -> int:
    """Best-effort monitoring-point count from free-text intake; default 8."""
    raw = site_info.get("monitoring_points")
    if raw is None:
        return 8
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    match = re.search(r"\d+", str(raw))
    if match:
        return max(1, int(match.group()))
    return 8


def _is_pharma(site_info: dict[str, Any]) -> bool:
    blob = " ".join(
        str(site_info.get(field) or "")
        for field in ("compliance_use", "storage_type", "temperature_humidity")
    ).lower()
    return any(token in blob for token in ("pharma", "vaccine", "medic", "gdp", "lab"))


def build_storageguard_proposal(site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    """FI.1.5 — StorageGuard proposal template.

    Produces an estimate-only lifecycle cost structure: initial hardware,
    installation, platform setup, included first-year support, then the annual
    Compliance AMC, calibration, and consumables that form recurring revenue.
    """
    site_info = site_info or {}
    points = _estimate_points(site_info)
    pharma = _is_pharma(site_info)

    # Per-point hardware band (gateway amortised). Pharma needs higher-grade,
    # certified probes and tighter calibration, so the band is wider.
    point_low, point_high = (180, 320) if pharma else (120, 240)
    gateway_low, gateway_high = (650, 900) if pharma else (450, 700)

    hardware_low = gateway_low + points * point_low
    hardware_high = gateway_high + points * point_high
    install_low = 600 + points * 35
    install_high = 1200 + points * 70
    platform_low, platform_high = 400, 900

    # Recurring lifecycle lines (from year 2; first year support included).
    amc_low = 300 + points * (60 if pharma else 30)
    amc_high = 600 + points * (140 if pharma else 80)
    calibration_low = points * (40 if pharma else 25)
    calibration_high = points * (90 if pharma else 55)
    consumables_low = points * 8
    consumables_high = points * 20

    first_year_low = hardware_low + install_low + platform_low
    first_year_high = hardware_high + install_high + platform_high
    recurring_low = amc_low + calibration_low + consumables_low
    recurring_high = amc_high + calibration_high + consumables_high

    def line(label: str, low: float, high: float, note: str, included: bool = False) -> dict[str, Any]:
        return {
            "label": label,
            "amount_min": round(low),
            "amount_max": round(high),
            "currency": "EUR",
            "included": included,
            "note": note,
        }

    return {
        "solution_line": "storageguard",
        "name": "StorageGuard Compliance Monitoring Package",
        "estimated_points": points,
        "compliance_grade": "pharmaceutical_gdp" if pharma else "food_haccp",
        "currency": "EUR",
        "estimate_only": True,
        "disclaimer": PRELIMINARY_NOTICE,
        "one_time": [
            line(
                "Initial Hardware & Gateway",
                hardware_low,
                hardware_high,
                "Gateway plus temperature/humidity and door monitoring points.",
            ),
            line(
                "Installation & Commissioning",
                install_low,
                install_high,
                "Mounting, wiring/wireless setup, threshold configuration, and verification.",
            ),
            line(
                "Platform Setup",
                platform_low,
                platform_high,
                "Cloud workspace, rooms, thresholds, alert routing, and report templates.",
            ),
            line(
                "First-Year Support",
                0,
                0,
                "Included: remote assurance, alert tuning, and supplier warranty coordination.",
                included=True,
            ),
        ],
        "recurring_annual": [
            line(
                "Annual Compliance AMC (from year 2)",
                amc_low,
                amc_high,
                "Remote monitoring, alarm watch, monthly/annual compliance reports, system health.",
            ),
            line(
                "Annual Calibration",
                calibration_low,
                calibration_high,
                "Scheduled probe calibration with certificate for audit traceability.",
            ),
            line(
                "Consumables (batteries / probes)",
                consumables_low,
                consumables_high,
                "Sensor batteries and probe replacement, billed as used or bundled into AMC.",
            ),
        ],
        "estimated_first_year_total": {
            "amount_min": round(first_year_low),
            "amount_max": round(first_year_high),
            "currency": "EUR",
        },
        "estimated_annual_recurring_total": {
            "amount_min": round(recurring_low),
            "amount_max": round(recurring_high),
            "currency": "EUR",
        },
        "recommended_contract_length_years": 3,
        "recurring_revenue_carriers": [
            "platform_fee",
            "compliance_report",
            "calibration",
            "consumable_replacement",
            "alarm_monitoring",
            "annual_maintenance_contract",
        ],
    }


def build_storageguard_bom(site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    """FI.1.6 — StorageGuard BOM template.

    Returns editable BOM rows (gateway, monitoring points, door sensors, outage
    alert, optional local display, spare kit, calibration line). Public-facing
    fields only — no supplier model or cost. Admin can refine into a real BOM.
    """
    site_info = site_info or {}
    points = _estimate_points(site_info)
    pharma = _is_pharma(site_info)
    # Roughly one door sensor per two monitoring rooms; at least one.
    door_sensors = max(1, points // 3)
    # Spare kit ~ 15% of points (storage probes are higher-attrition), min 1.
    spare_kit = max(1, round(points * 0.15))

    def row(
        category: str,
        name: str,
        qty: int,
        *,
        need_installation: bool = True,
        recurring: bool = False,
        optional: bool = False,
        notes: str = "",
    ) -> dict[str, Any]:
        return {
            "category": category,
            "name": name,
            "qty": qty,
            "need_ainerwise_supply": True,
            "need_installation": need_installation,
            "recurring": recurring,
            "optional": optional,
            "notes": notes,
        }

    items = [
        row(
            "gateway",
            "StorageGuard Monitoring Gateway",
            1,
            notes="Edge gateway with local buffering and cellular/Wi-Fi uplink for outage resilience.",
        ),
        row(
            "monitoring_point",
            "Temperature / Humidity Monitoring Point",
            points,
            notes=(
                "Certified probes for pharmaceutical/GDP storage." if pharma
                else "Food-grade temperature/humidity probes for HACCP storage."
            ),
        ),
        row(
            "door_sensor",
            "Cold Room Door Event Sensor",
            door_sensors,
            notes="Door open/close logging and door-ajar alerting.",
        ),
        row(
            "outage_alert",
            "Power Outage / Connectivity Alert Module",
            1,
            notes="Backup-powered outage detection so alerts fire even on mains failure.",
        ),
        row(
            "local_display",
            "Local Status Display (optional)",
            1,
            optional=True,
            notes="On-site readout of current readings and alarm state for staff and inspectors.",
        ),
        row(
            "spare_kit",
            "Spare Sensor & Battery Kit",
            spare_kit,
            need_installation=False,
            notes="Fast-replacement pool to keep compliance monitoring uninterrupted.",
        ),
        row(
            "calibration",
            "Annual Calibration & Certificate (per point)",
            points,
            need_installation=False,
            recurring=True,
            notes="Recurring calibration service line with audit-ready certificate.",
        ),
    ]

    return {
        "solution_line": "storageguard",
        "estimated_points": points,
        "estimate_only": True,
        "disclaimer": PRELIMINARY_NOTICE,
        "items": items,
    }

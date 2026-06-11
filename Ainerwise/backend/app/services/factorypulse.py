"""FactoryPulse (industrial OEE / energy / predictive maintenance) templates.

IND.9 — default industrial BOM template: OT gateway, machine energy meters,
PLC/SCADA connector, compressor/chiller meters, optional edge AI box, and a
service SLA line. Public-safe (no supplier cost/model). Estimate-only.
"""
from __future__ import annotations

import re
from typing import Any

PRELIMINARY_NOTICE = (
    "Preliminary FactoryPulse estimate. Machine count, protocols, OT safety, and pricing "
    "require engineering review, an OT/IT safety assessment, and a signed contract."
)

CLASSIFICATION_MATCH = "Industrial Factory"  # substring of the AI classification


def _estimate_machines(site_info: dict[str, Any]) -> int:
    raw = site_info.get("production_machines") or site_info.get("production") or site_info.get("machines")
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    if raw:
        m = re.findall(r"\d+", str(raw))
        if m:
            return max(1, sum(int(x) for x in m[:3]))  # rough: add the first few counts
    return 8


def build_factorypulse_bom(site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    """IND.9 — industrial BOM template scaled by machine count."""
    site_info = site_info or {}
    machines = _estimate_machines(site_info)
    utility_meters = max(2, machines // 4)  # compressor/chiller/main feeders

    def row(category: str, name: str, qty: int, *, need_installation: bool = True, recurring: bool = False, optional: bool = False, notes: str = "") -> dict[str, Any]:
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
        row("ot_gateway", "OT Data Gateway (PLC/SCADA/OPC-UA)", 1,
            notes="OT/IT isolated gateway bridging PLC, SCADA, MES and robots into the platform."),
        row("machine_meter", "Non-Invasive Machine Energy Meter", machines,
            notes="Per-machine current/power and run/stop monitoring (non-invasive CT)."),
        row("utility_meter", "Compressor / Chiller / Feeder Energy Meter", utility_meters,
            notes="Energy meters for compressed air, chillers, and main feeders."),
        row("vfd_module", "VFD / Motor Monitoring Module", max(1, machines // 3),
            notes="Vibration, temperature, energy and run-hours for predictive maintenance."),
        row("scada_connector", "PLC / SCADA / Robot OPC-UA Connector", 1,
            notes="Protocol connector with OT network isolation and vendor permissions."),
        row("edge_ai_box", "Industrial Edge AI Box (optional)", 1, optional=True,
            notes="On-prem OEE/anomaly compute for low-latency, data-sovereign deployments."),
        row("service_sla", "OEE Algorithm + SLA Subscription (per year)", 1,
            need_installation=False, recurring=True,
            notes="OEE dashboard, anomaly/algorithm subscription, point expansion, and SLA response."),
    ]
    return {
        "solution_line": "factorypulse",
        "estimated_machines": machines,
        "estimate_only": True,
        "disclaimer": PRELIMINARY_NOTICE,
        "items": items,
    }


def build_factorypulse_proposal(site_info: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lightweight industrial proposal: initial integration, pilot line, recurring SLA."""
    site_info = site_info or {}
    machines = _estimate_machines(site_info)
    hw_low = 6000 + machines * 350
    hw_high = 12000 + machines * 800
    integ_low, integ_high = 4000, 18000
    sla_low = 2000 + machines * 120
    sla_high = 6000 + machines * 320
    return {
        "solution_line": "factorypulse",
        "name": "FactoryPulse OEE & Energy Package",
        "estimated_machines": machines,
        "currency": "EUR",
        "estimate_only": True,
        "disclaimer": PRELIMINARY_NOTICE,
        "one_time": [
            {"label": "Hardware & Gateways", "amount_min": round(hw_low), "amount_max": round(hw_high), "currency": "EUR"},
            {"label": "OT Integration & Pilot Line", "amount_min": integ_low, "amount_max": integ_high, "currency": "EUR"},
        ],
        "recurring_annual": [
            {"label": "OEE Algorithm + SLA Subscription", "amount_min": round(sla_low), "amount_max": round(sla_high), "currency": "EUR"},
        ],
        "recommended_contract_length_years": 5,
        "recurring_revenue_carriers": ["algorithm_subscription", "point_expansion", "annual_inspection", "report_export", "amc"],
    }

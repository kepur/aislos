"""Project finance math + quote economics helpers (FI.4.4, FI.4.6).

- compute_finance: gross profit/margin, first-year & annual recurring profit,
  and 3/5/8-year LTV from a ProjectFinance input.
- compute_platform_fee: apply a PlatformFeeRule to a project value.
- build_customer_line_items: package a quote for the customer without exposing
  supplier cost or internal model.
"""
from __future__ import annotations

from typing import Any

# Cost components summed into direct cost.
_COST_FIELDS = (
    "supplier_cost", "shipping_cost", "customs_cost", "local_installer_cost",
    "labor_cost", "travel_cost", "spare_parts_cost", "warranty_reserve_cost",
)
_ONE_TIME_REVENUE_FIELDS = (
    "hardware_revenue", "design_fee", "installation_fee", "integration_fee",
    "platform_fee", "project_management_fee",
)
_RECURRING_REVENUE_FIELDS = (
    "consumable_revenue_estimate", "calibration_revenue_estimate",
    "report_revenue_estimate", "alarm_monitoring_revenue_estimate",
)


def _g(data: Any, field: str) -> float:
    if isinstance(data, dict):
        return float(data.get(field) or 0)
    return float(getattr(data, field, 0) or 0)


def compute_finance(data: Any) -> dict[str, float]:
    """FI.4.6 — derive margin and LTV metrics from finance inputs.

    `data` may be a ProjectFinance ORM object or a plain dict of inputs.
    Returns a dict of the derived fields (all rounded to 2dp).
    """
    direct_cost = sum(_g(data, f) for f in _COST_FIELDS)
    one_time_revenue = sum(_g(data, f) for f in _ONE_TIME_REVENUE_FIELDS)
    contract_total = _g(data, "contract_total") or one_time_revenue

    recurring_base = sum(_g(data, f) for f in _RECURRING_REVENUE_FIELDS)
    first_year_recurring = _g(data, "amc_fee_year_1") + recurring_base
    annual_recurring_revenue = _g(data, "amc_fee_annual") + recurring_base
    annual_service_cost = _g(data, "annual_service_cost")

    gross_profit = contract_total - direct_cost
    gross_margin_percent = (gross_profit / contract_total * 100) if contract_total else 0.0

    first_year_revenue = contract_total + first_year_recurring
    first_year_profit = first_year_revenue - direct_cost - annual_service_cost
    annual_recurring_profit = annual_recurring_revenue - annual_service_cost

    ltv_3 = first_year_profit + 2 * annual_recurring_profit
    ltv_5 = first_year_profit + 4 * annual_recurring_profit
    ltv_8 = first_year_profit + 7 * annual_recurring_profit

    def r(x: float) -> float:
        return round(x, 2)

    return {
        "direct_cost": r(direct_cost),
        "contract_total": r(contract_total),
        "gross_profit": r(gross_profit),
        "gross_margin_percent": r(gross_margin_percent),
        "first_year_revenue": r(first_year_revenue),
        "first_year_profit": r(first_year_profit),
        "annual_recurring_revenue": r(annual_recurring_revenue),
        "annual_recurring_profit": r(annual_recurring_profit),
        "ltv_3_year": r(ltv_3),
        "ltv_5_year": r(ltv_5),
        "ltv_8_year": r(ltv_8),
    }


def compute_platform_fee(rule: Any, project_value: float) -> dict[str, Any]:
    """FI.4.2 — apply a platform fee rule (fixed / percentage / hybrid)."""
    fee_type = _s(rule, "fee_type") or "percentage"
    percentage = _g(rule, "percentage")
    fixed_fee = _g(rule, "fixed_fee")
    min_fee = getattr(rule, "min_fee", None) if not isinstance(rule, dict) else rule.get("min_fee")
    max_fee = getattr(rule, "max_fee", None) if not isinstance(rule, dict) else rule.get("max_fee")

    if fee_type == "fixed":
        fee = fixed_fee
    elif fee_type == "hybrid":
        fee = fixed_fee + project_value * percentage
    else:
        fee = project_value * percentage

    if min_fee is not None:
        fee = max(fee, float(min_fee))
    if max_fee is not None:
        fee = min(fee, float(max_fee))
    return {"fee_type": fee_type, "platform_fee": round(fee, 2)}


def _s(data: Any, field: str) -> str | None:
    if isinstance(data, dict):
        return data.get(field)
    return getattr(data, field, None)


# --- FI.4.4 customer-facing line items --------------------------------------

# Order matters: this is the customer-facing package breakdown. No supplier cost
# or internal model is ever included here.
CUSTOMER_PACKAGE_LABELS = [
    ("hardware_package", "Hardware Package"),
    ("design", "Design & Engineering"),
    ("installation", "Installation & Commissioning"),
    ("integration", "System Integration"),
    ("platform", "Platform Setup"),
    ("management", "Project Management"),
    ("spare_reserve", "Spare Parts Reserve"),
    ("first_year_support", "First-Year Support"),
    ("optional_amc", "Optional: Annual Maintenance Contract"),
    ("optional_fast_replacement", "Optional: Fast Replacement Plan"),
]


# FI.4.5 — admin-only internal economics fields (never customer-facing).
INTERNAL_ECONOMICS_FIELDS = (
    "supplier", "real_model", "unit_cost", "lead_time_days", "warranty",
    "margin_percent", "alternatives", "risk", "recommended_spares",
)


def internal_economics_scaffold() -> dict[str, Any]:
    """FI.4.5 — empty internal-economics template for admins to populate."""
    return {
        "line_items": [],
        "fields": list(INTERNAL_ECONOMICS_FIELDS),
        "note": "Admin-only. Supplier cost, real model, and margin are never exposed on the customer quote or PDF.",
    }


def build_customer_line_items(amounts: dict[str, float], currency: str = "EUR") -> list[dict[str, Any]]:
    """FI.4.4 — turn component amounts into customer-facing packaged line items.

    `amounts` maps package keys (see CUSTOMER_PACKAGE_LABELS) to amounts. Keys
    starting with "optional_" are marked optional. Zero/missing amounts are
    skipped except optional items, which are kept with an "On request" note.
    """
    items = []
    for key, label in CUSTOMER_PACKAGE_LABELS:
        amount = float(amounts.get(key) or 0)
        optional = key.startswith("optional_")
        included = key == "first_year_support" and amount == 0
        if amount == 0 and not optional and not included:
            continue
        items.append({
            "key": key,
            "label": label,
            "amount": round(amount, 2),
            "currency": currency,
            "optional": optional,
            "included": included,
            "display": "Included" if included else ("On request" if optional and amount == 0 else f"{amount:,.2f} {currency}"),
        })
    return items

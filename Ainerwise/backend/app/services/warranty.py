"""Warranty coverage evaluator (FI.3.5).

Resolves how a ticket / fault should be handled: pass-through supplier warranty,
AinerWise managed warranty, AMC coverage, fast replacement, or paid service.
This is the decision the admin needs when triaging a ticket.
"""
from __future__ import annotations

from typing import Any

# Causes that are always excluded from warranty / AMC and become paid service.
EXCLUDED_CAUSES = {
    "misuse", "accidental_damage", "physical_damage", "water_ingress",
    "lightning", "surge", "tamper", "unauthorized_modification",
    "third_party_damage", "end_of_life",
}


def evaluate_coverage(
    *,
    cause: str | None = None,
    amc_covered: bool = False,
    within_supplier_warranty: bool = False,
    managed_warranty: bool = False,
    fast_replacement: bool = False,
) -> dict[str, Any]:
    """FI.3.5 — Resolve coverage for a fault.

    Returns coverage_type, whether the customer pays, the recommended action,
    and a short explanation. Order of precedence: excluded cause > AMC >
    fast replacement > managed warranty > pass-through supplier warranty > paid.
    """
    normalized_cause = (cause or "").lower().strip()

    if normalized_cause in EXCLUDED_CAUSES:
        return _result(
            "paid_service", True,
            "Quote a paid repair/replacement.",
            f"Cause '{normalized_cause}' is excluded from warranty and AMC coverage.",
        )

    if amc_covered:
        return _result(
            "amc", False,
            "Handle under the active AMC; log against included visits/quota.",
            "Covered by the customer's Annual Maintenance Contract.",
        )

    if fast_replacement:
        return _result(
            "fast_replacement", False,
            "Dispatch a replacement from the fast-replacement pool within the SLA.",
            "Covered by the customer's paid Fast Replacement Plan.",
        )

    if managed_warranty:
        return _result(
            "managed_warranty", False,
            "AinerWise replaces/repairs for the customer, then claims from the supplier.",
            "Covered by AinerWise Managed Warranty (single window for the customer).",
        )

    if within_supplier_warranty:
        return _result(
            "pass_through_warranty", False,
            "Coordinate a supplier warranty claim; customer pays only out-of-scope labor/shipping per terms.",
            "Hardware is within the original supplier warranty period.",
        )

    return _result(
        "paid_service", True,
        "Quote a paid service ticket.",
        "Outside supplier warranty and not covered by AMC / managed warranty / fast replacement.",
    )


def _result(coverage_type: str, customer_pays: bool, action: str, note: str) -> dict[str, Any]:
    return {
        "coverage_type": coverage_type,
        "customer_pays": customer_pays,
        "recommended_action": action,
        "note": note,
    }

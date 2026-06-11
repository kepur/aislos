"""Procurement confidence scoring and gate classification (Decimal, min aggregation)."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.models.portal_policy import FROZEN_CONFIDENCE_GATE
from app.models.procurement import BoqItem, ProcurementProjectFact

THREE_DP = Decimal("0.001")
ASK_BELOW = Decimal(FROZEN_CONFIDENCE_GATE["ask_below"])
REVIEW_ABOVE = Decimal(FROZEN_CONFIDENCE_GATE["review_above"])
FREEZE_MIN_CRITICAL = Decimal(FROZEN_CONFIDENCE_GATE["freeze_min_critical_confidence"])


def quantize_score(value: Decimal) -> Decimal:
    return value.quantize(THREE_DP, rounding=ROUND_HALF_UP)


def effective_fact_confidence(fact: ProcurementProjectFact) -> Decimal:
    if fact.user_confirmed:
        return Decimal("1")
    return Decimal(fact.confidence)


def effective_item_confidence(item: BoqItem) -> Decimal:
    return Decimal(item.confidence)


def compute_facts_score(facts: list[ProcurementProjectFact]) -> Decimal:
    required = [f for f in facts if f.required]
    if not required:
        return Decimal("0")
    total_weight = sum(Decimal(f.weight) for f in required)
    if total_weight <= 0:
        return Decimal("0")
    weighted = sum(Decimal(f.weight) * effective_fact_confidence(f) for f in required)
    return quantize_score(weighted / total_weight)


def compute_boq_score(items: list[BoqItem]) -> Decimal:
    included = [i for i in items if i.included]
    if not included:
        return Decimal("0")
    total_weight = sum(Decimal(i.weight) for i in included)
    if total_weight <= 0:
        return Decimal("0")
    weighted = sum(Decimal(i.weight) * effective_item_confidence(i) for i in included)
    return quantize_score(weighted / total_weight)


def compute_overall_confidence(facts_score: Decimal, boq_score: Decimal) -> Decimal:
    """Overall confidence is the minimum of facts and BOQ scores — never averaged."""
    return quantize_score(min(facts_score, boq_score))


def classify_project_status(overall_confidence: Decimal) -> str:
    """Map overall confidence to procurement project status after analyze."""
    if overall_confidence < ASK_BELOW:
        return "needs_information"
    if overall_confidence <= REVIEW_ABOVE:
        return "estimate_ready"
    return "review_ready"

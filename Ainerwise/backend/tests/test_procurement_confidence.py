"""C05: Decimal confidence gate and min(facts, boq) aggregation."""
from decimal import Decimal

from app.models.procurement import BoqItem, ProcurementProjectFact
from app.services.procurement_confidence import (
    ASK_BELOW,
    REVIEW_ABOVE,
    classify_project_status,
    compute_boq_score,
    compute_facts_score,
    compute_overall_confidence,
    effective_fact_confidence,
)


def _fact(*, required=True, critical=False, weight="1", confidence="0.9", confirmed=False):
    return ProcurementProjectFact(
        project_id=__import__("uuid").uuid4(),
        template_key="k",
        label="K",
        required=required,
        critical=critical,
        weight=Decimal(weight),
        confidence=Decimal(confidence),
        user_confirmed=confirmed,
        source="system",
    )


def _item(*, confidence="0.9", weight="1", included=True):
    return BoqItem(
        boq_version_id=__import__("uuid").uuid4(),
        category="x",
        name="item",
        qty=Decimal("1"),
        unit="ea",
        confidence=Decimal(confidence),
        weight=Decimal(weight),
        included=included,
        source="system",
    )


def test_effective_confidence_user_confirmed_is_one():
    f = _fact(confidence="0.3", confirmed=True)
    assert effective_fact_confidence(f) == Decimal("1")


def test_overall_uses_min_not_average():
    facts = [_fact(confidence="0.9")]
    items = [_item(confidence="0.5")]
    fs = compute_facts_score(facts)
    bs = compute_boq_score(items)
    overall = compute_overall_confidence(fs, bs)
    assert overall == bs
    assert overall < fs


def test_classify_boundary_599_needs_information():
    assert classify_project_status(Decimal("0.599")) == "needs_information"


def test_classify_boundary_600_estimate_ready():
    assert classify_project_status(Decimal("0.600")) == "estimate_ready"


def test_classify_boundary_800_estimate_ready():
    assert classify_project_status(Decimal("0.800")) == "estimate_ready"


def test_classify_boundary_801_review_ready():
    assert classify_project_status(Decimal("0.801")) == "review_ready"


def test_threshold_constants():
    assert ASK_BELOW == Decimal("0.600")
    assert REVIEW_ABOVE == Decimal("0.800")

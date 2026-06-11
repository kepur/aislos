"""C05: orchestrator procurement_analyze validation."""
from app.workflows.procurement_analyze import _fallback_analyze, validate_analyze_output


def test_fallback_has_required_keys():
    data = _fallback_analyze({"project_type": "villa_smart_home", "title": "Villa"})
    assert validate_analyze_output(data) == []


def test_fallback_low_confidence_empty_boq():
    data = _fallback_analyze({"test_scenario": "low", "title": "X"})
    assert data["boq_items"] == []
    assert data["missing_questions"]


def test_validate_rejects_missing_tiers():
    data = _fallback_analyze({"title": "X"})
    data["boq_items"][0]["options"] = []
    assert validate_analyze_output(data)

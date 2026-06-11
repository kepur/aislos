"""Tests for the StorageGuard sellable slice (FI.1.3 - FI.1.6).

Covers rule-based classification, missing-info prompts, and the proposal / BOM
templates. These exercise pure logic without touching the database.
"""
from app.models.lead import Lead
from app.services import storageguard
from app.services.ai_analysis import _classify, _missing_fields


def _storage_lead(**site_info) -> Lead:
    return Lead(
        project_type="Cold Chain / Storage (StorageGuard)",
        country="Serbia",
        budget_range="6k-18k",
        systems_needed_json=["StorageGuard", "Temperature & Humidity Monitoring"],
        description="Pharmaceutical cold storage compliance monitoring",
        contact_email="ops@pharma.example",
        site_info_json={"category_key": "storage", **site_info},
    )


# --- FI.1.4 classification --------------------------------------------------

def test_classify_detects_storageguard_by_category_key():
    classification, complexity = _classify("", [], category_key="storage")
    assert classification == storageguard.CLASSIFICATION
    assert complexity == "medium"


def test_classify_detects_storageguard_by_keywords():
    text = "we run a food cold storage facility and need temperature monitoring"
    classification, _ = _classify(text, [])
    assert classification == storageguard.CLASSIFICATION


def test_classify_storage_takes_precedence_over_warehouse_factory():
    # "warehouse" alone would look industrial; pharma cold storage must win.
    text = "pharmaceutical warehouse cold room temperature and humidity compliance"
    classification, _ = _classify(text, [])
    assert classification == storageguard.CLASSIFICATION


def test_classify_non_storage_unaffected():
    classification, _ = _classify("hotel guest room control", [])
    assert classification != storageguard.CLASSIFICATION


# --- FI.1.4 missing-info ----------------------------------------------------

def test_missing_fields_requests_storage_specifics():
    lead = _storage_lead()  # no storage details provided
    missing = _missing_fields(lead)
    for field in storageguard.STORAGEGUARD_REQUIRED_FIELDS:
        assert f"site_info.{field}" in missing


def test_missing_fields_cleared_when_storage_details_present():
    lead = _storage_lead(
        storage_type="3 cold rooms",
        temperature_humidity="2-8C",
        compliance_use="pharma GDP audit reports",
        monitoring_points="24",
        alert_channels="telegram, email",
        calibration_cycle="annual, 3 year term",
    )
    missing = _missing_fields(lead)
    assert not any(m.startswith("site_info.storage") for m in missing)
    assert "site_info.monitoring_points" not in missing


# --- FI.1.5 proposal template -----------------------------------------------

def test_proposal_template_structure():
    proposal = storageguard.build_storageguard_proposal({"monitoring_points": "20"})
    assert proposal["solution_line"] == "storageguard"
    assert proposal["estimate_only"] is True
    one_time_labels = {line["label"] for line in proposal["one_time"]}
    assert "Initial Hardware & Gateway" in one_time_labels
    assert "Installation & Commissioning" in one_time_labels
    assert "Platform Setup" in one_time_labels
    assert "First-Year Support" in one_time_labels
    recurring_labels = {line["label"] for line in proposal["recurring_annual"]}
    assert any("Compliance AMC" in label for label in recurring_labels)
    assert any("Calibration" in label for label in recurring_labels)
    assert any("Consumables" in label for label in recurring_labels)
    assert proposal["recommended_contract_length_years"] == 3
    # First-year support line is included (zero cost) not billed.
    support = next(line for line in proposal["one_time"] if line["label"] == "First-Year Support")
    assert support["included"] is True


def test_proposal_scales_with_points():
    small = storageguard.build_storageguard_proposal({"monitoring_points": "5"})
    large = storageguard.build_storageguard_proposal({"monitoring_points": "50"})
    assert (
        large["estimated_first_year_total"]["amount_min"]
        > small["estimated_first_year_total"]["amount_min"]
    )
    assert (
        large["estimated_annual_recurring_total"]["amount_min"]
        > small["estimated_annual_recurring_total"]["amount_min"]
    )


def test_proposal_defaults_points_when_unknown():
    proposal = storageguard.build_storageguard_proposal({})
    assert proposal["estimated_points"] == 8


def test_proposal_pharma_grade_detected():
    proposal = storageguard.build_storageguard_proposal(
        {"monitoring_points": "10", "compliance_use": "pharmaceutical GDP"}
    )
    assert proposal["compliance_grade"] == "pharmaceutical_gdp"


# --- FI.1.6 BOM template ----------------------------------------------------

def test_bom_template_contains_required_lines():
    bom = storageguard.build_storageguard_bom({"monitoring_points": "12"})
    categories = {item["category"] for item in bom["items"]}
    for expected in {
        "gateway",
        "monitoring_point",
        "door_sensor",
        "outage_alert",
        "local_display",
        "spare_kit",
        "calibration",
    }:
        assert expected in categories
    points_row = next(i for i in bom["items"] if i["category"] == "monitoring_point")
    assert points_row["qty"] == 12
    # The local display is optional and the calibration line is recurring.
    display = next(i for i in bom["items"] if i["category"] == "local_display")
    assert display["optional"] is True
    calibration = next(i for i in bom["items"] if i["category"] == "calibration")
    assert calibration["recurring"] is True


def test_bom_does_not_expose_supplier_cost_or_model():
    bom = storageguard.build_storageguard_bom({"monitoring_points": "10"})
    for item in bom["items"]:
        assert "cost" not in item
        assert "supplier" not in item
        assert "internal_model" not in item


# --- FI.1.7 demo buyer project plan -----------------------------------------

def test_storageguard_demo_plan_has_all_required_elements():
    from scripts.create_demo_buyer import STORAGEGUARD_DEMO_PLAN as plan

    assert plan["solution_line"] == "storageguard"
    assert plan["sample"] is True
    # points, compliance risk, initial cost, ARR, AMC, calibration due, alert flow, report
    assert plan["monitoring_points"]["total"] == 24
    assert plan["compliance"]["risk_level"] == "high"
    econ = plan["economics"]
    assert econ["initial_cost_min"] and econ["initial_cost_max"]
    assert econ["arr_min"] and econ["arr_max"]
    assert "AMC" in econ["amc_plan"]
    assert plan["calibration"]["next_due"] == "2027-01-15"
    assert len(plan["alert_flow"]) >= 3
    report = plan["report_preview"]
    assert report["sample"] is True
    assert len(report["rooms"]) == 3
    assert all("compliance_pct" in r for r in report["rooms"])

"""Tests for lifecycle operations + recurring-revenue scoring (FI.3, FI.6.1/6.2)."""
from app.main import app
from app.models.lead import Lead
from app.services import amc, recurring_revenue, spare_parts, warranty


# --- FI.3.2 AMC pricing -----------------------------------------------------

def test_amc_percentage_pricing_by_solution_line():
    q = amc.amc_annual_fee(mode="percentage", solution_line="storageguard", project_value=10000)
    assert q["amount_min"] == 800  # 8%
    assert q["amount_max"] == 1800  # 18%
    assert q["estimate_only"] is True


def test_amc_point_based_pricing():
    q = amc.amc_annual_fee(mode="point_based", points={"temperature": 10, "gateway": 1})
    # base 300 + temp(30-80)*10 + gateway(50-200)*1
    assert q["amount_min"] == 300 + 300 + 50
    assert q["amount_max"] == 300 + 800 + 200
    assert len(q["breakdown"]) == 2


def test_amc_service_level_pricing_uses_catalog_band():
    q = amc.amc_annual_fee(mode="service_level", tier="compliance")
    assert q["tier"] == "compliance"
    assert q["amount_min"] == 900 and q["amount_max"] == 3500


def test_amc_catalog_has_all_tiers():
    tiers = {t["tier"] for t in amc.AMC_CATALOG}
    assert {"basic", "compliance", "commercial", "premium", "enterprise"}.issubset(tiers)
    assert amc.BASELINE_REMOTE_ASSURANCE["years"] == 3


# --- FI.3.3 / FI.3.4 spare parts -------------------------------------------

def test_spare_kit_recommendation_scales_and_costs():
    res = spare_parts.recommend_spare_kit(
        [{"category": "temperature", "qty": 20, "unit_cost": 100}], plan="shared_pool"
    )
    line = res["lines"][0]
    assert line["recommended_spares_min"] >= 2  # >=10%
    assert res["reserve_cost_pct_min"] is not None
    assert res["plan"] == "shared_pool"


def test_fast_replacement_eligibility():
    assert spare_parts.fast_replacement_eligible("temperature") is True
    assert spare_parts.fast_replacement_eligible("critical_gateway") is False


# --- FI.3.5 warranty coverage evaluator ------------------------------------

def test_coverage_excluded_cause_is_paid():
    r = warranty.evaluate_coverage(cause="water_ingress", within_supplier_warranty=True)
    assert r["coverage_type"] == "paid_service"
    assert r["customer_pays"] is True


def test_coverage_precedence_amc_over_warranty():
    r = warranty.evaluate_coverage(amc_covered=True, within_supplier_warranty=True)
    assert r["coverage_type"] == "amc"
    assert r["customer_pays"] is False


def test_coverage_pass_through_when_only_supplier_warranty():
    r = warranty.evaluate_coverage(within_supplier_warranty=True)
    assert r["coverage_type"] == "pass_through_warranty"


def test_coverage_paid_when_nothing_applies():
    r = warranty.evaluate_coverage()
    assert r["coverage_type"] == "paid_service"
    assert r["customer_pays"] is True


# --- FI.6.1 / FI.6.2 recurring-revenue scoring -----------------------------

def _lead(desc: str, **site) -> Lead:
    return Lead(project_type="x", description=desc, systems_needed_json=[], site_info_json=site)


def test_scoring_compliance_cashflow():
    lead = _lead(
        "Cold storage needing HACCP audit compliance reports and annual calibration of probes",
        monitoring_points="24", category_key="storage",
    )
    res = recurring_revenue.score_lead(lead)
    assert res["recurring_revenue_score"] >= 70
    assert res["classification"] in ("Compliance Cashflow", "Enterprise Expansion", "High LTV")
    assert res["monitoring_points_count"] == 24
    assert res["compliance_risk_level"] in ("medium", "high")


def test_scoring_device_only_penalty():
    lead = _lead("Customer only wants to buy the device, one-time, no service or maintenance")
    res = recurring_revenue.score_lead(lead)
    assert res["recurring_revenue_score"] <= 10
    assert res["classification"] == "Low LTV"
    assert res["signals"]["device_only"] is True


def test_scoring_multi_site_enterprise():
    lead = _lead(
        "Compliance reports, calibration, consumable probes, alarm monitoring across multiple sites and branches, 5-year contract",
        monitoring_points="40",
    )
    res = recurring_revenue.score_lead(lead)
    assert res["is_multi_site"] is True
    assert res["classification"] == "Enterprise Expansion"
    assert res["estimated_arr_max"] > res["estimated_arr_min"]


# --- route registration -----------------------------------------------------

def test_lifecycle_ops_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/amc-catalog",
        "/api/v1/amc-catalog/quote",
        "/api/v1/spare-kit/recommend",
        "/api/v1/fast-replacement-plan",
        "/api/v1/warranty/evaluate-coverage",
        "/api/v1/contract-boundary-template",
        "/api/v1/lifecycle/alerts",
    ):
        assert p in paths, p

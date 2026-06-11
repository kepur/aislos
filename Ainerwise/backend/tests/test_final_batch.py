"""Tests for IND.8, IND.9, 5.14, 5.15, FI.7."""
import asyncio

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lead import Lead
from app.services import ai_graph, factorypulse, lifecycle_lines
from app.services.ai_analysis import _classify


# --- FI.7 KitchenGuard / AquaGuard / EnergyGuard ----------------------------

def test_lifecycle_lines_classification():
    assert _classify("commercial kitchen gas leak and CO monitoring", [])[0] == lifecycle_lines.SPECS["kitchenguard"]["classification"]
    assert _classify("factory effluent wastewater pH and COD discharge compliance", [])[0] == lifecycle_lines.SPECS["aquaguard"]["classification"]
    assert _classify("solar pv inverter battery storage energy monitoring", [])[0] == lifecycle_lines.SPECS["energyguard"]["classification"]


def test_lifecycle_lines_proposal_and_bom():
    for line in ("kitchenguard", "aquaguard", "energyguard"):
        prop = lifecycle_lines.build_proposal(line, {"monitoring_points": "10"})
        assert prop["solution_line"] == line and prop["estimate_only"]
        assert any(li["included"] for li in prop["one_time"] if li["label"] == "First-Year Support")
        bom = lifecycle_lines.build_bom(line, {"monitoring_points": "10"})
        assert any(i["category"] == "gateway" for i in bom["items"])
        for i in bom["items"]:
            assert "cost" not in i and "supplier" not in i
    assert lifecycle_lines.build_proposal("aquaguard", {})["professional_partner_required"] is True


def test_lifecycle_lines_detect_and_missing():
    assert lifecycle_lines.detect("kitchen", "") == "kitchenguard"
    assert lifecycle_lines.detect(None, "wastewater discharge cod compliance") == "aquaguard"
    missing = lifecycle_lines.missing_fields("kitchenguard", {})
    assert "site_info.gas_type" in missing


# --- IND.9 FactoryPulse BOM template ----------------------------------------

def test_factorypulse_bom_template():
    bom = factorypulse.build_factorypulse_bom({"production_machines": "12 CNC machines"})
    cats = {i["category"] for i in bom["items"]}
    for expected in ("ot_gateway", "machine_meter", "utility_meter", "scada_connector", "service_sla"):
        assert expected in cats
    meter = next(i for i in bom["items"] if i["category"] == "machine_meter")
    assert meter["qty"] == 12
    edge = next(i for i in bom["items"] if i["category"] == "edge_ai_box")
    assert edge["optional"] is True
    for item in bom["items"]:
        assert "cost" not in item and "supplier" not in item  # no leakage


def test_factorypulse_proposal_scales():
    small = factorypulse.build_factorypulse_proposal({"production_machines": "2"})
    large = factorypulse.build_factorypulse_proposal({"production_machines": "40"})
    assert large["one_time"][0]["amount_min"] > small["one_time"][0]["amount_min"]


# --- 5.14 graph orchestrator ------------------------------------------------

def test_graph_produces_equivalent_output():
    """The graph output must match the rule-based MVP on key fields, plus a trace."""
    from app.services.ai_analysis import build_lead_analysis

    async def _run():
        await engine.dispose()
        lead = Lead(
            project_type="Cold Chain / Storage (StorageGuard)",
            country="Serbia", budget_range="6k-18k",
            systems_needed_json=["StorageGuard"],
            description="Pharmaceutical cold storage compliance, calibration, audit reports",
            site_info_json={"category_key": "storage", "monitoring_points": "24"},
        )
        async with async_session_factory() as db:
            mvp = await build_lead_analysis(db, lead)
            graph = await ai_graph.run_lead_graph(db, lead)
        return mvp, graph

    mvp, graph = asyncio.run(_run())
    assert graph["classification"] == mvp["classification"]
    assert graph["solution_line"] == mvp["solution_line"] == "storageguard"
    assert graph["recurring_revenue"]["recurring_revenue_score"] == mvp["recurring_revenue"]["recurring_revenue_score"]
    assert graph["bom_template"]["solution_line"] == "storageguard"
    # the graph adds an explicit node trace
    assert graph["graph_trace"] == ["normalize", "completeness", "classify", "risk", "match", "recommend", "compat", "draft", "summarize"]


def test_graph_factorypulse_attaches_industrial_bom():
    async def _run():
        await engine.dispose()
        lead = Lead(
            project_type="Factory / Industrial Plant",
            description="factory with PLC, SCADA, compressors, chillers, robots, OEE",
            systems_needed_json=["PLC/SCADA"],
            site_info_json={"category_key": "factory", "production_machines": "15"},
        )
        async with async_session_factory() as db:
            return await ai_graph.run_lead_graph(db, lead)

    out = asyncio.run(_run())
    assert "Industrial Factory" in out["classification"]["project_class"]
    assert out["bom_template"]["solution_line"] == "factorypulse"
    assert out["solution_line"] == "factorypulse"


# --- 5.15 Telegram webhook --------------------------------------------------

def test_telegram_webhook_route_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/telegram/webhook" in paths


def test_telegram_ignores_unauthorized_chat():
    from app.services.telegram_bot import handle_update

    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            return await handle_update(db, {"message": {"chat": {"id": -999}, "text": "/leads"}})

    res = asyncio.run(_run())
    assert res["ok"] is True and res.get("ignored") == "unauthorized_chat"

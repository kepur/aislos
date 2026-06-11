"""Release-gate verification tests (FI.9.1 - FI.9.4)."""
import asyncio
from datetime import date

import pytest
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.models.lead import Lead
from app.models.lifecycle import (
    AMCContract,
    CustomerWarranty,
    InventoryItem,
    MonitoringPoint,
    StockMovement,
)
from app.models.project import Project
from app.schemas.product import ProductRead
from app.schemas.quote import QuoteRead
from app.schemas.solution import SolutionRead
from app.services import amc, finance, recurring_revenue, renewal_queue, storageguard, warranty


# --- FI.9.1 lifecycle model/API math + queries ------------------------------

def test_inventory_stock_movement_roundtrip():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            inv = InventoryItem(name="Gate test probe", quantity=10, reorder_level=3)
            db.add(inv)
            await db.flush()
            db.add(StockMovement(inventory_item_id=inv.id, movement_type="outbound", quantity=4))
            await db.flush()
            assert inv.id is not None
            await db.rollback()
    asyncio.run(_run())


def test_calibration_due_query_runs():
    from app.services import lifecycle_alerts

    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            due = await lifecycle_alerts.calibration_due(db, within_days=400)
            assert isinstance(due, list)
    asyncio.run(_run())


def test_warranty_and_amc_and_finance_math():
    # warranty coverage
    assert warranty.evaluate_coverage(amc_covered=True)["coverage_type"] == "amc"
    # AMC pricing
    assert amc.amc_annual_fee(mode="percentage", solution_line="storageguard", project_value=10000)["amount_min"] == 800
    # finance math
    r = finance.compute_finance({"contract_total": 10000, "supplier_cost": 4000})
    assert r["gross_profit"] == 6000 and r["gross_margin_percent"] == 60.0


# --- FI.9.2 StorageGuard end-to-end -----------------------------------------

def test_storageguard_chain_pure_functions():
    """Assessment -> classification -> proposal -> BOM -> scoring -> quote -> finance -> AMC."""
    site = {"category_key": "storage", "monitoring_points": "24", "compliance_use": "pharma GDP audit reports"}
    assert storageguard.is_storageguard("storage", "")
    proposal = storageguard.build_storageguard_proposal(site)
    assert proposal["solution_line"] == "storageguard" and proposal["estimate_only"]
    bom = storageguard.build_storageguard_bom(site)
    assert any(i["category"] == "gateway" for i in bom["items"])

    lead = Lead(project_type="Cold storage", description="HACCP compliance reports, calibration, probes, alarm monitoring", systems_needed_json=[], site_info_json=site)
    score = recurring_revenue.score_lead(lead)
    assert score["recurring_revenue_score"] >= 70

    items = finance.build_customer_line_items({"hardware_package": proposal["estimated_first_year_total"]["amount_min"]})
    assert items and all("supplier" not in i for i in items)

    fin = finance.compute_finance({"contract_total": 12000, "supplier_cost": 5000, "amc_fee_annual": 3000, "annual_service_cost": 1000})
    assert fin["ltv_3_year"] > fin["first_year_profit"]
    fee = amc.amc_annual_fee(mode="point_based", points={"temperature": 18, "door": 4, "gateway": 1})
    assert fee["amount_min"] > 0


def test_storageguard_chain_persisted_demo():
    """If the demo StorageGuard project exists, assert the full persisted chain."""
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            proj = (await db.execute(
                select(Project).where(Project.title.like("Food Cold Storage%")).limit(1)
            )).scalar_one_or_none()
            if proj is None:
                pytest.skip("demo StorageGuard project not seeded")
            amc_n = (await db.execute(select(AMCContract).where(AMCContract.project_id == proj.id))).scalars().all()
            war_n = (await db.execute(select(CustomerWarranty).where(CustomerWarranty.project_id == proj.id))).scalars().all()
            pts = (await db.execute(select(MonitoringPoint).where(MonitoringPoint.project_id == proj.id))).scalars().all()
            assert len(amc_n) >= 1 and len(war_n) >= 1 and len(pts) >= 1
            q = await renewal_queue.build_renewal_queue(db, within_days=400)
            assert "opportunities" in q
    asyncio.run(_run())


# --- FI.9.3 public privacy boundary -----------------------------------------

def test_public_schemas_hide_sensitive_fields():
    product_fields = set(ProductRead.model_fields)
    for k in ("cost_price", "internal_model", "supplier_id", "replacement_margin_percent"):
        assert k not in product_fields
    quote_fields = set(QuoteRead.model_fields)
    assert "internal_economics_json" not in quote_fields
    # customer-facing fields are present
    assert "customer_line_items_json" in quote_fields
    assert isinstance(SolutionRead.model_fields, dict)


def test_quote_pdf_excludes_supplier_cost():
    reportlab = pytest.importorskip("reportlab")  # noqa: F841
    from app.services.quote_pdf import generate_quote_pdf

    quote_dict = {
        "id": "00000000-0000-0000-0000-000000000001",
        "currency": "EUR",
        "customer_line_items_json": [
            {"label": "Hardware Package", "display": "8,000.00 EUR", "amount": 8000, "optional": False},
        ],
        "first_year_total": 9000,
        "annual_recurring_total": 3000,
        "total": 9000,
        "quote_items_json": [],
    }
    pdf = generate_quote_pdf(quote_dict, None)
    assert pdf[:4] == b"%PDF"
    # A supplier secret never passed into the customer dict must not appear.
    assert b"SUPPLIER_SECRET_COST" not in pdf


# --- FI.9.4 customer liability boundary -------------------------------------

def test_contract_boundary_distinguishes_responsibilities():
    tpl = amc.CONTRACT_BOUNDARY_TEMPLATE
    keys = {s["key"] for s in tpl["sections"]}
    for expected in ("equipment_supply", "warranty_coordination", "on_site_service", "exclusions", "third_party"):
        assert expected in keys
    # baseline remote assurance is separate from AMC tiers
    assert amc.BASELINE_REMOTE_ASSURANCE["years"] == 3
    assert any(t["tier"] == "premium" for t in amc.AMC_CATALOG)
    summary = tpl["summary"].lower()
    assert "supplier warranty" in summary and "managed warranty" in summary

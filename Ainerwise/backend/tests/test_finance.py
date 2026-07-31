"""Tests for project finance + quote economics (FI.4.4, FI.4.6)."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import User
from app.services import finance
from app.services.portal_access import sync_role_portal_access
from tests.route_utils import registered_route_paths


def test_compute_finance_margin_and_ltv():
    data = {
        "contract_total": 20000,
        "supplier_cost": 8000,
        "shipping_cost": 500,
        "customs_cost": 500,
        "local_installer_cost": 1000,
        "labor_cost": 1000,
        "amc_fee_year_1": 3000,
        "amc_fee_annual": 3000,
        "consumable_revenue_estimate": 500,
        "annual_service_cost": 1500,
    }
    r = finance.compute_finance(data)
    assert r["direct_cost"] == 11000
    assert r["gross_profit"] == 9000
    assert r["gross_margin_percent"] == 45.0
    # first-year revenue = 20000 + (3000 + 500) = 23500
    assert r["first_year_revenue"] == 23500
    # first-year profit = 23500 - 11000 - 1500 = 11000
    assert r["first_year_profit"] == 11000
    # annual recurring revenue = 3000 + 500 = 3500; profit = 3500 - 1500 = 2000
    assert r["annual_recurring_revenue"] == 3500
    assert r["annual_recurring_profit"] == 2000
    # LTV 3 = 11000 + 2*2000 = 15000; 5 = +4*; 8 = +7*
    assert r["ltv_3_year"] == 15000
    assert r["ltv_5_year"] == 19000
    assert r["ltv_8_year"] == 25000


def test_compute_finance_defaults_contract_total_from_one_time_revenue():
    r = finance.compute_finance({"hardware_revenue": 5000, "design_fee": 2000, "supplier_cost": 3000})
    assert r["contract_total"] == 7000
    assert r["gross_profit"] == 4000


def test_compute_platform_fee_modes():
    pct = finance.compute_platform_fee({"fee_type": "percentage", "percentage": 0.08}, 10000)
    assert pct["platform_fee"] == 800
    fixed = finance.compute_platform_fee({"fee_type": "fixed", "fixed_fee": 500}, 10000)
    assert fixed["platform_fee"] == 500
    hybrid = finance.compute_platform_fee({"fee_type": "hybrid", "fixed_fee": 300, "percentage": 0.05}, 10000)
    assert hybrid["platform_fee"] == 800
    clamped = finance.compute_platform_fee(
        {"fee_type": "percentage", "percentage": 0.5, "max_fee": 1000}, 10000
    )
    assert clamped["platform_fee"] == 1000


def test_build_customer_line_items_hides_supplier_and_marks_optional():
    items = finance.build_customer_line_items({
        "hardware_package": 8000, "design": 2000, "platform": 1000,
        "first_year_support": 0,
    })
    keys = {i["key"] for i in items}
    assert "hardware_package" in keys
    # no supplier cost / internal model keys ever
    for i in items:
        assert "supplier" not in i and "cost" not in i and "internal_model" not in i
    support = next(i for i in items if i["key"] == "first_year_support")
    assert support["included"] is True and support["display"] == "Included"
    amc = next(i for i in items if i["key"] == "optional_amc")
    assert amc["optional"] is True


def test_finance_routes_registered():
    paths = registered_route_paths(app)
    for p in (
        "/api/v1/project-finances",
        "/api/v1/project-finances/compute",
        "/api/v1/platform-fee-rules",
        "/api/v1/platform-fee-rules/compute",
        "/api/v1/quotes/{id}/build-customer-view",
        "/api/v1/quotes/{id}/internal-economics",
    ):
        assert p in paths, p


async def _finance_identity(role: str) -> dict:
    async with async_session_factory() as db:
        row = User(
            email=f"finance-access-{role}-{uuid.uuid4().hex[:10]}@example.com",
            password_hash=hash_password("finance-access-123"),
            full_name=f"Finance Access {role}",
            role=role,
            is_active=True,
        )
        db.add(row)
        await db.flush()
        await sync_role_portal_access(db, user_id=row.id, role=row.role)
        await db.commit()
        return {"Authorization": f"Bearer {create_access_token(str(row.id), row.role)}"}


def test_finance_operator_can_use_finance_api_but_buyer_cannot():
    async def _run():
        await engine.dispose()
        finance_headers = await _finance_identity("finance")
        buyer_headers = await _finance_identity("buyer")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            portals = await client.get("/api/v1/auth/me/portals", headers=finance_headers)
            assert portals.status_code == 200, portals.text
            assert "admin_finance" in {item["portal_key"] for item in portals.json()["items"]}

            listing = await client.get("/api/v1/project-finances", headers=finance_headers)
            assert listing.status_code == 200, listing.text
            preview = await client.post(
                "/api/v1/project-finances/compute",
                headers=finance_headers,
                json={"contract_total": 1000, "supplier_cost": 400},
            )
            assert preview.status_code == 200, preview.text
            assert preview.json()["gross_profit"] == 600

            created = await client.post(
                "/api/v1/project-finances",
                headers=finance_headers,
                json={"contract_total": 1000, "supplier_cost": 400},
            )
            assert created.status_code == 201, created.text
            deleted = await client.delete(
                f"/api/v1/project-finances/{created.json()['id']}", headers=finance_headers
            )
            assert deleted.status_code == 200, deleted.text

            fee = await client.post(
                "/api/v1/platform-fee-rules",
                headers=finance_headers,
                json={"name": "Finance operator rule", "percentage": 0.05},
            )
            assert fee.status_code == 201, fee.text
            fee_preview = await client.post(
                "/api/v1/platform-fee-rules/compute",
                headers=finance_headers,
                json={"rule_id": fee.json()["id"], "project_value": 1000},
            )
            assert fee_preview.status_code == 200, fee_preview.text
            fee_deleted = await client.delete(
                f"/api/v1/platform-fee-rules/{fee.json()['id']}", headers=finance_headers
            )
            assert fee_deleted.status_code == 200, fee_deleted.text

            denied = await client.get("/api/v1/project-finances", headers=buyer_headers)
            assert denied.status_code == 403, denied.text

    asyncio.run(_run())

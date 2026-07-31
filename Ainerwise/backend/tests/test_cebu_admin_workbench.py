"""Unified Cebu Admin workbench uses Core data and rejects non-admin roles."""
import asyncio

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_cebu_admin_workbench_is_real_and_admin_only():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        admin_email, password, _ = await _create_identity(role="admin", with_company=False)
        buyer_email, buyer_password, buyer_company = await _create_identity(role="buyer")
        admin = await _login(admin_email, password)
        buyer = await _login(buyer_email, buyer_password)

        async with _client() as client:
            request = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer,
                json={"title": "Admin workbench request", "portal_key": "cebu"},
            )
            assert request.status_code == 201, request.text
            request_id = request.json()["id"]

            for path in (
                "/api/v1/admin/cebu/dashboard",
                "/api/v1/admin/cebu/users",
                "/api/v1/admin/cebu/staff",
                "/api/v1/admin/cebu/companies",
                "/api/v1/admin/cebu/procurement-requests",
                "/api/v1/admin/cebu/orders",
                "/api/v1/admin/cebu/trade",
                "/api/v1/admin/cebu/audit-logs",
            ):
                denied = await client.get(path, headers=buyer)
                assert denied.status_code == 403, (path, denied.text)

            dashboard = await client.get("/api/v1/admin/cebu/dashboard", headers=admin)
            assert dashboard.status_code == 200, dashboard.text
            assert dashboard.json()["stats"]["procurement_requests"] >= 1

            requests = await client.get("/api/v1/admin/cebu/procurement-requests", headers=admin)
            assert requests.status_code == 200, requests.text
            assert request_id in {row["id"] for row in requests.json()["items"]}

            moderated = await client.patch(
                f"/api/v1/admin/cebu/procurement-requests/{request_id}/status",
                headers=admin,
                json={"status": "cancelled", "reason": "Admin moderation test"},
            )
            assert moderated.status_code == 200, moderated.text
            assert moderated.json()["status"] == "cancelled"

            company = await client.patch(
                f"/api/v1/admin/cebu/companies/{buyer_company}/verification",
                headers=admin,
                json={"verification_status": "review", "reason": "KYC review"},
            )
            assert company.status_code == 200, company.text

            company_status = await client.patch(
                f"/api/v1/admin/cebu/companies/{buyer_company}/status",
                headers=admin,
                json={"status": "restricted", "reason": "Operational review"},
            )
            assert company_status.status_code == 200, company_status.text
            assert company_status.json()["operational_status"] == "restricted"

            invited = await client.post(
                "/api/v1/admin/cebu/staff/invite",
                headers=admin,
                json={
                    "email": f"cebu-finance-{request_id[:8]}@example.com",
                    "full_name": "Cebu Finance",
                    "role": "finance",
                },
            )
            assert invited.status_code == 201, invited.text
            assert invited.json()["password_reset_required"] is True
            staff_id = invited.json()["id"]
            role_changed = await client.put(
                f"/api/v1/admin/cebu/staff/{staff_id}/role",
                headers=admin,
                json={"role": "sales_manager", "reason": "Move to support operations"},
            )
            assert role_changed.status_code == 200, role_changed.text
            assert role_changed.json()["role"] == "sales_manager"

            audit = await client.get("/api/v1/admin/cebu/audit-logs", headers=admin)
            assert audit.status_code == 200, audit.text
            actions = {row["action"] for row in audit.json()["items"]}
            assert "cebu.admin.request_status_changed" in actions
            assert "cebu.admin.company_verification_changed" in actions
            assert "cebu.admin.company_status_changed" in actions
            assert "cebu.admin.staff_invited" in actions
            assert "cebu.admin.staff_role_changed" in actions

            trade = await client.get("/api/v1/admin/cebu/trade", headers=admin)
            assert trade.status_code == 200, trade.text
            assert "shipping_routes" in trade.json()
            assert "verification_queue" in trade.json()

            schedule = await client.post(
                "/api/v1/admin/cebu/backups/schedules",
                headers=admin,
                json={"name": "Test weekly backup", "frequency": "WEEKLY", "day_of_week": 1},
            )
            assert schedule.status_code == 201, schedule.text
            manual = await client.post("/api/v1/admin/cebu/backups/manual", headers=admin)
            assert manual.status_code == 200, manual.text
            assert manual.json()["status"] == "SUCCESS"
            jobs = await client.get("/api/v1/admin/cebu/backups/jobs", headers=admin)
            assert jobs.status_code == 200, jobs.text
            assert manual.json()["id"] in {row["id"] for row in jobs.json()["items"]}

    asyncio.run(_run())

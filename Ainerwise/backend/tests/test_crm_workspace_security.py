"""CRM Lead Workspace isolation."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lead import Lead
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.quote import Quote
from app.models.user import Company, User
from app.services.portal_access import ensure_membership, sync_role_portal_access


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


def test_lead_workspace_isolation_for_sales_and_customer():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"CRM A {suffix}", slug=f"crm-a-{suffix}")
            workspace_b = Workspace(name=f"CRM B {suffix}", slug=f"crm-b-{suffix}")
            company = Company(name=f"CRM Buyer {suffix}", type="buyer")
            db.add_all([workspace_a, workspace_b, company])
            await db.flush()
            sales = User(
                email=f"crm-sales-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="sales_manager",
            )
            buyer = User(
                email=f"crm-buyer-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=company.id,
            )
            admin = User(
                email=f"crm-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            db.add_all([sales, buyer, admin])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=sales.id,
                role=sales.role,
                workspace_id=workspace_a.id,
            )
            await ensure_membership(
                db,
                user_id=buyer.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
                company_id=company.id,
            )
            lead_a = Lead(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer.id,
                contact_email=buyer.email,
                project_type="Workspace A requirement",
                status="new",
            )
            lead_b = Lead(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer.id,
                contact_email=buyer.email,
                project_type="Workspace B private requirement",
                status="new",
            )
            project_b = Project(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                title="Workspace B delivery",
                status="planning",
            )
            db.add_all([lead_a, lead_b, project_b])
            await db.flush()
            quote_a = Quote(
                workspace_id=workspace_a.id,
                lead_id=lead_a.id,
                status="sent",
                currency="EUR",
            )
            quote_b = Quote(
                workspace_id=workspace_b.id,
                lead_id=lead_b.id,
                status="sent",
                currency="EUR",
            )
            db.add_all([quote_a, quote_b])
            await db.commit()
            ids = {
                "a": str(lead_a.id),
                "b": str(lead_b.id),
                "project_b": str(project_b.id),
                "quote_a": str(quote_a.id),
                "quote_b": str(quote_b.id),
            }
            sales_headers = _headers(sales)
            buyer_headers = _headers(buyer)
            admin_headers = _headers(admin)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            sales_list = await client.get("/api/v1/leads", headers=sales_headers)
            assert sales_list.status_code == 200, sales_list.text
            assert {item["id"] for item in sales_list.json()["items"]} == {ids["a"]}
            sales_denied = await client.get(f"/api/v1/leads/{ids['b']}", headers=sales_headers)
            assert sales_denied.status_code == 403, sales_denied.text
            sales_write_denied = await client.patch(
                f"/api/v1/leads/{ids['b']}/status",
                headers=sales_headers,
                json={"status": "matched"},
            )
            assert sales_write_denied.status_code == 403, sales_write_denied.text

            buyer_list = await client.get("/api/v1/leads/my", headers=buyer_headers)
            assert buyer_list.status_code == 200, buyer_list.text
            assert {item["id"] for item in buyer_list.json()["items"]} == {ids["a"]}
            buyer_denied = await client.get(f"/api/v1/leads/my/{ids['b']}", headers=buyer_headers)
            assert buyer_denied.status_code == 403, buyer_denied.text
            quote_list = await client.get("/api/v1/quotes/my", headers=buyer_headers)
            assert quote_list.status_code == 200, quote_list.text
            assert {item["id"] for item in quote_list.json()["items"]} == {ids["quote_a"]}
            quote_denied = await client.get(f"/api/v1/quotes/{ids['quote_b']}", headers=buyer_headers)
            assert quote_denied.status_code == 403, quote_denied.text
            approvals = await client.get("/api/v1/customer/workspace/approvals", headers=buyer_headers)
            assert approvals.status_code == 200, approvals.text
            assert {item["id"] for item in approvals.json()["quotes"]} == {ids["quote_a"]}

            admin_list = await client.get("/api/v1/leads", headers=admin_headers)
            assert admin_list.status_code == 200, admin_list.text
            assert {ids["a"], ids["b"]} <= {item["id"] for item in admin_list.json()["items"]}
            quote_mismatch = await client.post(
                "/api/v1/quotes",
                headers=admin_headers,
                json={"lead_id": ids["a"], "project_id": ids["project_b"]},
            )
            assert quote_mismatch.status_code == 409, quote_mismatch.text
            rfq_mismatch = await client.post(
                "/api/v1/admin/rfqs",
                headers=admin_headers,
                json={
                    "title": "Cross Workspace RFQ",
                    "lead_id": ids["a"],
                    "project_id": ids["project_b"],
                },
            )
            assert rfq_mismatch.status_code == 409, rfq_mismatch.text

    asyncio.run(_run())

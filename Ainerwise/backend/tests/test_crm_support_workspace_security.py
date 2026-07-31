"""Workspace isolation for Inquiry, Proposal Plan, and support Ticket roots."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.lifecycle import MonitoringPoint
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company, User
from app.services.portal_access import ensure_membership, sync_role_portal_access


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


def test_crm_support_roots_require_exact_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Support A {suffix}", slug=f"support-a-{suffix}")
            workspace_b = Workspace(name=f"Support B {suffix}", slug=f"support-b-{suffix}")
            company = Company(name=f"Support Buyer {suffix}", type="buyer")
            db.add_all([workspace_a, workspace_b, company])
            await db.flush()

            sales = User(
                email=f"support-sales-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="sales_manager",
            )
            buyer_a = User(
                email=f"support-buyer-a-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=company.id,
            )
            buyer_b = User(
                email=f"support-buyer-b-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=company.id,
            )
            admin = User(
                email=f"support-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            db.add_all([sales, buyer_a, buyer_b, admin])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=sales.id,
                role=sales.role,
                workspace_id=workspace_a.id,
            )
            await ensure_membership(
                db,
                user_id=buyer_a.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
                company_id=company.id,
            )
            await ensure_membership(
                db,
                user_id=buyer_b.id,
                membership_type="customer_owner",
                workspace_id=workspace_b.id,
                company_id=company.id,
            )
            lead_a = Lead(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer_a.id,
                project_type="Workspace A requirement",
                status="new",
            )
            project_a = Project(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                title="Workspace A project",
                status="planning",
            )
            project_b = Project(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                title="Workspace B project",
                status="planning",
            )
            db.add_all([lead_a, project_a, project_b])
            await db.flush()
            monitoring_b = MonitoringPoint(
                workspace_id=workspace_b.id,
                project_id=project_b.id,
                device_name="Private B monitor",
            )
            inquiry_a = Inquiry(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer_a.id,
                contact_email=buyer_a.email,
                message="Workspace A inquiry",
                status="new",
            )
            inquiry_b = Inquiry(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer_b.id,
                contact_email=buyer_b.email,
                message="Workspace B private inquiry",
                status="new",
            )
            ticket_a = Ticket(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer_a.id,
                title="Workspace A ticket",
                status="open",
            )
            ticket_b = Ticket(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer_b.id,
                title="Workspace B private ticket",
                status="open",
            )
            db.add_all([monitoring_b, inquiry_a, inquiry_b, ticket_a, ticket_b])
            await db.commit()
            ids = {
                "workspace_b": str(workspace_b.id),
                "lead_a": str(lead_a.id),
                "project_a": str(project_a.id),
                "project_b": str(project_b.id),
                "monitoring_b": str(monitoring_b.id),
                "inquiry_a": str(inquiry_a.id),
                "inquiry_b": str(inquiry_b.id),
                "ticket_a": str(ticket_a.id),
                "ticket_b": str(ticket_b.id),
            }
            sales_headers = _headers(sales)
            buyer_headers = _headers(buyer_a)
            admin_headers = _headers(admin)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            sales_inquiries = await client.get("/api/v1/inquiries", headers=sales_headers)
            assert sales_inquiries.status_code == 200, sales_inquiries.text
            assert {item["id"] for item in sales_inquiries.json()["items"]} == {ids["inquiry_a"]}
            sales_inquiry_denied = await client.get(
                f"/api/v1/inquiries/{ids['inquiry_b']}", headers=sales_headers
            )
            assert sales_inquiry_denied.status_code == 403, sales_inquiry_denied.text

            sales_tickets = await client.get("/api/v1/tickets", headers=sales_headers)
            assert sales_tickets.status_code == 200, sales_tickets.text
            assert {item["id"] for item in sales_tickets.json()["items"]} == {ids["ticket_a"]}
            sales_ticket_denied = await client.get(
                f"/api/v1/tickets/{ids['ticket_b']}", headers=sales_headers
            )
            assert sales_ticket_denied.status_code == 403, sales_ticket_denied.text
            sales_status_denied = await client.patch(
                f"/api/v1/tickets/{ids['ticket_b']}/status",
                headers=sales_headers,
                json={"status": "resolved"},
            )
            assert sales_status_denied.status_code == 403, sales_status_denied.text

            my_inquiries = await client.get("/api/v1/inquiries/my", headers=buyer_headers)
            assert my_inquiries.status_code == 200, my_inquiries.text
            assert {item["id"] for item in my_inquiries.json()["items"]} == {ids["inquiry_a"]}
            my_tickets = await client.get("/api/v1/tickets/my", headers=buyer_headers)
            assert my_tickets.status_code == 200, my_tickets.text
            assert {item["id"] for item in my_tickets.json()["items"]} == {ids["ticket_a"]}
            buyer_ticket_denied = await client.get(
                f"/api/v1/tickets/{ids['ticket_b']}", headers=buyer_headers
            )
            assert buyer_ticket_denied.status_code == 403, buyer_ticket_denied.text
            forged_workspace = await client.post(
                "/api/v1/tickets",
                headers=buyer_headers,
                json={"workspace_id": ids["workspace_b"], "title": "Forged B ticket"},
            )
            assert forged_workspace.status_code == 403, forged_workspace.text

            mixed_ticket = await client.post(
                "/api/v1/tickets",
                headers=admin_headers,
                json={
                    "project_id": ids["project_a"],
                    "monitoring_point_id": ids["monitoring_b"],
                    "title": "Mixed Workspace ticket",
                },
            )
            assert mixed_ticket.status_code == 409, mixed_ticket.text
            mixed_proposal = await client.post(
                "/api/v1/proposals",
                headers=admin_headers,
                json={
                    "lead_id": ids["lead_a"],
                    "project_id": ids["project_b"],
                    "tier": "standard",
                },
            )
            assert mixed_proposal.status_code == 409, mixed_proposal.text

    asyncio.run(_run())

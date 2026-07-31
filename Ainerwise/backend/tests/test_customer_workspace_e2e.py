"""Customer Workspace ownership and delivery workflow tests."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.asset import Asset, Site
from app.models.commerce import CommerceOrder, OrderDelivery, ProcurementRequest
from app.models.field_service import FieldTask, TaskEvidence, WorkPackage
from app.models.lead import Lead
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.quote import Quote
from app.models.ticket import Ticket
from app.models.user import Company, User


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_customer_workspace_is_company_scoped_and_quote_safe():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        password = "customer-workspace-test"
        async with async_session_factory() as db:
            own_company = Company(name=f"Customer A {suffix}", type="buyer")
            other_company = Company(name=f"Customer B {suffix}", type="buyer")
            workspace = Workspace(name=f"Customer delivery {suffix}", slug=f"customer-delivery-{suffix}")
            db.add_all([own_company, other_company, workspace])
            await db.flush()
            own_user = User(
                email=f"customer-a-{suffix}@example.com",
                password_hash=hash_password(password),
                role="buyer",
                company_id=own_company.id,
            )
            other_user = User(
                email=f"customer-b-{suffix}@example.com",
                password_hash=hash_password(password),
                role="buyer",
                company_id=other_company.id,
            )
            db.add_all([own_user, other_user])
            await db.flush()
            own_lead = Lead(
                buyer_company_id=own_company.id,
                buyer_user_id=own_user.id,
                contact_email=own_user.email,
                project_type="Villa smart home",
                status="quotation_sent",
            )
            other_lead = Lead(
                buyer_company_id=other_company.id,
                buyer_user_id=other_user.id,
                contact_email=other_user.email,
                project_type="Other project",
                status="quotation_sent",
            )
            own_project = Project(
                buyer_company_id=own_company.id,
                title="Owned villa",
                status="installation",
            )
            other_project = Project(
                buyer_company_id=other_company.id,
                title="Other villa",
                status="installation",
            )
            db.add_all([own_lead, other_lead, own_project, other_project])
            await db.flush()
            own_quote = Quote(lead_id=own_lead.id, status="sent", total=1200, currency="EUR")
            other_quote = Quote(lead_id=other_lead.id, status="sent", total=9999, currency="EUR")
            own_package = WorkPackage(
                workspace_id=workspace.id,
                project_id=own_project.id,
                title="Owned installation",
                status="in_progress",
            )
            other_package = WorkPackage(
                workspace_id=workspace.id,
                project_id=other_project.id,
                title="Other installation",
                status="in_progress",
            )
            own_site = Site(company_id=own_company.id, name="Owned site")
            other_site = Site(company_id=other_company.id, name="Other site")
            own_request = ProcurementRequest(
                buyer_company_id=own_company.id,
                buyer_user_id=own_user.id,
                title="Owned procurement",
                status="awarded",
            )
            other_request = ProcurementRequest(
                buyer_company_id=other_company.id,
                buyer_user_id=other_user.id,
                title="Other procurement",
                status="awarded",
            )
            db.add_all(
                [
                    own_quote,
                    other_quote,
                    own_package,
                    other_package,
                    own_site,
                    other_site,
                    own_request,
                    other_request,
                ]
            )
            await db.flush()
            own_task = FieldTask(
                work_package_id=own_package.id,
                task_type="installation",
                title="Owned task",
                status="in_progress",
            )
            other_task = FieldTask(
                work_package_id=other_package.id,
                task_type="installation",
                title="Other task",
                status="in_progress",
            )
            own_asset = Asset(
                site_id=own_site.id,
                project_id=own_project.id,
                name="Owned controller",
                status="active",
            )
            other_asset = Asset(
                site_id=other_site.id,
                project_id=other_project.id,
                name="Other controller",
                status="active",
            )
            own_order = CommerceOrder(
                procurement_request_id=own_request.id,
                buyer_company_id=own_company.id,
                status="in_delivery",
                total_minor=120000,
                currency="EUR",
            )
            other_order = CommerceOrder(
                procurement_request_id=other_request.id,
                buyer_company_id=other_company.id,
                status="in_delivery",
                total_minor=999900,
                currency="EUR",
            )
            db.add_all([own_task, other_task, own_asset, other_asset, own_order, other_order])
            await db.flush()
            own_delivery = OrderDelivery(commerce_order_id=own_order.id, status="delivered")
            other_delivery = OrderDelivery(commerce_order_id=other_order.id, status="delivered")
            own_ticket = Ticket(
                project_id=own_project.id,
                buyer_company_id=own_company.id,
                buyer_user_id=own_user.id,
                title="Owned support",
                status="open",
            )
            db.add_all([own_delivery, other_delivery, own_ticket])
            await db.flush()
            db.add(
                TaskEvidence(
                    field_task_id=own_task.id,
                    evidence_type="photo",
                    payload_json={
                        "object_key": "customer-safe.jpg",
                        "lat": 44.8,
                        "lng": 20.4,
                        "notes": "Installed",
                    },
                    captured_by=own_user.id,
                )
            )
            await db.commit()
            ids = {
                "own_lead": str(own_lead.id),
                "other_lead": str(other_lead.id),
                "own_quote": str(own_quote.id),
                "other_quote": str(other_quote.id),
                "own_package": str(own_package.id),
                "other_package": str(other_package.id),
                "own_project": str(own_project.id),
                "other_project": str(other_project.id),
                "own_delivery": str(own_delivery.id),
            }

        async with _client() as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": f"customer-a-{suffix}@example.com", "password": password},
            )
            assert login.status_code == 200, login.text
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            summary = await client.get("/api/v1/customer/workspace/summary", headers=headers)
            assert summary.status_code == 200, summary.text
            assert summary.json() == {
                "requirements": 1,
                "procurement_requests": 1,
                "projects": 1,
                "pending_quote_approvals": 1,
                "pending_delivery_approvals": 1,
                "installations": 1,
                "installation_tasks_open": 1,
                "assets": 1,
                "open_tickets": 1,
            }

            installations = await client.get("/api/v1/customer/workspace/installations", headers=headers)
            assert installations.status_code == 200, installations.text
            assert {item["id"] for item in installations.json()["items"]} == {ids["own_package"]}

            detail = await client.get(
                f"/api/v1/customer/workspace/installations/{ids['own_package']}",
                headers=headers,
            )
            assert detail.status_code == 200, detail.text
            assert detail.json()["tasks"][0]["evidence"][0]["evidence_type"] == "photo"
            evidence_payload = detail.json()["tasks"][0]["evidence"][0]["payload_json"]
            assert evidence_payload == {"notes": "Installed", "photo_captured": True}

            blocked_package = await client.get(
                f"/api/v1/customer/workspace/installations/{ids['other_package']}",
                headers=headers,
            )
            assert blocked_package.status_code == 404

            assets = await client.get("/api/v1/customer/workspace/assets", headers=headers)
            assert assets.status_code == 200, assets.text
            assert {item["name"] for item in assets.json()["items"]} == {"Owned controller"}

            blocked_assets = await client.get(
                f"/api/v1/customer/workspace/assets?project_id={ids['other_project']}",
                headers=headers,
            )
            assert blocked_assets.status_code == 404

            approvals = await client.get("/api/v1/customer/workspace/approvals", headers=headers)
            assert approvals.status_code == 200, approvals.text
            assert {item["id"] for item in approvals.json()["quotes"]} == {ids["own_quote"]}
            assert {item["id"] for item in approvals.json()["deliveries"]} == {ids["own_delivery"]}

            own_lead = await client.get(f"/api/v1/leads/my/{ids['own_lead']}", headers=headers)
            assert own_lead.status_code == 200, own_lead.text
            blocked_lead = await client.get(f"/api/v1/leads/my/{ids['other_lead']}", headers=headers)
            assert blocked_lead.status_code == 404

            blocked_quote = await client.get(f"/api/v1/quotes/{ids['other_quote']}", headers=headers)
            assert blocked_quote.status_code == 403
            blocked_quote_update = await client.patch(
                f"/api/v1/quotes/{ids['other_quote']}/status",
                headers=headers,
                json={"status": "accepted"},
            )
            assert blocked_quote_update.status_code == 403
            own_quote_update = await client.patch(
                f"/api/v1/quotes/{ids['own_quote']}/status",
                headers=headers,
                json={"status": "accepted"},
            )
            assert own_quote_update.status_code == 200, own_quote_update.text

    asyncio.run(_run())

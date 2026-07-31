"""Customer APIs must not serialize internal CRM and operations fields."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lead import Lead
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company, User
from app.models.inquiry import Inquiry


def test_customer_projections_hide_internal_fields():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            company = Company(name=f"Projection {uuid.uuid4().hex[:8]}", type="buyer")
            db.add(company)
            await db.flush()
            user = User(
                email=f"projection-{uuid.uuid4().hex[:8]}@example.com",
                password_hash=hash_password("projection-123"),
                full_name="Projection Customer",
                role="buyer",
                company_id=company.id,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            lead = Lead(
                buyer_company_id=company.id,
                buyer_user_id=user.id,
                contact_email=user.email,
                status="new",
                notes="internal lead note",
                assigned_admin_id=user.id,
                lead_score=99,
                estimated_ltv=123456,
            )
            project = Project(
                buyer_company_id=company.id,
                title="Customer projection",
                status="planning",
                notes="internal project note",
                telegram_chat_id="-100-secret",
            )
            inquiry = Inquiry(
                buyer_company_id=company.id,
                buyer_user_id=user.id,
                contact_email=user.email,
                status="new",
                admin_notes="internal inquiry note",
                vendor_company_id=company.id,
            )
            db.add_all([lead, project, inquiry])
            await db.flush()
            ticket = Ticket(
                project_id=project.id,
                buyer_company_id=company.id,
                buyer_user_id=user.id,
                title="Projection ticket",
                priority="medium",
                status="open",
                assigned_to=user.id,
            )
            db.add(ticket)
            await db.commit()
            ids = {
                "lead": lead.id,
                "project": project.id,
                "ticket": ticket.id,
            }
            headers = {
                "Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"
            }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            lead_response = await client.get("/api/v1/leads/my", headers=headers)
            assert lead_response.status_code == 200, lead_response.text
            lead_row = lead_response.json()["items"][0]
            for field in ("notes", "assigned_admin_id", "lead_score", "estimated_ltv"):
                assert field not in lead_row

            inquiry_response = await client.get("/api/v1/inquiries/my", headers=headers)
            assert inquiry_response.status_code == 200, inquiry_response.text
            inquiry_row = inquiry_response.json()["items"][0]
            for field in ("admin_notes", "vendor_company_id", "buyer_user_id"):
                assert field not in inquiry_row

            project_response = await client.get(
                f"/api/v1/projects/{ids['project']}", headers=headers
            )
            assert project_response.status_code == 200, project_response.text
            for field in ("notes", "telegram_chat_id", "buyer_company_id"):
                assert field not in project_response.json()

            ticket_response = await client.get(
                f"/api/v1/tickets/{ids['ticket']}", headers=headers
            )
            assert ticket_response.status_code == 200, ticket_response.text
            for field in ("assigned_to", "buyer_user_id", "buyer_company_id"):
                assert field not in ticket_response.json()

    asyncio.run(_run())

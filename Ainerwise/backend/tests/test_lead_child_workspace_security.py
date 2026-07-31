"""Workspace isolation for Lead child records."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lead import Lead, SiteSurvey
from app.models.portal_access import Workspace
from app.models.user import User
from app.services.portal_access import sync_role_portal_access


def test_site_surveys_inherit_and_require_exact_lead_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Lead child A {suffix}", slug=f"lead-child-a-{suffix}")
            workspace_b = Workspace(name=f"Lead child B {suffix}", slug=f"lead-child-b-{suffix}")
            sales = User(
                email=f"lead-child-sales-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="sales_manager",
            )
            db.add_all([workspace_a, workspace_b, sales])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=sales.id,
                role=sales.role,
                workspace_id=workspace_a.id,
            )
            lead_a = Lead(workspace_id=workspace_a.id, project_type="A", status="new")
            lead_b = Lead(workspace_id=workspace_b.id, project_type="B", status="new")
            db.add_all([lead_a, lead_b])
            await db.flush()
            mismatched = SiteSurvey(
                workspace_id=workspace_b.id,
                lead_id=lead_a.id,
                survey_type="quick",
            )
            db.add(mismatched)
            await db.commit()
            ids = {
                "workspace_a": str(workspace_a.id),
                "lead_a": str(lead_a.id),
                "lead_b": str(lead_b.id),
                "mismatched": str(mismatched.id),
            }
            headers = {
                "Authorization": f"Bearer {create_access_token(str(sales.id), sales.role)}"
            }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post(
                f"/api/v1/leads/{ids['lead_a']}/surveys",
                headers=headers,
                json={"lead_id": ids["lead_b"], "survey_type": "detailed"},
            )
            assert created.status_code == 201, created.text
            assert created.json()["lead_id"] == ids["lead_a"]
            assert created.json()["workspace_id"] == ids["workspace_a"]

            listed = await client.get(
                f"/api/v1/leads/{ids['lead_a']}/surveys", headers=headers
            )
            assert listed.status_code == 200, listed.text
            assert {item["id"] for item in listed.json()["items"]} == {created.json()["id"]}

            mismatched_update = await client.put(
                f"/api/v1/leads/{ids['lead_a']}/surveys/{ids['mismatched']}",
                headers=headers,
                json={"risk_score": 0.8},
            )
            assert mismatched_update.status_code == 409, mismatched_update.text

            denied = await client.post(
                f"/api/v1/leads/{ids['lead_b']}/surveys",
                headers=headers,
                json={"lead_id": ids["lead_b"], "survey_type": "quick"},
            )
            assert denied.status_code == 403, denied.text

    asyncio.run(_run())

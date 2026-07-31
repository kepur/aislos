"""Workspace isolation for finance, payment plans, and report jobs."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.finance import ProjectFinance
from app.models.notification import ReportJob
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.quote import Quote
from app.models.user import Company, User
from app.services.lifecycle_automation import generate_report_jobs
from app.services.payments import create_plan_from_quote
from app.services.portal_access import sync_role_portal_access


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


def test_finance_resources_require_exact_workspace_and_inherit_scope():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Finance A {suffix}", slug=f"finance-a-{suffix}")
            workspace_b = Workspace(name=f"Finance B {suffix}", slug=f"finance-b-{suffix}")
            customer = Company(name=f"Finance Customer {suffix}", type="buyer")
            db.add_all([workspace_a, workspace_b, customer])
            await db.flush()
            finance_user = User(
                email=f"finance-scope-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="finance",
            )
            admin = User(
                email=f"finance-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            db.add_all([finance_user, admin])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=finance_user.id,
                role=finance_user.role,
                workspace_id=workspace_a.id,
            )
            project_a = Project(
                workspace_id=workspace_a.id,
                buyer_company_id=customer.id,
                title="Workspace A finance project",
                status="planning",
                project_plan_json={"solution_line": "storageguard"},
            )
            project_b = Project(
                workspace_id=workspace_b.id,
                buyer_company_id=customer.id,
                title="Workspace B finance project",
                status="planning",
                project_plan_json={"solution_line": "storageguard"},
            )
            db.add_all([project_a, project_b])
            await db.flush()
            finance_a = ProjectFinance(
                workspace_id=workspace_a.id,
                project_id=project_a.id,
                customer_id=customer.id,
                contract_total=1000,
            )
            finance_b = ProjectFinance(
                workspace_id=workspace_b.id,
                project_id=project_b.id,
                customer_id=customer.id,
                contract_total=9000,
            )
            quote_a = Quote(
                workspace_id=workspace_a.id,
                project_id=project_a.id,
                total=1200,
                currency="EUR",
                status="accepted",
            )
            db.add_all([finance_a, finance_b, quote_a])
            await db.flush()
            plan_a = await create_plan_from_quote(db, quote_a)
            assert plan_a.workspace_id == workspace_a.id
            await db.commit()
            await generate_report_jobs(db, period_label=f"scope-{suffix}")
            report_a = (
                await db.execute(
                    select(ReportJob).where(
                        ReportJob.project_id == project_a.id,
                        ReportJob.period_label == f"scope-{suffix}",
                    )
                )
            ).scalar_one()
            report_b = (
                await db.execute(
                    select(ReportJob).where(
                        ReportJob.project_id == project_b.id,
                        ReportJob.period_label == f"scope-{suffix}",
                    )
                )
            ).scalar_one()
            assert report_a.workspace_id == workspace_a.id
            assert report_b.workspace_id == workspace_b.id
            ids = {
                "workspace_b": str(workspace_b.id),
                "project_a": str(project_a.id),
                "project_b": str(project_b.id),
                "finance_a": str(finance_a.id),
                "finance_b": str(finance_b.id),
            }
            finance_headers = _headers(finance_user)
            admin_headers = _headers(admin)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            listing = await client.get("/api/v1/project-finances", headers=finance_headers)
            assert listing.status_code == 200, listing.text
            assert {item["id"] for item in listing.json()["items"]} == {ids["finance_a"]}
            denied_read = await client.get(
                f"/api/v1/project-finances/{ids['finance_b']}", headers=finance_headers
            )
            assert denied_read.status_code == 403, denied_read.text
            denied_update = await client.put(
                f"/api/v1/project-finances/{ids['finance_b']}",
                headers=finance_headers,
                json={"contract_total": 1},
            )
            assert denied_update.status_code == 403, denied_update.text
            denied_delete = await client.delete(
                f"/api/v1/project-finances/{ids['finance_b']}", headers=finance_headers
            )
            assert denied_delete.status_code == 403, denied_delete.text
            forged = await client.post(
                "/api/v1/project-finances",
                headers=finance_headers,
                json={"workspace_id": ids["workspace_b"], "project_id": ids["project_b"]},
            )
            assert forged.status_code == 403, forged.text
            mixed = await client.post(
                "/api/v1/project-finances",
                headers=finance_headers,
                json={"workspace_id": ids["workspace_b"], "project_id": ids["project_a"]},
            )
            assert mixed.status_code == 409, mixed.text

            admin_listing = await client.get("/api/v1/project-finances", headers=admin_headers)
            assert admin_listing.status_code == 200, admin_listing.text
            assert {ids["finance_a"], ids["finance_b"]} <= {
                item["id"] for item in admin_listing.json()["items"]
            }

    asyncio.run(_run())

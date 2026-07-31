"""PF03–PF10: Field Service E2E smoke tests."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.field_service import FieldTask, PartnerCrew, WorkPackage
from app.models.portal_access import Workspace
from app.models.service import ServicePartner
from app.models.user import Company, User
from app.services.portal_access import ensure_grant, ensure_membership, get_default_workspace


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_field_ops_create_and_assign_task():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        async with async_session_factory() as db:
            ws = await get_default_workspace(db)
            assert ws is not None
            workspace_id = ws.id

        async with _client() as client:
            pkg = await client.post(
                "/api/v1/admin/field-ops/work-packages",
                headers=admin,
                json={
                    "workspace_id": str(workspace_id),
                    "title": "Villa KNX install",
                    "trade": "knx_commissioner",
                },
            )
            assert pkg.status_code == 201, pkg.text
            package_id = pkg.json()["id"]

            task = await client.post(
                f"/api/v1/admin/field-ops/work-packages/{package_id}/tasks",
                headers=admin,
                json={
                    "work_package_id": package_id,
                    "task_type": "installation",
                    "title": "Mount panels",
                },
            )
            assert task.status_code == 201, task.text
            task_id = task.json()["id"]

            from app.models.user import User

            async with async_session_factory() as db:
                worker = (
                    await db.execute(
                        select(User).where(User.email == "installer@example.com")
                    )
                ).scalar_one_or_none()
                assert worker is not None, "seeded installer@example.com worker is required"
                await ensure_membership(
                    db,
                    user_id=worker.id,
                    membership_type="field_worker",
                    workspace_id=workspace_id,
                )
                await ensure_grant(
                    db,
                    user_id=worker.id,
                    grant_key="field_task.read_assigned",
                    workspace_id=workspace_id,
                    portal_key="field_worker",
                )
                await db.commit()
                worker_id = worker.id

            assigned = await client.post(
                f"/api/v1/admin/field-ops/tasks/{task_id}/assignments",
                headers=admin,
                json={"assignee_user_id": str(worker_id)},
            )
            assert assigned.status_code == 201, assigned.text

    asyncio.run(_run())


def test_supplier_dashboard_requires_grant():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": "demo@ainerwise.com", "password": "demo123"},
            )
            assert login.status_code == 200, login.text
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            resp = await client.get("/api/v1/supplier/dashboard", headers=headers)
        assert resp.status_code == 403

    asyncio.run(_run())


def test_partner_company_field_ops_is_company_scoped():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        password = "field-ops-test"
        async with async_session_factory() as db:
            workspace = Workspace(name=f"Partner field {suffix}", slug=f"partner-field-{suffix}")
            company_a = Company(name=f"Partner A {suffix}", type="service_partner")
            company_b = Company(name=f"Partner B {suffix}", type="service_partner")
            db.add_all([workspace, company_a, company_b])
            await db.flush()
            owner_a = User(
                email=f"partner-a-{suffix}@example.com",
                password_hash=hash_password(password),
                role="service_partner",
                company_id=company_a.id,
            )
            owner_b = User(
                email=f"partner-b-{suffix}@example.com",
                password_hash=hash_password(password),
                role="service_partner",
                company_id=company_b.id,
            )
            worker_a = User(
                email=f"worker-a-{suffix}@example.com",
                password_hash=hash_password(password),
                role="partner_worker",
                company_id=company_a.id,
            )
            worker_b = User(
                email=f"worker-b-{suffix}@example.com",
                password_hash=hash_password(password),
                role="partner_worker",
                company_id=company_b.id,
            )
            db.add_all([owner_a, owner_b, worker_a, worker_b])
            await db.flush()
            db.add_all(
                [
                    ServicePartner(
                        user_id=owner_a.id,
                        company_id=company_a.id,
                        partner_type="installer",
                    ),
                    ServicePartner(
                        user_id=owner_b.id,
                        company_id=company_b.id,
                        partner_type="installer",
                    ),
                ]
            )
            for owner in (owner_a, owner_b):
                await ensure_membership(
                    db,
                    user_id=owner.id,
                    membership_type="partner_company_owner",
                    workspace_id=workspace.id,
                    company_id=owner.company_id,
                )
                await ensure_grant(
                    db,
                    user_id=owner.id,
                    grant_key="partner.work_package.read",
                    workspace_id=workspace.id,
                    portal_key="partner_company_pc",
                )
            for worker in (worker_a, worker_b):
                await ensure_membership(
                    db,
                    user_id=worker.id,
                    membership_type="field_worker",
                    workspace_id=workspace.id,
                    company_id=worker.company_id,
                )
            package_a = WorkPackage(
                workspace_id=workspace.id,
                partner_company_id=company_a.id,
                title="Company A package",
            )
            package_b = WorkPackage(
                workspace_id=workspace.id,
                partner_company_id=company_b.id,
                title="Company B package",
            )
            crew_b = PartnerCrew(
                workspace_id=workspace.id,
                partner_company_id=company_b.id,
                name="Company B crew",
            )
            db.add_all([package_a, package_b, crew_b])
            await db.flush()
            task_a = FieldTask(
                work_package_id=package_a.id,
                task_type="install",
                title="Company A task",
            )
            task_b = FieldTask(
                work_package_id=package_b.id,
                task_type="install",
                title="Company B task",
            )
            db.add_all([task_a, task_b])
            await db.commit()
            ids = {
                "workspace": str(workspace.id),
                "company_b": str(company_b.id),
                "worker_a": str(worker_a.id),
                "worker_b": str(worker_b.id),
                "package_a": str(package_a.id),
                "package_b": str(package_b.id),
                "task_a": str(task_a.id),
                "task_b": str(task_b.id),
                "crew_b": str(crew_b.id),
            }

        async with _client() as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": f"partner-a-{suffix}@example.com", "password": password},
            )
            assert login.status_code == 200, login.text
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            listed = await client.get("/api/v1/partner/field-ops/work-packages", headers=headers)
            assert listed.status_code == 200, listed.text
            assert {item["id"] for item in listed.json()["items"]} == {ids["package_a"]}

            blocked_package = await client.get(
                f"/api/v1/partner/field-ops/work-packages/{ids['package_b']}",
                headers=headers,
            )
            assert blocked_package.status_code == 404

            workers = await client.get("/api/v1/partner/field-ops/workers", headers=headers)
            assert workers.status_code == 200, workers.text
            assert {item["id"] for item in workers.json()["items"]} == {ids["worker_a"]}

            cross_worker = await client.post(
                f"/api/v1/partner/field-ops/tasks/{ids['task_a']}/assignments",
                headers=headers,
                json={"assignee_user_id": ids["worker_b"]},
            )
            assert cross_worker.status_code == 404

            cross_crew = await client.post(
                f"/api/v1/partner/field-ops/tasks/{ids['task_a']}/assignments",
                headers=headers,
                json={"assignee_user_id": ids["worker_a"], "crew_id": ids["crew_b"]},
            )
            assert cross_crew.status_code == 404

            assigned = await client.post(
                f"/api/v1/partner/field-ops/tasks/{ids['task_a']}/assignments",
                headers=headers,
                json={"assignee_user_id": ids["worker_a"]},
            )
            assert assigned.status_code == 201, assigned.text

            created_crew = await client.post(
                "/api/v1/partner/field-ops/crews",
                headers=headers,
                json={
                    "workspace_id": ids["workspace"],
                    "partner_company_id": ids["company_b"],
                    "name": "Company A managed crew",
                },
            )
            assert created_crew.status_code == 201, created_crew.text
            assert created_crew.json()["partner_company_id"] != ids["company_b"]
            crew_a_id = created_crew.json()["id"]

            promoted = await client.post(
                f"/api/v1/partner/field-ops/crews/{crew_a_id}/members",
                headers=headers,
                json={"user_id": ids["worker_a"], "role_in_crew": "lead"},
            )
            assert promoted.status_code == 200, promoted.text

            crew_assignment = await client.post(
                f"/api/v1/partner/field-ops/tasks/{ids['task_a']}/assignments",
                headers=headers,
                json={"assignee_user_id": ids["worker_a"], "crew_id": crew_a_id},
            )
            assert crew_assignment.status_code == 201, crew_assignment.text

            blocked_evidence = await client.get(
                f"/api/v1/partner/field-ops/tasks/{ids['task_b']}/evidence",
                headers=headers,
            )
            assert blocked_evidence.status_code == 404

            worker_login = await client.post(
                "/api/v1/auth/login",
                json={"email": f"worker-a-{suffix}@example.com", "password": password},
            )
            assert worker_login.status_code == 200, worker_login.text
            worker_headers = {"Authorization": f"Bearer {worker_login.json()['access_token']}"}
            portals = await client.get("/api/v1/auth/me/portals", headers=worker_headers)
            assert portals.status_code == 200, portals.text
            assert "crew_lead_h5" in {item["portal_key"] for item in portals.json()["items"]}

            crew_dashboard = await client.get("/api/v1/crew", headers=worker_headers)
            assert crew_dashboard.status_code == 200, crew_dashboard.text
            assert crew_dashboard.json()["counts"]["crews"] == 1

            crew_tasks = await client.get("/api/v1/crew/tasks", headers=worker_headers)
            assert crew_tasks.status_code == 200, crew_tasks.text
            assert {item["id"] for item in crew_tasks.json()["items"]} == {ids["task_a"]}

            blocked_crew_task = await client.get(
                f"/api/v1/crew/tasks/{ids['task_b']}",
                headers=worker_headers,
            )
            assert blocked_crew_task.status_code == 404

            reported = await client.post(
                f"/api/v1/crew/tasks/{ids['task_a']}/exceptions",
                headers=worker_headers,
                json={"notes": "Site access delayed", "payload_json": {"severity": "medium"}},
            )
            assert reported.status_code == 200, reported.text
            assert reported.json()["evidence_type"] == "exception"

            completed = await client.post(
                f"/api/v1/crew/tasks/{ids['task_a']}/completion",
                headers=worker_headers,
                json={"notes": "Crew checklist complete"},
            )
            assert completed.status_code == 200, completed.text

    asyncio.run(_run())

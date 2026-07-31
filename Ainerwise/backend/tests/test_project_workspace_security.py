"""Delivery Project Workspace isolation and Field Operations consistency."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import Agent, AgentObjectGrant
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company, User
from app.services.portal_access import ensure_membership, sync_role_portal_access
from app.services.agent_runtime import AgentAuthorizationError, require_agent


def _headers(user_id: uuid.UUID, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user_id), role)}"}


def test_project_workspace_isolation_and_work_package_consistency():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Project A {suffix}", slug=f"project-a-{suffix}")
            workspace_b = Workspace(name=f"Project B {suffix}", slug=f"project-b-{suffix}")
            company = Company(name=f"Shared Buyer {suffix}", type="buyer")
            db.add_all([workspace_a, workspace_b, company])
            await db.flush()

            manager = User(
                email=f"project-manager-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="project_manager",
            )
            buyer = User(
                email=f"project-buyer-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=company.id,
            )
            admin = User(
                email=f"project-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            db.add_all([manager, buyer, admin])
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=manager.id,
                role=manager.role,
                workspace_id=workspace_a.id,
            )
            await ensure_membership(
                db,
                user_id=buyer.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
                company_id=company.id,
            )
            project_a = Project(
                workspace_id=workspace_a.id,
                buyer_company_id=company.id,
                title="Workspace A delivery",
                status="planning",
            )
            project_b = Project(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                title="Workspace B delivery",
                status="planning",
            )
            db.add_all([project_a, project_b])
            await db.flush()
            ticket_b = Ticket(
                project_id=project_b.id,
                buyer_company_id=company.id,
                buyer_user_id=buyer.id,
                title="Workspace B private ticket",
                status="open",
            )
            db.add(ticket_b)
            await db.commit()
            ids = {
                "workspace_a": str(workspace_a.id),
                "workspace_b": str(workspace_b.id),
                "project_a": str(project_a.id),
                "project_b": str(project_b.id),
                "ticket_b": str(ticket_b.id),
            }
            manager_headers = _headers(manager.id, manager.role)
            buyer_headers = _headers(buyer.id, buyer.role)
            admin_headers = _headers(admin.id, admin.role)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            manager_list = await client.get("/api/v1/projects", headers=manager_headers)
            assert manager_list.status_code == 200, manager_list.text
            assert {item["id"] for item in manager_list.json()["items"]} == {ids["project_a"]}

            allowed = await client.get(f"/api/v1/projects/{ids['project_a']}", headers=manager_headers)
            assert allowed.status_code == 200, allowed.text
            denied = await client.get(f"/api/v1/projects/{ids['project_b']}", headers=manager_headers)
            assert denied.status_code == 403, denied.text
            denied_create = await client.post(
                "/api/v1/projects",
                headers=manager_headers,
                json={"workspace_id": ids["workspace_b"], "title": "Cross Workspace write"},
            )
            assert denied_create.status_code == 403, denied_create.text

            buyer_list = await client.get("/api/v1/projects/my", headers=buyer_headers)
            assert buyer_list.status_code == 200, buyer_list.text
            assert {item["id"] for item in buyer_list.json()["items"]} == {ids["project_a"]}
            summary = await client.get("/api/v1/customer/workspace/summary", headers=buyer_headers)
            assert summary.status_code == 200, summary.text
            assert summary.json()["projects"] == 1
            buyer_denied = await client.get(f"/api/v1/projects/{ids['project_b']}", headers=buyer_headers)
            assert buyer_denied.status_code == 403, buyer_denied.text
            ticket_list = await client.get("/api/v1/tickets/my", headers=buyer_headers)
            assert ticket_list.status_code == 200, ticket_list.text
            assert ids["ticket_b"] not in {item["id"] for item in ticket_list.json()["items"]}
            ticket_denied = await client.get(f"/api/v1/tickets/{ids['ticket_b']}", headers=buyer_headers)
            assert ticket_denied.status_code == 403, ticket_denied.text

            mismatch = await client.post(
                "/api/v1/admin/field-ops/work-packages",
                headers=admin_headers,
                json={
                    "workspace_id": ids["workspace_a"],
                    "project_id": ids["project_b"],
                    "title": "Cross Workspace package",
                },
            )
            assert mismatch.status_code == 409, mismatch.text

    asyncio.run(_run())


def test_project_agent_object_grant_requires_exact_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace = Workspace(name=f"Agent Project {suffix}", slug=f"agent-project-{suffix}")
            db.add(workspace)
            await db.flush()
            project = Project(workspace_id=workspace.id, title="Scoped Agent Project", status="planning")
            db.add(project)
            await db.flush()
            support = (
                await db.execute(select(Agent).where(Agent.slug == "support-agent"))
            ).scalar_one()
            db.add(
                AgentObjectGrant(
                    agent_id=support.id,
                    object_type="project",
                    object_id=project.id,
                    scope="project_data",
                    workspace_id=None,
                    granted=True,
                )
            )
            await db.flush()
            with pytest.raises(AgentAuthorizationError, match="lacks project"):
                await require_agent(
                    db,
                    "support-agent",
                    scopes=("project_data",),
                    workflow="ticket_triage",
                    object_type="project",
                    object_id=project.id,
                    workspace_id=workspace.id,
                )
            db.add(
                AgentObjectGrant(
                    agent_id=support.id,
                    object_type="project",
                    object_id=project.id,
                    scope="project_data",
                    workspace_id=workspace.id,
                    granted=True,
                )
            )
            await db.flush()
            authorized = await require_agent(
                db,
                "support-agent",
                scopes=("project_data",),
                workflow="ticket_triage",
                object_type="project",
                object_id=project.id,
                workspace_id=workspace.id,
            )
            assert authorized.id == support.id
            await db.rollback()

    asyncio.run(_run())

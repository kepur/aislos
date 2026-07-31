"""Role-to-portal and role-to-API alignment for internal scoped operators."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.project import Project
from app.models.user import User
from app.services.portal_access import get_default_workspace, sync_role_portal_access


async def _identity(role: str) -> tuple[dict[str, str], uuid.UUID]:
    async with async_session_factory() as db:
        user = User(
            email=f"staff-access-{role}-{uuid.uuid4().hex[:10]}@example.com",
            password_hash=hash_password("staff-access-123"),
            full_name=f"Staff Access {role}",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await sync_role_portal_access(db, user_id=user.id, role=user.role)
        await db.commit()
        return (
            {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"},
            user.id,
        )


async def _portal_keys(client: AsyncClient, headers: dict[str, str]) -> set[str]:
    response = await client.get("/api/v1/auth/me/portals", headers=headers)
    assert response.status_code == 200, response.text
    return {item["portal_key"] for item in response.json()["items"]}


def test_scoped_staff_roles_match_portals_and_api_access():
    async def _run():
        await engine.dispose()
        sales_headers, _ = await _identity("sales_manager")
        project_headers, _ = await _identity("project_manager")
        finance_headers, _ = await _identity("finance")
        buyer_headers, _ = await _identity("buyer")
        admin_headers, _ = await _identity("admin")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            sales_portals = await _portal_keys(client, sales_headers)
            assert "admin_crm" in sales_portals
            assert {"admin_project", "admin_field_ops", "admin_finance"}.isdisjoint(
                sales_portals
            )
            for path in ("/api/v1/leads", "/api/v1/inquiries", "/api/v1/tickets"):
                response = await client.get(path, headers=sales_headers)
                assert response.status_code == 200, (path, response.text)
            for path in ("/api/v1/projects", "/api/v1/project-finances"):
                response = await client.get(path, headers=sales_headers)
                assert response.status_code == 403, (path, response.text)

            project_portals = await _portal_keys(client, project_headers)
            assert {"admin_project", "admin_field_ops"} <= project_portals
            assert {"admin_crm", "admin_finance"}.isdisjoint(project_portals)
            response = await client.get("/api/v1/projects", headers=project_headers)
            assert response.status_code == 200, response.text
            for path in ("/api/v1/leads", "/api/v1/project-finances"):
                response = await client.get(path, headers=project_headers)
                assert response.status_code == 403, (path, response.text)

            finance_portals = await _portal_keys(client, finance_headers)
            assert "admin_finance" in finance_portals
            assert {"admin_crm", "admin_project", "admin_field_ops"}.isdisjoint(
                finance_portals
            )
            for path in ("/api/v1/leads", "/api/v1/projects"):
                response = await client.get(path, headers=finance_headers)
                assert response.status_code == 403, (path, response.text)

            for path in (
                "/api/v1/leads",
                "/api/v1/inquiries",
                "/api/v1/tickets",
                "/api/v1/projects",
                "/api/v1/project-finances",
                "/api/v1/proposals",
                "/api/v1/product-compatibility",
                "/api/v1/products/admin/all",
            ):
                response = await client.get(path, headers=buyer_headers)
                assert response.status_code == 403, (path, response.text)

            missing_id = uuid.uuid4()
            for path in (
                f"/api/v1/inquiries/{missing_id}",
                f"/api/v1/proposals/{missing_id}",
                f"/api/v1/proposals/{missing_id}/bom",
            ):
                response = await client.get(path, headers=buyer_headers)
                assert response.status_code == 403, (path, response.text)

            sales_inquiry = await client.get(
                f"/api/v1/inquiries/{missing_id}", headers=sales_headers
            )
            assert sales_inquiry.status_code == 404, sales_inquiry.text
            sales_proposals = await client.get(
                "/api/v1/proposals", headers=sales_headers
            )
            assert sales_proposals.status_code == 403, sales_proposals.text
            admin_proposals = await client.get(
                "/api/v1/proposals", headers=admin_headers
            )
            assert admin_proposals.status_code == 200, admin_proposals.text
            admin_compatibility = await client.get(
                "/api/v1/product-compatibility", headers=admin_headers
            )
            assert admin_compatibility.status_code == 200, admin_compatibility.text
            admin_products = await client.get(
                "/api/v1/products/admin/all", headers=admin_headers
            )
            assert admin_products.status_code == 200, admin_products.text

    asyncio.run(_run())


def test_project_manager_can_read_project_detail_without_bypassing_customer_ownership():
    async def _run():
        await engine.dispose()
        project_headers, _ = await _identity("project_manager")
        buyer_headers, _ = await _identity("buyer")

        async with async_session_factory() as db:
            workspace = await get_default_workspace(db)
            assert workspace is not None
            project = Project(
                workspace_id=workspace.id,
                title="Scoped role access project",
                status="planning",
            )
            db.add(project)
            await db.commit()
            project_id = project.id

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            allowed = await client.get(
                f"/api/v1/projects/{project_id}", headers=project_headers
            )
            assert allowed.status_code == 200, allowed.text

            denied = await client.get(
                f"/api/v1/projects/{project_id}", headers=buyer_headers
            )
            assert denied.status_code == 403, denied.text

    asyncio.run(_run())

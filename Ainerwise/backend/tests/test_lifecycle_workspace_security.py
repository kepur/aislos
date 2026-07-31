"""Workspace link validation for lifecycle and installed-asset resources."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lifecycle import AMCContract
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.user import Company, User
from app.services.portal_access import ensure_membership


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}


def test_lifecycle_links_and_customer_views_are_workspace_scoped():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Lifecycle A {suffix}", slug=f"lifecycle-a-{suffix}")
            workspace_b = Workspace(name=f"Lifecycle B {suffix}", slug=f"lifecycle-b-{suffix}")
            company = Company(name=f"Lifecycle buyer {suffix}", type="buyer")
            db.add_all([workspace_a, workspace_b, company])
            await db.flush()
            admin = User(
                email=f"lifecycle-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            buyer = User(
                email=f"lifecycle-buyer-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=company.id,
            )
            db.add_all([admin, buyer])
            await db.flush()
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
                title="Lifecycle A project",
                status="active",
            )
            project_b = Project(
                workspace_id=workspace_b.id,
                buyer_company_id=company.id,
                title="Lifecycle B private project",
                status="active",
            )
            db.add_all([project_a, project_b])
            await db.flush()
            private_amc = AMCContract(
                workspace_id=workspace_b.id,
                customer_id=company.id,
                package="private-workspace-b",
            )
            db.add(private_amc)
            await db.commit()
            ids = {
                "company": str(company.id),
                "workspace_a": str(workspace_a.id),
                "workspace_b": str(workspace_b.id),
                "project_a": str(project_a.id),
                "project_b": str(project_b.id),
                "private_amc": str(private_amc.id),
            }
            admin_headers = _headers(admin)
            buyer_headers = _headers(buyer)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            site = await client.post(
                "/api/v1/admin/sites",
                headers=admin_headers,
                json={
                    "workspace_id": ids["workspace_a"],
                    "company_id": ids["company"],
                    "name": "Workspace A site",
                },
            )
            assert site.status_code == 200, site.text
            assert site.json()["workspace_id"] == ids["workspace_a"]
            site_id = site.json()["id"]

            asset_mismatch = await client.post(
                "/api/v1/admin/assets",
                headers=admin_headers,
                json={
                    "site_id": site_id,
                    "project_id": ids["project_b"],
                    "name": "Cross Workspace asset",
                },
            )
            assert asset_mismatch.status_code == 409, asset_mismatch.text
            asset = await client.post(
                "/api/v1/admin/assets",
                headers=admin_headers,
                json={
                    "site_id": site_id,
                    "project_id": ids["project_a"],
                    "name": "Workspace A asset",
                },
            )
            assert asset.status_code == 200, asset.text
            assert asset.json()["workspace_id"] == ids["workspace_a"]

            amc_mismatch = await client.post(
                "/api/v1/amc-contracts",
                headers=admin_headers,
                json={
                    "workspace_id": ids["workspace_b"],
                    "project_id": ids["project_a"],
                    "customer_id": ids["company"],
                    "package": "invalid",
                },
            )
            assert amc_mismatch.status_code == 409, amc_mismatch.text
            amc = await client.post(
                "/api/v1/amc-contracts",
                headers=admin_headers,
                json={
                    "project_id": ids["project_a"],
                    "customer_id": ids["company"],
                    "package": "workspace-a",
                },
            )
            assert amc.status_code == 201, amc.text
            assert amc.json()["workspace_id"] == ids["workspace_a"]

            monitoring = await client.post(
                "/api/v1/monitoring-points",
                headers=admin_headers,
                json={"project_id": ids["project_b"], "device_name": "Workspace B point"},
            )
            assert monitoring.status_code == 201, monitoring.text
            assert monitoring.json()["workspace_id"] == ids["workspace_b"]
            maintenance_mismatch = await client.post(
                "/api/v1/maintenance-schedules",
                headers=admin_headers,
                json={
                    "project_id": ids["project_a"],
                    "monitoring_point_id": monitoring.json()["id"],
                    "task_type": "inspection",
                },
            )
            assert maintenance_mismatch.status_code == 409, maintenance_mismatch.text

            portal_amc = await client.get(
                f"/api/v1/portal/projects/{ids['project_a']}/amc-contracts",
                headers=buyer_headers,
            )
            assert portal_amc.status_code == 200, portal_amc.text
            packages = {item["package"] for item in portal_amc.json()["items"]}
            assert "workspace-a" in packages
            assert "private-workspace-b" not in packages

    asyncio.run(_run())

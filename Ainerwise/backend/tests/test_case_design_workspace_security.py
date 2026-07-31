"""Workspace consistency for Living Cases and Design Revisions."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.asset import Site
from app.models.portal_access import Workspace
from app.models.project import Project
from app.models.user import User


def test_case_and_design_links_must_share_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Case A {suffix}", slug=f"case-a-{suffix}")
            workspace_b = Workspace(name=f"Case B {suffix}", slug=f"case-b-{suffix}")
            admin = User(
                email=f"case-admin-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="admin",
            )
            db.add_all([workspace_a, workspace_b, admin])
            await db.flush()
            project_a = Project(workspace_id=workspace_a.id, title="Workspace A project")
            site_b = Site(workspace_id=workspace_b.id, name="Workspace B site")
            db.add_all([project_a, site_b])
            await db.commit()
            headers = {
                "Authorization": f"Bearer {create_access_token(str(admin.id), admin.role)}"
            }
            ids = {
                "workspace_a": str(workspace_a.id),
                "workspace_b": str(workspace_b.id),
                "project_a": str(project_a.id),
                "site_b": str(site_b.id),
            }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            case = await client.post(
                "/api/v1/admin/cases",
                headers=headers,
                json={"title": "Scoped case", "project_id": ids["project_a"]},
            )
            assert case.status_code == 200, case.text
            assert case.json()["workspace_id"] == ids["workspace_a"]
            mixed_case = await client.post(
                "/api/v1/admin/cases",
                headers=headers,
                json={
                    "title": "Mixed case",
                    "workspace_id": ids["workspace_b"],
                    "project_id": ids["project_a"],
                },
            )
            assert mixed_case.status_code == 409, mixed_case.text
            design = await client.post(
                "/api/v1/admin/design-revisions",
                headers=headers,
                json={
                    "title": "Scoped design",
                    "file_minio_key": "designs/scoped.pdf",
                    "project_id": ids["project_a"],
                },
            )
            assert design.status_code == 200, design.text
            assert design.json()["workspace_id"] == ids["workspace_a"]
            mixed_design = await client.post(
                "/api/v1/admin/design-revisions",
                headers=headers,
                json={
                    "title": "Mixed design",
                    "file_minio_key": "designs/mixed.pdf",
                    "project_id": ids["project_a"],
                    "site_id": ids["site_b"],
                },
            )
            assert mixed_design.status_code == 409, mixed_design.text

    asyncio.run(_run())

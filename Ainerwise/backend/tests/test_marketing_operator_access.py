"""Scoped Marketing operator access across PC/H5 and API surfaces."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import User
from app.services.portal_access import sync_role_portal_access


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _marketing_operator_headers() -> dict:
    email = f"marketing-operator-{uuid.uuid4().hex[:10]}@example.com"
    password = "marketing-test-123"
    async with async_session_factory() as db:
        row = User(
            email=email,
            password_hash=hash_password(password),
            full_name="Scoped Marketing Operator",
            role="marketing_operator",
            is_active=True,
        )
        db.add(row)
        await db.flush()
        await sync_role_portal_access(db, user_id=row.id, role=row.role)
        await db.commit()

    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_marketing_operator_is_scoped_to_marketing_portals_and_apis():
    async def _run():
        await engine.dispose()
        headers = await _marketing_operator_headers()
        async with _client() as client:
            portals = await client.get("/api/v1/auth/me/portals", headers=headers)
            assert portals.status_code == 200, portals.text
            portal_keys = {item["portal_key"] for item in portals.json()["items"]}
            assert {"marketing_pc", "marketing_h5"} <= portal_keys
            assert "admin_marketing" not in portal_keys
            assert "admin_audit" not in portal_keys
            assert "admin_finance" not in portal_keys

            dashboard = await client.get("/api/v1/marketing/dashboard", headers=headers)
            assert dashboard.status_code == 200, dashboard.text
            briefs = await client.get("/api/v1/admin/marketing/creative-briefs", headers=headers)
            assert briefs.status_code == 200, briefs.text
            integration_clients = await client.get(
                "/api/v1/admin/marketing/integration-clients", headers=headers
            )
            assert integration_clients.status_code == 200, integration_clients.text

            users = await client.get("/api/v1/users", headers=headers)
            assert users.status_code == 403
            cebu_admin = await client.get("/api/v1/admin/cebu/staff", headers=headers)
            assert cebu_admin.status_code == 403

    asyncio.run(_run())


def test_internal_roles_cannot_be_self_registered():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            for role in ("admin", "marketing_operator", "finance", "partner_worker"):
                response = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": f"forbidden-{role}-{uuid.uuid4().hex[:8]}@example.com",
                        "password": "forbidden-role-123",
                        "role": role,
                    },
                )
                assert response.status_code == 403, response.text

    asyncio.run(_run())

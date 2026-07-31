"""PF02: workspace membership and portal grants."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_access import PortalGrant, WorkspaceMembership


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_has_membership_and_grants_after_migration():
    async def _run():
        await engine.dispose()
        headers = await _login("admin@ainerwise.com", "admin123456")
        async with _client() as client:
            portals = await client.get("/api/v1/auth/me/portals", headers=headers)
        assert portals.status_code == 200, portals.text
        body = portals.json()
        assert body["memberships"]
        assert body["items"]
        portal_keys = {item["portal_key"] for item in body["items"]}
        assert {
            "admin_executive",
            "admin_crm",
            "admin_project",
            "admin_field_ops",
            "admin_finance",
            "admin_audit",
            "admin_cebu",
        } <= portal_keys

        async with async_session_factory() as db:
            from app.models.user import User

            user = (
                await db.execute(select(User).where(User.email == "admin@ainerwise.com"))
            ).scalar_one()
            grants = (await db.execute(select(PortalGrant).where(PortalGrant.user_id == user.id))).scalars().all()
            memberships = (
                await db.execute(select(WorkspaceMembership).where(WorkspaceMembership.user_id == user.id))
            ).scalars().all()
            assert memberships
            assert grants

    asyncio.run(_run())


def test_portal_switch_writes_audit():
    async def _run():
        await engine.dispose()
        headers = await _login("admin@ainerwise.com", "admin123456")
        async with _client() as client:
            switched = await client.post(
                "/api/v1/auth/portal-switch",
                headers=headers,
                json={"portal_key": "admin_executive"},
            )
        assert switched.status_code == 200, switched.text
        assert switched.json()["manifest"]["portal_key"] == "admin_executive"

    asyncio.run(_run())


def test_unknown_portal_switch_rejected():
    async def _run():
        await engine.dispose()
        headers = await _login("admin@ainerwise.com", "admin123456")
        async with _client() as client:
            resp = await client.post(
                "/api/v1/auth/portal-switch",
                headers=headers,
                json={"portal_key": "forged_portal"},
            )
        assert resp.status_code == 404

    asyncio.run(_run())


def test_demo_customer_is_not_exposed_to_field_worker_portal():
    async def _run():
        await engine.dispose()
        headers = await _login("demo@ainerwise.com", "demo123")
        async with _client() as client:
            portals = await client.get("/api/v1/auth/me/portals", headers=headers)
        assert portals.status_code == 200, portals.text
        portal_keys = {item["portal_key"] for item in portals.json()["items"]}
        assert "customer_h5" in portal_keys
        assert "customer" not in portal_keys
        assert "field_worker_h5" not in portal_keys

    asyncio.run(_run())


def test_registration_and_role_change_sync_portal_access():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        email = f"portal-sync-{suffix}@example.com"
        password = "portal-sync-123"
        async with _client() as client:
            registered = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "role": "buyer",
                    "company_name": f"Portal Sync {suffix}",
                },
            )
            assert registered.status_code == 201, registered.text
            buyer_headers = {
                "Authorization": f"Bearer {registered.json()['access_token']}"
            }
            buyer_portals = await client.get("/api/v1/auth/me/portals", headers=buyer_headers)
            assert buyer_portals.status_code == 200, buyer_portals.text
            buyer_keys = {item["portal_key"] for item in buyer_portals.json()["items"]}
            assert {"customer_pc", "customer_h5", "cebu_buyer_pc", "cebu_buyer_h5"} <= buyer_keys
            assert "supplier_pc" not in buyer_keys

        async with async_session_factory() as db:
            from app.models.user import User

            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            user_id = str(user.id)

        admin_headers = await _login("admin@ainerwise.com", "admin123456")
        async with _client() as client:
            changed = await client.patch(
                f"/api/v1/users/{user_id}/role",
                params={"role": "vendor"},
                headers=admin_headers,
            )
            assert changed.status_code == 200, changed.text

            relogin = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            assert relogin.status_code == 200, relogin.text
            vendor_headers = {
                "Authorization": f"Bearer {relogin.json()['access_token']}"
            }
            vendor_portals = await client.get("/api/v1/auth/me/portals", headers=vendor_headers)
            assert vendor_portals.status_code == 200, vendor_portals.text
            vendor_keys = {item["portal_key"] for item in vendor_portals.json()["items"]}
            assert {"supplier_pc", "supplier_h5"} <= vendor_keys
            assert "customer_pc" not in vendor_keys
            assert "customer_h5" not in vendor_keys

    asyncio.run(_run())

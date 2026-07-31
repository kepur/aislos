"""Demo mode persistence and login guard."""
import asyncio

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.services.demo_mode import is_demo_mode_enabled, set_demo_mode_enabled


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_demo_mode_persisted_and_blocks_demo_buyer():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await set_demo_mode_enabled(db, True)

        async with _client() as client:
            mode = await client.get("/api/v1/demo-mode")
            assert mode.status_code == 200
            assert mode.json()["enabled"] is True
            assert mode.json()["buyer"]["email"] == "demo@ainerwise.com"
            assert "admin" not in mode.json()
            assert "service_accounts" not in mode.json()

            admin = await _admin_headers()
            admin_mode = await client.get("/api/v1/demo-mode/admin", headers=admin)
            assert admin_mode.status_code == 200
            admin_body = admin_mode.json()
            assert admin_body["admin"]["email"] == "admin@ainerwise.com"
            assert admin_body["service_accounts"]
            matrix = {row["key"]: row for row in admin_body["account_matrix"]}
            assert {"demo_customer", "store_admin", "marketing_operator", "agent_operator", "kiosk_device"} <= set(matrix)
            assert matrix["demo_customer"]["login_blocked_when_demo_off"] is True
            assert matrix["kiosk_device"]["auth_type"] == "device_token"
            off = await client.patch("/api/v1/demo-mode", headers=admin, json={"enabled": False})
            assert off.status_code == 200
            assert off.json()["enabled"] is False

            public_off = await client.get("/api/v1/demo-mode")
            assert "buyer" not in public_off.json()

            blocked = await client.post(
                "/api/v1/auth/login",
                json={"email": "demo@ainerwise.com", "password": "demo123"},
            )
            assert blocked.status_code == 403

            on = await client.patch("/api/v1/demo-mode", headers=admin, json={"enabled": True})
            assert on.status_code == 200

            ok = await client.post(
                "/api/v1/auth/login",
                json={"email": "demo@ainerwise.com", "password": "demo123"},
            )
            assert ok.status_code == 200, ok.text

        async with async_session_factory() as db:
            assert await is_demo_mode_enabled(db) is True

    asyncio.run(_run())

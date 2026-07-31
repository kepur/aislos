"""Phase 2: Cebu trade domain on Core."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.commerce import CommerceOrder, ProcurementRequest


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _demo_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@ainerwise.com", "password": "demo123"},
        )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_commerce_request_publish_and_candidates():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        demo = await _demo_headers()
        async with _client() as client:
            cat = await client.post(
                "/api/v1/commerce/category-schemas",
                headers=admin,
                json={"slug": f"smart-lighting-{uuid.uuid4().hex[:6]}", "name": "Smart Lighting", "definition": {"fields": []}},
            )
            assert cat.status_code == 201, cat.text
            cat_id = cat.json()["id"]

            req = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=demo,
                json={"title": "Hotel lobby retrofit", "category_schema_id": cat_id, "portal_key": "cebu"},
            )
            assert req.status_code == 201, req.text
            rid = req.json()["id"]

            pub = await client.post(f"/api/v1/commerce/procurement-requests/{rid}/publish", headers=demo)
            assert pub.status_code == 200, pub.text
            assert pub.json()["status"] == "published"

            candidates = await client.get(
                f"/api/v1/commerce/procurement-requests/{rid}/supplier-candidates",
                headers=demo,
            )
            assert candidates.status_code == 200

    asyncio.run(_run())


def test_legacy_bridge_creates_procurement_request_and_lead():
    async def _run():
        await engine.dispose()
        from tests.test_legacy_bridge import BASE, _sign

        import json

        body = {
            "event_type": "procurement.request.created",
            "portal_key": "cebu",
            "payload": {
                "legacy_request_id": f"legacy-{uuid.uuid4().hex[:8]}",
                "title": "Bridge test request",
                "contact_email": "bridge@test.local",
                "description": "From legacy bridge",
            },
        }
        raw = json.dumps(body).encode()
        headers = _sign(raw)
        async with _client() as client:
            resp = await client.post(BASE, headers=headers, content=raw)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("lead_id")
        assert data.get("procurement_request_id")

        async with async_session_factory() as db:
            req = await db.get(ProcurementRequest, uuid.UUID(data["procurement_request_id"]))
            assert req is not None
            assert req.legacy_request_id

    asyncio.run(_run())

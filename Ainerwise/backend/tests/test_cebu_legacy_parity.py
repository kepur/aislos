"""P3-06: Legacy Cebu compat routes match Core commerce behaviour."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from tests.route_utils import registered_route_paths


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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_legacy_intent_and_candidates_match_core():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        demo = await _demo_headers()
        slug = f"parity-{uuid.uuid4().hex[:6]}"
        async with _client() as client:
            cat = await client.post(
                "/api/v1/commerce/category-schemas",
                headers=admin,
                json={"slug": slug, "name": "Parity Cat", "definition": {}},
            )
            cat_id = cat.json()["id"]

            legacy_intent = await client.post(
                "/api/v1/cebu-compat/intents",
                headers=demo,
                json={"title": "Legacy intent", "category_schema_id": cat_id, "portal_key": "cebu"},
            )
            assert legacy_intent.status_code == 201, legacy_intent.text
            intent_id = legacy_intent.json()["id"]

            core_intent = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=demo,
                json={"title": "Core intent", "category_schema_id": cat_id, "portal_key": "cebu"},
            )
            assert core_intent.status_code == 201

            pub_legacy = await client.post(
                f"/api/v1/cebu-compat/intents/{intent_id}/publish", headers=demo
            )
            assert pub_legacy.status_code == 200
            assert pub_legacy.json()["status"] == "published"

            legacy_candidates = await client.get(
                f"/api/v1/cebu-compat/intents/{intent_id}/supplier-candidates", headers=demo
            )
            core_candidates = await client.get(
                f"/api/v1/commerce/procurement-requests/{intent_id}/supplier-candidates",
                headers=demo,
            )
            assert legacy_candidates.status_code == 200
            assert core_candidates.status_code == 200
            assert legacy_candidates.json()["total"] == core_candidates.json()["total"]
            if legacy_candidates.json()["items"]:
                item = legacy_candidates.json()["items"][0]
                assert "catalog_item_id" in item
                detail = await client.get(
                    f"/api/v1/cebu-compat/intents/{intent_id}/supplier-candidates/{item['catalog_item_id']}",
                    headers=demo,
                )
                assert detail.status_code == 200
                assert detail.json()["item"]["catalog_item_id"] == item["catalog_item_id"]

    asyncio.run(_run())


def test_compat_routes_registered():
    paths = registered_route_paths(app)
    for p in (
        "/api/v1/cebu-compat/intents",
        "/api/v1/cebu-compat/intents/{intent_id}/supplier-candidates",
        "/api/v1/cebu-compat/intents/{intent_id}/supplier-candidates/{catalog_item_id}/bind",
    ):
        assert p in paths, p

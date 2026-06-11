"""Cumulative verify gates for MI01-MI04 (independent verification agent)."""
import asyncio
import uuid

from app.db.session import engine
from tests.test_marketing_creative_briefs import BRIEF_BODY, _admin_headers, _client
from tests.test_media_integration_export import _create_integration_client, _integration_headers


def test_integration_client_cannot_call_admin_marketing_api():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        ih = _integration_headers(ic["client_secret"])
        async with _client() as client:
            resp = await client.get("/api/v1/admin/marketing/creative-briefs", headers=ih)
        assert resp.status_code in (401, 403), resp.text

    asyncio.run(_run())


def test_integration_client_cannot_approve_marketing_asset():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        ih = _integration_headers(ic["client_secret"])
        async with _client() as client:
            resp = await client.post(
                "/api/v1/admin/marketing/assets/00000000-0000-0000-0000-000000000001/approve",
                headers=ih,
                json={},
            )
        assert resp.status_code in (401, 403, 404), resp.text

    asyncio.run(_run())


def test_unapproved_brief_not_in_external_request_list():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        ih = _integration_headers(ic["client_secret"])
        unique_key = f"verify-draft-{uuid.uuid4().hex[:8]}"
        body = dict(BRIEF_BODY)
        body["title"] = f"Draft gate {unique_key}"
        body["version"] = dict(BRIEF_BODY["version"])
        body["version"]["deliverables_json"] = [
            {**BRIEF_BODY["version"]["deliverables_json"][0], "key": unique_key}
        ]
        async with _client() as client:
            await client.post("/api/v1/admin/marketing/creative-briefs", headers=admin, json=body)
            listed = await client.get("/api/v1/media-integration/v1/requests", headers=ih)
        assert listed.status_code == 200
        keys = [item["deliverable"]["key"] for item in listed.json().get("items", [])]
        assert unique_key not in keys

    asyncio.run(_run())


def test_invalid_frontend_style_scopes_rejected():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        async with _client() as client:
            resp = await client.post(
                "/api/v1/admin/marketing/integration-clients",
                headers=admin,
                json={
                    "name": "bad-scopes",
                    "scopes": ["requests:read", "requests:claim"],
                },
            )
        assert resp.status_code == 422, resp.text

    asyncio.run(_run())

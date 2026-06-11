"""MI02: Integration Client auth, external Media Request export and claim lifecycle."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.marketing import MarketingMediaRequest
from tests.test_marketing_creative_briefs import BRIEF_BODY, SAMPLE_DELIVERABLE, _admin_headers, _approve_brief, _create_brief, _client

INTEGRATION_SCOPES = ["briefs:read", "briefs:claim", "briefs:progress"]


async def _create_integration_client(headers: dict, **kwargs) -> dict:
    body = {
        "name": kwargs.get("name", "Test Media Provider"),
        "scopes": kwargs.get("scopes", INTEGRATION_SCOPES),
        "allowed_region_ids": kwargs.get("allowed_region_ids"),
    }
    async with _client() as client:
        resp = await client.post("/api/v1/admin/marketing/integration-clients", headers=headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _setup_approved_request(headers: dict, region_id: str | None = None) -> tuple[dict, str]:
    body = dict(BRIEF_BODY)
    if region_id:
        body["region_id"] = region_id
    async with _client() as client:
        brief_resp = await client.post("/api/v1/admin/marketing/creative-briefs", headers=headers, json=body)
    assert brief_resp.status_code == 201, brief_resp.text
    brief = brief_resp.json()
    version_id = brief["current_version"]["id"]
    await _approve_brief(headers, version_id)
    async with _client() as client:
        media = await client.post(
            f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
            headers=headers,
        )
    assert media.status_code == 201, media.text
    return media.json()[0], brief


def _integration_headers(secret: str) -> dict:
    return {"Authorization": f"Bearer {secret}"}


def test_media_integration_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/media-integration/v1/requests",
        "/api/v1/media-integration/v1/requests/{request_id}",
        "/api/v1/media-integration/v1/requests/{request_id}/claim",
        "/api/v1/media-integration/v1/requests/{request_id}/heartbeat",
        "/api/v1/admin/marketing/integration-clients",
    ):
        assert p in paths, p


def test_external_client_lists_and_claims_request():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        media_req, _brief = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])

        async with _client() as client:
            listed = await client.get("/api/v1/media-integration/v1/requests", headers=ih)
            assert listed.status_code == 200, listed.text
            assert listed.json()["total"] >= 1
            item = listed.json()["items"][0]
            assert "source_refs" not in str(item).lower()
            assert "review_id" not in item["brief"]
            assert item["deliverable"]["key"] == SAMPLE_DELIVERABLE["key"]

            claimed = await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=ih | {"Idempotency-Key": "claim-1"},
            )
        assert claimed.status_code == 200, claimed.text
        assert claimed.json()["status"] == "claimed"

    asyncio.run(_run())


def test_user_jwt_rejected_by_integration_api():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        async with _client() as client:
            resp = await client.get("/api/v1/media-integration/v1/requests", headers=admin)
        assert resp.status_code == 401

    asyncio.run(_run())


def test_suspended_client_denied():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        async with _client() as client:
            await client.post(
                f"/api/v1/admin/marketing/integration-clients/{ic['id']}/suspend",
                headers=admin,
            )
            resp = await client.get(
                "/api/v1/media-integration/v1/requests",
                headers=_integration_headers(ic["client_secret"]),
            )
        assert resp.status_code == 403

    asyncio.run(_run())


def test_second_client_cannot_claim_active_request():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic1 = await _create_integration_client(admin, name="Provider A")
        ic2 = await _create_integration_client(admin, name="Provider B")
        media_req, _ = await _setup_approved_request(admin)

        async with _client() as client:
            first = await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=_integration_headers(ic1["client_secret"]) | {"Idempotency-Key": "c1"},
            )
            assert first.status_code == 200
            second = await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=_integration_headers(ic2["client_secret"]) | {"Idempotency-Key": "c2"},
            )
        assert second.status_code == 409

    asyncio.run(_run())


def test_claim_idempotency_returns_same_result():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        media_req, _ = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"]) | {"Idempotency-Key": "same-key"}

        async with _client() as client:
            r1 = await client.post(f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim", headers=ih)
            r2 = await client.post(f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim", headers=ih)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["status"] == r2.json()["status"] == "claimed"

    asyncio.run(_run())


def test_idempotency_conflict_on_different_payload():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        media_req, _ = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])
        rid = media_req["id"]

        async with _client() as client:
            await client.post(f"/api/v1/media-integration/v1/requests/{rid}/claim", headers=ih | {"Idempotency-Key": "hb-claim"})
            await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/heartbeat",
                headers=ih | {"Idempotency-Key": "hb-key"},
                json={"progress_percent": 10, "progress_message": "a"},
            )
            conflict = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/heartbeat",
                headers=ih | {"Idempotency-Key": "hb-key"},
                json={"progress_percent": 20, "progress_message": "b"},
            )
        assert conflict.status_code == 409

    asyncio.run(_run())


def test_expired_claim_reopens_request():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic1 = await _create_integration_client(admin, name="Provider A")
        ic2 = await _create_integration_client(admin, name="Provider B")
        media_req, _ = await _setup_approved_request(admin)

        async with _client() as client:
            await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=_integration_headers(ic1["client_secret"]) | {"Idempotency-Key": "exp-1"},
            )

        async with async_session_factory() as db:
            row = (
                await db.execute(
                    select(MarketingMediaRequest).where(MarketingMediaRequest.id == uuid.UUID(media_req["id"]))
                )
            ).scalar_one()
            row.claim_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            await db.commit()

        async with _client() as client:
            reclaimed = await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=_integration_headers(ic2["client_secret"]) | {"Idempotency-Key": "exp-2"},
            )
        assert reclaimed.status_code == 200, reclaimed.text
        assert reclaimed.json()["status"] == "claimed"

    asyncio.run(_run())


def test_region_scoped_client_cannot_see_other_regions():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        region_id = str(uuid.uuid4())
        ic = await _create_integration_client(admin, allowed_region_ids=[region_id])
        await _setup_approved_request(admin)  # no region_id
        ih = _integration_headers(ic["client_secret"])

        async with _client() as client:
            resp = await client.get("/api/v1/media-integration/v1/requests", headers=ih)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    asyncio.run(_run())


def test_insufficient_scope_denied():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin, scopes=["briefs:read"])
        media_req, _ = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])

        async with _client() as client:
            resp = await client.post(
                f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
                headers=ih | {"Idempotency-Key": "no-scope"},
            )
        assert resp.status_code == 403

    asyncio.run(_run())


def test_heartbeat_and_complete_flow():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        media_req, _ = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])
        rid = media_req["id"]

        async with _client() as client:
            await client.post(f"/api/v1/media-integration/v1/requests/{rid}/claim", headers=ih | {"Idempotency-Key": "f1"})
            hb = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/heartbeat",
                headers=ih | {"Idempotency-Key": "f2"},
                json={"progress_percent": 55, "progress_message": "Rendering", "external_job_ref": "job-xyz"},
            )
            assert hb.status_code == 200
            assert hb.json()["status"] == "in_progress"
            done = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/complete",
                headers=ih | {"Idempotency-Key": "f3"},
            )
        assert done.status_code == 200
        assert done.json()["status"] == "completed"

    asyncio.run(_run())


def test_secret_only_shown_on_create_and_rotate():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin)
        assert ic.get("client_secret")
        async with _client() as client:
            listed = await client.get("/api/v1/admin/marketing/integration-clients", headers=admin)
        assert "client_secret" not in str(listed.json())
        async with _client() as client:
            rotated = await client.post(
                f"/api/v1/admin/marketing/integration-clients/{ic['id']}/rotate-secret",
                headers=admin,
            )
        assert rotated.status_code == 200
        assert rotated.json().get("client_secret")

    asyncio.run(_run())

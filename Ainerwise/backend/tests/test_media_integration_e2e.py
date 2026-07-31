"""MI07: end-to-end media integration publish gate."""
import asyncio
import hashlib
import io
import uuid
from datetime import datetime, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.content import PublishJob
from app.models.marketing import MARKETING_ASSETS_BUCKET
from app.services.knowledge import get_minio_client
from tests.test_media_integration_assets import FULL_SCOPES, PNG_BYTES, PNG_SHA256
from tests.test_media_integration_export import (
    _create_integration_client,
    _integration_headers,
    _setup_approved_request,
)
from tests.test_marketing_creative_briefs import _admin_headers

SENSITIVE_MARKERS = (
    "source_refs",
    "review_id",
    "margin",
    "cost_price",
    "crm_internal",
    "ai_analysis_json",
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _assert_no_leaks(payload: object) -> None:
    text = str(payload).lower()
    for marker in SENSITIVE_MARKERS:
        assert marker not in text, marker


async def _full_external_delivery(admin: dict, ih: dict, request_id: str) -> dict:
    async with _client() as client:
        claim = await client.post(
            f"/api/v1/media-integration/v1/requests/{request_id}/claim",
            headers=ih | {"Idempotency-Key": f"e2e-claim-{uuid.uuid4().hex}"},
        )
        assert claim.status_code == 200, claim.text
        _assert_no_leaks(claim.json())

        hb = await client.post(
            f"/api/v1/media-integration/v1/requests/{request_id}/heartbeat",
            headers=ih | {"Idempotency-Key": f"e2e-hb-{uuid.uuid4().hex}"},
            json={"progress_percent": 55, "message": "Rendering"},
        )
        assert hb.status_code == 200, hb.text

        upload_resp = await client.post(
            f"/api/v1/media-integration/v1/requests/{request_id}/uploads",
            headers=ih | {"Idempotency-Key": f"e2e-up-{uuid.uuid4().hex}"},
            json={
                "file_name": "e2e-creative.png",
                "mime_type": "image/png",
                "size_bytes": len(PNG_BYTES),
                "sha256": PNG_SHA256,
            },
        )
        assert upload_resp.status_code == 201, upload_resp.text
        upload = upload_resp.json()

    minio = get_minio_client()
    if not minio.bucket_exists(MARKETING_ASSETS_BUCKET):
        minio.make_bucket(MARKETING_ASSETS_BUCKET)
    minio.put_object(
        MARKETING_ASSETS_BUCKET,
        upload["object_key"],
        io.BytesIO(PNG_BYTES),
        len(PNG_BYTES),
        content_type="image/png",
    )

    async with _client() as client:
        submit = await client.post(
            f"/api/v1/media-integration/v1/requests/{request_id}/assets",
            headers=ih | {"Idempotency-Key": f"e2e-sub-{uuid.uuid4().hex}"},
            json={
                "upload_id": upload["upload_id"],
                "external_asset_ref": f"e2e-{uuid.uuid4().hex}",
                "variant_key": "main",
                "mime_type": "image/png",
                "width": 1080,
                "height": 1080,
                "sha256": PNG_SHA256,
            },
        )
        assert submit.status_code == 201, submit.text
        body = submit.json()
        assert body["status"] == "in_review"

        complete = await client.post(
            f"/api/v1/media-integration/v1/requests/{request_id}/complete",
            headers=ih | {"Idempotency-Key": f"e2e-done-{uuid.uuid4().hex}"},
            json={"message": "Delivered"},
        )
        assert complete.status_code == 200, complete.text

        blocked = await client.post(
            f"/api/v1/admin/marketing/assets/{body['asset_id']}/schedule",
            headers=admin,
            json={
                "platform": "instagram",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert blocked.status_code == 409

        approved = await client.post(
            f"/api/v1/admin/marketing/assets/{body['asset_id']}/approve",
            headers=admin,
            json={"notes": "E2E approved"},
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        scheduled = await client.post(
            f"/api/v1/admin/marketing/assets/{body['asset_id']}/schedule",
            headers=admin,
            json={
                "platform": "instagram",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert scheduled.status_code == 200, scheduled.text
        assert scheduled.json()["status"] == "scheduled"

    async with async_session_factory() as db:
        job = (
            await db.execute(
                select(PublishJob).where(PublishJob.asset_id == uuid.UUID(body["asset_id"]))
            )
        ).scalar_one_or_none()
        assert job is not None
        assert job.status == "scheduled"

    return body


def test_e2e_brief_to_publish_job_happy_path():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin, scopes=FULL_SCOPES, name="MI07 E2E Client")
        media_req, _brief = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])
        await _full_external_delivery(admin, ih, media_req["id"])

    asyncio.run(_run())


def test_e2e_revoked_client_rejected():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin, scopes=FULL_SCOPES)
        async with _client() as client:
            await client.post(
                f"/api/v1/admin/marketing/integration-clients/{ic['id']}/revoke",
                headers=admin,
            )
            resp = await client.get(
                "/api/v1/media-integration/v1/requests",
                headers=_integration_headers(ic["client_secret"]),
            )
        assert resp.status_code == 403

    asyncio.run(_run())


def test_e2e_invalid_integration_token_rejected():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            resp = await client.get(
                "/api/v1/media-integration/v1/requests",
                headers={"Authorization": "Bearer not-a-real-secret"},
            )
        assert resp.status_code == 401

    asyncio.run(_run())


def test_e2e_fail_request_marks_failed():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        ic = await _create_integration_client(admin, scopes=FULL_SCOPES)
        media_req, _ = await _setup_approved_request(admin)
        ih = _integration_headers(ic["client_secret"])
        rid = media_req["id"]
        async with _client() as client:
            await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/claim",
                headers=ih | {"Idempotency-Key": f"fail-claim-{uuid.uuid4().hex}"},
            )
            failed = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/fail",
                headers=ih | {"Idempotency-Key": f"fail-{uuid.uuid4().hex}"},
                json={"failure_code": "provider_offline", "failure_message": "GPU farm offline", "retryable": True},
            )
        assert failed.status_code == 200, failed.text
        assert failed.json()["status"] == "failed"

    asyncio.run(_run())

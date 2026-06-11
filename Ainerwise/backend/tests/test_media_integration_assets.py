"""MI03: presigned upload, external asset import and human review gate."""
import asyncio
import hashlib
import io
import uuid
from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from app.models.marketing import MARKETING_ASSETS_BUCKET
from app.services.knowledge import get_minio_client
from tests.test_marketing_creative_briefs import BRIEF_BODY, _admin_headers, _approve_brief, _create_brief
from tests.test_media_integration_export import (
    INTEGRATION_SCOPES,
    _create_integration_client,
    _integration_headers,
    _setup_approved_request,
)

# Minimal valid PNG (1x1)
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
PNG_SHA256 = hashlib.sha256(PNG_BYTES).hexdigest()

FULL_SCOPES = INTEGRATION_SCOPES + ["assets:upload", "assets:submit"]


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _claimed_request_with_client():
    admin = await _admin_headers()
    ic = await _create_integration_client(admin, scopes=FULL_SCOPES)
    media_req, _ = await _setup_approved_request(admin)
    ih = _integration_headers(ic["client_secret"])
    async with _client() as client:
        await client.post(
            f"/api/v1/media-integration/v1/requests/{media_req['id']}/claim",
            headers=ih | {"Idempotency-Key": f"claim-{uuid.uuid4().hex}"},
        )
    return admin, ic, media_req, ih


def test_upload_and_submit_creates_in_review_asset():
    async def _run():
        await engine.dispose()
        admin, ic, media_req, ih = await _claimed_request_with_client()
        rid = media_req["id"]

        async with _client() as client:
            upload_resp = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/uploads",
                headers=ih | {"Idempotency-Key": f"up-{uuid.uuid4().hex}"},
                json={
                    "file_name": "creative-01.png",
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
                f"/api/v1/media-integration/v1/requests/{rid}/assets",
                headers=ih | {"Idempotency-Key": f"sub-{uuid.uuid4().hex}"},
                json={
                    "upload_id": upload["upload_id"],
                    "external_asset_ref": "provider-asset-001",
                    "variant_key": "variant-a",
                    "mime_type": "image/png",
                    "width": 1080,
                    "height": 1080,
                    "sha256": PNG_SHA256,
                    "metadata": {"generation_note": "test"},
                },
            )
        assert submit.status_code == 201, submit.text
        body = submit.json()
        assert body["status"] == "in_review"
        assert body["review_id"]

        async with _client() as client:
            approve_block = await client.post(
                f"/api/v1/admin/marketing/assets/{body['asset_id']}/schedule",
                headers=admin,
                json={"platform": "instagram", "scheduled_at": datetime.now(timezone.utc).isoformat()},
            )
        assert approve_block.status_code == 409

        async with _client() as client:
            approved = await client.post(
                f"/api/v1/admin/marketing/assets/{body['asset_id']}/approve",
                headers=admin,
                json={"notes": "OK for publish"},
            )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

    asyncio.run(_run())


def test_checksum_mismatch_rejected():
    async def _run():
        await engine.dispose()
        _admin, ic, media_req, ih = await _claimed_request_with_client()
        rid = media_req["id"]
        async with _client() as client:
            upload_resp = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/uploads",
                headers=ih | {"Idempotency-Key": f"up2-{uuid.uuid4().hex}"},
                json={
                    "file_name": "creative-02.png",
                    "mime_type": "image/png",
                    "size_bytes": len(PNG_BYTES),
                    "sha256": PNG_SHA256,
                },
            )
        upload = upload_resp.json()
        minio = get_minio_client()
        minio.put_object(
            MARKETING_ASSETS_BUCKET, upload["object_key"], io.BytesIO(PNG_BYTES), len(PNG_BYTES)
        )
        async with _client() as client:
            bad = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/assets",
                headers=ih | {"Idempotency-Key": f"sub2-{uuid.uuid4().hex}"},
                json={
                    "upload_id": upload["upload_id"],
                    "mime_type": "image/png",
                    "sha256": "0" * 64,
                },
            )
        assert bad.status_code == 422

    asyncio.run(_run())


def test_duplicate_external_asset_ref_is_idempotent():
    async def _run():
        await engine.dispose()
        _admin, ic, media_req, ih = await _claimed_request_with_client()
        rid = media_req["id"]
        ref = f"dup-{uuid.uuid4().hex}"

        async def _submit(idem: str):
            async with _client() as client:
                up = await client.post(
                    f"/api/v1/media-integration/v1/requests/{rid}/uploads",
                    headers=ih | {"Idempotency-Key": f"up-{idem}"},
                    json={
                        "file_name": f"{idem}.png",
                        "mime_type": "image/png",
                        "size_bytes": len(PNG_BYTES),
                        "sha256": PNG_SHA256,
                    },
                )
            upload = up.json()
            minio = get_minio_client()
            minio.put_object(
                MARKETING_ASSETS_BUCKET, upload["object_key"], io.BytesIO(PNG_BYTES), len(PNG_BYTES)
            )
            async with _client() as client:
                return await client.post(
                    f"/api/v1/media-integration/v1/requests/{rid}/assets",
                    headers=ih | {"Idempotency-Key": f"sub-{idem}"},
                    json={
                        "upload_id": upload["upload_id"],
                        "external_asset_ref": ref,
                        "mime_type": "image/png",
                        "sha256": PNG_SHA256,
                    },
                )

        r1 = await _submit("a")
        r2 = await _submit("b")
        assert r1.status_code == 201 and r2.status_code == 201
        assert r1.json()["asset_id"] == r2.json()["asset_id"]

    asyncio.run(_run())


def test_integration_client_cannot_approve_asset():
    async def _run():
        await engine.dispose()
        admin, ic, media_req, ih = await _claimed_request_with_client()
        rid = media_req["id"]
        async with _client() as client:
            up = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/uploads",
                headers=ih | {"Idempotency-Key": "x1"},
                json={
                    "file_name": "x.png",
                    "mime_type": "image/png",
                    "size_bytes": len(PNG_BYTES),
                    "sha256": PNG_SHA256,
                },
            )
        upload = up.json()
        get_minio_client().put_object(
            MARKETING_ASSETS_BUCKET, upload["object_key"], io.BytesIO(PNG_BYTES), len(PNG_BYTES)
        )
        async with _client() as client:
            sub = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/assets",
                headers=ih | {"Idempotency-Key": "x2"},
                json={"upload_id": upload["upload_id"], "mime_type": "image/png", "sha256": PNG_SHA256},
            )
        asset_id = sub.json()["asset_id"]
        async with _client() as client:
            resp = await client.post(
                f"/api/v1/admin/marketing/assets/{asset_id}/approve",
                headers=ih,
                json={"notes": "hack"},
            )
        assert resp.status_code == 401

    asyncio.run(_run())


def test_missing_upload_object_rejected():
    async def _run():
        await engine.dispose()
        _admin, ic, media_req, ih = await _claimed_request_with_client()
        rid = media_req["id"]
        async with _client() as client:
            up = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/uploads",
                headers=ih | {"Idempotency-Key": "m1"},
                json={
                    "file_name": "missing.png",
                    "mime_type": "image/png",
                    "size_bytes": len(PNG_BYTES),
                    "sha256": PNG_SHA256,
                },
            )
        upload = up.json()
        async with _client() as client:
            resp = await client.post(
                f"/api/v1/media-integration/v1/requests/{rid}/assets",
                headers=ih | {"Idempotency-Key": "m2"},
                json={"upload_id": upload["upload_id"], "mime_type": "image/png", "sha256": PNG_SHA256},
            )
        assert resp.status_code == 422

    asyncio.run(_run())

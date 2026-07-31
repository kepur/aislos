"""Field Worker offline sync, QR bind, signature, and version conflict."""
import asyncio
import base64
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app

TINY_PNG_DATA_URL = "data:image/png;base64," + base64.b64encode(
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
).decode()


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _worker_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "installer@example.com", "password": "worker123"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _setup_assigned_task(client, admin: dict, worker_h: dict) -> str:
    from app.db.session import async_session_factory
    from app.models.user import User
    from app.services.portal_access import ensure_grant, ensure_membership, get_default_workspace
    from sqlalchemy import select

    ws_resp = await client.get("/api/v1/auth/me/portals", headers=worker_h)
    assert ws_resp.status_code == 200

    async with async_session_factory() as db:
        user = (await db.execute(select(User).where(User.email == "installer@example.com"))).scalar_one()
        ws = await get_default_workspace(db)
        await ensure_membership(db, user_id=user.id, membership_type="field_worker", workspace_id=ws.id)
        await ensure_grant(db, user_id=user.id, grant_key="field_task.read_assigned", workspace_id=ws.id)
        await db.commit()
        workspace_id = str(ws.id)
        worker_id = str(user.id)

    pkg = await client.post(
        "/api/v1/admin/field-ops/work-packages",
        headers=admin,
        json={"workspace_id": workspace_id, "title": "Offline sync package"},
    )
    assert pkg.status_code == 201, pkg.text
    package_id = pkg.json()["id"]

    task = await client.post(
        f"/api/v1/admin/field-ops/work-packages/{package_id}/tasks",
        headers=admin,
        json={"work_package_id": package_id, "task_type": "install", "title": "Offline panel"},
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]

    assigned = await client.post(
        f"/api/v1/admin/field-ops/tasks/{task_id}/assignments",
        headers=admin,
        json={"assignee_user_id": worker_id},
    )
    assert assigned.status_code == 201, assigned.text
    return task_id


def test_offline_sync_and_version_conflict():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        worker_h = await _worker_headers()

        async with _client() as client:
            task_id = await _setup_assigned_task(client, admin, worker_h)

            patched = await client.patch(
                f"/api/v1/field/tasks/{task_id}/status",
                headers=worker_h,
                json={"status": "in_progress", "offline_version": 0},
            )
            assert patched.status_code == 200, patched.text
            assert patched.json()["offline_version"] == 1

            conflict = await client.patch(
                f"/api/v1/field/tasks/{task_id}/status",
                headers=worker_h,
                json={"status": "paused", "offline_version": 0},
            )
            assert conflict.status_code == 409

            sync = await client.post(
                "/api/v1/field/sync",
                headers=worker_h,
                json={
                    "items": [
                        {
                            "type": "evidence",
                            "task_id": task_id,
                            "idempotency_key": f"ev-{uuid.uuid4().hex}",
                            "evidence_type": "location",
                            "payload_json": {"lat": 44.8, "lng": 20.4},
                        }
                    ]
                },
            )
            assert sync.status_code == 200, sync.text
            assert sync.json()["items"][0]["status"] == "ok"

    asyncio.run(_run())


def test_field_worker_qr_bind_and_signature():
    async def _run():
        await engine.dispose()
        admin = await _admin_headers()
        worker_h = await _worker_headers()

        async with _client() as client:
            task_id = await _setup_assigned_task(client, admin, worker_h)

            qr = await client.post(
                f"/api/v1/field/tasks/{task_id}/bind-qr",
                headers=worker_h,
                json={"qr_code": f"DEV-{uuid.uuid4().hex[:8]}", "device_label": "Panel A"},
            )
            assert qr.status_code == 200, qr.text
            assert qr.json()["evidence_type"] == "qr"
            assert qr.json()["payload_json"]["qr_code"]

            sig = await client.post(
                f"/api/v1/field/tasks/{task_id}/signature",
                headers=worker_h,
                json={
                    "signature_data_url": TINY_PNG_DATA_URL,
                    "signer_name": "Site Manager",
                    "idempotency_key": f"sig-{uuid.uuid4().hex}",
                },
            )
            assert sig.status_code == 200, sig.text
            assert sig.json()["evidence_type"] == "signature"

            offline_qr = await client.post(
                "/api/v1/field/sync",
                headers=worker_h,
                json={
                    "items": [
                        {
                            "type": "evidence",
                            "task_id": task_id,
                            "idempotency_key": f"ev-qr-{uuid.uuid4().hex}",
                            "evidence_type": "qr",
                            "payload_json": {"qr_code": "OFFLINE-DEV-99"},
                        }
                    ]
                },
            )
            assert offline_qr.status_code == 200
            assert offline_qr.json()["items"][0]["status"] == "ok"

    asyncio.run(_run())

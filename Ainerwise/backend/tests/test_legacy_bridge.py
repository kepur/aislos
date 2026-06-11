"""SP03: legacy bridge signature, idempotency, and audit."""
import asyncio
import hashlib
import hmac
import json
import time
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.lead import Lead
from app.models.legacy_bridge import LegacyBridgeIdempotency
from app.services.legacy_bridge import LEGACY_BRIDGE_STREAM_KEY
from sqlalchemy import select

BASE = "/api/v1/legacy-bridge/events"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _sign(body: bytes, *, timestamp: str | None = None) -> dict[str, str]:
    ts = timestamp or str(int(time.time()))
    signing = f"{ts}\nPOST\n{BASE}\n{hashlib.sha256(body).hexdigest()}"
    sig = hmac.new(
        settings.LEGACY_BRIDGE_SECRET.encode(),
        signing.encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-Legacy-Client-Id": settings.LEGACY_BRIDGE_CLIENT_ID,
        "X-Legacy-Timestamp": ts,
        "X-Legacy-Signature": sig,
        "X-Idempotency-Key": f"idem-{uuid.uuid4().hex[:12]}",
    }


def test_legacy_bridge_rejects_missing_signature():
    async def _run():
        await engine.dispose()
        async with _client() as ac:
            resp = await ac.post(
                BASE,
                json={"event_type": "procurement.request.created", "payload": {}},
            )
        assert resp.status_code == 401

    asyncio.run(_run())


def test_legacy_bridge_creates_lead_and_is_idempotent():
    async def _run():
        await engine.dispose()
        payload = {
            "event_type": "procurement.request.created",
            "portal_key": "cebu",
            "payload": {
                "legacy_request_id": "req-100",
                "contact_name": "Cebu Buyer",
                "contact_email": "buyer@cebu.test",
                "project_type": "small_hotel_smart_upgrade",
                "country": "PH",
                "description": "Bridge test",
            },
        }
        body = json.dumps(payload).encode()
        headers = _sign(body)
        idem = headers["X-Idempotency-Key"]

        async with _client() as ac:
            first = await ac.post(BASE, content=body, headers=headers)
            assert first.status_code == 200, first.text
            data = first.json()
            assert data["lead_id"]
            assert data["idempotency_key"] == idem

            second = await ac.post(BASE, content=body, headers=headers)
            assert second.status_code == 200
            assert second.json()["lead_id"] == data["lead_id"]

        async with async_session_factory() as db:
            lead = await db.get(Lead, uuid.UUID(data["lead_id"]))
            assert lead is not None
            assert lead.source_channel == "cebu_legacy"
            audits = (
                await db.execute(
                    select(AuditLog).where(AuditLog.source == "legacy_bridge")
                )
            ).scalars().all()
            assert audits
            idem_rows = (
                await db.execute(
                    select(LegacyBridgeIdempotency).where(
                        LegacyBridgeIdempotency.idempotency_key == idem
                    )
                )
            ).scalars().all()
            assert len(idem_rows) == 1

    asyncio.run(_run())


def test_legacy_bridge_identity_map():
    async def _run():
        await engine.dispose()
        from app.core.security import hash_password
        from app.models.user import User

        async with async_session_factory() as db:
            user = User(
                email=f"map-{uuid.uuid4().hex[:8]}@test.local",
                password_hash=hash_password("x"),
                full_name="Core User",
                role="buyer",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            core_user_id = str(user.id)

        payload = {
            "event_type": "legacy.identity.map",
            "portal_key": "cebu",
            "payload": {
                "legacy_user_id": "cebu-user-42",
                "core_user_id": core_user_id,
            },
        }
        body = json.dumps(payload).encode()
        headers = _sign(body)

        async with _client() as ac:
            resp = await ac.post(BASE, content=body, headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["mapping_id"]

    asyncio.run(_run())


def test_bridge_stream_key_isolated():
    assert LEGACY_BRIDGE_STREAM_KEY.startswith("cebu-legacy:")

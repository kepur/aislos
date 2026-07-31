import asyncio
import re
import uuid
from urllib.parse import parse_qs, urlparse

from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints import auth
from app.db.session import engine
from app.main import app


def _token_from_body(body: str) -> str:
    match = re.search(r"https?://\S+", body)
    assert match is not None
    return parse_qs(urlparse(match.group(0)).query)["token"][0]


def test_password_reset_is_generic_one_time_and_changes_login(monkeypatch):
    async def _run():
        await engine.dispose()
        email = f"reset-{uuid.uuid4().hex[:10]}@example.com"
        old_password = "old-password-123"
        new_password = "new-password-456"
        sent: list[dict] = []

        async def capture_email(_db, **kwargs):
            sent.append(kwargs)
            return {"sent": True}

        monkeypatch.setattr(auth, "send_email", capture_email)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": old_password, "role": "buyer"},
            )
            assert created.status_code == 201

            requested = await client.post("/api/v1/auth/request-password-reset", json={"email": email})
            assert requested.status_code == 200
            assert "active account exists" in requested.json()["message"]
            assert len(sent) == 1
            token = _token_from_body(sent[0]["body"])
            assert token not in requested.text

            reset = await client.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": new_password},
            )
            assert reset.status_code == 200

            reused = await client.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": "third-password-789"},
            )
            assert reused.status_code == 400
            assert reused.json()["detail"] == "Password reset token is invalid or expired"

            old_login = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": old_password}
            )
            assert old_login.status_code == 401
            new_login = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": new_password}
            )
            assert new_login.status_code == 200

    asyncio.run(_run())


def test_password_reset_does_not_reveal_unknown_accounts(monkeypatch):
    async def _run():
        await engine.dispose()
        sent: list[dict] = []

        async def capture_email(_db, **kwargs):
            sent.append(kwargs)
            return {"sent": True}

        monkeypatch.setattr(auth, "send_email", capture_email)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/request-password-reset",
                json={"email": f"missing-{uuid.uuid4().hex[:10]}@example.com"},
            )
            assert response.status_code == 200
            assert "active account exists" in response.json()["message"]
            assert sent == []

    asyncio.run(_run())

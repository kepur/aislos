import hashlib
import hmac
import json
import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.main as gateway
from app.adapters.base import NormalizedMessage


client = TestClient(gateway.app)


def test_health_exposes_all_shared_adapters():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["channels"] == ["email", "telegram", "whatsapp"]


def test_whatsapp_verification_returns_plain_challenge(monkeypatch):
    monkeypatch.setattr(gateway.adapters["whatsapp"], "verify_token", AsyncMock(return_value="verify-me"))

    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "123456",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "123456"


def test_whatsapp_webhook_requires_valid_signature(monkeypatch):
    secret = "app-secret"
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"profile": {"name": "Ana"}}],
                            "messages": [
                                {
                                    "from": "381601234567",
                                    "id": "wamid.42",
                                    "type": "text",
                                    "text": {"body": "Need a quote"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    monkeypatch.setattr(gateway.adapters["whatsapp"], "app_secret", AsyncMock(return_value=secret))
    monkeypatch.setattr(gateway.database, "store_inbound", AsyncMock(return_value=uuid.uuid4()))
    monkeypatch.setattr(gateway.backend, "forward_inbound", AsyncMock(return_value=None))

    rejected = client.post("/webhooks/whatsapp", content=raw, headers={"content-type": "application/json"})
    accepted = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"content-type": "application/json", "X-Hub-Signature-256": signature},
    )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    gateway.database.store_inbound.assert_awaited()


def test_email_webhook_fails_closed_without_secret(monkeypatch):
    monkeypatch.setattr(gateway.adapters["email"], "webhook_secret", AsyncMock(return_value=""))
    monkeypatch.setattr(
        gateway.adapters["email"],
        "receive",
        AsyncMock(
            return_value=NormalizedMessage(
                external_thread_id="sender@example.com",
                external_message_id="message-1",
                content="Hello",
                contact_name="Sender",
                raw_payload={},
            )
        ),
    )

    response = client.post(
        "/webhooks/email",
        json={"from_email": "sender@example.com", "text": "Hello"},
    )

    assert response.status_code == 503

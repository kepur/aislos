"""SP03: post signed events to Ainerwise Core legacy bridge."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any

import httpx

BRIDGE_PATH = "/api/v1/legacy-bridge/events"


def _sign(secret: str, method: str, path: str, body: bytes, timestamp: str) -> str:
    signing = f"{timestamp}\n{method.upper()}\n{path}\n{hashlib.sha256(body).hexdigest()}"
    return hmac.new(secret.encode(), signing.encode(), hashlib.sha256).hexdigest()


async def post_legacy_event(
    *,
    event_type: str,
    payload: dict[str, Any],
    portal_key: str = "cebu",
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    base_url = os.getenv("AINERWISE_CORE_URL", "http://localhost:8000").rstrip("/")
    client_id = os.getenv("LEGACY_BRIDGE_CLIENT_ID", "cebu-legacy")
    secret = os.getenv("LEGACY_BRIDGE_SECRET", "")
    if not secret:
        raise RuntimeError("LEGACY_BRIDGE_SECRET is not configured")

    body_obj = {
        "event_type": event_type,
        "portal_key": portal_key,
        "payload": payload,
        "correlation_id": correlation_id,
    }
    body = json.dumps(body_obj, separators=(",", ":")).encode()
    ts = str(int(time.time()))
    headers = {
        "Content-Type": "application/json",
        "X-Legacy-Client-Id": client_id,
        "X-Legacy-Timestamp": ts,
        "X-Legacy-Signature": _sign(secret, "POST", BRIDGE_PATH, body, ts),
        "X-Idempotency-Key": idempotency_key or str(uuid.uuid4()),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{base_url}{BRIDGE_PATH}", content=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

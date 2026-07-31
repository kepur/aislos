"""SP03: signed, idempotent Legacy → Core API bridge."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import select

from app.models.commerce import CommerceOrder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.legacy_bridge import LegacyBridgeIdempotency, LegacyIdentityMapping
from app.schemas.legacy_bridge import LegacyBridgeEventIn, LegacyBridgeEventOut
from app.services.audit import append_audit_event
from app.services.event_bus import emit_event
from app.services.legacy_identity import upsert_identity_mapping

LEGACY_BRIDGE_STREAM_KEY = "cebu-legacy:stream:bridge"

ALLOWED_LEGACY_EVENT_TYPES = frozenset(
    {
        "procurement.request.created",
        "procurement.request.published",
        "commerce.order.completed",
        "commerce.dispute.opened",
        "legacy.identity.map",
    }
)

CORE_EVENT_MAP = {
    "procurement.request.created": "procurement.request.created",
    "procurement.request.published": "procurement.request.published",
    "commerce.order.completed": "commerce.order.completed",
    "commerce.dispute.opened": "commerce.dispute.opened",
}


class LegacyBridgeError(ValueError):
    pass


class LegacyBridgeAuthError(LegacyBridgeError):
    pass


def _body_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def verify_legacy_signature(
    *,
    secret: str,
    method: str,
    path: str,
    body: bytes,
    client_id: str,
    timestamp: str,
    signature: str,
    expected_client_id: str,
) -> None:
    if client_id != expected_client_id:
        raise LegacyBridgeAuthError("invalid client id")
    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise LegacyBridgeAuthError("invalid timestamp") from exc
    skew = abs(int(time.time()) - ts)
    if skew > settings.LEGACY_BRIDGE_MAX_SKEW_SECONDS:
        raise LegacyBridgeAuthError("timestamp outside allowed skew")
    signing = f"{timestamp}\n{method.upper()}\n{path}\n{_body_hash(body)}"
    expected = hmac.new(secret.encode("utf-8"), signing.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise LegacyBridgeAuthError("invalid signature")


async def get_idempotent_response(
    db: AsyncSession, *, client_id: str, idempotency_key: str
) -> dict[str, Any] | None:
    result = await db.execute(
        select(LegacyBridgeIdempotency).where(
            LegacyBridgeIdempotency.client_id == client_id,
            LegacyBridgeIdempotency.idempotency_key == idempotency_key,
        )
    )
    row = result.scalar_one_or_none()
    return row.response_json if row else None


async def store_idempotent_response(
    db: AsyncSession,
    *,
    client_id: str,
    idempotency_key: str,
    event_type: str,
    response: dict[str, Any],
) -> None:
    db.add(
        LegacyBridgeIdempotency(
            client_id=client_id,
            idempotency_key=idempotency_key,
            event_type=event_type,
            response_json=response,
        )
    )
    await db.flush()


async def _mirror_to_bridge_stream(
    redis_client: aioredis.Redis | None,
    *,
    event_type: str,
    payload: dict[str, Any],
    correlation_id: str | None,
) -> None:
    owns = redis_client is None
    client = redis_client or aioredis.from_url(settings.REDIS_URL)
    try:
        await client.xadd(
            LEGACY_BRIDGE_STREAM_KEY,
            {
                "type": event_type,
                "payload": json.dumps(payload, sort_keys=True),
                "correlation_id": correlation_id or "",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
            maxlen=10_000,
            approximate=True,
        )
    finally:
        if owns:
            await client.aclose()


async def process_legacy_event(
    db: AsyncSession,
    data: LegacyBridgeEventIn,
    *,
    client_id: str,
    idempotency_key: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> LegacyBridgeEventOut:
    if data.event_type not in ALLOWED_LEGACY_EVENT_TYPES:
        raise LegacyBridgeError(f"event type not allowed: {data.event_type!r}")

    cached = await get_idempotent_response(db, client_id=client_id, idempotency_key=idempotency_key)
    if cached is not None:
        return LegacyBridgeEventOut.model_validate(cached)

    out = LegacyBridgeEventOut(
        event_type=data.event_type,
        idempotency_key=idempotency_key,
        correlation_id=data.correlation_id,
    )
    payload = dict(data.payload)
    payload.setdefault("portal_key", data.portal_key)
    payload.setdefault("legacy_client_id", client_id)

    if data.event_type == "procurement.request.created":
        from app.services.commerce_trade import upsert_request_from_legacy

        req, lead = await upsert_request_from_legacy(db, payload, portal_key=data.portal_key)
        if lead:
            out.lead_id = lead.id
            payload["lead_id"] = str(lead.id)
        payload["procurement_request_id"] = str(req.id)
        out.procurement_request_id = req.id

    elif data.event_type == "procurement.request.published":
        from app.services.commerce_trade import publish_request

        rid = payload.get("procurement_request_id") or payload.get("core_request_id")
        if not rid:
            raise LegacyBridgeError("procurement_request_id required")
        row = await publish_request(db, uuid.UUID(str(rid)))
        payload["procurement_request_id"] = str(row.id)
        out.procurement_request_id = row.id

    elif data.event_type == "commerce.order.completed":
        from app.services.commerce_trade import complete_order

        order = await complete_order(
            db,
            order_id=uuid.UUID(str(payload["order_id"])) if payload.get("order_id") else None,
            legacy_order_id=str(payload.get("legacy_order_id") or ""),
        )
        payload["commerce_order_id"] = str(order.id)
        out.commerce_order_id = order.id

    elif data.event_type == "commerce.dispute.opened":
        from app.models.user import User
        from app.services.commerce_trade import get_order, open_dispute

        order = None
        if payload.get("order_id"):
            order = await get_order(db, uuid.UUID(str(payload["order_id"])))
        elif payload.get("legacy_order_id"):
            order = (
                await db.execute(
                    select(CommerceOrder).where(
                        CommerceOrder.legacy_order_id == str(payload["legacy_order_id"])
                    )
                )
            ).scalar_one_or_none()
        if order is None:
            raise LegacyBridgeError("order not found for dispute")
        system_user = (
            await db.execute(select(User).where(User.role == "super_admin").limit(1))
        ).scalar_one_or_none()
        if system_user is None:
            raise LegacyBridgeError("no system user for bridge dispute")
        dispute = await open_dispute(
            db,
            order_id=order.id,
            user=system_user,
            reason_code=str(payload.get("reason_code") or "legacy_import"),
            description=payload.get("description"),
            legacy_dispute_id=str(payload.get("legacy_dispute_id") or "") or None,
        )
        payload["dispute_id"] = str(dispute.id)
        out.dispute_id = dispute.id
        out.commerce_order_id = order.id

    elif data.event_type == "legacy.identity.map":
        mapping = await upsert_identity_mapping(
            db,
            portal_key=data.portal_key,
            legacy_system=str(payload.get("legacy_system") or "cebu"),
            legacy_user_id=str(payload.get("legacy_user_id") or ""),
            legacy_company_id=payload.get("legacy_company_id"),
            core_user_id=uuid.UUID(str(payload["core_user_id"]))
            if payload.get("core_user_id")
            else None,
            core_company_id=uuid.UUID(str(payload["core_company_id"]))
            if payload.get("core_company_id")
            else None,
            metadata_json=payload.get("metadata"),
        )
        out.mapping_id = mapping.id
        payload["mapping_id"] = str(mapping.id)

    core_type = CORE_EVENT_MAP.get(data.event_type, data.event_type)
    core_event = await emit_event(
        db,
        core_type,
        payload,
        aggregate_type="legacy_bridge",
        aggregate_id=out.lead_id or out.mapping_id or out.procurement_request_id or out.commerce_order_id,
    )
    out.core_event_id = core_event.id

    await append_audit_event(
        db,
        actor_type="system",
        action=f"legacy.bridge.{data.event_type.replace('.', '_')}",
        entity_type="legacy_bridge",
        entity_id=out.lead_id or out.mapping_id or out.procurement_request_id or out.commerce_order_id or core_event.id,
        portal_key=data.portal_key,
        after=payload,
        source="legacy_bridge",
        correlation_id=data.correlation_id,
        ip=ip,
        user_agent=user_agent,
    )

    response = out.model_dump(mode="json")
    await store_idempotent_response(
        db,
        client_id=client_id,
        idempotency_key=idempotency_key,
        event_type=data.event_type,
        response=response,
    )
    await db.commit()

    try:
        await _mirror_to_bridge_stream(
            None,
            event_type=data.event_type,
            payload=payload,
            correlation_id=data.correlation_id,
        )
    except Exception:
        # The Core outbox row is authoritative. A non-authoritative Legacy
        # observability stream must not turn a committed write into a false 5xx.
        pass

    return out

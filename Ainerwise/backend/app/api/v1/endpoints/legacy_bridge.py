"""SP03: Legacy → Core signed event bridge (Cebu migration path)."""
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import DB
from app.core.config import settings
from app.schemas.legacy_bridge import LegacyBridgeEventIn, LegacyBridgeEventOut
from app.services.legacy_bridge import (
    LegacyBridgeAuthError,
    LegacyBridgeError,
    process_legacy_event,
    verify_legacy_signature,
)

router = APIRouter(prefix="/legacy-bridge", tags=["legacy-bridge"])

BRIDGE_PATH = "/api/v1/legacy-bridge/events"


@router.post("/events", response_model=LegacyBridgeEventOut)
async def ingest_legacy_event(
    request: Request,
    db: DB,
    x_legacy_client_id: Annotated[str | None, Header()] = None,
    x_legacy_timestamp: Annotated[str | None, Header()] = None,
    x_legacy_signature: Annotated[str | None, Header()] = None,
    x_idempotency_key: Annotated[str | None, Header()] = None,
):
    if not settings.LEGACY_BRIDGE_SECRET:
        raise HTTPException(status_code=503, detail="Legacy bridge is not configured")
    for header, name in (
        (x_legacy_client_id, "X-Legacy-Client-Id"),
        (x_legacy_timestamp, "X-Legacy-Timestamp"),
        (x_legacy_signature, "X-Legacy-Signature"),
        (x_idempotency_key, "X-Idempotency-Key"),
    ):
        if not header:
            raise HTTPException(status_code=401, detail=f"Missing {name}")

    body = await request.body()
    try:
        data = LegacyBridgeEventIn.model_validate_json(body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid event payload") from exc

    try:
        verify_legacy_signature(
            secret=settings.LEGACY_BRIDGE_SECRET,
            method=request.method,
            path=BRIDGE_PATH,
            body=body,
            client_id=x_legacy_client_id,
            timestamp=x_legacy_timestamp,
            signature=x_legacy_signature,
            expected_client_id=settings.LEGACY_BRIDGE_CLIENT_ID,
        )
    except LegacyBridgeAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        return await process_legacy_event(
            db,
            data,
            client_id=x_legacy_client_id,
            idempotency_key=x_idempotency_key,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except LegacyBridgeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

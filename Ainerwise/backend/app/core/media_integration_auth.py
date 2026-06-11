"""Integration Client authentication — separate from user JWT.

Bearer tokens are opaque integration secrets (hashed at rest). User JWTs
must never authenticate against this dependency.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.marketing import MarketingIntegrationClient

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class IntegrationClientContext:
    client: MarketingIntegrationClient


def hash_integration_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


async def get_integration_client(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IntegrationClientContext:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail={"error": _error("missing_token", "Integration client token required", request, False)},
        )

    token = credentials.credentials.strip()
    # Reject user JWTs — integration secrets are opaque, not JWT payloads.
    jwt_payload = decode_token(token)
    if jwt_payload is not None and jwt_payload.get("type") in ("access", "refresh"):
        raise HTTPException(
            status_code=401,
            detail={"error": _error("invalid_token", "User JWT cannot access media integration API", request, False)},
        )

    secret_hash = hash_integration_secret(token)
    client = (
        await db.execute(
            select(MarketingIntegrationClient).where(MarketingIntegrationClient.secret_hash == secret_hash)
        )
    ).scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=401,
            detail={"error": _error("invalid_token", "Invalid integration client token", request, False)},
        )
    if client.status != "active":
        raise HTTPException(
            status_code=403,
            detail={"error": _error("client_inactive", f"Integration client is {client.status}", request, False)},
        )

    from datetime import datetime, timezone

    client.last_used_at = datetime.now(timezone.utc)
    await db.flush()
    return IntegrationClientContext(client=client)


def require_scopes(*scopes: str):
    async def checker(ctx: Annotated[IntegrationClientContext, Depends(get_integration_client)]) -> IntegrationClientContext:
        granted = set(ctx.client.scopes_json or [])
        if not all(s in granted for s in scopes):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "insufficient_scope",
                        "message": f"Required scopes: {', '.join(scopes)}",
                        "correlation_id": "",
                        "retryable": False,
                    }
                },
            )
        return ctx

    return checker


IntegrationClientDep = Annotated[IntegrationClientContext, Depends(get_integration_client)]
ReadClientDep = Annotated[IntegrationClientContext, Depends(require_scopes("briefs:read"))]
ClaimClientDep = Annotated[IntegrationClientContext, Depends(require_scopes("briefs:claim"))]
ProgressClientDep = Annotated[IntegrationClientContext, Depends(require_scopes("briefs:progress"))]
UploadClientDep = Annotated[IntegrationClientContext, Depends(require_scopes("assets:upload"))]
SubmitClientDep = Annotated[IntegrationClientContext, Depends(require_scopes("assets:submit"))]


def _error(code: str, message: str, request: Request, retryable: bool) -> dict:
    import uuid

    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    return {
        "code": code,
        "message": message,
        "correlation_id": correlation_id,
        "retryable": retryable,
    }

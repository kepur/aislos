"""Analytics client authentication — API keys for external projects.

Modelled on the media-integration client auth already in the codebase: the
token is an opaque secret hashed at rest, and a user JWT is explicitly refused
so the two authentication worlds never blur.

The important property here is that `source_app` comes from the key, never
from the request. A client cannot attribute its traffic to another project,
which is what makes cross-project reporting trustworthy.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.analytics import AnalyticsClient

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AnalyticsClientContext:
    client: AnalyticsClient

    @property
    def source_app(self) -> str:
        return self.client.source_app

    def allows_region(self, region_id: uuid.UUID | None) -> bool:
        allowed = self.client.allowed_region_ids_json
        if not allowed:
            return True          # unfenced key
        if region_id is None:
            return False         # fenced key must say which region it means
        return str(region_id) in {str(r) for r in allowed}

    def allows_portal(self, portal_key: str | None) -> bool:
        allowed = self.client.allowed_portal_keys_json
        if not allowed:
            return True
        if not portal_key:
            return False
        return portal_key in set(allowed)


def hash_client_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


async def get_analytics_client(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsClientContext:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Analytics client key required")

    token = credentials.credentials.strip()
    # A user JWT must not authenticate here: these keys are machine identities
    # with their own attribution, and mixing them would let a signed-in person
    # write events as any app.
    payload = decode_token(token)
    if payload is not None and payload.get("type") in ("access", "refresh"):
        raise HTTPException(status_code=401, detail="User token cannot be used as an analytics client key")

    client = (
        await db.execute(
            select(AnalyticsClient).where(AnalyticsClient.secret_hash == hash_client_secret(token))
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=401, detail="Invalid analytics client key")
    if client.status != "active":
        raise HTTPException(status_code=403, detail=f"Analytics client is {client.status}")

    client.last_used_at = datetime.now(timezone.utc)
    await db.flush()
    return AnalyticsClientContext(client=client)


def require_analytics_scope(scope: str):
    async def checker(
        ctx: Annotated[AnalyticsClientContext, Depends(get_analytics_client)],
    ) -> AnalyticsClientContext:
        if scope not in set(ctx.client.scopes_json or []):
            raise HTTPException(status_code=403, detail=f"Key is missing the '{scope}' scope")
        return ctx

    return checker


EventWriteClient = Annotated[AnalyticsClientContext, Depends(require_analytics_scope("events:write"))]
ReportReadClient = Annotated[AnalyticsClientContext, Depends(require_analytics_scope("reports:read"))]

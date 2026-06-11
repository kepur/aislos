"""Trusted Portal Context for the procurement engine.

Trust boundary (PROCUREMENT_PHASE1_EXECUTION_TASKS.md §3.2):

- In production the ``X-Portal-Key`` header is stripped from external requests
  and re-written by the trusted gateway (nginx) based on hostname. The backend
  therefore treats the header value as gateway-asserted, never browser-asserted.
- Local development may rely on ``PROCUREMENT_DEFAULT_PORTAL_KEY`` from backend
  settings when no header is present.
- Automated tests inject the context via FastAPI dependency override.
- Anything unresolvable or illegal fails closed.

Clients can never switch portals through query strings or request bodies:
the only inputs are the gateway header and backend configuration.
"""
import re
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.portal_policy import PortalPolicy

_PORTAL_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,49}$")


@dataclass(frozen=True)
class PortalContext:
    portal_key: str
    policy: PortalPolicy


def resolve_portal_key(request: Request) -> str | None:
    """Resolve the trusted portal key from gateway header or local default."""
    raw = request.headers.get(settings.PROCUREMENT_PORTAL_HEADER, "")
    portal_key = raw.strip().lower()
    if not portal_key:
        portal_key = settings.PROCUREMENT_DEFAULT_PORTAL_KEY.strip().lower()
    return portal_key or None


async def get_portal_context(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortalContext:
    # Imported here to avoid a core -> services import cycle at module load.
    from app.services.portal_policy import get_active_policy, validate_policy

    portal_key = resolve_portal_key(request)
    if not portal_key or not _PORTAL_KEY_RE.match(portal_key):
        raise HTTPException(status_code=400, detail="Portal context could not be resolved")

    policy = await get_active_policy(db, portal_key)
    if policy is None:
        raise HTTPException(
            status_code=503, detail="No active portal policy for this portal"
        )

    problems = validate_policy(policy)
    if problems:
        # Fail closed: an illegal active policy must never drive behavior.
        raise HTTPException(status_code=503, detail="Active portal policy is invalid")

    return PortalContext(portal_key=portal_key, policy=policy)


PortalContextDep = Annotated[PortalContext, Depends(get_portal_context)]

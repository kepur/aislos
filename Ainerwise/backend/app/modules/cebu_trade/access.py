"""Workspace access helpers for Cebu trade/payment compatibility surfaces."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_access import PortalGrant, Workspace
from app.models.user import User

CEBU_TRADE_ADMIN_GRANTS = frozenset(
    {
        "admin.cebu.read",
        "admin.commerce.read",
        "admin.finance.read",
    }
)


class CebuTradeAccessDenied(PermissionError):
    pass


async def cebu_trade_admin_workspace_ids(
    db: AsyncSession,
    user: User,
    *,
    grant_keys: frozenset[str] = CEBU_TRADE_ADMIN_GRANTS,
) -> set[uuid.UUID]:
    result = await db.execute(
        select(PortalGrant.workspace_id)
        .join(Workspace, Workspace.id == PortalGrant.workspace_id)
        .where(
            PortalGrant.user_id == user.id,
            PortalGrant.grant_key.in_(grant_keys),
            PortalGrant.granted.is_(True),
            PortalGrant.revoked_at.is_(None),
            PortalGrant.workspace_id.is_not(None),
            Workspace.status == "active",
        )
    )
    return {workspace_id for workspace_id in result.scalars().all() if workspace_id is not None}


async def require_cebu_trade_admin_workspace(
    db: AsyncSession,
    user: User,
    workspace_id: uuid.UUID | None,
) -> None:
    if workspace_id is None:
        raise CebuTradeAccessDenied("Workspace-scoped Cebu trade operation required")
    workspace_ids = await cebu_trade_admin_workspace_ids(db, user)
    if workspace_id not in workspace_ids:
        raise CebuTradeAccessDenied("No Cebu trade grant in this Workspace")

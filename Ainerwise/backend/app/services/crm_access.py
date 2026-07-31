"""Workspace authorization for CRM resources."""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.models.user import User
from app.services.portal_access import list_memberships, user_has_grant

GLOBAL_CRM_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}


async def crm_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID] | None:
    if user.role in GLOBAL_CRM_ROLES:
        return None
    memberships = await list_memberships(db, user.id)
    allowed: set[uuid.UUID] = set()
    for membership in memberships:
        if await user_has_grant(
            db,
            user.id,
            "admin.crm.read",
            workspace_id=membership.workspace_id,
            portal_key="admin_crm",
        ):
            allowed.add(membership.workspace_id)
    return allowed


async def require_crm_workspace_access(
    db: AsyncSession,
    user: User,
    workspace_id: uuid.UUID | None,
) -> None:
    if user.role in GLOBAL_CRM_ROLES:
        return
    if workspace_id is None:
        raise HTTPException(
            status_code=403,
            detail="Legacy unscoped CRM resources require a global administrator",
        )
    allowed = await crm_workspace_ids(db, user)
    if allowed is None or workspace_id not in allowed:
        raise HTTPException(status_code=403, detail="CRM Workspace access required")


async def customer_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID]:
    return {
        membership.workspace_id
        for membership in await list_memberships(db, user.id)
        if user.company_id is not None and membership.company_id == user.company_id
    }


async def require_customer_workspace_resource(
    db: AsyncSession,
    user: User,
    *,
    workspace_id: uuid.UUID | None,
) -> None:
    if workspace_id is None:
        return
    if workspace_id not in await customer_workspace_ids(db, user):
        raise HTTPException(status_code=403, detail="Customer Workspace membership required")

"""Workspace resolution and authorization for financial resources."""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.models.portal_access import Workspace, WorkspaceMembership
from app.models.project import Project
from app.models.quote import Quote
from app.models.user import User
from app.services.portal_access import get_default_workspace, list_memberships, user_has_grant

GLOBAL_FINANCE_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}


async def finance_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID] | None:
    if user.role in GLOBAL_FINANCE_ROLES:
        return None
    allowed: set[uuid.UUID] = set()
    for membership in await list_memberships(db, user.id):
        if await user_has_grant(
            db,
            user.id,
            "admin.finance.read",
            workspace_id=membership.workspace_id,
            portal_key="admin_finance",
        ):
            allowed.add(membership.workspace_id)
    return allowed


async def require_finance_workspace_access(
    db: AsyncSession,
    user: User,
    workspace_id: uuid.UUID | None,
) -> None:
    if user.role in GLOBAL_FINANCE_ROLES:
        return
    if workspace_id is None:
        raise HTTPException(
            status_code=403,
            detail="Legacy unscoped finance resources require a global administrator",
        )
    allowed = await finance_workspace_ids(db, user)
    if allowed is None or workspace_id not in allowed:
        raise HTTPException(status_code=403, detail="Finance Workspace access required")


async def resolve_financial_workspace(
    db: AsyncSession,
    *,
    requested_workspace_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    quote_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
) -> uuid.UUID:
    candidates: set[uuid.UUID] = set()
    for model, resource_id, label in (
        (Project, project_id, "Project"),
        (Quote, quote_id, "Quote"),
    ):
        if resource_id is None:
            continue
        resource = await db.get(model, resource_id)
        if resource is None:
            raise ValueError(f"Linked {label} not found")
        if resource.workspace_id is not None:
            candidates.add(resource.workspace_id)

    if requested_workspace_id is not None:
        workspace = await db.get(Workspace, requested_workspace_id)
        if workspace is None or workspace.status != "active":
            raise ValueError("Requested Workspace is unavailable")
        candidates.add(requested_workspace_id)

    if customer_id is not None:
        customer_workspace_ids = set(
            (
                await db.execute(
                    select(WorkspaceMembership.workspace_id)
                    .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
                    .where(
                        WorkspaceMembership.company_id == customer_id,
                        WorkspaceMembership.status == "active",
                        Workspace.status == "active",
                    )
                    .distinct()
                )
            ).scalars()
        )
        if candidates and customer_workspace_ids and not candidates.issubset(customer_workspace_ids):
            raise ValueError("Customer and linked resources belong to different Workspaces")
        if not candidates and len(customer_workspace_ids) == 1:
            candidates.update(customer_workspace_ids)
        elif not candidates and len(customer_workspace_ids) > 1:
            raise ValueError("workspace_id is required for a customer with multiple Workspaces")

    if len(candidates) > 1:
        raise ValueError("Linked financial resources belong to different Workspaces")
    if candidates:
        return next(iter(candidates))
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise ValueError("No active default Workspace is available")
    return workspace.id


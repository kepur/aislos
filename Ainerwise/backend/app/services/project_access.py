"""Workspace authorization for delivery Projects."""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.models.portal_access import Workspace
from app.models.portal_access import WorkspaceMembership
from app.models.project import Project
from app.models.user import User
from app.services.portal_access import (
    get_default_workspace,
    list_memberships,
    resolve_workspace_scope,
    user_has_grant,
)

GLOBAL_PROJECT_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}


async def project_operator_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID] | None:
    """Return exact accessible Workspaces, or None for global administrators."""
    if user.role in GLOBAL_PROJECT_ROLES:
        return None
    memberships = await list_memberships(db, user.id)
    allowed: set[uuid.UUID] = set()
    for membership in memberships:
        if await user_has_grant(
            db,
            user.id,
            "admin.project.read",
            workspace_id=membership.workspace_id,
            portal_key="admin_project",
        ):
            allowed.add(membership.workspace_id)
    return allowed


async def resolve_project_workspace(
    db: AsyncSession,
    user: User,
    requested_workspace_id: uuid.UUID | None,
) -> uuid.UUID:
    """Resolve the Workspace for a new Project without allowing implicit cross-tenant writes."""
    if user.role in GLOBAL_PROJECT_ROLES:
        workspace = (
            await db.get(Workspace, requested_workspace_id)
            if requested_workspace_id is not None
            else await get_default_workspace(db)
        )
        if workspace is None or workspace.status != "active":
            raise HTTPException(status_code=400, detail="An active workspace_id is required")
        return workspace.id

    try:
        workspace_id = await resolve_workspace_scope(
            db,
            user_id=user.id,
            requested_workspace_id=requested_workspace_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if workspace_id is None:
        raise HTTPException(status_code=403, detail="No active Project Workspace membership")
    if not await user_has_grant(
        db,
        user.id,
        "admin.project.read",
        workspace_id=workspace_id,
        portal_key="admin_project",
    ):
        raise HTTPException(status_code=403, detail="Project Workspace grant required")
    return workspace_id


async def require_project_operator_access(
    db: AsyncSession,
    user: User,
    project: Project,
) -> None:
    if user.role in GLOBAL_PROJECT_ROLES:
        return
    if project.workspace_id is None:
        raise HTTPException(
            status_code=403,
            detail="Legacy unscoped Projects require a global administrator",
        )
    allowed = await project_operator_workspace_ids(db, user)
    if allowed is None or project.workspace_id not in allowed:
        raise HTTPException(status_code=403, detail="Project Workspace access required")


async def require_customer_project_access(
    db: AsyncSession,
    user: User,
    project: Project,
) -> None:
    if not user.company_id or project.buyer_company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Not your project")
    if project.workspace_id is None:
        return
    memberships = await list_memberships(db, user.id)
    if not any(
        membership.workspace_id == project.workspace_id
        and membership.company_id == user.company_id
        for membership in memberships
    ):
        raise HTTPException(status_code=403, detail="Project Workspace membership required")


async def customer_project_ids_query(db: AsyncSession, user: User):
    """Return a reusable subquery containing only Projects visible to this customer."""
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Customer company membership required")
    memberships = await list_memberships(db, user.id)
    workspace_ids = {
        membership.workspace_id
        for membership in memberships
        if membership.company_id == user.company_id
    }
    workspace_scope = (
        or_(Project.workspace_id.in_(workspace_ids), Project.workspace_id.is_(None))
        if workspace_ids
        else Project.workspace_id.is_(None)
    )
    return select(Project.id).where(
        Project.buyer_company_id == user.company_id,
        workspace_scope,
    )


async def infer_company_project_workspace(
    db: AsyncSession,
    company_id: uuid.UUID | None,
) -> uuid.UUID:
    """Infer an unambiguous Workspace for internal Project creation."""
    workspace_ids: list[uuid.UUID] = []
    if company_id is not None:
        workspace_ids = list(
            (
                await db.execute(
                    select(WorkspaceMembership.workspace_id)
                    .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
                    .where(
                        WorkspaceMembership.company_id == company_id,
                        WorkspaceMembership.status == "active",
                        Workspace.status == "active",
                    )
                    .distinct()
                )
            ).scalars()
        )
    if len(workspace_ids) == 1:
        return workspace_ids[0]
    if len(workspace_ids) > 1:
        raise ValueError("Cannot infer Project Workspace for a company with multiple active Workspaces")
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise ValueError("No active default Workspace is available for Project creation")
    return workspace.id


async def resolve_linked_resource_workspace(
    db: AsyncSession,
    *,
    requested_workspace_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve and validate the shared Workspace for a linked commercial resource."""
    candidates: set[uuid.UUID] = set()
    if project_id is not None:
        project = await db.get(Project, project_id)
        if project is None:
            raise ValueError("Linked Project not found")
        if project.workspace_id is not None:
            candidates.add(project.workspace_id)
    if lead_id is not None:
        from app.models.lead import Lead

        lead = await db.get(Lead, lead_id)
        if lead is None:
            raise ValueError("Linked Lead not found")
        if lead.workspace_id is not None:
            candidates.add(lead.workspace_id)
    if requested_workspace_id is not None:
        workspace = await db.get(Workspace, requested_workspace_id)
        if workspace is None or workspace.status != "active":
            raise ValueError("Requested Workspace is unavailable")
        candidates.add(requested_workspace_id)
    if len(candidates) > 1:
        raise ValueError("Linked resources belong to different Workspaces")
    if candidates:
        return next(iter(candidates))
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise ValueError("No active default Workspace is available")
    return workspace.id

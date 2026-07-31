"""Workspace authorization and link validation for Marketing resources."""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import UserRole
from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.marketing import (
    MarketingActivity,
    MarketingCampaign,
    MarketingContact,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
)
from app.models.portal_access import Workspace
from app.models.user import User
from app.services.portal_access import get_default_workspace, list_memberships, user_has_grant

GLOBAL_MARKETING_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}
MARKETING_PORTALS = ("admin_marketing", "marketing_pc", "marketing_h5")


async def marketing_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID] | None:
    if user.role in GLOBAL_MARKETING_ROLES:
        return None
    allowed: set[uuid.UUID] = set()
    for membership in await list_memberships(db, user.id):
        for portal_key in MARKETING_PORTALS:
            if await user_has_grant(
                db,
                user.id,
                "admin.marketing.read",
                workspace_id=membership.workspace_id,
                portal_key=portal_key,
            ):
                allowed.add(membership.workspace_id)
                break
    return allowed


async def require_marketing_workspace_access(
    db: AsyncSession, user: User, workspace_id: uuid.UUID | None
) -> None:
    if user.role in GLOBAL_MARKETING_ROLES:
        return
    if workspace_id is None or workspace_id not in (await marketing_workspace_ids(db, user) or set()):
        raise HTTPException(status_code=403, detail="Marketing Workspace access required")


async def resolve_marketing_workspace(
    db: AsyncSession,
    *,
    requested_workspace_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    contact_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    inquiry_id: uuid.UUID | None = None,
) -> uuid.UUID:
    candidates: set[uuid.UUID] = set()
    for model, resource_id, label in (
        (MarketingCampaign, campaign_id, "Campaign"),
        (MarketingContact, contact_id, "Contact"),
        (Lead, lead_id, "Lead"),
        (Inquiry, inquiry_id, "Inquiry"),
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
    if len(candidates) > 1:
        raise ValueError("Linked Marketing resources belong to different Workspaces")
    if candidates:
        return next(iter(candidates))
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise ValueError("No active default Workspace is available")
    return workspace.id


async def require_marketing_version_access(
    db: AsyncSession, user: User, version_id: uuid.UUID
) -> MarketingCreativeBrief:
    version = await db.get(MarketingCreativeBriefVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Creative brief version not found")
    brief = await db.get(MarketingCreativeBrief, version.brief_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Creative brief not found")
    await require_marketing_workspace_access(db, user, brief.workspace_id)
    return brief


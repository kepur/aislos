"""PF02: Workspace membership, portal grants and role backfill helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.portal_registry import COMPATIBILITY_PORTAL_SUCCESSORS, PORTAL_REGISTRY, get_manifest
from app.models.audit import AuditLog
from app.models.portal_access import PortalGrant, Workspace, WorkspaceMembership

DEFAULT_WORKSPACE_SLUG = "default"

ROLE_ACCESS_PROFILES: dict[str, dict[str, object]] = {
    "buyer": {
        "membership_type": "customer_owner",
        "grants": [
            ("customer", "portal.h5.customer"),
            ("customer_pc", "portal.pc.customer"),
            ("customer_h5", "portal.h5.customer"),
            ("cebu_buyer_pc", "portal.pc.cebu_buyer"),
            ("cebu_buyer_h5", "portal.h5.cebu_buyer"),
        ],
    },
    "customer_user": {
        "membership_type": "customer_member",
        "grants": [
            ("customer", "portal.h5.customer"),
            ("customer_pc", "portal.pc.customer"),
            ("customer_h5", "portal.h5.customer"),
        ],
    },
    "service_partner": {
        "membership_type": "partner_company_owner",
        "grants": [
            ("partner_company", "partner.rfq.read"),
            ("partner_company", "partner.work_package.read"),
            ("partner_company_pc", "partner.rfq.read"),
            ("partner_company_pc", "partner.work_package.read"),
            ("partner_company_h5", "partner.rfq.read"),
            ("partner_company_h5", "partner.work_package.read"),
        ],
    },
    "partner_worker": {
        "membership_type": "field_worker",
        "grants": [
            ("field_worker", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.read_assigned"),
        ],
    },
    "maintenance_worker": {
        "membership_type": "field_worker",
        "grants": [
            ("field_worker", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.maintenance"),
        ],
    },
    "vendor": {
        "membership_type": "supplier_operator",
        "grants": [
            ("supplier", "supplier.rfq.read"),
            ("supplier", "supplier.catalog.read"),
            ("supplier_pc", "supplier.rfq.read"),
            ("supplier_pc", "supplier.catalog.read"),
            ("supplier_h5", "supplier.rfq.read"),
            ("supplier_h5", "supplier.catalog.read"),
        ],
    },
    "project_manager": {
        "membership_type": "project_manager",
        "grants": [
            ("admin_field_ops", "admin.field_ops.read"),
            ("admin_project", "admin.project.read"),
        ],
    },
    "sales_manager": {
        "membership_type": "admin_operator",
        "grants": [("admin_crm", "admin.crm.read")],
    },
    "finance": {
        "membership_type": "admin_operator",
        "grants": [("admin_finance", "admin.finance.read")],
    },
    "marketing_operator": {
        "membership_type": "marketing_operator",
        "grants": [
            ("admin_marketing", "admin.marketing.read"),
            ("marketing_pc", "admin.marketing.read"),
            ("marketing_h5", "admin.marketing.read"),
        ],
    },
    "admin": {
        "membership_type": "admin_operator",
        "grants": [
            ("admin_executive", "admin.executive.read"),
            ("admin_crm", "admin.crm.read"),
            ("admin_ai_solution", "admin.ai_solution.read"),
            ("admin_procurement", "admin.procurement.read"),
            ("admin_supplier_ops", "admin.supplier_ops.read"),
            ("admin_partner", "admin.partner.read"),
            ("admin_field_ops", "admin.field_ops.read"),
            ("admin_project", "admin.project.read"),
            ("admin_asset", "admin.asset.read"),
            ("admin_commerce", "admin.commerce.read"),
            ("admin_marketing", "admin.marketing.read"),
            ("marketing_pc", "admin.marketing.read"),
            ("marketing_h5", "admin.marketing.read"),
            ("admin_ai_supervisor", "admin.ai_supervisor.read"),
            ("admin_knowledge", "admin.knowledge.read"),
            ("admin_finance", "admin.finance.read"),
            ("admin_audit", "admin.audit.read"),
            ("admin_cebu", "admin.cebu.read"),
        ],
    },
    "super_admin": {
        "membership_type": "admin_operator",
        "grants": [
            ("admin_executive", "admin.executive.read"),
            ("admin_crm", "admin.crm.read"),
            ("admin_ai_solution", "admin.ai_solution.read"),
            ("admin_procurement", "admin.procurement.read"),
            ("admin_supplier_ops", "admin.supplier_ops.read"),
            ("admin_partner", "admin.partner.read"),
            ("admin_field_ops", "admin.field_ops.read"),
            ("admin_project", "admin.project.read"),
            ("admin_asset", "admin.asset.read"),
            ("admin_commerce", "admin.commerce.read"),
            ("admin_marketing", "admin.marketing.read"),
            ("marketing_pc", "admin.marketing.read"),
            ("marketing_h5", "admin.marketing.read"),
            ("admin_ai_supervisor", "admin.ai_supervisor.read"),
            ("admin_knowledge", "admin.knowledge.read"),
            ("admin_finance", "admin.finance.read"),
            ("admin_audit", "admin.audit.read"),
            ("admin_cebu", "admin.cebu.read"),
        ],
    },
    "developer": {
        "membership_type": "developer",
        "grants": [("developer", "portal.pc.developer")],
    },
}


async def get_default_workspace(db: AsyncSession) -> Workspace | None:
    return (
        await db.execute(select(Workspace).where(Workspace.slug == DEFAULT_WORKSPACE_SLUG))
    ).scalar_one_or_none()


async def list_active_grants(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    workspace_id: uuid.UUID | None,
    portal_key: str | None = None,
    region_id: uuid.UUID | None = None,
) -> set[str]:
    workspace = None
    if workspace_id is not None:
        memberships = await list_memberships(db, user_id)
        if workspace_id not in {membership.workspace_id for membership in memberships}:
            return set()
        workspace = await db.get(Workspace, workspace_id)
        if workspace is None or workspace.status != "active":
            return set()
        if region_id is not None and workspace.region_id is not None and workspace.region_id != region_id:
            return set()
    workspace_scope = (
        PortalGrant.workspace_id.is_(None)
        if workspace_id is None
        else PortalGrant.workspace_id == workspace_id
    )
    portal_scope = (
        PortalGrant.portal_key.is_(None)
        if portal_key is None
        else PortalGrant.portal_key == portal_key
    )
    result = await db.execute(
        select(PortalGrant).where(
            PortalGrant.user_id == user_id,
            PortalGrant.granted.is_(True),
            PortalGrant.revoked_at.is_(None),
            workspace_scope,
            portal_scope,
        )
    )
    grants: set[str] = set()
    for grant in result.scalars().all():
        scope = grant.scope_json or {}
        allowed_regions = scope.get("allowed_region_ids")
        exact_region = scope.get("region_id")
        if allowed_regions:
            if region_id is None or str(region_id) not in {str(item) for item in allowed_regions}:
                continue
        if exact_region:
            if region_id is None or str(region_id) != str(exact_region):
                continue
        grants.add(grant.grant_key)
    return grants


async def user_has_grant(
    db: AsyncSession,
    user_id: uuid.UUID,
    grant_key: str,
    *,
    workspace_id: uuid.UUID | None,
    portal_key: str | None = None,
    region_id: uuid.UUID | None = None,
) -> bool:
    grants = await list_active_grants(
        db,
        user_id,
        workspace_id=workspace_id,
        portal_key=portal_key,
        region_id=region_id,
    )
    return grant_key in grants


async def user_has_grant_in_any_workspace(
    db: AsyncSession,
    user_id: uuid.UUID,
    grant_key: str,
    *,
    portal_key: str | None = None,
) -> bool:
    """Portal-entry discovery only; object operations must pass an exact workspace."""
    memberships = await list_memberships(db, user_id)
    workspace_ids: list[uuid.UUID | None] = [m.workspace_id for m in memberships] or [None]
    for workspace_id in workspace_ids:
        if await user_has_grant(
            db,
            user_id,
            grant_key,
            workspace_id=workspace_id,
            portal_key=portal_key,
        ):
            return True
    return False


async def user_has_grants(
    db: AsyncSession,
    user_id: uuid.UUID,
    required: list[str],
    *,
    workspace_id: uuid.UUID | None,
    portal_key: str | None = None,
    region_id: uuid.UUID | None = None,
    any_of: bool = False,
) -> bool:
    if not required:
        return True
    grants = await list_active_grants(
        db,
        user_id,
        workspace_id=workspace_id,
        portal_key=portal_key,
        region_id=region_id,
    )
    if any_of:
        return any(g in grants for g in required)
    return all(g in grants for g in required)


def portals_for_grants(grants: set[str]) -> list[dict]:
    items: list[dict] = []
    for manifest in PORTAL_REGISTRY.values():
        required = manifest.get("required_grants") or []
        if not required:
            continue
        if all(g in grants for g in required):
            items.append(
                {
                    "portal_key": manifest["portal_key"],
                    "display_name": manifest["display_name"],
                    "physical_frontend": manifest["physical_frontend"],
                    "home_route": manifest["home_route"],
                    "legacy_portal_mode": manifest.get("legacy_portal_mode"),
                }
            )
    return sorted(items, key=lambda x: x["portal_key"])


async def list_user_portals(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    memberships = await list_memberships(db, user_id)
    workspace_ids: list[uuid.UUID | None] = [m.workspace_id for m in memberships] or [None]
    items: dict[str, dict] = {}
    for manifest in PORTAL_REGISTRY.values():
        if manifest["portal_key"] in COMPATIBILITY_PORTAL_SUCCESSORS:
            continue
        required = manifest.get("required_grants") or []
        for workspace_id in workspace_ids:
            if await user_has_grants(
                db,
                user_id,
                required,
                workspace_id=workspace_id,
                portal_key=manifest["portal_key"],
            ):
                items[manifest["portal_key"]] = {
                    "portal_key": manifest["portal_key"],
                    "display_name": manifest["display_name"],
                    "physical_frontend": manifest["physical_frontend"],
                    "home_route": manifest["home_route"],
                    "legacy_portal_mode": manifest.get("legacy_portal_mode"),
                }
                break
    return sorted(items.values(), key=lambda x: x["portal_key"])


async def resolve_workspace_scope(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    requested_workspace_id: uuid.UUID | None,
) -> uuid.UUID | None:
    memberships = await list_memberships(db, user_id)
    workspace_ids = {membership.workspace_id for membership in memberships}
    if requested_workspace_id is not None:
        if requested_workspace_id not in workspace_ids:
            raise PermissionError("No active membership in requested workspace")
        return requested_workspace_id
    if len(workspace_ids) == 1:
        return next(iter(workspace_ids))
    if len(workspace_ids) > 1:
        raise ValueError("workspace_id is required when multiple memberships are active")
    return None


async def switch_portal_audit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    portal_key: str,
    workspace_id: uuid.UUID | None,
    ip_address: str | None = None,
) -> None:
    manifest = get_manifest(portal_key)
    if manifest is None:
        raise ValueError("Unknown portal")
    required = manifest.get("required_grants") or []
    if required and not await user_has_grants(
        db,
        user_id,
        required,
        workspace_id=workspace_id,
        portal_key=manifest["portal_key"],
    ):
        raise PermissionError("Missing grants for portal")
    db.add(
        AuditLog(
            actor_user_id=user_id,
            action="auth.portal_switch",
            entity_type="portal",
            entity_id=user_id,
            portal_key=manifest["portal_key"],
            after_json={
                "portal_key": manifest["portal_key"],
                "workspace_id": str(workspace_id) if workspace_id else None,
                "ip": ip_address,
            },
        )
    )
    await db.flush()


async def list_memberships(db: AsyncSession, user_id: uuid.UUID) -> list[WorkspaceMembership]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WorkspaceMembership)
        .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
        .where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "active",
            Workspace.status == "active",
            or_(
                WorkspaceMembership.valid_from.is_(None),
                WorkspaceMembership.valid_from <= now,
            ),
            or_(
                WorkspaceMembership.valid_until.is_(None),
                WorkspaceMembership.valid_until > now,
            ),
        )
    )
    return list(result.scalars().all())


async def ensure_membership(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    membership_type: str,
    workspace_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
) -> WorkspaceMembership:
    existing = (
        await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.membership_type == membership_type,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.status = "active"
        existing.valid_from = existing.valid_from or datetime.now(timezone.utc)
        existing.valid_until = None
        if company_id is not None:
            existing.company_id = company_id
        await db.flush()
        return existing
    row = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=user_id,
        company_id=company_id,
        membership_type=membership_type,
        status="active",
        valid_from=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    return row


async def ensure_grant(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    grant_key: str,
    workspace_id: uuid.UUID | None,
    portal_key: str | None = None,
    scope_json: dict | None = None,
) -> PortalGrant:
    q = select(PortalGrant).where(
        PortalGrant.user_id == user_id,
        PortalGrant.grant_key == grant_key,
        PortalGrant.workspace_id == workspace_id,
        (
            PortalGrant.portal_key.is_(None)
            if portal_key is None
            else PortalGrant.portal_key == portal_key
        ),
    )
    existing = (await db.execute(q)).scalar_one_or_none()
    if existing:
        if not existing.granted or existing.revoked_at is not None:
            existing.granted = True
            existing.revoked_at = None
        if scope_json is not None:
            existing.scope_json = scope_json
        await db.flush()
        return existing
    row = PortalGrant(
        user_id=user_id,
        workspace_id=workspace_id,
        portal_key=portal_key,
        grant_key=grant_key,
        granted=True,
        scope_json=scope_json,
    )
    db.add(row)
    await db.flush()
    return row


async def sync_role_portal_access(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    role: str,
    company_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
) -> None:
    """Synchronize default role-derived access without touching manual grants."""
    profile = ROLE_ACCESS_PROFILES.get(role)
    if profile is None:
        return
    workspace = (
        await db.get(Workspace, workspace_id)
        if workspace_id is not None
        else await get_default_workspace(db)
    )
    if workspace is None or workspace.status != "active":
        return

    membership_type = str(profile["membership_type"])
    if role == "vendor" and company_id is not None:
        current_owner = (
            await db.execute(
                select(WorkspaceMembership.id).where(
                    WorkspaceMembership.workspace_id == workspace.id,
                    WorkspaceMembership.user_id == user_id,
                    WorkspaceMembership.company_id == company_id,
                    WorkspaceMembership.membership_type == "supplier_owner",
                )
            )
        ).scalar_one_or_none()
        company_owner = (
            await db.execute(
                select(WorkspaceMembership.id)
                .where(
                    WorkspaceMembership.workspace_id == workspace.id,
                    WorkspaceMembership.company_id == company_id,
                    WorkspaceMembership.membership_type == "supplier_owner",
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if current_owner is not None or company_owner is None:
            membership_type = "supplier_owner"
    await ensure_membership(
        db,
        user_id=user_id,
        membership_type=membership_type,
        workspace_id=workspace.id,
        company_id=company_id,
    )

    desired = {(str(portal_key), str(grant_key)) for portal_key, grant_key in profile["grants"]}
    role_grants = list(
        (
            await db.execute(
                select(PortalGrant).where(
                    PortalGrant.user_id == user_id,
                    PortalGrant.workspace_id == workspace.id,
                    PortalGrant.scope_json["source"].astext == "role_sync",
                )
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(timezone.utc)
    for grant in role_grants:
        if (grant.portal_key, grant.grant_key) not in desired:
            grant.granted = False
            grant.revoked_at = now

    for portal_key, grant_key in desired:
        await ensure_grant(
            db,
            user_id=user_id,
            workspace_id=workspace.id,
            portal_key=portal_key,
            grant_key=grant_key,
            scope_json={"source": "role_sync", "role": role},
        )
    await db.flush()


async def suspend_user_portal_access(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    """Suspend all portal entry points when a user account is deactivated."""
    now = datetime.now(timezone.utc)
    memberships = list(
        (
            await db.execute(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.user_id == user_id,
                    WorkspaceMembership.status == "active",
                )
            )
        )
        .scalars()
        .all()
    )
    for membership in memberships:
        membership.status = "suspended"
        membership.valid_until = now

    grants = list(
        (
            await db.execute(
                select(PortalGrant).where(
                    PortalGrant.user_id == user_id,
                    PortalGrant.granted.is_(True),
                    PortalGrant.revoked_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    for grant in grants:
        grant.granted = False
        grant.revoked_at = now
    await db.flush()

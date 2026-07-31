"""Workspace resolution and link validation for lifecycle resources."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, Site
from app.models.lifecycle import (
    AMCContract,
    CustomerWarranty,
    InventoryItem,
    MonitoringPoint,
)
from app.models.portal_access import Workspace, WorkspaceMembership
from app.models.project import Project
from app.services.portal_access import get_default_workspace


async def _linked_workspace(
    db: AsyncSession,
    model,
    resource_id: uuid.UUID | None,
    label: str,
) -> uuid.UUID | None:
    if resource_id is None:
        return None
    resource = await db.get(model, resource_id)
    if resource is None:
        raise ValueError(f"Linked {label} not found")
    return resource.workspace_id


async def resolve_lifecycle_workspace(
    db: AsyncSession,
    *,
    requested_workspace_id: uuid.UUID | None = None,
    company_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    site_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    parent_asset_id: uuid.UUID | None = None,
    monitoring_point_id: uuid.UUID | None = None,
    inventory_item_id: uuid.UUID | None = None,
    customer_warranty_id: uuid.UUID | None = None,
    amc_contract_id: uuid.UUID | None = None,
) -> uuid.UUID:
    candidates: set[uuid.UUID] = set()
    links = (
        (Project, project_id, "Project"),
        (Site, site_id, "Site"),
        (Asset, asset_id, "Asset"),
        (Asset, parent_asset_id, "parent Asset"),
        (MonitoringPoint, monitoring_point_id, "Monitoring Point"),
        (InventoryItem, inventory_item_id, "Inventory Item"),
        (CustomerWarranty, customer_warranty_id, "Customer Warranty"),
        (AMCContract, amc_contract_id, "AMC Contract"),
    )
    for model, resource_id, label in links:
        workspace_id = await _linked_workspace(db, model, resource_id, label)
        if workspace_id is not None:
            candidates.add(workspace_id)

    if requested_workspace_id is not None:
        workspace = await db.get(Workspace, requested_workspace_id)
        if workspace is None or workspace.status != "active":
            raise ValueError("Requested Workspace is unavailable")
        candidates.add(requested_workspace_id)

    company_workspace_ids: set[uuid.UUID] = set()
    if company_id is not None:
        company_workspace_ids = set(
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
        if candidates and company_workspace_ids and not candidates.issubset(company_workspace_ids):
            raise ValueError("Company and linked resources belong to different Workspaces")
        if not candidates and len(company_workspace_ids) == 1:
            candidates.update(company_workspace_ids)
        elif not candidates and len(company_workspace_ids) > 1:
            raise ValueError("workspace_id is required for a company with multiple Workspaces")

    if len(candidates) > 1:
        raise ValueError("Linked lifecycle resources belong to different Workspaces")
    if candidates:
        return next(iter(candidates))
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise ValueError("No active default Workspace is available")
    return workspace.id


def _value(payload: dict, existing, *names: str):
    for name in names:
        if name in payload:
            return payload[name]
        if existing is not None and hasattr(existing, name):
            value = getattr(existing, name)
            if value is not None:
                return value
    return None


async def resolve_lifecycle_payload_workspace(
    db: AsyncSession,
    payload: dict,
    *,
    existing=None,
) -> uuid.UUID:
    return await resolve_lifecycle_workspace(
        db,
        requested_workspace_id=_value(payload, existing, "workspace_id"),
        company_id=_value(payload, existing, "company_id", "customer_id"),
        project_id=_value(payload, existing, "project_id", "reserved_for_project_id"),
        site_id=_value(payload, existing, "site_id"),
        asset_id=_value(payload, existing, "asset_id"),
        parent_asset_id=_value(payload, existing, "parent_asset_id"),
        monitoring_point_id=_value(payload, existing, "monitoring_point_id"),
        inventory_item_id=_value(payload, existing, "inventory_item_id"),
        customer_warranty_id=_value(payload, existing, "customer_warranty_id"),
        amc_contract_id=_value(payload, existing, "amc_contract_id"),
    )

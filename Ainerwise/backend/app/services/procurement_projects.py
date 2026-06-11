"""Procurement project service — flush-only; endpoint owns commit."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.portal_context import PortalContext
from app.models.file import FileAsset
from app.models.portal_policy import PortalPolicy
from app.models.procurement import ProcurementProject, ProcurementProjectFact, ProcurementTemplate
from app.models.user import User
from app.services.portal_policy import get_active_policy


class ProcurementProjectError(ValueError):
    pass


def policy_snapshot_from_policy(policy: PortalPolicy) -> dict[str, Any]:
    """Immutable snapshot of policy fields frozen at project creation / transfer."""
    return {
        "portal_key": policy.portal_key,
        "policy_id": str(policy.id),
        "version": policy.version,
        "default_procurement_mode": policy.default_procurement_mode,
        "allowed_project_types": list(policy.allowed_project_types_json or []),
        "price_visibility_rule": policy.price_visibility_rule,
        "supplier_visibility_rule": policy.supplier_visibility_rule,
        "confidence_gate": dict(policy.confidence_gate_json or {}),
    }


async def get_active_template(
    db: AsyncSession, project_type: str
) -> ProcurementTemplate | None:
    result = await db.execute(
        select(ProcurementTemplate).where(
            ProcurementTemplate.project_type == project_type,
            ProcurementTemplate.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def create_project(
    db: AsyncSession,
    *,
    user: User,
    ctx: PortalContext,
    project_type: str,
    title: str,
    description: str | None = None,
    region: str | None = None,
    country: str | None = None,
    city: str | None = None,
) -> tuple[ProcurementProject, list[ProcurementProjectFact]]:
    allowed = ctx.policy.allowed_project_types_json or []
    if project_type not in allowed:
        raise ProcurementProjectError(
            f"project_type {project_type!r} is not allowed by portal policy"
        )

    template = await get_active_template(db, project_type)
    if template is None:
        raise ProcurementProjectError(f"no active template for project_type {project_type!r}")

    project = ProcurementProject(
        owner_user_id=user.id,
        company_id=user.company_id,
        portal_key=ctx.portal_key,
        portal_policy_id=ctx.policy.id,
        policy_snapshot_json=policy_snapshot_from_policy(ctx.policy),
        project_type=project_type,
        title=title,
        description=description,
        region=region,
        country=country,
        city=city,
        status="draft",
        created_by=user.id,
    )
    db.add(project)
    await db.flush()

    facts: list[ProcurementProjectFact] = []
    for defn in template.fact_definitions_json or []:
        if not defn.get("required"):
            continue
        fact = ProcurementProjectFact(
            project_id=project.id,
            template_key=defn["key"],
            label=defn.get("label", defn["key"]),
            required=True,
            critical=bool(defn.get("critical")),
            weight=defn.get("weight", 1),
            source="system",
            confidence=0,
            user_confirmed=False,
        )
        db.add(fact)
        facts.append(fact)
    await db.flush()
    return project, facts


async def list_projects(
    db: AsyncSession,
    *,
    user: User,
    portal_key: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ProcurementProject], int]:
    base = select(ProcurementProject).where(
        ProcurementProject.portal_key == portal_key,
        ProcurementProject.owner_user_id == user.id,
    )
    count_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = int(count_result.scalar_one())
    result = await db.execute(
        base.order_by(ProcurementProject.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_project_for_user(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user: User,
    portal_key: str,
) -> ProcurementProject | None:
    result = await db.execute(
        select(ProcurementProject).where(
            ProcurementProject.id == project_id,
            ProcurementProject.portal_key == portal_key,
            ProcurementProject.owner_user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def get_project_by_id(
    db: AsyncSession, project_id: uuid.UUID
) -> ProcurementProject | None:
    return await db.get(ProcurementProject, project_id)


async def transfer_portal(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    target_portal_key: str,
    reason: str,
) -> tuple[ProcurementProject, dict[str, Any], dict[str, Any]]:
    target_policy = await get_active_policy(db, target_portal_key)
    if target_policy is None:
        raise ProcurementProjectError(
            f"no active portal policy for portal {target_portal_key!r}"
        )

    if project.project_type not in (target_policy.allowed_project_types_json or []):
        raise ProcurementProjectError(
            f"project_type {project.project_type!r} is not allowed by target portal policy"
        )

    before = {
        "portal_key": project.portal_key,
        "portal_policy_id": str(project.portal_policy_id),
        "policy_snapshot_json": dict(project.policy_snapshot_json),
    }
    project.portal_key = target_portal_key
    project.portal_policy_id = target_policy.id
    project.policy_snapshot_json = policy_snapshot_from_policy(target_policy)
    await db.flush()

    after = {
        "portal_key": project.portal_key,
        "portal_policy_id": str(project.portal_policy_id),
        "policy_snapshot_json": dict(project.policy_snapshot_json),
    }
    return project, before, after


async def attach_file(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    user: User,
    original_name: str,
    storage_path: str,
    mime_type: str | None = None,
    size_bytes: int | None = None,
    file_type: str | None = None,
) -> FileAsset:
    asset = FileAsset(
        entity_type="procurement_project",
        entity_id=project.id,
        file_type=file_type,
        original_name=original_name,
        storage_path=storage_path,
        mime_type=mime_type,
        size_bytes=size_bytes,
        uploaded_by=user.id,
    )
    db.add(asset)
    await db.flush()
    return asset

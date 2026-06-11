"""Auto-split frozen BOQ into procurement packages and match partner capabilities."""
from __future__ import annotations

import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement import (
    COMMERCIAL_TYPES,
    PACKAGE_STATUSES,
    PACKAGE_TRADES,
    PROCUREMENT_MODES,
    BoqItem,
    BoqItemOption,
    BoqVersion,
    ProcurementPackage,
    ProcurementPackageItem,
    ProcurementProject,
)
from app.models.service import PartnerCapability, ServicePartner
from app.services.procurement_boq import list_items_for_version, list_options_for_items

_CATEGORY_TRADE: dict[str, str] = {
    "lighting": "lighting",
    "network": "network",
    "networking": "network",
    "security": "security",
    "access": "access",
    "hvac": "hvac",
    "energy": "energy",
}

_COMMERCIAL_SORT = {t: i for i, t in enumerate(COMMERCIAL_TYPES)}
_TRADE_SORT = {t: i for i, t in enumerate(PACKAGE_TRADES)}


class ProcurementPackageError(ValueError):
    pass


def resolve_trade(item: BoqItem) -> str:
    if item.trade:
        trade = item.trade.lower().strip()
        if trade in PACKAGE_TRADES:
            return trade
    category = (item.category or "").lower().strip()
    return _CATEGORY_TRADE.get(category, "general")


def classify_commercial_type(option: BoqItemOption) -> str:
    if option.maintain_included and not option.install_included:
        return "maintenance"
    if option.install_included:
        return "installation"
    return "equipment"


def default_procurement_mode(project: ProcurementProject, commercial_type: str) -> str:
    if commercial_type in ("installation", "maintenance"):
        return "managed"
    snapshot = project.policy_snapshot_json or {}
    mode = snapshot.get("default_procurement_mode", "managed")
    return mode if mode in PROCUREMENT_MODES else "managed"


def _package_title(trade: str, commercial_type: str) -> str:
    trade_label = trade.replace("_", " ").title()
    type_label = commercial_type.replace("_", " ").title()
    return f"{trade_label} — {type_label}"


def _region_for_project(project: ProcurementProject) -> str | None:
    return project.country or project.region


def _region_matches(capability: PartnerCapability, region: str | None) -> bool:
    if not region:
        return True
    supported = capability.supported_regions_json or []
    if not supported:
        return True
    region_upper = region.upper()
    return any(str(r).upper() == region_upper for r in supported)


def _commercial_flag_match(capability: PartnerCapability, commercial_type: str) -> bool:
    if commercial_type == "equipment":
        return capability.supply
    if commercial_type == "installation":
        return capability.install
    return capability.maintain


async def match_partner_candidates(
    db: AsyncSession,
    *,
    trade: str,
    commercial_type: str,
    region: str | None,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PartnerCapability, ServicePartner)
        .join(ServicePartner, PartnerCapability.partner_id == ServicePartner.id)
        .where(PartnerCapability.active.is_(True))
        .where(PartnerCapability.verification_status == "verified")
        .where(PartnerCapability.trade == trade)
        .where(ServicePartner.verification_status == "verified")
    )
    candidates: list[dict[str, Any]] = []
    seen: set[uuid.UUID] = set()
    for capability, partner in result.all():
        if partner.id in seen:
            continue
        if not _commercial_flag_match(capability, commercial_type):
            continue
        if not _region_matches(capability, region):
            continue
        seen.add(partner.id)
        candidates.append(
            {
                "partner_id": partner.id,
                "partner_type": partner.partner_type,
                "country": partner.country,
                "trade": capability.trade,
                "commercial_type": commercial_type,
                "capability_keys": capability.capability_keys_json or [],
            }
        )
    return candidates


async def list_packages_for_project(
    db: AsyncSession, project_id: uuid.UUID, *, boq_version_id: uuid.UUID | None = None
) -> list[ProcurementPackage]:
    stmt = select(ProcurementPackage).where(ProcurementPackage.project_id == project_id)
    if boq_version_id is not None:
        stmt = stmt.where(ProcurementPackage.boq_version_id == boq_version_id)
    stmt = stmt.order_by(
        ProcurementPackage.revision.desc(),
        ProcurementPackage.commercial_type,
        ProcurementPackage.trade,
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_package_items(
    db: AsyncSession, package_ids: list[uuid.UUID]
) -> list[ProcurementPackageItem]:
    if not package_ids:
        return []
    result = await db.execute(
        select(ProcurementPackageItem).where(ProcurementPackageItem.package_id.in_(package_ids))
    )
    return list(result.scalars().all())


async def get_package_for_project(
    db: AsyncSession, project_id: uuid.UUID, package_id: uuid.UUID
) -> ProcurementPackage | None:
    package = await db.get(ProcurementPackage, package_id)
    if package is None or package.project_id != project_id:
        return None
    return package


async def _delete_regeneratable_packages(
    db: AsyncSession, packages: list[ProcurementPackage]
) -> None:
    if not packages:
        return
    ids = [p.id for p in packages]
    await db.execute(delete(ProcurementPackageItem).where(ProcurementPackageItem.package_id.in_(ids)))
    await db.execute(delete(ProcurementPackage).where(ProcurementPackage.id.in_(ids)))


async def generate_packages_from_frozen_boq(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    boq_version: BoqVersion | None = None,
) -> tuple[list[ProcurementPackage], list[ProcurementPackageItem], dict[uuid.UUID, list[dict]]]:
    version = boq_version
    if version is None:
        if project.current_boq_version_id is None:
            raise ProcurementPackageError("No BOQ version for project")
        version = await db.get(BoqVersion, project.current_boq_version_id)
    if version is None or version.project_id != project.id:
        raise ProcurementPackageError("BOQ version not found")
    if version.status != "frozen":
        raise ProcurementPackageError("BOQ must be frozen before generating packages")

    items = [i for i in await list_items_for_version(db, version.id) if i.included]
    if not items:
        raise ProcurementPackageError("No included BOQ items to package")

    options = await list_options_for_items(db, [i.id for i in items])
    standard_by_item: dict[uuid.UUID, BoqItemOption] = {}
    for opt in options:
        if opt.tier == "standard":
            standard_by_item[opt.boq_item_id] = opt

    missing_standard = [i.id for i in items if i.id not in standard_by_item]
    if missing_standard:
        raise ProcurementPackageError("Each included BOQ item requires a standard tier option")

    existing = await list_packages_for_project(db, project.id, boq_version_id=version.id)
    published = [p for p in existing if p.status == "published"]
    if published:
        revision = max(p.revision for p in existing) + 1
    else:
        await _delete_regeneratable_packages(db, existing)
        revision = existing[0].revision if existing else 1

    groups: dict[tuple[str, str], list[tuple[BoqItem, BoqItemOption]]] = defaultdict(list)
    assigned: set[uuid.UUID] = set()
    region = _region_for_project(project)

    for item in sorted(items, key=lambda i: (resolve_trade(i), i.sort_order, i.name)):
        standard = standard_by_item[item.id]
        commercial_type = classify_commercial_type(standard)
        trade = resolve_trade(item)
        key = (commercial_type, trade)
        if item.id in assigned:
            raise ProcurementPackageError(f"BOQ item {item.id} would be duplicated")
        assigned.add(item.id)
        groups[key].append((item, standard))

    if len(assigned) != len(items):
        raise ProcurementPackageError("Package assignment mismatch")

    packages: list[ProcurementPackage] = []
    package_items: list[ProcurementPackageItem] = []
    partner_map: dict[uuid.UUID, list[dict]] = {}

    sorted_keys = sorted(
        groups.keys(),
        key=lambda k: (_COMMERCIAL_SORT.get(k[0], 99), _TRADE_SORT.get(k[1], 99)),
    )
    for commercial_type, trade in sorted_keys:
        grouped = groups[(commercial_type, trade)]
        mode = default_procurement_mode(project, commercial_type)
        package = ProcurementPackage(
            project_id=project.id,
            boq_version_id=version.id,
            title=_package_title(trade, commercial_type),
            trade=trade,
            commercial_type=commercial_type,
            procurement_mode=mode,
            region=region,
            compatibility_json={"portal_key": project.portal_key},
            delivery_constraints_json=None,
            status="draft",
            revision=revision,
        )
        db.add(package)
        await db.flush()

        for item, standard in grouped:
            package_items.append(
                ProcurementPackageItem(
                    package_id=package.id,
                    boq_item_id=item.id,
                    boq_item_option_id=standard.id,
                    quantity=item.qty,
                )
            )

        candidates = await match_partner_candidates(
            db, trade=trade, commercial_type=commercial_type, region=region
        )
        partner_map[package.id] = candidates
        packages.append(package)

    if package_items:
        db.add_all(package_items)
    project.status = "packaged"
    await db.flush()
    return packages, package_items, partner_map


async def patch_package(
    db: AsyncSession,
    *,
    package: ProcurementPackage,
    title: str | None = None,
    title_provided: bool = False,
    procurement_mode: str | None = None,
    mode_provided: bool = False,
    status: str | None = None,
    status_provided: bool = False,
) -> tuple[ProcurementPackage, dict, dict]:
    if package.status in ("published", "closed"):
        raise ProcurementPackageError("Published or closed packages cannot be modified")

    before = {
        "title": package.title,
        "procurement_mode": package.procurement_mode,
        "status": package.status,
    }
    if title_provided and title is not None:
        package.title = title
    if mode_provided:
        if procurement_mode not in PROCUREMENT_MODES:
            raise ProcurementPackageError(f"Invalid procurement_mode: {procurement_mode!r}")
        package.procurement_mode = procurement_mode
    if status_provided:
        if status not in ("draft", "ready"):
            raise ProcurementPackageError("Only draft or ready status allowed via patch")
        package.status = status

    after = {
        "title": package.title,
        "procurement_mode": package.procurement_mode,
        "status": package.status,
    }
    await db.flush()
    return package, before, after


def serialize_package(
    package: ProcurementPackage,
    items: list[ProcurementPackageItem],
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": package.id,
        "project_id": package.project_id,
        "boq_version_id": package.boq_version_id,
        "title": package.title,
        "trade": package.trade,
        "commercial_type": package.commercial_type,
        "procurement_mode": package.procurement_mode,
        "region": package.region,
        "compatibility_json": package.compatibility_json,
        "delivery_constraints_json": package.delivery_constraints_json,
        "status": package.status,
        "revision": package.revision,
        "items": [
            {
                "id": row.id,
                "boq_item_id": row.boq_item_id,
                "boq_item_option_id": row.boq_item_option_id,
                "quantity": str(row.quantity),
            }
            for row in items
            if row.package_id == package.id
        ],
        "candidate_partners": candidates or [],
    }

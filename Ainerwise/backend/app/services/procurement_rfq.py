"""Commercial Snapshot creation and procurement RFQ publish (C07)."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement import (
    BoqVersion,
    CommercialSnapshot,
    ProcurementPackage,
    ProcurementPackageItem,
    ProcurementProject,
)
from app.models.rfq import RFQ, RFQ_TRADES
from app.services.procurement_boq import get_project_boq_version

_PACKAGE_TO_RFQ_TRADE = {
    "network": "network",
    "security": "security",
    "access": "security",
    "lighting": "electrical",
    "hvac": "hvac",
    "energy": "solar",
    "general": "general",
}

_REQUIRED_COMMERCIAL_KEYS = (
    "currency",
    "exchange_rate_snapshot_json",
    "tax_mode",
    "margin_rule_json",
    "service_fee_json",
    "warranty_rule_json",
    "delivery_region_json",
    "quote_expiry",
    "payment_terms_json",
)

_SENSITIVE_SNAPSHOT_KEYS = frozenset(
    {"margin_rule_json", "service_fee_json", "payment_terms_json"}
)


class ProcurementRfqError(ValueError):
    pass


class CommercialSnapshotImmutableError(ProcurementRfqError):
    pass


def map_package_trade_to_rfq_trade(package_trade: str) -> str:
    mapped = _PACKAGE_TO_RFQ_TRADE.get(package_trade.lower(), "general")
    return mapped if mapped in RFQ_TRADES else "general"


def canonical_terms_payload(terms: dict[str, Any]) -> dict[str, Any]:
    """Normalize commercial terms for stable hashing."""
    out: dict[str, Any] = {}
    for key in _REQUIRED_COMMERCIAL_KEYS:
        value = terms.get(key)
        if key == "quote_expiry" and isinstance(value, datetime):
            out[key] = value.astimezone(timezone.utc).isoformat()
        elif isinstance(value, (dict, list)):
            out[key] = json.loads(json.dumps(value, sort_keys=True))
        else:
            out[key] = value
    return out


def compute_terms_hash(terms: dict[str, Any]) -> str:
    canonical = canonical_terms_payload(terms)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_commercial_terms(terms: dict[str, Any]) -> None:
    problems: list[str] = []
    for key in _REQUIRED_COMMERCIAL_KEYS:
        if key not in terms or terms[key] in (None, "", {}, []):
            problems.append(f"missing or empty commercial field: {key}")
    if problems:
        raise ProcurementRfqError("; ".join(problems))
    if not isinstance(terms.get("exchange_rate_snapshot_json"), dict):
        raise ProcurementRfqError("exchange_rate_snapshot_json must be an object")
    for obj_key in (
        "margin_rule_json",
        "service_fee_json",
        "warranty_rule_json",
        "delivery_region_json",
        "payment_terms_json",
    ):
        if not isinstance(terms.get(obj_key), dict):
            raise ProcurementRfqError(f"{obj_key} must be an object")
    expiry = terms["quote_expiry"]
    if not isinstance(expiry, datetime):
        raise ProcurementRfqError("quote_expiry must be a datetime")


async def get_existing_procurement_rfq(
    db: AsyncSession, package_id: uuid.UUID, revision: int
) -> RFQ | None:
    result = await db.execute(
        select(RFQ).where(
            RFQ.procurement_package_id == package_id,
            RFQ.revision == revision,
        )
    )
    return result.scalar_one_or_none()


async def get_snapshot_for_package_revision(
    db: AsyncSession, package_id: uuid.UUID, revision: int
) -> CommercialSnapshot | None:
    result = await db.execute(
        select(CommercialSnapshot).where(
            CommercialSnapshot.package_id == package_id,
            CommercialSnapshot.package_revision == revision,
        )
    )
    return result.scalar_one_or_none()


def assert_snapshot_immutable() -> None:
    raise CommercialSnapshotImmutableError(
        "Commercial snapshots are immutable after creation"
    )


async def create_commercial_snapshot(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    package: ProcurementPackage,
    boq_version: BoqVersion,
    terms: dict[str, Any],
    created_by: uuid.UUID,
) -> CommercialSnapshot:
    validate_commercial_terms(terms)
    existing = await get_snapshot_for_package_revision(db, package.id, package.revision)
    if existing is not None:
        return existing

    terms_hash = compute_terms_hash(terms)
    snapshot = CommercialSnapshot(
        portal_key=project.portal_key,
        portal_policy_id=project.portal_policy_id,
        procurement_project_id=project.id,
        boq_version_id=boq_version.id,
        package_id=package.id,
        package_revision=package.revision,
        currency=str(terms["currency"]),
        exchange_rate_snapshot_json=terms["exchange_rate_snapshot_json"],
        tax_mode=str(terms["tax_mode"]),
        margin_rule_json=terms["margin_rule_json"],
        service_fee_json=terms["service_fee_json"],
        warranty_rule_json=terms["warranty_rule_json"],
        delivery_region_json=terms["delivery_region_json"],
        quote_expiry=terms["quote_expiry"],
        payment_terms_json=terms["payment_terms_json"],
        terms_hash=terms_hash,
        created_by=created_by,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


def build_rfq_scope(
    *,
    project: ProcurementProject,
    package: ProcurementPackage,
    item_count: int,
) -> dict[str, Any]:
    """Partner-safe scope without internal economics."""
    return {
        "procurement_project_id": str(project.id),
        "package_id": str(package.id),
        "commercial_type": package.commercial_type,
        "trade": package.trade,
        "region": package.region,
        "country": project.country,
        "city": project.city,
        "item_count": item_count,
        "summary": package.title,
        "procurement_mode": package.procurement_mode,
    }


async def create_procurement_rfq(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    package: ProcurementPackage,
    snapshot: CommercialSnapshot,
    created_by: uuid.UUID,
    bid_deadline: datetime | None = None,
    item_count: int = 0,
) -> RFQ:
    existing = await get_existing_procurement_rfq(db, package.id, package.revision)
    if existing is not None:
        return existing

    rfq = RFQ(
        trade=map_package_trade_to_rfq_trade(package.trade),
        title=package.title,
        scope_json=build_rfq_scope(project=project, package=package, item_count=item_count),
        currency=snapshot.currency,
        status="inviting",
        bid_deadline=bid_deadline,
        created_by=created_by,
        procurement_package_id=package.id,
        commercial_snapshot_id=snapshot.id,
        portal_key=project.portal_key,
        revision=package.revision,
    )
    db.add(rfq)
    await db.flush()
    return rfq


async def count_package_items(db: AsyncSession, package_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(ProcurementPackageItem)
        .where(ProcurementPackageItem.package_id == package_id)
    )
    return int(result.scalar_one())


async def all_project_packages_published(
    db: AsyncSession, project_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(ProcurementPackage.status).where(ProcurementPackage.project_id == project_id)
    )
    statuses = [row[0] for row in result.all()]
    return bool(statuses) and all(s == "published" for s in statuses)


async def publish_package_rfq(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    package: ProcurementPackage,
    user_id: uuid.UUID,
    terms: dict[str, Any],
    bid_deadline: datetime | None = None,
) -> tuple[CommercialSnapshot, RFQ, bool]:
    """Publish RFQ for a ready package. Returns (snapshot, rfq, created).

    Idempotent: if already published for this package revision, returns existing
    records with created=False.
    """
    if project.status not in ("packaged", "rfq_published"):
        raise ProcurementRfqError(
            f"project must be packaged before RFQ publish (status={project.status!r})"
        )
    if package.status == "published":
        existing_rfq = await get_existing_procurement_rfq(db, package.id, package.revision)
        snapshot = await get_snapshot_for_package_revision(db, package.id, package.revision)
        if existing_rfq and snapshot:
            return snapshot, existing_rfq, False
        raise ProcurementRfqError("package is published but RFQ linkage is missing")
    if package.status != "ready":
        raise ProcurementRfqError(f"package must be ready to publish (status={package.status!r})")

    boq_version = await db.get(BoqVersion, package.boq_version_id)
    if boq_version is None or boq_version.status != "frozen":
        raise ProcurementRfqError("package BOQ version must be frozen")

    current = await get_project_boq_version(db, project)
    if current is None or current.id != boq_version.id:
        raise ProcurementRfqError("package BOQ version is not the project frozen version")

    existing_rfq = await get_existing_procurement_rfq(db, package.id, package.revision)
    if existing_rfq is not None:
        snapshot = await get_snapshot_for_package_revision(db, package.id, package.revision)
        if snapshot is None:
            raise ProcurementRfqError("RFQ exists without commercial snapshot")
        package.status = "published"
        await db.flush()
        if await all_project_packages_published(db, project.id):
            project.status = "rfq_published"
        return snapshot, existing_rfq, False

    snapshot = await create_commercial_snapshot(
        db,
        project=project,
        package=package,
        boq_version=boq_version,
        terms=terms,
        created_by=user_id,
    )
    item_count = await count_package_items(db, package.id)
    rfq = await create_procurement_rfq(
        db,
        project=project,
        package=package,
        snapshot=snapshot,
        created_by=user_id,
        bid_deadline=bid_deadline,
        item_count=item_count,
    )
    package.status = "published"
    await db.flush()
    if await all_project_packages_published(db, project.id):
        project.status = "rfq_published"
    await db.flush()
    return snapshot, rfq, True


def _policy_snapshot(project: ProcurementProject) -> dict[str, Any]:
    return dict(project.policy_snapshot_json or {})


def serialize_snapshot_for_customer(
    snapshot: CommercialSnapshot, project: ProcurementProject
) -> dict[str, Any]:
    policy = _policy_snapshot(project)
    data = {
        "id": snapshot.id,
        "portal_key": snapshot.portal_key,
        "package_id": snapshot.package_id,
        "package_revision": snapshot.package_revision,
        "currency": snapshot.currency,
        "exchange_rate_snapshot_json": snapshot.exchange_rate_snapshot_json,
        "tax_mode": snapshot.tax_mode,
        "warranty_rule_json": snapshot.warranty_rule_json,
        "delivery_region_json": snapshot.delivery_region_json,
        "quote_expiry": snapshot.quote_expiry,
        "terms_hash": snapshot.terms_hash,
        "created_at": snapshot.created_at,
    }
    if policy.get("price_visibility_rule") == "line_estimates":
        data["payment_terms_json"] = snapshot.payment_terms_json
    if policy.get("supplier_visibility_rule") != "hidden":
        data["service_fee_json"] = snapshot.service_fee_json
    # margin_rule_json never exposed to customer serializers
    return data


def serialize_snapshot_for_supplier(snapshot: CommercialSnapshot) -> dict[str, Any]:
    return {
        "id": snapshot.id,
        "currency": snapshot.currency,
        "tax_mode": snapshot.tax_mode,
        "warranty_rule_json": snapshot.warranty_rule_json,
        "delivery_region_json": snapshot.delivery_region_json,
        "quote_expiry": snapshot.quote_expiry,
        "terms_hash": snapshot.terms_hash,
    }


def serialize_rfq_for_customer(
    rfq: RFQ, snapshot: CommercialSnapshot, project: ProcurementProject
) -> dict[str, Any]:
    return {
        "id": rfq.id,
        "title": rfq.title,
        "trade": rfq.trade,
        "status": rfq.status,
        "currency": rfq.currency,
        "bid_deadline": rfq.bid_deadline,
        "portal_key": rfq.portal_key,
        "revision": rfq.revision,
        "commercial_snapshot": serialize_snapshot_for_customer(snapshot, project),
    }


def serialize_rfq_for_supplier(rfq: RFQ, snapshot: CommercialSnapshot) -> dict[str, Any]:
    scope = dict(rfq.scope_json or {})
    for key in list(scope.keys()):
        if key in _SENSITIVE_SNAPSHOT_KEYS or "margin" in key or "fee" in key:
            scope.pop(key, None)
    return {
        "id": rfq.id,
        "title": rfq.title,
        "trade": rfq.trade,
        "scope_json": scope,
        "currency": rfq.currency,
        "status": rfq.status,
        "bid_deadline": rfq.bid_deadline,
        "commercial_snapshot": serialize_snapshot_for_supplier(snapshot),
    }


def portal_brand_payload(project: ProcurementProject) -> dict[str, Any]:
    """Branding hints for Channel Gateway outbox consumers."""
    policy = _policy_snapshot(project)
    return {
        "portal_key": project.portal_key,
        "portal_policy_id": str(project.portal_policy_id),
        "policy_version": policy.get("version"),
        "price_visibility_rule": policy.get("price_visibility_rule"),
        "supplier_visibility_rule": policy.get("supplier_visibility_rule"),
    }

"""BOQ versioning, tier derivation, review and freeze — flush-only."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai import AIReview
from app.models.procurement import (
    BOQ_TIERS,
    BoqItem,
    BoqItemOption,
    BoqVersion,
    ProcurementProject,
    ProcurementProjectFact,
    SolutionPlan,
)
from app.models.user import User
from app.services.procurement_confidence import (
    FREEZE_MIN_CRITICAL,
    compute_boq_score,
    compute_facts_score,
    compute_overall_confidence,
    effective_fact_confidence,
    effective_item_confidence,
    quantize_score as _quantize_score,
)

class ProcurementBoqError(ValueError):
    pass


async def get_next_boq_version_number(db: AsyncSession, project_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(BoqVersion.version), 0)).where(
            BoqVersion.project_id == project_id
        )
    )
    return int(result.scalar_one()) + 1


async def get_project_boq_version(
    db: AsyncSession, project: ProcurementProject
) -> BoqVersion | None:
    if project.current_boq_version_id is None:
        result = await db.execute(
            select(BoqVersion)
            .where(BoqVersion.project_id == project.id)
            .order_by(BoqVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    return await db.get(BoqVersion, project.current_boq_version_id)


async def list_items_for_version(db: AsyncSession, version_id: uuid.UUID) -> list[BoqItem]:
    result = await db.execute(
        select(BoqItem)
        .where(BoqItem.boq_version_id == version_id)
        .order_by(BoqItem.sort_order, BoqItem.created_at)
    )
    return list(result.scalars().all())


async def list_options_for_items(
    db: AsyncSession, item_ids: list[uuid.UUID]
) -> list[BoqItemOption]:
    if not item_ids:
        return []
    result = await db.execute(
        select(BoqItemOption).where(BoqItemOption.boq_item_id.in_(item_ids))
    )
    return list(result.scalars().all())


async def list_solution_plans(db: AsyncSession, version_id: uuid.UUID) -> list[SolutionPlan]:
    result = await db.execute(
        select(SolutionPlan)
        .where(SolutionPlan.boq_version_id == version_id)
        .order_by(SolutionPlan.tier)
    )
    return list(result.scalars().all())


def derive_option_totals(qty: Decimal, unit_min: Decimal, unit_max: Decimal) -> tuple[Decimal, Decimal]:
    return (qty * unit_min).quantize(Decimal("0.01")), (qty * unit_max).quantize(Decimal("0.01"))


def derive_solution_plan_totals(
    items: list[BoqItem], options: list[BoqItemOption], tier: str
) -> tuple[Decimal, Decimal, str]:
    item_by_id = {i.id: i for i in items if i.included}
    total_min = Decimal("0")
    total_max = Decimal("0")
    currency = "USD"
    for opt in options:
        if opt.tier != tier:
            continue
        item = item_by_id.get(opt.boq_item_id)
        if item is None:
            continue
        currency = opt.currency
        total_min += opt.total_price_min
        total_max += opt.total_price_max
    return total_min.quantize(Decimal("0.01")), total_max.quantize(Decimal("0.01")), currency


async def rebuild_solution_plans(
    db: AsyncSession,
    version: BoqVersion,
    items: list[BoqItem],
    options: list[BoqItemOption],
    *,
    summary: str | None = None,
    assumptions: str | None = None,
    exclusions: str | None = None,
) -> list[SolutionPlan]:
    existing = await list_solution_plans(db, version.id)
    for plan in existing:
        await db.delete(plan)
    await db.flush()

    plans: list[SolutionPlan] = []
    for tier in BOQ_TIERS:
        t_min, t_max, currency = derive_solution_plan_totals(items, options, tier)
        plan = SolutionPlan(
            boq_version_id=version.id,
            tier=tier,
            total_min=t_min,
            total_max=t_max,
            currency=currency,
            summary=summary,
            assumptions=assumptions,
            exclusions=exclusions,
            estimate_only=True,
        )
        db.add(plan)
        plans.append(plan)
    await db.flush()
    return plans


async def supersede_open_drafts(db: AsyncSession, project_id: uuid.UUID) -> None:
    result = await db.execute(
        select(BoqVersion).where(
            BoqVersion.project_id == project_id,
            BoqVersion.status.in_(("draft", "estimate", "in_review", "approved")),
        )
    )
    for version in result.scalars().all():
        version.status = "superseded"
    await db.flush()


async def create_draft_boq(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    facts: list[ProcurementProjectFact],
    items_payload: list[dict[str, Any]],
    disclaimer: str | None = None,
    source_run_id: uuid.UUID | None = None,
) -> tuple[BoqVersion, list[BoqItem], list[BoqItemOption], list[SolutionPlan]]:
    frozen = await db.execute(
        select(BoqVersion).where(
            BoqVersion.project_id == project.id,
            BoqVersion.status == "frozen",
        )
    )
    if frozen.scalar_one_or_none() is not None:
        # New drafts are allowed alongside frozen; they must not mutate frozen rows.
        await supersede_open_drafts(db, project.id)

    version_num = await get_next_boq_version_number(db, project.id)
    facts_score = compute_facts_score(facts)

    version = BoqVersion(
        project_id=project.id,
        version=version_num,
        status="draft",
        source_run_id=source_run_id,
        disclaimer=disclaimer
        or "Preliminary estimate only. Final pricing subject to site survey and approval.",
        facts_score=facts_score,
    )
    db.add(version)
    await db.flush()

    items: list[BoqItem] = []
    all_options: list[BoqItemOption] = []
    for idx, raw in enumerate(items_payload):
        item = BoqItem(
            boq_version_id=version.id,
            category=raw["category"],
            trade=raw.get("trade"),
            name=raw["name"],
            description=raw.get("description"),
            specs=raw.get("specs"),
            qty=Decimal(str(raw.get("qty", 1))),
            unit=raw.get("unit", "ea"),
            quantity_basis=raw.get("quantity_basis"),
            assumptions=raw.get("assumptions"),
            confidence=Decimal(str(raw.get("confidence", "0.9"))),
            source=raw.get("source", "system"),
            source_ref_json=raw.get("source_ref_json"),
            critical=bool(raw.get("critical", False)),
            weight=Decimal(str(raw.get("weight", "1"))),
            included=bool(raw.get("included", True)),
            sort_order=raw.get("sort_order", idx),
        )
        db.add(item)
        await db.flush()
        items.append(item)

        for opt in raw.get("options", []):
            tier = opt["tier"]
            if tier not in BOQ_TIERS:
                raise ProcurementBoqError(f"invalid tier: {tier!r}")
            unit_min = Decimal(str(opt["unit_price_min"]))
            unit_max = Decimal(str(opt["unit_price_max"]))
            t_min, t_max = derive_option_totals(item.qty, unit_min, unit_max)
            option = BoqItemOption(
                boq_item_id=item.id,
                tier=tier,
                capability=opt["capability"],
                recommended_brand=opt.get("recommended_brand"),
                unit_price_min=unit_min,
                unit_price_max=unit_max,
                total_price_min=t_min,
                total_price_max=t_max,
                currency=opt.get("currency", "USD"),
                supply_included=bool(opt.get("supply_included", True)),
                install_included=bool(opt.get("install_included", False)),
                maintain_included=bool(opt.get("maintain_included", False)),
                notes=opt.get("notes"),
            )
            db.add(option)
            all_options.append(option)

    await db.flush()
    version.boq_score = compute_boq_score(items)
    version.overall_confidence = compute_overall_confidence(version.facts_score, version.boq_score)
    project.facts_score = version.facts_score
    project.boq_score = version.boq_score
    project.overall_confidence = version.overall_confidence
    project.current_boq_version_id = version.id
    await db.flush()

    plans = await rebuild_solution_plans(
        db,
        version,
        items,
        all_options,
        assumptions="Totals derived from BOQ item options only.",
    )
    return version, items, all_options, plans


async def submit_boq_for_review(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    version: BoqVersion,
    user: User,
) -> AIReview:
    if version.status == "frozen":
        raise ProcurementBoqError("frozen BOQ versions cannot be submitted for review")
    if version.status not in ("draft", "estimate", "approved"):
        if version.status == "in_review" and version.review_id:
            review = await db.get(AIReview, version.review_id)
            if review:
                return review
        raise ProcurementBoqError(f"cannot review BOQ in status {version.status!r}")

    if version.review_id:
        review = await db.get(AIReview, version.review_id)
        if review and review.status == "preliminary":
            return review

    review = AIReview(
        target_type="boq_version",
        target_id=version.id,
        draft_json={"boq_version_id": str(version.id), "project_id": str(project.id)},
        status="preliminary",
    )
    db.add(review)
    await db.flush()
    version.review_id = review.id
    version.status = "in_review"
    await db.flush()
    return review


def validate_freeze_preconditions(
    *,
    project: ProcurementProject,
    version: BoqVersion,
    facts: list[ProcurementProjectFact],
    items: list[BoqItem],
    review: AIReview | None,
) -> None:
    if version.status == "frozen":
        raise ProcurementBoqError("BOQ version is already frozen")
    if version.status not in ("draft", "estimate", "in_review", "approved"):
        raise ProcurementBoqError(f"cannot freeze BOQ in status {version.status!r}")

    for fact in facts:
        if fact.required and not fact.user_confirmed:
            raise ProcurementBoqError(f"required fact not confirmed: {fact.template_key}")
        if fact.critical and effective_fact_confidence(fact) < FREEZE_MIN_CRITICAL:
            raise ProcurementBoqError(
                f"critical fact below confidence gate: {fact.template_key}"
            )

    for item in items:
        if not item.included:
            continue
        if not item.quantity_basis or not str(item.quantity_basis).strip():
            raise ProcurementBoqError(f"included item missing quantity_basis: {item.name}")
        if item.critical and effective_item_confidence(item) < FREEZE_MIN_CRITICAL:
            raise ProcurementBoqError(f"critical item below confidence gate: {item.name}")

    if review is None or review.status != "approved":
        raise ProcurementBoqError("approved human review is required before freeze")

    if version.overall_confidence < FREEZE_MIN_CRITICAL:
        raise ProcurementBoqError("overall confidence below freeze gate")


async def freeze_boq_version(
    db: AsyncSession,
    *,
    project: ProcurementProject,
    version: BoqVersion,
    user: User,
) -> BoqVersion:
    facts_result = await db.execute(
        select(ProcurementProjectFact).where(ProcurementProjectFact.project_id == project.id)
    )
    facts = list(facts_result.scalars().all())
    items = await list_items_for_version(db, version.id)
    review = await db.get(AIReview, version.review_id) if version.review_id else None

    validate_freeze_preconditions(
        project=project, version=version, facts=facts, items=items, review=review
    )

    now = datetime.now(timezone.utc)
    version.status = "frozen"
    version.frozen_by = user.id
    version.frozen_at = now
    project.status = "boq_frozen"
    project.current_boq_version_id = version.id
    await db.flush()
    return version


def serialize_boq_public(
    version: BoqVersion,
    items: list[BoqItem],
    options: list[BoqItemOption],
    plans: list[SolutionPlan],
) -> dict[str, Any]:
    """Customer-visible BOQ — no internal margin or source_ref leakage."""
    options_by_item: dict[uuid.UUID, list[BoqItemOption]] = {}
    for opt in options:
        options_by_item.setdefault(opt.boq_item_id, []).append(opt)

    public_items = []
    for item in items:
        if not item.included:
            continue
        public_items.append(
            {
                "id": str(item.id),
                "category": item.category,
                "trade": item.trade,
                "name": item.name,
                "description": item.description,
                "specs": item.specs,
                "qty": str(item.qty),
                "unit": item.unit,
                "quantity_basis": item.quantity_basis,
                "assumptions": item.assumptions,
                "options": [
                    {
                        "tier": o.tier,
                        "capability": o.capability,
                        "recommended_brand": o.recommended_brand,
                        "unit_price_min": str(o.unit_price_min),
                        "unit_price_max": str(o.unit_price_max),
                        "total_price_min": str(o.total_price_min),
                        "total_price_max": str(o.total_price_max),
                        "currency": o.currency,
                        "supply_included": o.supply_included,
                        "install_included": o.install_included,
                        "maintain_included": o.maintain_included,
                        "notes": o.notes,
                    }
                    for o in options_by_item.get(item.id, [])
                ],
            }
        )

    return {
        "version_id": str(version.id),
        "version": version.version,
        "status": version.status,
        "facts_score": str(version.facts_score),
        "boq_score": str(version.boq_score),
        "overall_confidence": str(version.overall_confidence),
        "disclaimer": version.disclaimer,
        "items": public_items,
        "solution_plans": [
            {
                "tier": p.tier,
                "total_min": str(p.total_min),
                "total_max": str(p.total_max),
                "currency": p.currency,
                "summary": p.summary,
                "assumptions": p.assumptions,
                "exclusions": p.exclusions,
                "estimate_only": p.estimate_only,
            }
            for p in plans
        ],
    }

"""Creative Brief lifecycle: versions, human review gate and Media Request seeding.

All mutators flush() only; the API endpoint owns commit/rollback.
Audit rows and outbox events are written in the same transaction.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIReview
from app.models.audit import AuditLog
from app.models.marketing import (
    BRIEF_STATUSES,
    DELIVERABLE_MEDIA_TYPES,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
    MarketingMediaRequest,
)
from app.models.user import User
from app.services.event_bus import emit_event


class MarketingBriefError(ValueError):
    """Raised when a brief operation violates the V4 state machine."""


MARKETING_EVENTS = {
    "created": "marketing.creative_brief.created",
    "submitted": "marketing.creative_brief.submitted",
    "approved": "marketing.creative_brief.approved",
    "rejected": "marketing.creative_brief.rejected",
    "media_request_available": "marketing.media_request.available",
}


async def _append_audit(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
    reason: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before,
            after_json=after,
        )
    )
    await db.flush()


def validate_deliverables(deliverables: list | None) -> list[str]:
    problems: list[str] = []
    if not deliverables or not isinstance(deliverables, list):
        return ["deliverables_json must be a non-empty list"]
    keys: set[str] = set()
    for idx, item in enumerate(deliverables):
        if not isinstance(item, dict):
            problems.append(f"deliverable[{idx}] must be an object")
            continue
        key = item.get("key")
        if not key or not isinstance(key, str):
            problems.append(f"deliverable[{idx}] missing key")
        elif key in keys:
            problems.append(f"duplicate deliverable key: {key}")
        else:
            keys.add(key)
        media_type = item.get("media_type")
        if media_type not in DELIVERABLE_MEDIA_TYPES:
            problems.append(f"deliverable[{idx}] invalid media_type: {media_type!r}")
        for field in ("channel", "language", "format"):
            if not item.get(field):
                problems.append(f"deliverable[{idx}] missing {field}")
    return problems


def build_export_payload(
    brief: MarketingCreativeBrief,
    version: MarketingCreativeBriefVersion,
) -> dict[str, Any]:
    """Provider-neutral outward payload used for content_hash and future export."""
    return {
        "brief_id": str(brief.id),
        "title": brief.title,
        "objective": brief.objective,
        "version": version.version,
        "copy": version.copy_json or {},
        "audience": version.audience_json or {},
        "brand_constraints": version.brand_constraints_json or {},
        "channel_specs": version.channel_specs_json or {},
        "deliverables": version.deliverables_json or [],
        "compliance": version.compliance_json or {},
    }


def compute_content_hash(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def version_content_fields(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "copy_json": data.get("copy_json"),
        "audience_json": data.get("audience_json"),
        "brand_constraints_json": data.get("brand_constraints_json"),
        "channel_specs_json": data.get("channel_specs_json"),
        "deliverables_json": data.get("deliverables_json"),
        "source_refs_json": data.get("source_refs_json"),
        "compliance_json": data.get("compliance_json"),
    }


async def get_brief(db: AsyncSession, brief_id: uuid.UUID) -> MarketingCreativeBrief | None:
    return (
        await db.execute(select(MarketingCreativeBrief).where(MarketingCreativeBrief.id == brief_id))
    ).scalar_one_or_none()


async def get_version(db: AsyncSession, version_id: uuid.UUID) -> MarketingCreativeBriefVersion | None:
    return (
        await db.execute(
            select(MarketingCreativeBriefVersion).where(MarketingCreativeBriefVersion.id == version_id)
        )
    ).scalar_one_or_none()


async def _next_version_number(db: AsyncSession, brief_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(MarketingCreativeBriefVersion.version), 0)).where(
            MarketingCreativeBriefVersion.brief_id == brief_id
        )
    )
    return int(result.scalar_one()) + 1


def _apply_content_hash(
    brief: MarketingCreativeBrief, version: MarketingCreativeBriefVersion
) -> None:
    payload = build_export_payload(brief, version)
    version.content_hash = compute_content_hash(payload)


async def create_brief(
    db: AsyncSession,
    *,
    actor: User,
    title: str,
    objective: str | None,
    campaign_id: uuid.UUID | None,
    region_id: uuid.UUID | None,
    version_data: dict[str, Any],
) -> tuple[MarketingCreativeBrief, MarketingCreativeBriefVersion]:
    problems = validate_deliverables(version_data.get("deliverables_json"))
    if problems:
        raise MarketingBriefError("; ".join(problems))

    brief = MarketingCreativeBrief(
        title=title,
        objective=objective,
        campaign_id=campaign_id,
        region_id=region_id,
        status="draft",
        created_by=actor.id,
    )
    db.add(brief)
    await db.flush()

    version = MarketingCreativeBriefVersion(
        brief_id=brief.id,
        version=1,
        status="draft",
        created_by=actor.id,
        **version_content_fields(version_data),
    )
    db.add(version)
    await db.flush()
    _apply_content_hash(brief, version)
    brief.current_version_id = version.id
    await db.flush()

    await _append_audit(
        db,
        actor_user_id=actor.id,
        action=MARKETING_EVENTS["created"],
        entity_type="marketing_creative_brief",
        entity_id=brief.id,
        after={"status": brief.status, "version": version.version},
    )
    await emit_event(
        db,
        MARKETING_EVENTS["created"],
        {"brief_id": str(brief.id), "version_id": str(version.id)},
        aggregate_type="marketing_creative_brief",
        aggregate_id=brief.id,
    )
    return brief, version


async def create_brief_version(
    db: AsyncSession,
    *,
    actor: User,
    brief_id: uuid.UUID,
    version_data: dict[str, Any],
    from_rejected: bool = False,
) -> MarketingCreativeBriefVersion:
    brief = await get_brief(db, brief_id)
    if brief is None:
        raise MarketingBriefError("brief not found")
    if brief.status == "retired":
        raise MarketingBriefError("retired brief cannot receive new versions")

    current = await get_version(db, brief.current_version_id) if brief.current_version_id else None
    if current and current.status == "draft" and not from_rejected:
        raise MarketingBriefError("current draft version must be submitted or updated before creating another version")
    if current and current.status == "approved":
        pass  # allowed: new version for re-approval
    elif current and current.status == "in_review":
        raise MarketingBriefError("cannot create a new version while current version is in review")
    elif current and current.status == "rejected" and not from_rejected:
        raise MarketingBriefError("copy rejected version explicitly or create from rejected endpoint")

    problems = validate_deliverables(version_data.get("deliverables_json"))
    if problems:
        raise MarketingBriefError("; ".join(problems))

    version = MarketingCreativeBriefVersion(
        brief_id=brief.id,
        version=await _next_version_number(db, brief.id),
        status="draft",
        created_by=actor.id,
        **version_content_fields(version_data),
    )
    db.add(version)
    await db.flush()
    _apply_content_hash(brief, version)
    brief.current_version_id = version.id
    brief.status = "draft"
    brief.approved_by = None
    brief.approved_at = None
    await db.flush()
    return version


async def update_draft_version(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
    version_data: dict[str, Any],
) -> MarketingCreativeBriefVersion:
    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "draft":
        raise MarketingBriefError("only draft versions can be edited")

    problems = validate_deliverables(version_data.get("deliverables_json", version.deliverables_json))
    if problems:
        raise MarketingBriefError("; ".join(problems))

    brief = await get_brief(db, version.brief_id)
    if brief is None:
        raise MarketingBriefError("brief not found")

    for field in version_content_fields(version_data):
        if field in version_data:
            setattr(version, field, version_data[field])
    _apply_content_hash(brief, version)
    await db.flush()
    return version


async def submit_version_review(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
) -> MarketingCreativeBriefVersion:
    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "draft":
        raise MarketingBriefError("only draft versions can be submitted for review")

    brief = await get_brief(db, version.brief_id)
    if brief is None:
        raise MarketingBriefError("brief not found")

    review = AIReview(
        target_type="marketing_creative_brief",
        target_id=version.id,
        draft_json=build_export_payload(brief, version),
        status="preliminary",
    )
    db.add(review)
    await db.flush()
    version.review_id = review.id
    version.status = "in_review"
    brief.status = "in_review"
    await db.flush()

    await _append_audit(
        db,
        actor_user_id=actor.id,
        action=MARKETING_EVENTS["submitted"],
        entity_type="marketing_creative_brief_version",
        entity_id=version.id,
        before={"status": "draft"},
        after={"status": "in_review", "review_id": str(review.id)},
    )
    await emit_event(
        db,
        MARKETING_EVENTS["submitted"],
        {"brief_id": str(brief.id), "version_id": str(version.id)},
        aggregate_type="marketing_creative_brief",
        aggregate_id=brief.id,
    )
    return version


async def approve_version(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
    notes: str | None = None,
) -> MarketingCreativeBriefVersion:
    if actor.role not in ("super_admin", "admin"):
        raise MarketingBriefError("only human admin users may approve creative briefs")

    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "in_review":
        raise MarketingBriefError("only in_review versions can be approved")

    brief = await get_brief(db, version.brief_id)
    if brief is None:
        raise MarketingBriefError("brief not found")

    if version.review_id:
        review = (
            await db.execute(select(AIReview).where(AIReview.id == version.review_id))
        ).scalar_one_or_none()
        if review:
            review.status = "approved"
            review.reviewed_by = actor.id
            review.reviewed_at = datetime.now(timezone.utc)
            review.review_notes = notes

    version.status = "approved"
    brief.status = "approved"
    brief.current_version_id = version.id
    brief.approved_by = actor.id
    brief.approved_at = datetime.now(timezone.utc)
    await db.flush()

    await _append_audit(
        db,
        actor_user_id=actor.id,
        action=MARKETING_EVENTS["approved"],
        entity_type="marketing_creative_brief_version",
        entity_id=version.id,
        before={"status": "in_review"},
        after={"status": "approved"},
        reason=notes,
    )
    await emit_event(
        db,
        MARKETING_EVENTS["approved"],
        {"brief_id": str(brief.id), "version_id": str(version.id)},
        aggregate_type="marketing_creative_brief",
        aggregate_id=brief.id,
    )
    return version


async def reject_version(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
    reason: str,
) -> MarketingCreativeBriefVersion:
    if actor.role not in ("super_admin", "admin"):
        raise MarketingBriefError("only human admin users may reject creative briefs")
    if not reason.strip():
        raise MarketingBriefError("rejection reason is required")

    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "in_review":
        raise MarketingBriefError("only in_review versions can be rejected")

    brief = await get_brief(db, version.brief_id)
    if brief is None:
        raise MarketingBriefError("brief not found")

    if version.review_id:
        review = (
            await db.execute(select(AIReview).where(AIReview.id == version.review_id))
        ).scalar_one_or_none()
        if review:
            review.status = "rejected"
            review.reviewed_by = actor.id
            review.reviewed_at = datetime.now(timezone.utc)
            review.review_notes = reason

    version.status = "rejected"
    brief.status = "rejected"
    await db.flush()

    await _append_audit(
        db,
        actor_user_id=actor.id,
        action=MARKETING_EVENTS["rejected"],
        entity_type="marketing_creative_brief_version",
        entity_id=version.id,
        before={"status": "in_review"},
        after={"status": "rejected"},
        reason=reason,
    )
    await emit_event(
        db,
        MARKETING_EVENTS["rejected"],
        {"brief_id": str(brief.id), "version_id": str(version.id), "reason": reason},
        aggregate_type="marketing_creative_brief",
        aggregate_id=brief.id,
    )
    return version


async def copy_rejected_to_draft(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
) -> MarketingCreativeBriefVersion:
    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "rejected":
        raise MarketingBriefError("only rejected versions can be copied to a new draft")

    return await create_brief_version(
        db,
        actor=actor,
        brief_id=version.brief_id,
        version_data=version_content_fields(
            {
                "copy_json": version.copy_json,
                "audience_json": version.audience_json,
                "brand_constraints_json": version.brand_constraints_json,
                "channel_specs_json": version.channel_specs_json,
                "deliverables_json": version.deliverables_json,
                "source_refs_json": version.source_refs_json,
                "compliance_json": version.compliance_json,
            }
        ),
        from_rejected=True,
    )


async def create_media_requests_for_version(
    db: AsyncSession,
    *,
    actor: User,
    version_id: uuid.UUID,
) -> list[MarketingMediaRequest]:
    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    if version.status != "approved":
        raise MarketingBriefError("only approved versions can create media requests")

    deliverables = version.deliverables_json or []
    problems = validate_deliverables(deliverables)
    if problems:
        raise MarketingBriefError("; ".join(problems))

    created: list[MarketingMediaRequest] = []
    for item in deliverables:
        key = item["key"]
        existing = (
            await db.execute(
                select(MarketingMediaRequest).where(
                    MarketingMediaRequest.brief_version_id == version.id,
                    MarketingMediaRequest.deliverable_key == key,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise MarketingBriefError(f"media request already exists for deliverable {key!r}")

        request = MarketingMediaRequest(
            brief_version_id=version.id,
            deliverable_key=key,
            status="available",
        )
        db.add(request)
        await db.flush()
        created.append(request)
        await emit_event(
            db,
            MARKETING_EVENTS["media_request_available"],
            {
                "media_request_id": str(request.id),
                "brief_version_id": str(version.id),
                "deliverable_key": key,
            },
            aggregate_type="marketing_media_request",
            aggregate_id=request.id,
        )
    return created


async def list_media_requests_for_version(
    db: AsyncSession,
    version_id: uuid.UUID,
) -> list[MarketingMediaRequest]:
    version = await get_version(db, version_id)
    if version is None:
        raise MarketingBriefError("version not found")
    rows = (
        await db.execute(
            select(MarketingMediaRequest)
            .where(MarketingMediaRequest.brief_version_id == version_id)
            .order_by(MarketingMediaRequest.created_at.asc())
        )
    ).scalars().all()
    return list(rows)

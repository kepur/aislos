"""KYC & verification service layer."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.kyc.models import CompanyDocument, KYCAnalysisResult, VerificationReview


class KYCError(ValueError):
    pass


async def upload_document(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    doc_type: str,
    file_url: str,
    original_filename: str | None = None,
) -> CompanyDocument:
    doc = CompanyDocument(
        company_id=company_id,
        doc_type=doc_type,
        file_url=file_url,
        original_filename=original_filename,
    )
    db.add(doc)
    await db.flush()
    return doc


async def list_documents(
    db: AsyncSession, company_id: uuid.UUID
) -> list[CompanyDocument]:
    return list(
        (
            await db.execute(
                select(CompanyDocument)
                .where(CompanyDocument.company_id == company_id)
                .order_by(CompanyDocument.created_at.desc())
            )
        ).scalars().all()
    )


async def review_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    status: str,
    reviewer_note: str | None = None,
) -> CompanyDocument:
    doc = await db.get(CompanyDocument, document_id)
    if doc is None:
        raise KYCError("Document not found")
    if doc.status != "PENDING":
        raise KYCError(f"Document already reviewed: {doc.status}")
    doc.status = status
    doc.reviewed_by = reviewer_id
    doc.reviewed_at = datetime.now(timezone.utc)
    doc.reviewer_note = reviewer_note
    await db.flush()
    return doc


async def get_or_create_verification(
    db: AsyncSession, company_id: uuid.UUID
) -> VerificationReview:
    existing = (
        await db.execute(
            select(VerificationReview)
            .where(VerificationReview.company_id == company_id)
            .order_by(VerificationReview.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    review = VerificationReview(company_id=company_id, status="NOT_STARTED")
    db.add(review)
    await db.flush()
    return review


async def submit_for_verification(
    db: AsyncSession, company_id: uuid.UUID
) -> VerificationReview:
    review = await get_or_create_verification(db, company_id)
    if review.status not in ("NOT_STARTED", "NEEDS_MORE_INFO"):
        raise KYCError(f"Cannot submit in status {review.status}")
    review.status = "SUBMITTED"
    await db.flush()
    return review


async def decide_verification(
    db: AsyncSession,
    review_id: uuid.UUID,
    admin_id: uuid.UUID,
    decision: str,
    decision_reason: str | None = None,
    internal_note: str | None = None,
    user_facing_note: str | None = None,
) -> VerificationReview:
    review = await db.get(VerificationReview, review_id)
    if review is None:
        raise KYCError("Verification review not found")
    if review.status not in ("SUBMITTED", "IN_REVIEW"):
        raise KYCError(f"Cannot decide in status {review.status}")

    status_map = {
        "APPROVE_BASIC": "APPROVED_BASIC",
        "APPROVE_BUSINESS": "APPROVED_BUSINESS",
        "REQUEST_MORE_INFO": "NEEDS_MORE_INFO",
        "REJECT": "REJECTED",
        "ESCALATE_TO_RISK": "IN_REVIEW",
    }
    review.status = status_map.get(decision, "IN_REVIEW")
    review.decision = decision
    review.decision_reason = decision_reason
    review.internal_note = internal_note
    review.user_facing_note = user_facing_note
    review.decided_by = admin_id
    review.decided_at = datetime.now(timezone.utc)
    await db.flush()
    return review


async def list_verification_queue(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 50,
) -> list[VerificationReview]:
    q = select(VerificationReview).order_by(VerificationReview.created_at.desc()).limit(limit)
    if status:
        q = q.where(VerificationReview.status == status)
    return list((await db.execute(q)).scalars().all())

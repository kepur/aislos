"""KYC & verification API routes."""
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUser, CurrentUser, DB, FinanceUser
from app.modules.kyc.models import CompanyDocument, VerificationReview
from app.modules.kyc.schemas import (
    CompanyDocumentCreate,
    CompanyDocumentRead,
    DocumentReviewRequest,
    KYCAnalysisRead,
    VerificationDecisionRequest,
    VerificationReviewRead,
)
from app.modules.kyc.service import (
    KYCError,
    decide_verification,
    get_or_create_verification,
    list_documents,
    list_verification_queue,
    review_document,
    submit_for_verification,
    upload_document,
)
from app.services.audit import append_audit_event

router = APIRouter(prefix="/kyc", tags=["kyc-verification"])
admin_router = APIRouter(prefix="/admin/kyc", tags=["kyc-admin"])


@router.get("/documents")
async def list_my_documents(db: DB, user: CurrentUser):
    if user.company_id is None:
        return {"items": [], "total": 0}
    items = await list_documents(db, user.company_id)
    return {
        "items": [CompanyDocumentRead.model_validate(d).model_dump() for d in items],
        "total": len(items),
    }


@router.post("/documents", response_model=CompanyDocumentRead, status_code=201)
async def upload_my_document(data: CompanyDocumentCreate, db: DB, user: CurrentUser):
    if user.company_id is None:
        raise HTTPException(status_code=403, detail="Company required")
    doc = await upload_document(
        db,
        company_id=user.company_id,
        doc_type=data.doc_type,
        file_url=data.file_url,
        original_filename=data.original_filename,
    )
    await db.commit()
    await db.refresh(doc)
    return CompanyDocumentRead.model_validate(doc)


@router.get("/verification/status", response_model=VerificationReviewRead)
async def my_verification_status(db: DB, user: CurrentUser):
    if user.company_id is None:
        raise HTTPException(status_code=403, detail="Company required")
    review = await get_or_create_verification(db, user.company_id)
    await db.commit()
    await db.refresh(review)
    return VerificationReviewRead.model_validate(review)


@router.post("/verification/submit", response_model=VerificationReviewRead)
async def submit_my_verification(db: DB, user: CurrentUser):
    if user.company_id is None:
        raise HTTPException(status_code=403, detail="Company required")
    try:
        review = await submit_for_verification(db, user.company_id)
        await db.commit()
        await db.refresh(review)
        return VerificationReviewRead.model_validate(review)
    except KYCError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


# ── Admin ──────────────────────────────────────────────────────────


@admin_router.get("/documents/{company_id}")
async def admin_list_company_documents(company_id: uuid.UUID, db: DB, admin: AdminUser):
    items = await list_documents(db, company_id)
    return {
        "items": [CompanyDocumentRead.model_validate(d).model_dump() for d in items],
        "total": len(items),
    }


@admin_router.post("/documents/{document_id}/review", response_model=CompanyDocumentRead)
async def admin_review_document(
    document_id: uuid.UUID, data: DocumentReviewRequest, db: DB, admin: AdminUser
):
    try:
        current = await db.get(CompanyDocument, document_id)
        before_status = current.status if current else None
        doc = await review_document(
            db, document_id, admin.id, data.status, data.reviewer_note
        )
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=admin.id,
            portal_key="admin_cebu",
            action="cebu.admin.kyc_document_reviewed",
            entity_type="company_document",
            entity_id=doc.id,
            before={"status": before_status},
            after={"status": doc.status, "company_id": str(doc.company_id)},
            reason=data.reviewer_note,
            source="admin.kyc",
        )
        await db.commit()
        await db.refresh(doc)
        return CompanyDocumentRead.model_validate(doc)
    except KYCError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@admin_router.get("/verification/queue")
async def admin_verification_queue(
    db: DB, admin: AdminUser, status: str | None = None
):
    items = await list_verification_queue(db, status=status)
    return {
        "items": [VerificationReviewRead.model_validate(r).model_dump() for r in items],
        "total": len(items),
    }


@admin_router.post("/verification/{review_id}/decide", response_model=VerificationReviewRead)
async def admin_decide_verification(
    review_id: uuid.UUID, data: VerificationDecisionRequest, db: DB, admin: AdminUser
):
    try:
        current = await db.get(VerificationReview, review_id)
        before_status = current.status if current else None
        review = await decide_verification(
            db,
            review_id,
            admin.id,
            data.decision,
            data.decision_reason,
            data.internal_note,
            data.user_facing_note,
        )
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=admin.id,
            portal_key="admin_cebu",
            action="cebu.admin.kyc_verification_decided",
            entity_type="verification_review",
            entity_id=review.id,
            before={"status": before_status},
            after={"status": review.status, "decision": review.decision},
            reason=data.decision_reason,
            source="admin.kyc",
        )
        await db.commit()
        await db.refresh(review)
        return VerificationReviewRead.model_validate(review)
    except KYCError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None

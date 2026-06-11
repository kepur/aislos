import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.ai import AIReview, Conversation, ConversationMessage
from app.schemas.ai import (
    AIReviewDecision,
    AIReviewRead,
    ConversationMessageRead,
    ConversationRead,
)

router = APIRouter(prefix="/admin", tags=["ai-reviews"])


@router.get("/ai-reviews")
async def list_ai_reviews(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    target_type: str | None = None,
):
    filters = []
    if status:
        filters.append(AIReview.status == status)
    if target_type:
        filters.append(AIReview.target_type == target_type)

    query = select(AIReview).order_by(AIReview.created_at.desc())
    count_query = select(func.count()).select_from(AIReview)
    for item in filters:
        query = query.where(item)
        count_query = count_query.where(item)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [AIReviewRead.model_validate(r) for r in result.scalars().all()],
        "total": total,
    }


async def _decide(db, admin, id: uuid.UUID, status: str, notes: str | None) -> AIReviewRead:
    review = await db.get(AIReview, id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != "preliminary":
        raise HTTPException(status_code=409, detail=f"Review already {review.status}")
    if review.target_type == "mission_plan" and status == "approved":
        raise HTTPException(
            status_code=409,
            detail="Approve mission plans through the mission endpoint so project grants are created.",
        )
    review.status = status
    review.reviewed_by = admin.id
    review.reviewed_at = datetime.now(timezone.utc)
    review.review_notes = notes
    db.add(review)
    if review.target_type in ("mission_plan", "mission_final_report") and review.target_id:
        from app.models.mission import AgentMission

        mission = await db.get(AgentMission, review.target_id)
        if mission:
            if review.target_type == "mission_plan" and status == "rejected":
                mission.status = "plan_rejected"
            elif review.target_type == "mission_final_report" and status == "approved":
                mission.status = "completed"
                mission.completed_at = datetime.now(timezone.utc)
                report = dict(mission.final_report_json or {})
                report["preliminary"] = False
                report["review_status"] = "approved"
                report["approved_at"] = mission.completed_at.isoformat()
                reviewer_checks = dict(report.get("reviewer_checks") or {})
                reviewer_checks["human_approval_required"] = False
                reviewer_checks["human_approved"] = True
                report["reviewer_checks"] = reviewer_checks
                mission.final_report_json = report
            elif review.target_type == "mission_final_report" and status == "rejected":
                mission.status = "report_rejected"
            db.add(mission)
    await db.commit()
    await db.refresh(review)
    return AIReviewRead.model_validate(review)


@router.post("/ai-reviews/{id}/approve", response_model=AIReviewRead)
async def approve_ai_review(id: uuid.UUID, data: AIReviewDecision, db: DB, admin: AdminUser):
    return await _decide(db, admin, id, "approved", data.notes)


@router.post("/ai-reviews/{id}/reject", response_model=AIReviewRead)
async def reject_ai_review(id: uuid.UUID, data: AIReviewDecision, db: DB, admin: AdminUser):
    return await _decide(db, admin, id, "rejected", data.notes)


# --- conversation observability ----------------------------------------------


@router.get("/ai-conversations")
async def list_conversations(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    channel: str | None = None,
):
    query = select(Conversation).order_by(Conversation.updated_at.desc())
    count_query = select(func.count()).select_from(Conversation)
    if channel:
        query = query.where(Conversation.channel == channel)
        count_query = count_query.where(Conversation.channel == channel)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit))
    return {
        "items": [ConversationRead.model_validate(c) for c in result.scalars().all()],
        "total": total,
    }


@router.get("/ai-conversations/{id}/messages")
async def get_conversation_messages(id: uuid.UUID, db: DB, admin: AdminUser):
    convo = await db.get(Conversation, id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == id)
        .order_by(ConversationMessage.created_at)
    )
    return {
        "conversation": ConversationRead.model_validate(convo),
        "messages": [ConversationMessageRead.model_validate(m) for m in result.scalars().all()],
    }

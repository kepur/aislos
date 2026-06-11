from statistics import mean
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.audit_log import RiskLevel
from app.models.company import Company
from app.models.order import Order, OrderStatus
from app.models.transaction_review import ReviewTargetType, TransactionChannel, TransactionReview
from app.models.user import User, UserRole
from app.schemas.review import (
    BuyerReviewCreate,
    ReviewSummaryResponse,
    SellerReviewCreate,
    TransactionReviewResponse,
)
from app.services.audit_service import create_audit_log

router = APIRouter(tags=["Reviews"])

REVIEWABLE_ORDER_STATUSES = {
    OrderStatus.ACCEPTED,
    OrderStatus.PAYOUT_RELEASED,
}


async def _get_order_for_review(order_id: UUID, db: AsyncSession) -> Order:
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in REVIEWABLE_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Order can be reviewed after completion or buyer acceptance")
    return order


async def _supplier_company_for_user(user: User, db: AsyncSession) -> Company | None:
    if user.role not in (UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT):
        return None
    return (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalar_one_or_none()


async def _ensure_no_duplicate(order_id: UUID, reviewer_id: UUID, target_type: ReviewTargetType, db: AsyncSession) -> None:
    existing = (
        await db.execute(
            select(TransactionReview).where(
                TransactionReview.order_id == order_id,
                TransactionReview.reviewer_id == reviewer_id,
                TransactionReview.target_type == target_type,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Review already submitted for this order")


def _avg(values: list[int | None]) -> float | None:
    nums = [v for v in values if v is not None]
    return round(mean(nums), 2) if nums else None


@router.post("/orders/{order_id}/reviews/seller", response_model=TransactionReviewResponse, status_code=201)
async def review_seller(
    order_id: UUID,
    req: SellerReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_order_for_review(order_id, db)
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can review the seller")

    await _ensure_no_duplicate(order.id, user.id, ReviewTargetType.SELLER, db)

    rating_values = [req.product_quality_rating, req.communication_rating]
    if req.transaction_channel == TransactionChannel.ONLINE:
        rating_values.append(req.logistics_rating)

    review = TransactionReview(
        order_id=order.id,
        reviewer_id=user.id,
        reviewee_company_id=order.company_id,
        target_type=ReviewTargetType.SELLER,
        transaction_channel=req.transaction_channel,
        product_quality_rating=req.product_quality_rating,
        logistics_rating=req.logistics_rating,
        communication_rating=req.communication_rating,
        overall_rating=round(mean([v for v in rating_values if v is not None])),
        comment=req.comment,
    )
    db.add(review)
    await create_audit_log(
        db,
        action="TRANSACTION_REVIEW_CREATED",
        entity_type="TransactionReview",
        entity_id=review.id,
        actor_id=user.id,
        actor_role=user.role.value,
        after_json={"order_id": str(order.id), "target_type": "SELLER", "channel": req.transaction_channel.value},
        risk_level=RiskLevel.LOW,
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.post("/orders/{order_id}/reviews/buyer", response_model=TransactionReviewResponse, status_code=201)
async def review_buyer(
    order_id: UUID,
    req: BuyerReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_order_for_review(order_id, db)
    company = await _supplier_company_for_user(user, db)
    if not company or company.id != order.company_id:
        raise HTTPException(status_code=403, detail="Only the order seller can review the buyer")

    await _ensure_no_duplicate(order.id, user.id, ReviewTargetType.BUYER, db)

    review = TransactionReview(
        order_id=order.id,
        reviewer_id=user.id,
        reviewee_user_id=order.buyer_id,
        target_type=ReviewTargetType.BUYER,
        transaction_channel=req.transaction_channel,
        buyer_rating=req.buyer_rating,
        communication_rating=req.communication_rating,
        overall_rating=round(mean([req.buyer_rating, req.communication_rating])),
        comment=req.comment,
    )
    db.add(review)
    await create_audit_log(
        db,
        action="TRANSACTION_REVIEW_CREATED",
        entity_type="TransactionReview",
        entity_id=review.id,
        actor_id=user.id,
        actor_role=user.role.value,
        after_json={"order_id": str(order.id), "target_type": "BUYER", "channel": req.transaction_channel.value},
        risk_level=RiskLevel.LOW,
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/orders/{order_id}/reviews", response_model=list[TransactionReviewResponse])
async def list_order_reviews(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    company = await _supplier_company_for_user(user, db)
    can_view = order.buyer_id == user.id or (company is not None and company.id == order.company_id) or user.role in {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    }
    if not can_view:
        raise HTTPException(status_code=403, detail="Not allowed to view reviews for this order")
    rows = (
        await db.execute(select(TransactionReview).where(TransactionReview.order_id == order.id).order_by(TransactionReview.created_at.desc()))
    ).scalars().all()
    return rows


@router.get("/reviews/company/me", response_model=ReviewSummaryResponse)
async def my_company_reviews(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await _supplier_company_for_user(user, db)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    rows = (
        await db.execute(
            select(TransactionReview)
            .where(TransactionReview.reviewee_company_id == company.id, TransactionReview.target_type == ReviewTargetType.SELLER)
            .order_by(TransactionReview.created_at.desc())
        )
    ).scalars().all()
    return ReviewSummaryResponse(
        total_reviews=len(rows),
        average_overall_rating=_avg([r.overall_rating for r in rows]) or 0,
        average_product_quality_rating=_avg([r.product_quality_rating for r in rows]),
        average_logistics_rating=_avg([r.logistics_rating for r in rows]),
        average_communication_rating=_avg([r.communication_rating for r in rows]),
        online_reviews=sum(1 for r in rows if r.transaction_channel == TransactionChannel.ONLINE),
        offline_reviews=sum(1 for r in rows if r.transaction_channel == TransactionChannel.OFFLINE),
        reviews=rows,
    )


@router.get("/reviews/buyer/me", response_model=ReviewSummaryResponse)
async def my_buyer_reviews(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(TransactionReview)
            .where(TransactionReview.reviewee_user_id == user.id, TransactionReview.target_type == ReviewTargetType.BUYER)
            .order_by(TransactionReview.created_at.desc())
        )
    ).scalars().all()
    return ReviewSummaryResponse(
        total_reviews=len(rows),
        average_overall_rating=_avg([r.overall_rating for r in rows]) or 0,
        average_buyer_rating=_avg([r.buyer_rating for r in rows]),
        average_communication_rating=_avg([r.communication_rating for r in rows]),
        online_reviews=sum(1 for r in rows if r.transaction_channel == TransactionChannel.ONLINE),
        offline_reviews=sum(1 for r in rows if r.transaction_channel == TransactionChannel.OFFLINE),
        reviews=rows,
    )

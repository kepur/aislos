"""Phase 2: Trust, reviews, risk flags, payment intents, FX for commerce orders."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import (
    CommerceOrder,
    CommercePaymentIntent,
    OrderDispute,
    RiskFlag,
    TransactionReview,
    TrustProfile,
    TrustScoreEvent,
)
from app.models.payment import PaymentMilestone, PaymentPlan
from app.models.user import User
from app.services.event_bus import emit_event
from app.services.pricing import convert_amount

TWO_PLACES = Decimal("0.01")


class CommerceTrustError(ValueError):
    pass


def _recalculate_trust_score(profile: TrustProfile) -> None:
    score = 50
    score += min(profile.completed_orders * 5, 30)
    if profile.avg_rating is not None:
        score += int(float(profile.avg_rating) * 8)
    score -= profile.dispute_count * 10
    profile.trust_score = max(0, min(100, score))


async def _record_trust_score_event(
    db: AsyncSession,
    profile: TrustProfile,
    *,
    event_type: str,
    before_score: int,
    reason: str,
    related_entity_type: str | None = None,
    related_entity_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> TrustScoreEvent:
    row = TrustScoreEvent(
        trust_profile_id=profile.id,
        event_type=event_type,
        score_delta=profile.trust_score - before_score,
        before_score=before_score,
        after_score=profile.trust_score,
        reason=reason,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        created_by=created_by,
    )
    db.add(row)
    await db.flush()
    return row


async def get_or_create_trust_profile(
    db: AsyncSession, *, company_id: uuid.UUID, portal_key: str = "cebu"
) -> TrustProfile:
    row = (
        await db.execute(
            select(TrustProfile).where(
                TrustProfile.company_id == company_id,
                TrustProfile.portal_key == portal_key,
            )
        )
    ).scalar_one_or_none()
    if row:
        return row
    row = TrustProfile(company_id=company_id, portal_key=portal_key)
    db.add(row)
    await db.flush()
    return row


async def record_order_completed(db: AsyncSession, order: CommerceOrder) -> TrustProfile | None:
    if not order.supplier_company_id:
        return None
    profile = await get_or_create_trust_profile(db, company_id=order.supplier_company_id)
    before_score = profile.trust_score
    profile.completed_orders += 1
    _recalculate_trust_score(profile)
    await db.flush()
    await _record_trust_score_event(
        db,
        profile,
        event_type="ORDER_COMPLETED",
        before_score=before_score,
        reason="Supplier completed a commerce order",
        related_entity_type="ORDER",
        related_entity_id=order.id,
    )
    await emit_event(
        db,
        "commerce.trust.updated",
        {
            "company_id": str(order.supplier_company_id),
            "trust_score": profile.trust_score,
            "completed_orders": profile.completed_orders,
        },
        aggregate_type="trust_profile",
        aggregate_id=profile.id,
    )
    return profile


async def record_dispute_opened(
    db: AsyncSession, *, order: CommerceOrder, dispute: OrderDispute
) -> tuple[TrustProfile | None, RiskFlag]:
    profile = None
    if order.supplier_company_id:
        profile = await get_or_create_trust_profile(db, company_id=order.supplier_company_id)
        before_score = profile.trust_score
        profile.dispute_count += 1
        _recalculate_trust_score(profile)
        await db.flush()
        await _record_trust_score_event(
            db,
            profile,
            event_type="DISPUTE_OPENED",
            before_score=before_score,
            reason=f"Commerce dispute opened: {dispute.reason_code}",
            related_entity_type="ORDER",
            related_entity_id=order.id,
            created_by=dispute.opened_by_user_id,
        )
    flag = RiskFlag(
        subject_type="commerce_order",
        subject_id=order.id,
        company_id=order.supplier_company_id,
        reason_code=dispute.reason_code,
        severity="high" if dispute.reason_code in ("fraud", "non_delivery") else "medium",
        status="open",
        source_event="commerce.dispute.opened",
        details_json={
            "dispute_id": str(dispute.id),
            "order_id": str(order.id),
            "opened_by_role": dispute.opened_by_role,
        },
    )
    db.add(flag)
    await db.flush()
    await emit_event(
        db,
        "commerce.risk_flag.raised",
        {"flag_id": str(flag.id), "order_id": str(order.id), "reason_code": dispute.reason_code},
        aggregate_type="risk_flag",
        aggregate_id=flag.id,
    )
    return profile, flag


async def submit_transaction_review(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    user: User,
    rating: int,
    comment: str | None,
) -> TransactionReview:
    if rating < 1 or rating > 5:
        raise CommerceTrustError("rating must be 1-5")
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceTrustError("order not found")
    if order.workspace_id is None:
        raise CommerceTrustError("commerce order requires a Workspace")
    if order.status != "completed":
        raise CommerceTrustError("order must be completed before review")
    if order.buyer_company_id and user.company_id != order.buyer_company_id:
        if user.role not in ("admin", "super_admin"):
            raise CommerceTrustError("only buyer can review")
    existing = (
        await db.execute(
            select(TransactionReview).where(
                TransactionReview.commerce_order_id == order_id,
                TransactionReview.reviewer_user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise CommerceTrustError("review already submitted")
    row = TransactionReview(
        workspace_id=order.workspace_id,
        commerce_order_id=order_id,
        reviewer_user_id=user.id,
        supplier_company_id=order.supplier_company_id,
        rating=rating,
        comment=comment,
    )
    db.add(row)
    await db.flush()
    if order.supplier_company_id:
        profile = await get_or_create_trust_profile(db, company_id=order.supplier_company_id)
        before_score = profile.trust_score
        avg = (
            await db.execute(
                select(func.avg(TransactionReview.rating)).where(
                    TransactionReview.supplier_company_id == order.supplier_company_id,
                    TransactionReview.status == "published",
                )
            )
        ).scalar_one()
        profile.review_count += 1
        profile.avg_rating = Decimal(str(avg or rating)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        _recalculate_trust_score(profile)
        await db.flush()
        await _record_trust_score_event(
            db,
            profile,
            event_type="REVIEW_SUBMITTED",
            before_score=before_score,
            reason=f"Buyer submitted a {rating}-star transaction review",
            related_entity_type="ORDER",
            related_entity_id=order.id,
            created_by=user.id,
        )
    await emit_event(
        db,
        "commerce.review.submitted",
        {"order_id": str(order_id), "review_id": str(row.id), "rating": rating},
        aggregate_type="transaction_review",
        aggregate_id=row.id,
    )
    return row


async def list_risk_flags(
    db: AsyncSession, *, status: str | None = None, limit: int = 50
) -> list[RiskFlag]:
    q = select(RiskFlag).order_by(RiskFlag.created_at.desc()).limit(limit)
    if status:
        q = q.where(RiskFlag.status == status)
    return list((await db.execute(q)).scalars())


async def resolve_risk_flag(
    db: AsyncSession, flag_id: uuid.UUID, *, user: User, resolution: str
) -> RiskFlag:
    if resolution not in ("resolved", "dismissed"):
        raise CommerceTrustError("invalid resolution")
    row = await db.get(RiskFlag, flag_id)
    if row is None:
        raise CommerceTrustError("risk flag not found")
    if row.status != "open":
        raise CommerceTrustError("risk flag not open")
    row.status = resolution
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by_user_id = user.id
    await db.flush()
    return row


async def create_payment_intent(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    quote_currency: str | None = None,
    psp_provider: str = "stripe",
) -> CommercePaymentIntent:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceTrustError("order not found")
    if order.workspace_id is None:
        raise CommerceTrustError("commerce order requires a Workspace")
    if order.status in ("pending", "cancelled"):
        raise CommerceTrustError("order not payable in current status")
    existing = (
        await db.execute(
            select(CommercePaymentIntent).where(CommercePaymentIntent.commerce_order_id == order_id)
        )
    ).scalar_one_or_none()
    if existing:
        if existing.workspace_id != order.workspace_id:
            raise CommerceTrustError("payment intent and order belong to different Workspaces")
        return existing
    total = Decimal(order.total_minor) / 100
    plan = PaymentPlan(
        workspace_id=order.workspace_id,
        currency=order.currency,
        total=total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
        status="draft",
        notes=f"Commerce order {order_id}",
    )
    db.add(plan)
    await db.flush()
    milestone = PaymentMilestone(
        workspace_id=order.workspace_id,
        plan_id=plan.id,
        seq=1,
        label="Order total",
        pct=Decimal("100"),
        amount=plan.total,
        trigger="on_accept",
        status="pending",
    )
    db.add(milestone)
    fx_rate = None
    quote_amount_minor = None
    if quote_currency and quote_currency.upper() != order.currency.upper():
        converted = await convert_amount(db, plan.total, order.currency, quote_currency.upper())
        fx_rate = (converted / plan.total).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
        quote_amount_minor = int((converted * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    intent = CommercePaymentIntent(
        workspace_id=order.workspace_id,
        commerce_order_id=order_id,
        payment_plan_id=plan.id,
        psp_provider=psp_provider,
        status="pending",
        amount_minor=order.total_minor,
        currency=order.currency,
        quote_currency=quote_currency.upper() if quote_currency else None,
        fx_rate=fx_rate,
        quote_amount_minor=quote_amount_minor,
    )
    db.add(intent)
    await db.flush()
    await emit_event(
        db,
        "commerce.payment.intent.created",
        {"order_id": str(order_id), "intent_id": str(intent.id), "amount_minor": order.total_minor},
        aggregate_type="commerce_payment_intent",
        aggregate_id=intent.id,
    )
    return intent


async def fx_quote_for_order(
    db: AsyncSession, *, order_id: uuid.UUID, quote_currency: str
) -> dict:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceTrustError("order not found")
    base = Decimal(order.total_minor) / 100
    quote = quote_currency.upper()
    if quote == order.currency.upper():
        return {
            "order_id": str(order_id),
            "base_currency": order.currency,
            "quote_currency": quote,
            "base_amount_minor": order.total_minor,
            "quote_amount_minor": order.total_minor,
            "fx_rate": "1",
        }
    converted = await convert_amount(db, base, order.currency, quote)
    rate = (converted / base).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    quote_minor = int((converted * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {
        "order_id": str(order_id),
        "base_currency": order.currency,
        "quote_currency": quote,
        "base_amount_minor": order.total_minor,
        "quote_amount_minor": quote_minor,
        "fx_rate": str(rate),
    }

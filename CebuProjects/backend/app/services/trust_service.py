import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogItem, CatalogItemStatus
from app.models.company import Branch, Company, VerificationLevel
from app.models.dispute import Dispute
from app.models.order import Order, OrderStatus
from app.models.risk_flag import RiskFlag, RiskFlagStatus
from app.models.trust import (
    TrustEntityType,
    TrustProfile,
    TrustProfileStatus,
    TrustScoreEvent,
    TrustScoreEventType,
    TrustTier,
)
from app.models.user import User
from app.models.wallet import Wallet


SUCCESS_ORDER_STATUSES = {
    OrderStatus.ACCEPTED,
    OrderStatus.PAYOUT_RELEASED,
}
CANCELED_ORDER_STATUSES = {
    OrderStatus.CANCELED,
    OrderStatus.REFUNDED,
}


def tier_for_score(score: int) -> TrustTier:
    if score >= 850:
        return TrustTier.DIAMOND
    if score >= 700:
        return TrustTier.PLATINUM
    if score >= 400:
        return TrustTier.GOLD
    if score >= 200:
        return TrustTier.SILVER
    return TrustTier.BRONZE


def clamp(value: int, low: int = 0, high: int = 1000) -> int:
    return max(low, min(high, value))


async def get_or_create_trust_profile(
    db: AsyncSession,
    *,
    entity_type: TrustEntityType,
    entity_id: uuid.UUID,
) -> TrustProfile:
    result = await db.execute(
        select(TrustProfile).where(
            TrustProfile.entity_type == entity_type,
            TrustProfile.entity_id == entity_id,
        )
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile

    profile = TrustProfile(
        entity_type=entity_type,
        entity_id=entity_id,
        trust_score=0,
        trust_tier=TrustTier.BRONZE,
        status=TrustProfileStatus.ACTIVE,
    )
    db.add(profile)
    await db.flush()
    return profile


async def recalculate_trust_profile(
    db: AsyncSession,
    *,
    entity_type: TrustEntityType,
    entity_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    reason: str = "system_recalculate",
) -> TrustProfile:
    profile = await get_or_create_trust_profile(db, entity_type=entity_type, entity_id=entity_id)
    before_score = profile.trust_score

    if entity_type == TrustEntityType.USER:
        facts = await _calculate_user_facts(db, entity_id)
    else:
        facts = await _calculate_company_facts(db, entity_id)

    profile.profile_completion_rate = facts["profile_completion_rate"]
    profile.deal_completion_rate = facts["deal_completion_rate"]
    profile.deposit_amount_minor = facts["deposit_amount_minor"]
    profile.deposit_currency = facts["deposit_currency"]
    profile.verified_deposit_minor = facts["verified_deposit_minor"]
    profile.successful_deals_count = facts["successful_deals_count"]
    profile.canceled_deals_count = facts["canceled_deals_count"]
    profile.dispute_rate = facts["dispute_rate"]
    profile.refund_rate = facts["refund_rate"]
    profile.late_delivery_rate = facts["late_delivery_rate"]
    profile.late_payment_rate = facts["late_payment_rate"]
    profile.score_breakdown_json = facts["score_breakdown"]

    if profile.status != TrustProfileStatus.FROZEN:
        profile.trust_score = facts["trust_score"]
        profile.trust_tier = tier_for_score(profile.trust_score)

    profile.last_calculated_at = datetime.now(timezone.utc)

    db.add(
        TrustScoreEvent(
            trust_profile_id=profile.id,
            event_type=TrustScoreEventType.RECALCULATED,
            score_delta=profile.trust_score - before_score,
            before_score=before_score,
            after_score=profile.trust_score,
            reason=reason,
            created_by=actor_id,
        )
    )
    await db.flush()
    return profile


async def adjust_trust_profile(
    db: AsyncSession,
    *,
    entity_type: TrustEntityType,
    entity_id: uuid.UUID,
    score_delta: int,
    reason: str,
    actor_id: uuid.UUID,
    freeze: bool | None = None,
) -> TrustProfile:
    profile = await get_or_create_trust_profile(db, entity_type=entity_type, entity_id=entity_id)
    before_score = profile.trust_score
    profile.trust_score = clamp(profile.trust_score + score_delta)
    profile.trust_tier = tier_for_score(profile.trust_score)
    if freeze is True:
        profile.status = TrustProfileStatus.FROZEN
    elif freeze is False and profile.status == TrustProfileStatus.FROZEN:
        profile.status = TrustProfileStatus.ACTIVE

    db.add(
        TrustScoreEvent(
            trust_profile_id=profile.id,
            event_type=TrustScoreEventType.ADMIN_ADJUSTED,
            score_delta=profile.trust_score - before_score,
            before_score=before_score,
            after_score=profile.trust_score,
            reason=reason,
            created_by=actor_id,
        )
    )
    await db.flush()
    return profile


async def _calculate_user_facts(db: AsyncSession, user_id: uuid.UUID) -> dict:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return _empty_facts()

    profile_fields = [
        user.email,
        user.phone,
        user.full_name,
        user.avatar_url,
        user.email_verified_at,
        user.phone_verified_at,
    ]
    profile_completion = _completion_rate(profile_fields)

    orders = (await db.execute(select(Order).where(Order.buyer_id == user_id))).scalars().all()
    risk_count = await _risk_count(db, "User", user_id)
    wallets = (await db.execute(select(Wallet).where(Wallet.owner_user_id == user_id))).scalars().all()
    deposit_amount = sum(wallet.total_deposited_minor for wallet in wallets)
    deposit_currency = wallets[0].currency if wallets else "USDT"
    return _build_score(
        profile_completion_rate=profile_completion,
        verification_score=100 if user.email_verified_at else 60,
        orders=orders,
        risk_count=risk_count,
        deposit_amount_minor=deposit_amount,
        deposit_currency=deposit_currency,
        late_payment_rate=0,
    )


async def _calculate_company_facts(db: AsyncSession, company_id: uuid.UUID) -> dict:
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        return _empty_facts()

    branch_count = (await db.execute(select(func.count()).select_from(Branch).where(Branch.company_id == company_id))).scalar() or 0
    active_item_count = (
        await db.execute(
            select(func.count())
            .select_from(CatalogItem)
            .where(CatalogItem.company_id == company_id, CatalogItem.status == CatalogItemStatus.ACTIVE)
        )
    ).scalar() or 0

    profile_fields = [
        company.name,
        company.tax_id,
        company.country,
        company.city,
        company.address,
        branch_count > 0,
        active_item_count > 0,
    ]
    profile_completion = _completion_rate(profile_fields)
    verification_score = {
        VerificationLevel.TRUSTED: 100,
        VerificationLevel.BUSINESS: 85,
        VerificationLevel.BASIC: 65,
        VerificationLevel.UNVERIFIED: 20,
    }.get(company.verification_level, 20)

    orders = (await db.execute(select(Order).where(Order.company_id == company_id))).scalars().all()
    risk_count = await _risk_count(db, "Company", company_id)
    return _build_score(
        profile_completion_rate=profile_completion,
        verification_score=verification_score,
        orders=orders,
        risk_count=risk_count,
        deposit_amount_minor=0,
        deposit_currency="PHP",
        late_delivery_rate=0,
    )


def _completion_rate(fields: list[object]) -> int:
    if not fields:
        return 0
    filled = sum(1 for field in fields if bool(field))
    return round(filled / len(fields) * 100)


async def _risk_count(db: AsyncSession, entity_type: str, entity_id: uuid.UUID) -> int:
    return (
        await db.execute(
            select(func.count())
            .select_from(RiskFlag)
            .where(
                RiskFlag.entity_type == entity_type,
                RiskFlag.entity_id == entity_id,
                RiskFlag.status.in_([RiskFlagStatus.OPEN, RiskFlagStatus.IN_REVIEW, RiskFlagStatus.ACTION_TAKEN]),
            )
        )
    ).scalar() or 0


def _empty_facts() -> dict:
    return _build_score(
        profile_completion_rate=0,
        verification_score=0,
        orders=[],
        risk_count=0,
        deposit_amount_minor=0,
        deposit_currency="PHP",
    )


def _build_score(
    *,
    profile_completion_rate: int,
    verification_score: int,
    orders: list[Order],
    risk_count: int,
    deposit_amount_minor: int,
    deposit_currency: str,
    late_delivery_rate: int = 0,
    late_payment_rate: int = 0,
) -> dict:
    total_deals = len(orders)
    successful = sum(1 for order in orders if order.status in SUCCESS_ORDER_STATUSES)
    canceled = sum(1 for order in orders if order.status in CANCELED_ORDER_STATUSES)
    refunded = sum(1 for order in orders if order.status == OrderStatus.REFUNDED)
    disputed = sum(1 for order in orders if order.status == OrderStatus.DISPUTED)

    deal_completion_rate = round(successful / total_deals * 100) if total_deals else 0
    dispute_rate = round(disputed / total_deals * 100) if total_deals else 0
    refund_rate = round(refunded / total_deals * 100) if total_deals else 0
    deposit_score = min(round(deposit_amount_minor / 100000), 100)
    risk_score = max(0, 100 - risk_count * 20 - dispute_rate - refund_rate)

    trust_score = round(
        profile_completion_rate * 2.0
        + deal_completion_rate * 3.5
        + deposit_score * 2.0
        + verification_score * 1.5
        + risk_score * 1.0
    )
    trust_score = clamp(trust_score)

    score_breakdown = {
        "profile_score": profile_completion_rate,
        "deal_score": deal_completion_rate,
        "deposit_score": deposit_score,
        "verification_score": verification_score,
        "risk_penalty_score": risk_score,
        "risk_count": risk_count,
        "total_deals": total_deals,
    }

    return {
        "trust_score": trust_score,
        "profile_completion_rate": profile_completion_rate,
        "deal_completion_rate": deal_completion_rate,
        "deposit_amount_minor": deposit_amount_minor,
        "deposit_currency": deposit_currency,
        "verified_deposit_minor": deposit_amount_minor,
        "successful_deals_count": successful,
        "canceled_deals_count": canceled,
        "dispute_rate": dispute_rate,
        "refund_rate": refund_rate,
        "late_delivery_rate": late_delivery_rate,
        "late_payment_rate": late_payment_rate,
        "score_breakdown": score_breakdown,
    }

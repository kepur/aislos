import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.company import Company
from app.models.trust import TrustEntityType, TrustProfile
from app.models.user import User
from app.schemas.trust import TrustMeResponse, TrustProfileResponse, TrustSummaryResponse
from app.services.trust_service import recalculate_trust_profile

router = APIRouter(tags=["Trust"])


def _summary(profile: TrustProfile) -> TrustSummaryResponse:
    return TrustSummaryResponse(
        entity_type=profile.entity_type,
        entity_id=profile.entity_id,
        trust_score=profile.trust_score,
        trust_tier=profile.trust_tier,
        profile_completion_rate=profile.profile_completion_rate,
        deal_completion_rate=profile.deal_completion_rate,
        deposit_amount_minor=profile.deposit_amount_minor,
        deposit_currency=profile.deposit_currency,
        successful_deals_count=profile.successful_deals_count,
        canceled_deals_count=profile.canceled_deals_count,
        dispute_rate=profile.dispute_rate,
        refund_rate=profile.refund_rate,
        status=profile.status,
    )


@router.get("/trust/me", response_model=TrustMeResponse)
async def my_trust(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.USER,
        entity_id=user.id,
        actor_id=user.id,
        reason="self_view",
    )

    company_profile = None
    company = (
        await db.execute(select(Company).where(Company.owner_user_id == user.id))
    ).scalar_one_or_none()
    if company:
        company_profile = await recalculate_trust_profile(
            db,
            entity_type=TrustEntityType.COMPANY,
            entity_id=company.id,
            actor_id=user.id,
            reason="self_view",
        )

    await db.commit()
    await db.refresh(user_profile)
    if company_profile:
        await db.refresh(company_profile)

    return TrustMeResponse(user=user_profile, company=company_profile)


@router.get("/users/{user_id}/trust-summary", response_model=TrustSummaryResponse)
async def user_trust_summary(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.USER,
        entity_id=user_id,
        actor_id=current_user.id,
        reason="summary_view",
    )
    await db.commit()
    await db.refresh(profile)
    return _summary(profile)


@router.get("/companies/{company_id}/trust-summary", response_model=TrustSummaryResponse)
async def company_trust_summary(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = await recalculate_trust_profile(
        db,
        entity_type=TrustEntityType.COMPANY,
        entity_id=company_id,
        actor_id=current_user.id,
        reason="summary_view",
    )
    await db.commit()
    await db.refresh(profile)
    return _summary(profile)

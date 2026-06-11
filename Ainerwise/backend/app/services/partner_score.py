"""Composite partner score, recomputed daily (celery beat).

Cold-start aware: with little history the weight shifts to the internal
rating; as invitations/bids/awards accumulate, behavioural factors dominate.
Factors with no data are excluded and their weight redistributed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfq import PartnerBid, PartnerMetric, PartnerMetricSnapshot, RFQInvitation
from app.models.service import ServicePartner

WEIGHTS = {"rating": 40, "response": 20, "participation": 20, "awards": 20}


async def recompute_partner_metrics(db: AsyncSession) -> int:
    partners = (await db.execute(select(ServicePartner))).scalars().all()
    updated = 0
    for partner in partners:
        invitations_total = (
            await db.execute(
                select(func.count()).select_from(RFQInvitation).where(RFQInvitation.partner_id == partner.id)
            )
        ).scalar() or 0
        responded = (
            await db.execute(
                select(func.count()).select_from(RFQInvitation).where(
                    RFQInvitation.partner_id == partner.id, RFQInvitation.responded_at.isnot(None)
                )
            )
        ).scalar() or 0
        avg_response_hours = (
            await db.execute(
                select(func.avg(func.extract("epoch", RFQInvitation.responded_at - RFQInvitation.created_at) / 3600))
                .where(RFQInvitation.partner_id == partner.id, RFQInvitation.responded_at.isnot(None))
            )
        ).scalar()
        bids_total = (
            await db.execute(select(func.count()).select_from(PartnerBid).where(PartnerBid.partner_id == partner.id))
        ).scalar() or 0
        awarded = (
            await db.execute(
                select(func.count()).select_from(PartnerBid).where(
                    PartnerBid.partner_id == partner.id, PartnerBid.status == "awarded"
                )
            )
        ).scalar() or 0
        awarded_revenue = (
            await db.execute(
                select(func.coalesce(func.sum(PartnerBid.amount), 0)).where(
                    PartnerBid.partner_id == partner.id, PartnerBid.status == "awarded"
                )
            )
        ).scalar() or 0

        factors: dict[str, Decimal] = {}
        factors["rating"] = Decimal(str((partner.rating_internal or 2.5) * 20))
        if invitations_total > 0:
            # responded fast and often = high score
            response_rate = Decimal(responded) / Decimal(invitations_total) * 100
            speed_bonus = Decimal(0)
            if avg_response_hours is not None:
                speed_bonus = max(Decimal(0), Decimal(100) - Decimal(str(avg_response_hours)) * 2)
            factors["response"] = (response_rate * Decimal("0.7") + speed_bonus * Decimal("0.3"))
            factors["participation"] = min(Decimal(100), Decimal(bids_total) / Decimal(invitations_total) * 100)
        if bids_total > 0:
            factors["awards"] = min(Decimal(100), Decimal(awarded) / Decimal(bids_total) * 100 + Decimal(awarded) * 5)

        active_weight = sum(WEIGHTS[name] for name in factors)
        composite = sum(factors[name] * WEIGHTS[name] for name in factors) / active_weight
        composite = composite.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        metric = (
            await db.execute(select(PartnerMetric).where(PartnerMetric.partner_id == partner.id))
        ).scalar_one_or_none() or PartnerMetric(partner_id=partner.id)
        metric.response_hours_avg = (
            Decimal(str(avg_response_hours)).quantize(Decimal("0.01")) if avg_response_hours is not None else None
        )
        metric.completion_rate = None  # needs delivered-project links (Phase D scheduler)
        metric.cancellation_rate = None
        metric.on_time_rate = None
        metric.warranty_claim_rate = None  # needs partner-linked tickets via assets
        metric.customer_review_avg = None
        metric.revenue_total = Decimal(awarded_revenue)
        metric.composite_score = composite
        metric.breakdown_json = {
            "factors": {k: float(v.quantize(Decimal("0.1"))) for k, v in factors.items()},
            "weights_used": {k: WEIGHTS[k] for k in factors},
            "invitations": invitations_total,
            "bids": bids_total,
            "awarded": awarded,
            "note": "cold-start: missing factors excluded, weights redistributed",
        }
        metric.computed_at = datetime.now(timezone.utc)
        db.add(metric)
        # append-only history: the future Risk Engine's time series
        db.add(
            PartnerMetricSnapshot(
                partner_id=partner.id,
                composite_score=composite,
                breakdown_json=metric.breakdown_json,
                snapshot_date=metric.computed_at,
            )
        )
        updated += 1
    await db.commit()
    return updated

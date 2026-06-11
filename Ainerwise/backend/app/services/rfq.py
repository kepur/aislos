"""RFQ bidding: match partners -> invite -> collect bids -> score -> award.

Bid scoring is a deterministic, explainable algorithm (price / partner score /
lead time) — the recommendation lands in ai_reviews as preliminary and a human
awards. No black-box auto-award.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import AIReview
from app.models.project import Project
from app.models.rfq import RFQ, PartnerBid, PartnerMetric, RFQInvitation
from app.models.service import ServicePartner
from app.services.channel_gateway import send_channel_message
from app.services.event_bus import emit_event

EVENT_RFQ_CREATED = "rfq.created"
EVENT_RFQ_PARTNER_INVITED = "rfq.partner_invited"
EVENT_RFQ_BID_RECEIVED = "rfq.bid_received"
EVENT_RFQ_PARTNER_DECLINED = "rfq.partner_declined"
EVENT_RFQ_AWARDED = "rfq.awarded"

SCORE_WEIGHTS = {"price": 40, "partner": 40, "lead_time": 20}

_SUPPLIER_SCOPE_DENY = frozenset(
    {"margin_rule_json", "service_fee_json", "payment_terms_json", "customer_price_rule_json"}
)


def supplier_safe_scope(scope: dict | None) -> dict | None:
    """Strip internal economics from RFQ scope for partner-facing serializers."""
    if not scope:
        return scope
    cleaned = dict(scope)
    for key in list(cleaned.keys()):
        if key in _SUPPLIER_SCOPE_DENY or "margin" in key or "fee" in key:
            cleaned.pop(key, None)
    return cleaned


async def match_partners(db: AsyncSession, rfq: RFQ, limit: int = 10) -> list[dict]:
    """Candidate partners: trade skill match + country + availability, ranked
    by composite partner score (falls back to internal rating)."""
    scope = rfq.scope_json or {}
    country = scope.get("country")
    result = await db.execute(
        select(ServicePartner, PartnerMetric.composite_score)
        .outerjoin(PartnerMetric, PartnerMetric.partner_id == ServicePartner.id)
        .where(ServicePartner.availability_status != "unavailable")
    )
    candidates = []
    for partner, score in result.all():
        skills = [s.lower() for s in (partner.skills_json or [])]
        if rfq.trade != "general" and skills and rfq.trade.lower() not in skills:
            continue
        if country and partner.country and partner.country.lower() != country.lower():
            continue
        effective = float(score) if score is not None else (partner.rating_internal or 0) * 20
        candidates.append(
            {
                "partner_id": str(partner.id),
                "partner_type": partner.partner_type,
                "city": partner.city,
                "country": partner.country,
                "skills": partner.skills_json or [],
                "score": round(effective, 1),
                "verification_status": partner.verification_status,
                "has_telegram": bool(partner.telegram_chat_id),
            }
        )
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:limit]


async def _notify_partner(
    partner: ServicePartner,
    text: str,
    *,
    message_id: uuid.UUID,
    metadata: dict,
) -> str:
    if not partner.telegram_chat_id:
        return "manual"
    return await send_channel_message(
        message_id=message_id,
        channel="telegram",
        external_thread_id=partner.telegram_chat_id,
        content=text,
        metadata=metadata,
        account_name="AinerWise Partner Bot",
    )


def _invitation_text(rfq: RFQ) -> str:
    scope = rfq.scope_json or {}
    lines = [
        "AinerWise — new project request for quote",
        f"Trade: {rfq.trade}",
        f"Title: {rfq.title}",
    ]
    if scope.get("city") or scope.get("country"):
        lines.append(f"Location: {scope.get('city') or ''} {scope.get('country') or ''}".strip())
    if scope.get("summary"):
        lines.append(f"Scope: {scope['summary']}")
    if rfq.bid_deadline:
        lines.append(f"Bid deadline: {rfq.bid_deadline:%Y-%m-%d}")
    lines.append(f"View scope and submit your bid: {settings.PARTNER_PORTAL_URL.rstrip('/')}/partner/rfqs/{rfq.id}")
    return "\n".join(lines)


async def invite_partners(db: AsyncSession, rfq: RFQ, partner_ids: list[uuid.UUID]) -> list[RFQInvitation]:
    invitations = []
    for partner_id in partner_ids:
        existing = (
            await db.execute(
                select(RFQInvitation).where(
                    RFQInvitation.rfq_id == rfq.id, RFQInvitation.partner_id == partner_id
                )
            )
        ).scalar_one_or_none()
        if existing:
            invitations.append(existing)
            continue
        partner = await db.get(ServicePartner, partner_id)
        if partner is None:
            continue
        invitation = RFQInvitation(
            rfq_id=rfq.id, partner_id=partner_id, status="sent",
            sent_via="pending",
        )
        db.add(invitation)
        await db.flush()
        delivery_status = await _notify_partner(
            partner,
            _invitation_text(rfq),
            message_id=invitation.id,
            metadata={
                "purpose": "rfq_invitation",
                "rfq_id": str(rfq.id),
                "partner_id": str(partner.id),
                "invitation_id": str(invitation.id),
            },
        )
        invitation.sent_via = (
            "channel_gateway:telegram"
            if delivery_status == "sent"
            else "manual" if delivery_status == "manual" else f"channel_gateway:{delivery_status}"
        )
        db.add(invitation)
        await emit_event(
            db,
            EVENT_RFQ_PARTNER_INVITED,
            {
                "rfq_id": str(rfq.id),
                "partner_id": str(partner.id),
                "invitation_id": str(invitation.id),
                "delivery_status": delivery_status,
            },
            aggregate_type="rfq",
            aggregate_id=rfq.id,
        )
        invitations.append(invitation)
    if rfq.status in ("draft", "inviting"):
        rfq.status = "bidding"
        db.add(rfq)
    await db.flush()
    return invitations


async def record_bid(
    db: AsyncSession, rfq: RFQ, *, partner_id: uuid.UUID,
    amount: float, currency: str | None, lead_time_days: int | None, notes: str | None,
) -> PartnerBid:
    bid = PartnerBid(
        rfq_id=rfq.id, partner_id=partner_id,
        amount=Decimal(str(amount)), currency=currency or rfq.currency,
        lead_time_days=lead_time_days, notes=notes, status="submitted",
    )
    db.add(bid)
    invitation = (
        await db.execute(
            select(RFQInvitation).where(RFQInvitation.rfq_id == rfq.id, RFQInvitation.partner_id == partner_id)
        )
    ).scalar_one_or_none()
    if invitation:
        invitation.status = "bid_submitted"
        invitation.responded_at = datetime.now(timezone.utc)
        db.add(invitation)
    await db.flush()
    await emit_event(
        db, EVENT_RFQ_BID_RECEIVED,
        {"rfq_id": str(rfq.id), "partner_id": str(partner_id), "amount": amount},
        aggregate_type="rfq", aggregate_id=rfq.id, target_channel="telegram_admin",
    )
    return bid


async def evaluate_bids(db: AsyncSession, rfq: RFQ) -> AIReview:
    """Deterministic explainable scoring; recommendation goes to ai_reviews."""
    bids = (
        (await db.execute(select(PartnerBid).where(PartnerBid.rfq_id == rfq.id, PartnerBid.status == "submitted")))
        .scalars().all()
    )
    if not bids:
        raise ValueError("No submitted bids to evaluate")

    amounts = [Decimal(b.amount) for b in bids]
    min_amount, max_amount = min(amounts), max(amounts)
    lead_times = [b.lead_time_days for b in bids if b.lead_time_days is not None]
    min_lt = min(lead_times) if lead_times else None
    max_lt = max(lead_times) if lead_times else None

    metric_rows = (
        await db.execute(select(PartnerMetric).where(PartnerMetric.partner_id.in_([b.partner_id for b in bids])))
    ).scalars().all()
    metrics = {m.partner_id: m for m in metric_rows}

    ranking = []
    for bid in bids:
        # price: cheapest = 100, most expensive = 0 (single bid = 100)
        if max_amount == min_amount:
            price_score = Decimal(100)
        else:
            price_score = (Decimal(100) * (max_amount - Decimal(bid.amount)) / (max_amount - min_amount))
        metric = metrics.get(bid.partner_id)
        if metric and metric.composite_score is not None:
            partner_score = Decimal(metric.composite_score)
        else:
            partner = await db.get(ServicePartner, bid.partner_id)
            partner_score = Decimal(str((partner.rating_internal or 2.5) * 20)) if partner else Decimal(50)
        if bid.lead_time_days is None or min_lt is None or max_lt == min_lt:
            lead_score = Decimal(50)
        else:
            lead_score = Decimal(100) * (max_lt - bid.lead_time_days) / (max_lt - min_lt)

        total = (
            price_score * SCORE_WEIGHTS["price"]
            + partner_score * SCORE_WEIGHTS["partner"]
            + lead_score * SCORE_WEIGHTS["lead_time"]
        ) / 100
        total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        breakdown = {
            "price_score": float(price_score.quantize(Decimal("0.1"))),
            "partner_score": float(partner_score),
            "lead_time_score": float(lead_score.quantize(Decimal("0.1"))),
            "weights": SCORE_WEIGHTS,
        }
        bid.ai_score = total
        bid.ai_score_breakdown_json = breakdown
        db.add(bid)
        ranking.append(
            {"bid_id": str(bid.id), "partner_id": str(bid.partner_id),
             "amount": float(bid.amount), "currency": bid.currency,
             "lead_time_days": bid.lead_time_days, "score": float(total), "breakdown": breakdown}
        )

    ranking.sort(key=lambda r: r["score"], reverse=True)
    review = AIReview(
        target_type="bid_award",
        target_id=rfq.id,
        draft_json={
            "rfq_id": str(rfq.id),
            "recommended_bid_id": ranking[0]["bid_id"],
            "ranking": ranking,
            "method": "weighted price/partner/lead_time — deterministic, human award required",
        },
        status="preliminary",
    )
    db.add(review)
    rfq.status = "evaluating"
    db.add(rfq)
    await db.flush()
    return review


async def award_bid(db: AsyncSession, rfq: RFQ, bid_id: uuid.UUID, admin_id: uuid.UUID | None) -> PartnerBid:
    bids = (await db.execute(select(PartnerBid).where(PartnerBid.rfq_id == rfq.id))).scalars().all()
    winner = next((b for b in bids if b.id == bid_id), None)
    if winner is None:
        raise ValueError("Bid does not belong to this RFQ")
    for bid in bids:
        bid.status = "awarded" if bid.id == bid_id else "rejected"
        db.add(bid)
    rfq.status = "awarded"
    rfq.awarded_bid_id = bid_id
    db.add(rfq)

    # mark the pending review decided
    review = (
        await db.execute(
            select(AIReview).where(
                AIReview.target_type == "bid_award", AIReview.target_id == rfq.id,
                AIReview.status == "preliminary",
            )
        )
    ).scalars().first()
    if review:
        review.status = "approved"
        review.reviewed_by = admin_id
        review.reviewed_at = datetime.now(timezone.utc)
        db.add(review)

    if rfq.project_id is None and rfq.lead_id is not None:
        project = Project(lead_id=rfq.lead_id, title=f"{rfq.title} (RFQ awarded)", status="planning")
        db.add(project)
        await db.flush()
        rfq.project_id = project.id
        db.add(rfq)

    await db.flush()
    await emit_event(
        db, EVENT_RFQ_AWARDED,
        {"rfq_id": str(rfq.id), "bid_id": str(bid_id), "partner_id": str(winner.partner_id),
         "amount": float(winner.amount), "project_id": str(rfq.project_id) if rfq.project_id else None},
        aggregate_type="rfq", aggregate_id=rfq.id, target_channel="telegram_admin",
    )
    winner_partner = await db.get(ServicePartner, winner.partner_id)
    if winner_partner:
        await _notify_partner(
            winner_partner,
            f"AinerWise: your bid for '{rfq.title}' was accepted. We will contact you to schedule.",
            message_id=uuid.uuid5(uuid.NAMESPACE_URL, f"ainerwise:rfq-award:{rfq.id}:{winner.id}"),
            metadata={
                "purpose": "rfq_award",
                "rfq_id": str(rfq.id),
                "partner_id": str(winner.partner_id),
                "bid_id": str(winner.id),
            },
        )
    return winner

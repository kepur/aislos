import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.ai import AgentRun
from app.models.rfq import RFQ, PartnerBid, PartnerMetric, RFQInvitation
from app.services.agent_runtime import AgentAuthorizationError, require_agent
from app.services.event_bus import emit_event
from app.services.partner_score import recompute_partner_metrics
from app.services.rfq import (
    EVENT_RFQ_CREATED,
    award_bid,
    evaluate_bids,
    invite_partners,
    match_partners,
    record_bid,
)

router = APIRouter(prefix="/admin/rfqs", tags=["rfqs"])


class RFQCreate(BaseModel):
    title: str
    trade: str = "general"
    region_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    solution_id: uuid.UUID | None = None
    scope_json: dict | None = None
    budget_hint: float | None = None
    currency: str = "EUR"
    bid_deadline: datetime | None = None


class InviteRequest(BaseModel):
    partner_ids: list[uuid.UUID]


class BidCreate(BaseModel):
    partner_id: uuid.UUID
    amount: float
    currency: str | None = None
    lead_time_days: int | None = None
    notes: str | None = None


class AwardRequest(BaseModel):
    bid_id: uuid.UUID


def _rfq_dict(rfq: RFQ) -> dict:
    return {
        "id": str(rfq.id), "title": rfq.title, "trade": rfq.trade,
        "lead_id": str(rfq.lead_id) if rfq.lead_id else None,
        "project_id": str(rfq.project_id) if rfq.project_id else None,
        "status": rfq.status, "currency": rfq.currency,
        "budget_hint": float(rfq.budget_hint) if rfq.budget_hint is not None else None,
        "scope_json": rfq.scope_json,
        "bid_deadline": rfq.bid_deadline.isoformat() if rfq.bid_deadline else None,
        "awarded_bid_id": str(rfq.awarded_bid_id) if rfq.awarded_bid_id else None,
        "created_at": rfq.created_at.isoformat(),
    }


def _bid_dict(bid: PartnerBid) -> dict:
    return {
        "id": str(bid.id), "partner_id": str(bid.partner_id),
        "amount": float(bid.amount), "currency": bid.currency,
        "lead_time_days": bid.lead_time_days, "notes": bid.notes,
        "ai_score": float(bid.ai_score) if bid.ai_score is not None else None,
        "ai_score_breakdown": bid.ai_score_breakdown_json,
        "status": bid.status, "created_at": bid.created_at.isoformat(),
    }


@router.post("")
async def create_rfq(data: RFQCreate, db: DB, admin: AdminUser):
    rfq = RFQ(**data.model_dump(), status="draft", created_by=admin.id)
    db.add(rfq)
    await db.flush()
    await emit_event(
        db, EVENT_RFQ_CREATED,
        {"rfq_id": str(rfq.id), "title": rfq.title, "trade": rfq.trade},
        aggregate_type="rfq", aggregate_id=rfq.id,
    )
    await db.commit()
    await db.refresh(rfq)
    return _rfq_dict(rfq)


@router.get("")
async def list_rfqs(
    db: DB, admin: AdminUser,
    status: str | None = None, trade: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(RFQ).order_by(RFQ.created_at.desc())
    count_query = select(func.count()).select_from(RFQ)
    if status:
        query = query.where(RFQ.status == status)
        count_query = count_query.where(RFQ.status == status)
    if trade:
        query = query.where(RFQ.trade == trade)
        count_query = count_query.where(RFQ.trade == trade)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_rfq_dict(r) for r in rows], "total": total}


@router.get("/partner-metrics")
async def list_partner_metrics(db: DB, admin: AdminUser):
    rows = (
        await db.execute(select(PartnerMetric).order_by(PartnerMetric.composite_score.desc().nullslast()))
    ).scalars().all()
    return {
        "items": [
            {
                "partner_id": str(m.partner_id),
                "composite_score": float(m.composite_score) if m.composite_score is not None else None,
                "response_hours_avg": float(m.response_hours_avg) if m.response_hours_avg is not None else None,
                "revenue_total": float(m.revenue_total) if m.revenue_total is not None else None,
                "breakdown": m.breakdown_json,
                "computed_at": m.computed_at.isoformat() if m.computed_at else None,
            }
            for m in rows
        ]
    }


@router.post("/partner-metrics/recompute")
async def recompute_metrics(db: DB, admin: AdminUser):
    count = await recompute_partner_metrics(db)
    return {"recomputed": count}


@router.get("/{id}")
async def get_rfq(id: uuid.UUID, db: DB, admin: AdminUser):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    invitations = (
        (await db.execute(select(RFQInvitation).where(RFQInvitation.rfq_id == id))).scalars().all()
    )
    bids = (await db.execute(select(PartnerBid).where(PartnerBid.rfq_id == id))).scalars().all()
    return {
        **_rfq_dict(rfq),
        "invitations": [
            {"partner_id": str(i.partner_id), "status": i.status, "sent_via": i.sent_via,
             "responded_at": i.responded_at.isoformat() if i.responded_at else None}
            for i in invitations
        ],
        "bids": [_bid_dict(b) for b in bids],
    }


@router.get("/{id}/match-partners")
async def rfq_match_partners(id: uuid.UUID, db: DB, admin: AdminUser, limit: int = Query(10, ge=1, le=50)):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {"candidates": await match_partners(db, rfq, limit=limit)}


@router.post("/{id}/invite")
async def rfq_invite(id: uuid.UUID, data: InviteRequest, db: DB, admin: AdminUser):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status in ("awarded", "cancelled"):
        raise HTTPException(status_code=409, detail=f"RFQ already {rfq.status}")
    invitations = await invite_partners(db, rfq, data.partner_ids)
    await db.commit()
    return {"invited": len(invitations)}


@router.post("/{id}/bids")
async def rfq_record_bid(id: uuid.UUID, data: BidCreate, db: DB, admin: AdminUser):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status in ("awarded", "cancelled"):
        raise HTTPException(status_code=409, detail=f"RFQ already {rfq.status}")
    bid = await record_bid(
        db, rfq, partner_id=data.partner_id, amount=data.amount,
        currency=data.currency, lead_time_days=data.lead_time_days, notes=data.notes,
    )
    await db.commit()
    await db.refresh(bid)
    return _bid_dict(bid)


@router.post("/{id}/evaluate")
async def rfq_evaluate(id: uuid.UUID, db: DB, admin: AdminUser):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    try:
        await require_agent(
            db,
            "procurement-agent",
            scopes=("partners", "project_data"),
            workflow="bid_evaluation",
        )
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    try:
        review = await evaluate_bids(db, rfq)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    db.add(
        AgentRun(
            agent_slug="procurement-agent",
            workflow="bid_evaluation",
            input_json={"rfq_id": str(rfq.id)},
            output_json={"review_id": str(review.id), "draft": review.draft_json},
            status="completed",
        )
    )
    await db.commit()
    return {"review_id": str(review.id), "draft": review.draft_json}


@router.post("/{id}/award")
async def rfq_award(id: uuid.UUID, data: AwardRequest, db: DB, admin: AdminUser):
    rfq = await db.get(RFQ, id)
    if rfq is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status == "awarded":
        raise HTTPException(status_code=409, detail="RFQ already awarded")
    try:
        winner = await award_bid(db, rfq, data.bid_id, admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    await db.commit()
    return {"awarded_bid_id": str(winner.id), "project_id": str(rfq.project_id) if rfq.project_id else None}

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.payment import LedgerEntry, PaymentMilestone, PaymentPlan
from app.models.quote import Quote
from app.services.payments import create_plan_from_quote, mark_milestone_funded, release_milestone

router = APIRouter(prefix="/admin/payments", tags=["payments"])


class PlanCreate(BaseModel):
    quote_id: uuid.UUID
    retention_pct: float | None = None
    retention_release_days: int = 90


class MilestoneAction(BaseModel):
    memo: str | None = None


def _milestone_dict(m: PaymentMilestone) -> dict:
    return {
        "id": str(m.id), "seq": m.seq, "label": m.label, "pct": float(m.pct),
        "amount": float(m.amount), "trigger": m.trigger, "status": m.status,
        "funded_at": m.funded_at.isoformat() if m.funded_at else None,
        "released_at": m.released_at.isoformat() if m.released_at else None,
        "release_due_at": m.release_due_at.isoformat() if m.release_due_at else None,
    }


def _plan_dict(p: PaymentPlan) -> dict:
    return {
        "id": str(p.id),
        "project_id": str(p.project_id) if p.project_id else None,
        "quote_id": str(p.quote_id) if p.quote_id else None,
        "currency": p.currency, "total": float(p.total),
        "retention_pct": float(p.retention_pct) if p.retention_pct is not None else None,
        "retention_release_days": p.retention_release_days,
        "status": p.status, "created_at": p.created_at.isoformat(),
    }


@router.post("/plans")
async def create_plan(data: PlanCreate, db: DB, admin: AdminUser):
    quote = await db.get(Quote, data.quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    existing = (
        await db.execute(select(PaymentPlan).where(PaymentPlan.quote_id == quote.id,
                                                   PaymentPlan.status.in_(("draft", "active"))))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Quote already has an active payment plan")
    try:
        plan = await create_plan_from_quote(
            db, quote,
            retention_pct=Decimal(str(data.retention_pct)) if data.retention_pct else None,
            retention_release_days=data.retention_release_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    await db.commit()
    await db.refresh(plan)
    return _plan_dict(plan)


@router.get("/plans")
async def list_plans(
    db: DB, admin: AdminUser,
    status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(PaymentPlan).order_by(PaymentPlan.created_at.desc())
    count_query = select(func.count()).select_from(PaymentPlan)
    if status:
        query = query.where(PaymentPlan.status == status)
        count_query = count_query.where(PaymentPlan.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    plans = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_plan_dict(p) for p in plans], "total": total}


@router.get("/plans/{id}")
async def get_plan(id: uuid.UUID, db: DB, admin: AdminUser):
    plan = await db.get(PaymentPlan, id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    milestones = (
        await db.execute(
            select(PaymentMilestone).where(PaymentMilestone.plan_id == id).order_by(PaymentMilestone.seq)
        )
    ).scalars().all()
    ledger = (
        await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.milestone_id.in_([m.id for m in milestones] or [id]))
            .order_by(LedgerEntry.created_at)
        )
    ).scalars().all()
    return {
        **_plan_dict(plan),
        "milestones": [_milestone_dict(m) for m in milestones],
        "ledger": [
            {"account": e.account, "direction": e.direction, "amount": float(e.amount),
             "currency": e.currency, "memo": e.memo, "at": e.created_at.isoformat()}
            for e in ledger
        ],
    }


@router.post("/milestones/{id}/checkout-link")
async def milestone_checkout_link(id: uuid.UUID, db: DB, admin: AdminUser):
    """Online payment link (Stripe). Offline 'mark funded' keeps working."""
    from app.services.stripe_payments import create_milestone_checkout

    milestone = await db.get(PaymentMilestone, id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    try:
        url = await create_milestone_checkout(db, milestone)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return {"checkout_url": url, "milestone_status": milestone.status}


class TransferRequest(BaseModel):
    partner_id: uuid.UUID


@router.post("/milestones/{id}/transfer")
async def milestone_transfer(id: uuid.UUID, data: TransferRequest, db: DB, admin: AdminUser):
    from app.models.service import ServicePartner
    from app.services.stripe_payments import transfer_to_partner

    milestone = await db.get(PaymentMilestone, id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    partner = await db.get(ServicePartner, data.partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    try:
        transfer_id = await transfer_to_partner(db, milestone, partner)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return {"transfer_id": transfer_id}


class DepositCreate(BaseModel):
    partner_id: uuid.UUID
    amount: float
    currency: str = "EUR"


@router.post("/partner-deposits")
async def create_partner_deposit(data: DepositCreate, db: DB, admin: AdminUser):
    from app.models.payment import PartnerDeposit
    from app.services.stripe_payments import create_deposit_checkout, is_configured, stripe_config

    deposit = PartnerDeposit(
        partner_id=data.partner_id, amount=Decimal(str(data.amount)),
        currency=data.currency, status="requested",
    )
    db.add(deposit)
    await db.commit()
    await db.refresh(deposit)
    checkout_url = None
    if is_configured(await stripe_config(db)):
        checkout_url = await create_deposit_checkout(db, deposit)
    return {"deposit_id": str(deposit.id), "status": deposit.status, "checkout_url": checkout_url}


@router.post("/partners/{partner_id}/stripe-onboard")
async def partner_stripe_onboard(partner_id: uuid.UUID, db: DB, admin: AdminUser):
    from app.models.service import ServicePartner
    from app.services.stripe_payments import create_partner_onboarding_link

    partner = await db.get(ServicePartner, partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    try:
        url = await create_partner_onboarding_link(db, partner)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return {"onboarding_url": url, "stripe_account_id": partner.stripe_account_id}


@router.post("/milestones/{id}/fund")
async def fund_milestone(id: uuid.UUID, data: MilestoneAction, db: DB, admin: AdminUser):
    milestone = await db.get(PaymentMilestone, id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    try:
        await mark_milestone_funded(db, milestone, memo=data.memo)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    return _milestone_dict(milestone)


@router.post("/milestones/{id}/release")
async def release_milestone_endpoint(id: uuid.UUID, data: MilestoneAction, db: DB, admin: AdminUser):
    milestone = await db.get(PaymentMilestone, id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    try:
        await release_milestone(db, milestone, memo=data.memo)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    return _milestone_dict(milestone)

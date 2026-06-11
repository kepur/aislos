"""Payment plans + milestones + double-entry ledger. Ledger-first design:
real money stays at the bank (Phase C: offline transfers, admin confirms) or
at the PSP (Phase E: Stripe Connect webhooks replace the manual confirm).
The state machine and ledger do not change between phases.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import LedgerEntry, PaymentMilestone, PaymentPlan
from app.models.quote import Quote
from app.services.event_bus import emit_event

EVENT_MILESTONE_FUNDED = "payment.milestone_funded"
EVENT_MILESTONE_RELEASED = "payment.milestone_released"
EVENT_RETENTION_RELEASED = "payment.retention_released"

DEFAULT_SPLITS = (("deposit", Decimal(30), "on_accept"),
                  ("midterm", Decimal(40), "on_schedule"),
                  ("acceptance", Decimal(30), "on_acceptance"))
TWO = Decimal("0.01")


async def create_plan_from_quote(
    db: AsyncSession,
    quote: Quote,
    *,
    splits: tuple = DEFAULT_SPLITS,
    retention_pct: Decimal | None = None,
    retention_release_days: int = 90,
) -> PaymentPlan:
    total = Decimal(str(quote.total)).quantize(TWO)
    if total <= 0:
        raise ValueError("Quote total must be positive")
    plan = PaymentPlan(
        project_id=quote.project_id,
        quote_id=quote.id,
        currency=quote.currency,
        total=total,
        retention_pct=retention_pct,
        retention_release_days=retention_release_days if retention_pct else None,
        status="active",
    )
    db.add(plan)
    await db.flush()

    retention_amount = (
        (total * retention_pct / 100).quantize(TWO, rounding=ROUND_HALF_UP) if retention_pct else Decimal(0)
    )
    payable = total - retention_amount

    allocated = Decimal(0)
    for index, (label, pct, trigger) in enumerate(splits):
        if index < len(splits) - 1:
            amount = (payable * pct / 100).quantize(TWO, rounding=ROUND_HALF_UP)
            allocated += amount
        else:
            amount = payable - allocated  # last milestone absorbs rounding remainder
        db.add(PaymentMilestone(plan_id=plan.id, seq=index + 1, label=label, pct=pct, amount=amount, trigger=trigger))

    if retention_amount > 0:
        db.add(
            PaymentMilestone(
                plan_id=plan.id, seq=len(splits) + 1, label="retention",
                pct=retention_pct, amount=retention_amount, trigger="days_after_acceptance",
            )
        )
    await db.flush()
    return plan


def _ledger_pair(group: uuid.UUID, debit_account: str, credit_account: str, amount: Decimal, currency: str,
                 milestone_id: uuid.UUID, memo: str) -> list[LedgerEntry]:
    return [
        LedgerEntry(entry_group=group, account=debit_account, direction="debit",
                    amount=amount, currency=currency, milestone_id=milestone_id, memo=memo),
        LedgerEntry(entry_group=group, account=credit_account, direction="credit",
                    amount=amount, currency=currency, milestone_id=milestone_id, memo=memo),
    ]


async def mark_milestone_funded(
    db: AsyncSession,
    milestone: PaymentMilestone,
    *,
    memo: str | None = None,
    source_account: str = "bank:offline",
    external_ref: str | None = None,
) -> None:
    if milestone.status not in ("pending", "invoiced"):
        raise ValueError(f"Milestone is {milestone.status}, cannot fund")
    plan = await db.get(PaymentPlan, milestone.plan_id)
    now = datetime.now(timezone.utc)
    milestone.status = "funded"
    milestone.funded_at = now
    if external_ref:
        milestone.external_ref = external_ref
    if milestone.label == "retention" and plan.retention_release_days:
        milestone.release_due_at = now + timedelta(days=plan.retention_release_days)
    db.add(milestone)
    for entry in _ledger_pair(
        uuid.uuid4(), source_account, f"plan:{plan.id}:escrow",
        Decimal(milestone.amount), plan.currency, milestone.id,
        memo or f"{milestone.label} funded (offline transfer confirmed by admin)",
    ):
        db.add(entry)
    await db.flush()
    await emit_event(
        db, EVENT_MILESTONE_FUNDED,
        {"plan_id": str(plan.id), "milestone_id": str(milestone.id), "label": milestone.label,
         "amount": float(milestone.amount), "currency": plan.currency,
         "project_id": str(plan.project_id) if plan.project_id else None},
        aggregate_type="payment_plan", aggregate_id=plan.id, target_channel="telegram_admin",
    )


async def release_milestone(db: AsyncSession, milestone: PaymentMilestone, *, memo: str | None = None) -> None:
    if milestone.status != "funded":
        raise ValueError(f"Milestone is {milestone.status}, cannot release")
    plan = await db.get(PaymentPlan, milestone.plan_id)
    milestone.status = "released"
    milestone.released_at = datetime.now(timezone.utc)
    db.add(milestone)
    for entry in _ledger_pair(
        uuid.uuid4(), f"plan:{plan.id}:escrow", "platform:revenue",
        Decimal(milestone.amount), plan.currency, milestone.id,
        memo or f"{milestone.label} released",
    ):
        db.add(entry)
    await db.flush()
    event_type = EVENT_RETENTION_RELEASED if milestone.label == "retention" else EVENT_MILESTONE_RELEASED
    await emit_event(
        db, event_type,
        {"plan_id": str(plan.id), "milestone_id": str(milestone.id), "label": milestone.label,
         "amount": float(milestone.amount)},
        aggregate_type="payment_plan", aggregate_id=plan.id,
    )

    remaining = (
        await db.execute(
            select(PaymentMilestone).where(
                PaymentMilestone.plan_id == plan.id, PaymentMilestone.status.notin_(("released", "refunded"))
            )
        )
    ).scalars().first()
    if remaining is None:
        plan.status = "completed"
        db.add(plan)
        await db.flush()


async def release_due_retentions(db: AsyncSession) -> int:
    """Beat task: auto-release funded retention milestones past their hold."""
    due = (
        await db.execute(
            select(PaymentMilestone).where(
                PaymentMilestone.label == "retention",
                PaymentMilestone.status == "funded",
                PaymentMilestone.release_due_at.isnot(None),
                PaymentMilestone.release_due_at <= datetime.now(timezone.utc),
            )
        )
    ).scalars().all()
    for milestone in due:
        await release_milestone(db, milestone, memo="retention hold expired — auto release")
    await db.commit()
    return len(due)

"""Commerce payment settlement and ledger reconciliation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import (
    CommerceOrder,
    CommercePaymentIntent,
    CommerceReconciliationRun,
    CommerceSettlement,
)
from app.models.payment import LedgerEntry, PaymentMilestone
from app.models.user import User
from app.services.event_bus import emit_event
from app.services.payments import mark_milestone_funded

TWO = Decimal("0.01")


class CommerceSettlementError(ValueError):
    pass


async def _ledger_balanced(db: AsyncSession, milestone_id: uuid.UUID) -> tuple[bool, dict]:
    milestone = await db.get(PaymentMilestone, milestone_id)
    if milestone is None:
        return False, {"reason": "milestone_not_found"}
    rows = list(
        (
            await db.execute(
                select(LedgerEntry).where(
                    LedgerEntry.milestone_id == milestone_id,
                    LedgerEntry.workspace_id == milestone.workspace_id,
                )
            )
        ).scalars()
    )
    if not rows:
        return False, {"reason": "no_ledger_entries"}
    debits = sum((r.amount for r in rows if r.direction == "debit"), Decimal(0))
    credits = sum((r.amount for r in rows if r.direction == "credit"), Decimal(0))
    balanced = debits == credits and debits > 0
    return balanced, {
        "debit_total": str(debits.quantize(TWO)),
        "credit_total": str(credits.quantize(TWO)),
        "entry_count": len(rows),
    }


async def confirm_order_funding(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    external_ref: str,
    source_account: str = "bank:offline",
) -> CommerceSettlement:
    intent = (
        await db.execute(
            select(CommercePaymentIntent).where(CommercePaymentIntent.commerce_order_id == order_id)
        )
    ).scalar_one_or_none()
    if intent is None:
        raise CommerceSettlementError("payment intent not found")
    order = await db.get(CommerceOrder, order_id)
    if order is None or intent.workspace_id != order.workspace_id:
        raise CommerceSettlementError("payment intent and order belong to different Workspaces")
    if not intent.payment_plan_id:
        raise CommerceSettlementError("payment plan not linked")
    existing = (
        await db.execute(
            select(CommerceSettlement).where(CommerceSettlement.commerce_order_id == order_id)
        )
    ).scalar_one_or_none()
    if existing and existing.workspace_id != order.workspace_id:
        raise CommerceSettlementError("settlement and order belong to different Workspaces")
    if existing and existing.status not in ("pending",):
        if existing.status in ("funded", "settled", "reconciled"):
            return existing
        raise CommerceSettlementError("settlement already in progress")
    milestone = (
        await db.execute(
            select(PaymentMilestone)
            .where(PaymentMilestone.plan_id == intent.payment_plan_id)
            .order_by(PaymentMilestone.seq.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if milestone is None:
        raise CommerceSettlementError("milestone not found")
    if milestone.status == "funded":
        if existing:
            return existing
        intent.status = "funded"
        await db.flush()
        raise CommerceSettlementError("milestone funded but settlement missing")
    await mark_milestone_funded(
        db,
        milestone,
        external_ref=external_ref,
        source_account=source_account,
        memo=f"Commerce order {order_id} funded",
    )
    now = datetime.now(timezone.utc)
    intent.status = "funded"
    if existing:
        row = existing
        row.status = "funded"
        row.milestone_id = milestone.id
        row.external_ref = external_ref
        row.funded_at = now
    else:
        row = CommerceSettlement(
            workspace_id=order.workspace_id,
            commerce_order_id=order_id,
            payment_intent_id=intent.id,
            payment_plan_id=intent.payment_plan_id,
            milestone_id=milestone.id,
            status="funded",
            amount_minor=intent.amount_minor,
            currency=intent.currency,
            psp_provider=intent.psp_provider,
            external_ref=external_ref,
            funded_at=now,
        )
        db.add(row)
    await db.flush()
    await emit_event(
        db,
        "commerce.settlement.funded",
        {"order_id": str(order_id), "settlement_id": str(row.id), "external_ref": external_ref},
        aggregate_type="commerce_settlement",
        aggregate_id=row.id,
    )
    return row


async def mark_settlement_settled(
    db: AsyncSession,
    settlement_id: uuid.UUID,
    *,
    psp_settlement_ref: str,
    platform_fee_minor: int = 0,
) -> CommerceSettlement:
    row = await db.get(CommerceSettlement, settlement_id)
    if row is None:
        raise CommerceSettlementError("settlement not found")
    if row.status != "funded":
        raise CommerceSettlementError("settlement must be funded before settle")
    row.status = "settled"
    row.psp_settlement_ref = psp_settlement_ref
    row.platform_fee_minor = platform_fee_minor
    row.settled_at = datetime.now(timezone.utc)
    intent = (
        await db.execute(
            select(CommercePaymentIntent).where(CommercePaymentIntent.id == row.payment_intent_id)
        )
    ).scalar_one_or_none()
    if intent:
        if intent.workspace_id != row.workspace_id:
            raise CommerceSettlementError("settlement and payment intent belong to different Workspaces")
        intent.status = "completed"
    await db.flush()
    await emit_event(
        db,
        "commerce.settlement.settled",
        {"settlement_id": str(row.id), "psp_settlement_ref": psp_settlement_ref},
        aggregate_type="commerce_settlement",
        aggregate_id=row.id,
    )
    return row


async def list_settlements(
    db: AsyncSession, *, status: str | None = None, limit: int = 50
) -> list[CommerceSettlement]:
    q = select(CommerceSettlement).order_by(CommerceSettlement.created_at.desc()).limit(limit)
    if status:
        q = q.where(CommerceSettlement.status == status)
    return list((await db.execute(q)).scalars())


async def run_reconciliation(
    db: AsyncSession,
    *,
    period_start: datetime,
    period_end: datetime,
    user: User,
) -> CommerceReconciliationRun:
    run = CommerceReconciliationRun(
        period_start=period_start,
        period_end=period_end,
        status="running",
        created_by_user_id=user.id,
    )
    db.add(run)
    await db.flush()
    settlements = list(
        (
            await db.execute(
                select(CommerceSettlement).where(
                    CommerceSettlement.created_at >= period_start,
                    CommerceSettlement.created_at <= period_end,
                    CommerceSettlement.status.in_(("funded", "settled", "reconciled", "mismatch")),
                )
            )
        ).scalars()
    )
    matched = mismatch = pending = 0
    items: list[dict] = []
    for s in settlements:
        if s.status in ("pending",):
            pending += 1
            continue
        if not s.milestone_id:
            s.status = "mismatch"
            mismatch += 1
            items.append({"settlement_id": str(s.id), "result": "no_milestone"})
            continue
        ok, detail = await _ledger_balanced(db, s.milestone_id)
        if ok and s.status in ("funded", "settled"):
            s.status = "reconciled"
            s.reconciled_at = datetime.now(timezone.utc)
            matched += 1
            items.append({"settlement_id": str(s.id), "result": "matched", **detail})
        else:
            s.status = "mismatch"
            mismatch += 1
            items.append({"settlement_id": str(s.id), "result": "mismatch", **detail})
    run.matched_count = matched
    run.mismatch_count = mismatch
    run.pending_count = pending
    run.status = "completed"
    run.summary_json = {"items": items, "total_scanned": len(settlements)}
    await db.flush()
    await emit_event(
        db,
        "commerce.reconciliation.completed",
        {
            "run_id": str(run.id),
            "matched": matched,
            "mismatch": mismatch,
            "pending": pending,
        },
        aggregate_type="commerce_reconciliation_run",
        aggregate_id=run.id,
    )
    return run

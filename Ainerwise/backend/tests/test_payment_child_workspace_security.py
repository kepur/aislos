"""Workspace inheritance and mismatch rejection for payment child records."""
import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.models.payment import LedgerEntry, PaymentMilestone
from app.models.portal_access import Workspace
from app.models.quote import Quote
from app.services.payments import create_plan_from_quote, mark_milestone_funded


def test_payment_milestones_and_ledger_inherit_plan_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Payment child A {suffix}", slug=f"pay-a-{suffix}")
            workspace_b = Workspace(name=f"Payment child B {suffix}", slug=f"pay-b-{suffix}")
            db.add_all([workspace_a, workspace_b])
            await db.flush()
            quote = Quote(
                workspace_id=workspace_a.id,
                total=Decimal("1000"),
                currency="EUR",
                status="accepted",
            )
            db.add(quote)
            await db.flush()
            plan = await create_plan_from_quote(db, quote)
            milestones = list(
                (
                    await db.execute(
                        select(PaymentMilestone).where(PaymentMilestone.plan_id == plan.id)
                    )
                ).scalars()
            )
            assert milestones
            assert {row.workspace_id for row in milestones} == {workspace_a.id}

            milestone = milestones[0]
            await mark_milestone_funded(db, milestone)
            ledger = list(
                (
                    await db.execute(
                        select(LedgerEntry).where(LedgerEntry.milestone_id == milestone.id)
                    )
                ).scalars()
            )
            assert len(ledger) == 2
            assert {row.workspace_id for row in ledger} == {workspace_a.id}

            forged = milestones[1]
            forged.workspace_id = workspace_b.id
            with pytest.raises(ValueError, match="different Workspaces"):
                await mark_milestone_funded(db, forged)

    asyncio.run(_run())

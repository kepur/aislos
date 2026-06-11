"""Procurement project facts service — flush-only; endpoint owns commit."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement import ProcurementProjectFact


class ProcurementFactError(ValueError):
    pass


async def list_facts(
    db: AsyncSession, project_id: uuid.UUID
) -> list[ProcurementProjectFact]:
    result = await db.execute(
        select(ProcurementProjectFact)
        .where(ProcurementProjectFact.project_id == project_id)
        .order_by(ProcurementProjectFact.template_key)
    )
    return list(result.scalars().all())


async def get_fact_for_project(
    db: AsyncSession, project_id: uuid.UUID, fact_id: uuid.UUID
) -> ProcurementProjectFact | None:
    result = await db.execute(
        select(ProcurementProjectFact).where(
            ProcurementProjectFact.id == fact_id,
            ProcurementProjectFact.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def patch_fact(
    db: AsyncSession,
    fact: ProcurementProjectFact,
    *,
    value_json: Any | None = None,
    value_provided: bool = False,
    user_confirmed: bool | None = None,
    assumption: str | None = None,
    assumption_provided: bool = False,
) -> tuple[ProcurementProjectFact, dict[str, Any], dict[str, Any], bool]:
    """Patch a fact. Returns (fact, before, after, confirmed_now)."""
    before = {
        "value_json": fact.value_json,
        "user_confirmed": fact.user_confirmed,
        "confidence": str(fact.confidence),
        "assumption": fact.assumption,
        "source": fact.source,
    }

    confirmed_now = False
    if value_provided:
        fact.value_json = value_json
        if fact.source == "system":
            fact.source = "user"

    if assumption_provided:
        fact.assumption = assumption

    if user_confirmed is True and not fact.user_confirmed:
        fact.user_confirmed = True
        confirmed_now = True
        if fact.source == "system":
            fact.source = "user"

    await db.flush()

    after = {
        "value_json": fact.value_json,
        "user_confirmed": fact.user_confirmed,
        "confidence": str(fact.confidence),
        "assumption": fact.assumption,
        "source": fact.source,
    }
    return fact, before, after, confirmed_now

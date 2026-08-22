from app.db.session import run_db_task
from app.tasks.celery_app import celery_app


@celery_app.task(name="reprice_due_growth_rules")
def reprice_due_growth_rules():
    """Re-run the auto-markup for every active, non-manual PriceRule.

    ``reprice_rule`` only writes a new sell price when the change exceeds the
    rule's ``reprice_threshold_pct``, so running this daily is safe (no churn).
    Weekly rules are handled by their own threshold + cadence intent; a finer
    weekday gate can be added later if needed.
    """
    from sqlalchemy import select

    from app.modules.growth.models import PriceRule
    from app.modules.growth.service import reprice_rule

    async def _run(db):
        rules = (
            await db.execute(
                select(PriceRule).where(
                    PriceRule.is_active.is_(True),
                    PriceRule.reprice_cadence != "manual",
                )
            )
        ).scalars().all()
        summaries = []
        for rule in rules:
            try:
                summaries.append(await reprice_rule(db, rule))
            except Exception as exc:  # noqa: BLE001 — keep going, surface per-rule
                summaries.append({"rule_id": str(rule.id), "error": str(exc)[:200]})
        await db.commit()
        return {"rules": len(rules), "summaries": summaries}

    return run_db_task(_run)

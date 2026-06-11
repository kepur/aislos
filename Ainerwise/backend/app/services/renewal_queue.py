"""Renewal opportunity queue (FI.6.5).

Surfaces recurring-revenue follow-ups the admin should action: AMC renewals,
calibration due, probe/battery replacement, report renewal, and expansion
(tag / new-point) opportunities. Reuses the lifecycle due-date queries.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.lifecycle import MaintenanceSchedule
from app.services import lifecycle_alerts

# Maintenance task_type -> opportunity type / action.
_MAINTENANCE_OPPORTUNITY = {
    "probe_replace": ("probe_replacement", "Quote probe replacement"),
    "battery_replace": ("battery_replacement", "Schedule battery replacement"),
    "report_review": ("report_renewal", "Confirm compliance report renewal"),
    "inspection": ("inspection", "Schedule annual inspection"),
}


def _opp(type_: str, title: str, due_date, entity_type: str, entity_id, action: str, priority: str = "medium") -> dict[str, Any]:
    return {
        "type": type_,
        "title": title,
        "due_date": due_date.isoformat() if isinstance(due_date, date) else due_date,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "suggested_action": action,
        "priority": priority,
    }


async def build_renewal_queue(db: AsyncSession, *, within_days: int = 90) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []

    for amc in await lifecycle_alerts.amc_renewal_due(db, within_days=within_days):
        opportunities.append(_opp(
            "amc_renewal", f"AMC renewal ({amc.package or 'contract'})", amc.end_date,
            "amc_contract", amc.id, "Offer AMC renewal before expiry", "high",
        ))

    for point in await lifecycle_alerts.calibration_due(db, within_days=within_days):
        opportunities.append(_opp(
            "calibration", f"Calibration due: {point.device_name or point.point_type or 'point'}",
            point.next_calibration_at, "monitoring_point", point.id,
            "Schedule calibration + certificate", "medium",
        ))

    # Maintenance-driven opportunities (probe / battery / report / inspection).
    cutoff = date.today() + timedelta(days=within_days)
    result = await db.execute(
        select(MaintenanceSchedule).where(
            MaintenanceSchedule.due_date.is_not(None),
            MaintenanceSchedule.due_date <= cutoff,
            MaintenanceSchedule.status.notin_(["done", "skipped"]),
            MaintenanceSchedule.task_type.in_(list(_MAINTENANCE_OPPORTUNITY.keys())),
        ).order_by(MaintenanceSchedule.due_date).limit(100)
    )
    for task in result.scalars().all():
        type_, action = _MAINTENANCE_OPPORTUNITY[task.task_type]
        opportunities.append(_opp(
            type_, f"{task.task_type.replace('_', ' ').title()}: {task.device_name or ''}".strip(),
            task.due_date, "maintenance_schedule", task.id, action, "medium",
        ))

    # Expansion opportunities: high recurring, multi-site leads -> tag / new points.
    exp_result = await db.execute(
        select(Lead).where(
            Lead.is_multi_site == True,  # noqa: E712
            Lead.recurring_revenue_score >= 60,
            Lead.status.in_(["won", "converted", "matched"]),
        ).order_by(Lead.recurring_revenue_score.desc()).limit(20)
    )
    for lead in exp_result.scalars().all():
        opportunities.append(_opp(
            "expansion", f"Expansion: {lead.project_type or 'multi-site account'}", None,
            "lead", lead.id, "Propose new monitoring points / tag expansion", "low",
        ))

    counts: dict[str, int] = {}
    for o in opportunities:
        counts[o["type"]] = counts.get(o["type"], 0) + 1

    return {"total": len(opportunities), "counts": counts, "opportunities": opportunities}

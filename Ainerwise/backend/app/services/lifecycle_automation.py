"""Scheduled lifecycle automation (FI.8.4, FI.8.5).

scan_and_notify: scans due dates (AMC renewal, calibration, warranty expiry,
low stock) and emits lifecycle integration events (deduplicated within a
window). generate_report_jobs: creates monthly compliance ReportJob rows in
pending_review for active StorageGuard projects.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import IntegrationEvent
from app.models.notification import ReportJob
from app.models.project import Project
from app.services import lifecycle_alerts
from app.services.integration_events import create_integration_event


async def _recent_event_exists(db: AsyncSession, event_type: str, ref: str, *, days: int = 6) -> bool:
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(IntegrationEvent.id).where(
            IntegrationEvent.event_type == event_type,
            IntegrationEvent.payload_json["ref"].astext == ref,
            IntegrationEvent.created_at >= cutoff,
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _emit(db: AsyncSession, event_type: str, ref: str, payload: dict[str, Any]) -> bool:
    if await _recent_event_exists(db, event_type, ref):
        return False
    payload = {**payload, "ref": ref}
    await create_integration_event(db, event_type=event_type, payload=payload)
    return True


async def scan_and_notify(db: AsyncSession, *, within_days: int = 90) -> dict[str, int]:
    """FI.8.4 — scan due dates and emit deduplicated lifecycle events."""
    emitted: dict[str, int] = {}

    def bump(key: str, added: bool) -> None:
        if added:
            emitted[key] = emitted.get(key, 0) + 1

    for amc in await lifecycle_alerts.amc_renewal_due(db, within_days=within_days):
        bump("amc.renewal_due", await _emit(db, "amc.renewal_due", f"amc:{amc.id}", {
            "project_id": str(amc.project_id) if amc.project_id else None,
            "item": f"{amc.package or 'AMC'} contract",
            "due_date": amc.end_date.isoformat() if amc.end_date else None,
        }))

    for point in await lifecycle_alerts.calibration_due(db, within_days=within_days):
        bump("calibration.due", await _emit(db, "calibration.due", f"cal:{point.id}", {
            "solution_line": point.solution_line,
            "project_id": str(point.project_id) if point.project_id else None,
            "item": point.device_name or point.point_type,
            "due_date": point.next_calibration_at.isoformat() if point.next_calibration_at else None,
        }))

    for w in await lifecycle_alerts.warranty_expiring(db, within_days=within_days):
        bump("warranty.expiry", await _emit(db, "warranty.expiry", f"war:{w.id}", {
            "project_id": str(w.project_id) if w.project_id else None,
            "item": f"{w.warranty_model or 'warranty'} coverage",
            "due_date": w.end_date.isoformat() if w.end_date else None,
        }))

    for inv in await lifecycle_alerts.low_stock_items(db):
        bump("inventory.low_stock", await _emit(db, "inventory.low_stock", f"inv:{inv.id}", {
            "item": inv.name,
            "recommended_action": f"Reorder {inv.name} (qty {inv.quantity} <= reorder {inv.reorder_level})",
        }))

    return emitted


async def generate_report_jobs(db: AsyncSession, *, period_label: str | None = None) -> int:
    """FI.8.5 — create monthly compliance ReportJob rows (pending_review)."""
    if period_label is None:
        today = date.today()
        period_label = f"{today.year}-{today.month:02d}"

    # Active StorageGuard projects (by plan solution_line).
    result = await db.execute(
        select(Project).where(Project.status.notin_(["closed"]))
    )
    created = 0
    for project in result.scalars().all():
        plan = project.project_plan_json or {}
        if not (isinstance(plan, dict) and plan.get("solution_line") == "storageguard"):
            continue
        existing = await db.execute(
            select(ReportJob.id).where(
                ReportJob.project_id == project.id,
                ReportJob.period_label == period_label,
                ReportJob.report_type == "monthly",
            ).limit(1)
        )
        if existing.scalar_one_or_none():
            continue
        db.add(ReportJob(
            project_id=project.id,
            report_type="monthly",
            period_label=period_label,
            status="pending_review",
            review_status="pending_review",
            scheduled_for=date.today(),
            notes="Auto-scheduled monthly compliance report. Requires admin review before customer delivery.",
        ))
        created += 1
    await db.commit()
    return created

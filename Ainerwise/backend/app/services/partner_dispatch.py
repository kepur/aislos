"""Manual Partner task dispatch for Phase D.

Dispatch remains admin-confirmed in Phase D. Automatic award-to-task
dispatch is intentionally reserved for Phase E.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lifecycle import MaintenanceSchedule
from app.models.project import Project
from app.models.service import ServicePartner
from app.services.channel_gateway import send_channel_message
from app.services.event_bus import emit_event

EVENT_PARTNER_TASK_DISPATCHED = "partner.task_dispatched"
EVENT_PARTNER_TASK_STATUS_CHANGED = "partner.task_status_changed"

PARTNER_TASK_STATUS_TRANSITIONS = {
    "scheduled": {"in_progress", "done", "completed_pending_acceptance"},
    "due": {"in_progress", "done", "completed_pending_acceptance"},
    "in_progress": {"done", "completed_pending_acceptance"},
    "completed_pending_acceptance": {"done"},  # closed by customer signature
}


def partner_task_dict(task: MaintenanceSchedule, project: Project | None = None) -> dict:
    return {
        "id": str(task.id),
        "project_id": str(task.project_id) if task.project_id else None,
        "project_title": project.title if project else None,
        "project_region": project.region if project else None,
        "task_type": task.task_type,
        "device_name": task.device_name,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "status": task.status,
        "covered_by_amc": task.covered_by_amc,
        "notes": task.notes,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def _task_message(project: Project, task: MaintenanceSchedule) -> str:
    lines = [
        "AinerWise - new Partner task",
        f"Project: {project.title}",
        f"Task: {(task.task_type or 'service task').replace('_', ' ').title()}",
    ]
    if task.device_name:
        lines.append(f"Item: {task.device_name}")
    if project.region:
        lines.append(f"Region: {project.region}")
    if task.due_date:
        lines.append(f"Due: {task.due_date:%Y-%m-%d}")
    lines.append(
        f"Open task: {settings.PARTNER_PORTAL_URL.rstrip('/')}/partner/tasks/{task.id}"
    )
    return "\n".join(lines)


async def dispatch_partner_task(
    db: AsyncSession,
    *,
    project: Project,
    partner: ServicePartner,
    task_type: str,
    due_date,
    device_name: str | None,
    notes: str | None,
    covered_by_amc: bool,
) -> MaintenanceSchedule:
    if partner.user_id is None:
        raise ValueError("Partner account is not linked to a user")

    task = MaintenanceSchedule(
        project_id=project.id,
        assigned_to=partner.user_id,
        task_type=task_type,
        due_date=due_date,
        device_name=device_name,
        notes=notes,
        covered_by_amc=covered_by_amc,
        status="scheduled",
    )
    db.add(task)
    await db.flush()

    delivery_status = "manual"
    if partner.telegram_chat_id:
        delivery_status = await send_channel_message(
            message_id=task.id,
            channel="telegram",
            external_thread_id=partner.telegram_chat_id,
            content=_task_message(project, task),
            metadata={
                "purpose": "partner_task_dispatch",
                "task_id": str(task.id),
                "project_id": str(project.id),
                "partner_id": str(partner.id),
            },
            account_name="AinerWise Partner Bot",
        )

    await emit_event(
        db,
        EVENT_PARTNER_TASK_DISPATCHED,
        {
            "task_id": str(task.id),
            "project_id": str(project.id),
            "partner_id": str(partner.id),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "delivery_status": delivery_status,
        },
        aggregate_type="maintenance_schedule",
        aggregate_id=task.id,
    )
    return task


async def change_partner_task_status(
    db: AsyncSession,
    *,
    task: MaintenanceSchedule,
    status: str,
) -> None:
    allowed = PARTNER_TASK_STATUS_TRANSITIONS.get(task.status, set())
    if status not in allowed:
        raise ValueError(f"Cannot move task from {task.status} to {status}")
    previous = task.status
    task.status = status
    db.add(task)
    await emit_event(
        db,
        EVENT_PARTNER_TASK_STATUS_CHANGED,
        {
            "task_id": str(task.id),
            "project_id": str(task.project_id) if task.project_id else None,
            "from_status": previous,
            "to_status": status,
        },
        aggregate_type="maintenance_schedule",
        aggregate_id=task.id,
    )

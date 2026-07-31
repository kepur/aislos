"""PF03–PF06: Field Service operations."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_service import (
    CrewMembership,
    FieldTask,
    PartnerCrew,
    TaskAssignment,
    TaskEvidence,
    WorkPackage,
)


class FieldServiceError(ValueError):
    pass


async def list_work_packages(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID | None = None,
    partner_company_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[WorkPackage]:
    q = select(WorkPackage).order_by(WorkPackage.created_at.desc()).limit(limit)
    if workspace_id:
        q = q.where(WorkPackage.workspace_id == workspace_id)
    if partner_company_id:
        q = q.where(WorkPackage.partner_company_id == partner_company_id)
    return list((await db.execute(q)).scalars().all())


async def create_work_package(db: AsyncSession, **fields) -> WorkPackage:
    row = WorkPackage(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_assigned_task(
    db: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID
) -> tuple[FieldTask, TaskAssignment] | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(FieldTask, TaskAssignment)
        .join(TaskAssignment, TaskAssignment.field_task_id == FieldTask.id)
        .where(
            FieldTask.id == task_id,
            TaskAssignment.workspace_id == FieldTask.workspace_id,
            TaskAssignment.assignee_user_id == user_id,
            TaskAssignment.status == "active",
            (TaskAssignment.valid_until.is_(None)) | (TaskAssignment.valid_until > now),
        )
    )
    row = result.first()
    return (row[0], row[1]) if row else None


async def update_task_status(
    db: AsyncSession,
    *,
    task: FieldTask,
    new_status: str,
    client_version: int,
) -> FieldTask:
    if client_version < task.offline_version:
        raise FieldServiceError("version_conflict")
    allowed = {"scheduled", "in_progress", "paused", "blocked", "done"}
    if new_status not in allowed:
        raise FieldServiceError(f"invalid status {new_status!r}")
    task.status = new_status
    task.offline_version = task.offline_version + 1
    await db.flush()
    return task


async def list_assigned_tasks(db: AsyncSession, user_id: uuid.UUID) -> list[FieldTask]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(FieldTask)
        .join(TaskAssignment, TaskAssignment.field_task_id == FieldTask.id)
        .where(
            TaskAssignment.workspace_id == FieldTask.workspace_id,
            TaskAssignment.assignee_user_id == user_id,
            TaskAssignment.status == "active",
            (TaskAssignment.valid_until.is_(None)) | (TaskAssignment.valid_until > now),
        )
        .order_by(FieldTask.schedule_start.asc().nullslast())
    )
    return list(result.scalars().all())


async def assign_task(
    db: AsyncSession,
    *,
    field_task_id: uuid.UUID,
    assignee_user_id: uuid.UUID,
    assigned_by: uuid.UUID | None,
    crew_id: uuid.UUID | None = None,
) -> TaskAssignment:
    task = await db.get(FieldTask, field_task_id)
    if task is None:
        raise FieldServiceError("task not found")
    if crew_id is not None:
        crew = await db.get(PartnerCrew, crew_id)
        if crew is None:
            raise FieldServiceError("crew not found")
        if crew.workspace_id != task.workspace_id:
            raise FieldServiceError("crew and task must belong to the same workspace")
    row = TaskAssignment(
        workspace_id=task.workspace_id,
        field_task_id=field_task_id,
        assignee_user_id=assignee_user_id,
        assigned_by=assigned_by,
        crew_id=crew_id,
        status="active",
        valid_from=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    return row


async def add_evidence(
    db: AsyncSession,
    *,
    field_task_id: uuid.UUID,
    assignment_id: uuid.UUID | None,
    evidence_type: str,
    payload_json: dict | None,
    captured_by: uuid.UUID,
    idempotency_key: str | None,
) -> TaskEvidence:
    if idempotency_key:
        existing = (
            await db.execute(
                select(TaskEvidence).where(TaskEvidence.idempotency_key == idempotency_key)
            )
        ).scalar_one_or_none()
        if existing:
            return existing
    row = TaskEvidence(
        field_task_id=field_task_id,
        assignment_id=assignment_id,
        evidence_type=evidence_type,
        payload_json=payload_json,
        captured_by=captured_by,
        idempotency_key=idempotency_key,
        sync_status="synced",
    )
    db.add(row)
    await db.flush()
    return row


async def create_crew(db: AsyncSession, **fields) -> PartnerCrew:
    row = PartnerCrew(**fields)
    db.add(row)
    await db.flush()
    return row


async def add_crew_member(
    db: AsyncSession,
    *,
    crew_id: uuid.UUID,
    user_id: uuid.UUID,
    role_in_crew: str = "worker",
) -> CrewMembership:
    crew = await db.get(PartnerCrew, crew_id)
    if crew is None:
        raise FieldServiceError("crew not found")
    row = CrewMembership(
        workspace_id=crew.workspace_id,
        crew_id=crew_id,
        user_id=user_id,
        role_in_crew=role_in_crew,
        status="active",
        valid_from=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    return row

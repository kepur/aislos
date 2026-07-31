"""PF03: Field Service domain — WorkPackage, Crew, FieldTask, Assignment, Evidence."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, event, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class PartnerCrew(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "partner_crews"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    partner_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class CrewMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "crew_memberships"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    crew_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partner_crews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_in_crew: Mapped[str] = mapped_column(String(64), default="worker", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkPackage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_packages"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    partner_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    trade: Mapped[str | None] = mapped_column(String(64))
    scope_json: Mapped[dict | None] = mapped_column(JSONB)
    site_json: Mapped[dict | None] = mapped_column(JSONB)
    planned_start: Mapped[date | None] = mapped_column(Date)
    planned_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)


class FieldTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "field_tasks"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    work_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_packages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    site_json: Mapped[dict | None] = mapped_column(JSONB)
    checklist_json: Mapped[dict | None] = mapped_column(JSONB)
    required_skill: Mapped[str | None] = mapped_column(String(64))
    schedule_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    schedule_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safety_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False, index=True)
    offline_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class TaskAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_assignments"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    field_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignee_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    crew_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partner_crews.id"), nullable=True
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)


class TaskEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_evidence"

    field_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("task_assignments.id"), nullable=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONB)
    captured_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), default="synced", nullable=False)


@event.listens_for(CrewMembership, "before_insert")
@event.listens_for(CrewMembership, "before_update")
def _inherit_membership_workspace(mapper, connection, target: CrewMembership) -> None:
    if target.workspace_id is not None or target.crew_id is None:
        return
    target.workspace_id = connection.execute(
        select(PartnerCrew.workspace_id).where(PartnerCrew.id == target.crew_id)
    ).scalar_one_or_none()


@event.listens_for(FieldTask, "before_insert")
@event.listens_for(FieldTask, "before_update")
def _inherit_field_task_workspace(mapper, connection, target: FieldTask) -> None:
    if target.workspace_id is not None or target.work_package_id is None:
        return
    target.workspace_id = connection.execute(
        select(WorkPackage.workspace_id).where(WorkPackage.id == target.work_package_id)
    ).scalar_one_or_none()


@event.listens_for(TaskAssignment, "before_insert")
@event.listens_for(TaskAssignment, "before_update")
def _inherit_assignment_workspace(mapper, connection, target: TaskAssignment) -> None:
    if target.workspace_id is not None or target.field_task_id is None:
        return
    target.workspace_id = connection.execute(
        select(FieldTask.workspace_id).where(FieldTask.id == target.field_task_id)
    ).scalar_one_or_none()

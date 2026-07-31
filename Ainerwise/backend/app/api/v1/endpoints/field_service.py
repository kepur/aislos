"""PF03–PF07: Field Service and supplier-facing APIs."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DB, ServicePartnerUser
from app.models.field_service import (
    CrewMembership,
    FieldTask,
    PartnerCrew,
    TaskAssignment,
    TaskEvidence,
    WorkPackage,
)
from app.models.portal_access import WorkspaceMembership
from app.models.project import Project
from app.core.signature_image import validate_signature_data_url
from app.models.service import ServicePartner
from app.models.user import Company, User
from app.schemas.field_service import (
    CrewMembershipCreate,
    CrewMembershipRead,
    FieldTaskCreate,
    FieldTaskDetailRead,
    FieldTaskRead,
    FieldTaskStatusUpdate,
    OfflineSyncRequest,
    OfflineSyncResult,
    PartnerCrewCreate,
    PartnerCrewRead,
    QrBindRequest,
    SignatureCaptureRequest,
    TaskAssignmentCreate,
    TaskAssignmentRead,
    TaskEvidenceCreate,
    TaskEvidenceRead,
    WorkPackageCreate,
    WorkPackageRead,
)
from app.services.field_service import (
    FieldServiceError,
    add_crew_member,
    add_evidence,
    assign_task,
    create_crew,
    create_work_package,
    get_assigned_task,
    list_assigned_tasks,
    list_work_packages,
    update_task_status,
)
from app.services.portal_access import (
    ensure_grant,
    ensure_membership,
    user_has_grant,
    user_has_grant_in_any_workspace,
)
from app.services.project_access import require_project_operator_access

router = APIRouter(prefix="/field", tags=["field-service"])
admin_router = APIRouter(prefix="/admin/field-ops", tags=["field-ops-admin"])
supplier_router = APIRouter(prefix="/supplier", tags=["supplier-portal"])
partner_router = APIRouter(prefix="/partner/field-ops", tags=["partner-field-ops"])
crew_router = APIRouter(prefix="/crew", tags=["crew-lead"])


class CrewTaskStatusUpdate(BaseModel):
    status: str
    offline_version: int


class CrewTaskAction(BaseModel):
    notes: str | None = None
    payload_json: dict | None = None


async def _require_field_worker(db, user, *, workspace_id: uuid.UUID):
    if not await user_has_grant(
        db,
        user.id,
        "field_task.read_assigned",
        workspace_id=workspace_id,
        portal_key="field_worker",
    ):
        raise HTTPException(status_code=403, detail="Field worker grant required for task workspace")


async def _task_workspace_id(db, task: FieldTask) -> uuid.UUID:
    package = await db.get(WorkPackage, task.work_package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    return package.workspace_id


async def _require_field_ops_admin(db, user, *, workspace_id: uuid.UUID):
    if user.role in ("admin", "super_admin"):
        return
    if not await user_has_grant(
        db,
        user.id,
        "admin.field_ops.read",
        workspace_id=workspace_id,
        portal_key="admin_field_ops",
    ):
        raise HTTPException(status_code=403, detail="Field Operations workspace grant required")


async def _partner_company_id(db, user) -> uuid.UUID:
    partner = (
        await db.execute(select(ServicePartner).where(ServicePartner.user_id == user.id))
    ).scalars().first()
    company_id = partner.company_id if partner and partner.company_id else user.company_id
    if company_id is None:
        raise HTTPException(status_code=409, detail="Partner account is not linked to a company")
    return company_id


async def _require_partner_work_package_access(
    db,
    user,
    *,
    workspace_id: uuid.UUID,
    partner_company_id: uuid.UUID | None,
) -> uuid.UUID:
    company_id = await _partner_company_id(db, user)
    if partner_company_id != company_id:
        raise HTTPException(status_code=404, detail="Partner work package not found")
    for portal_key in ("partner_company_pc", "partner_company_h5", "partner_company"):
        if await user_has_grant(
            db,
            user.id,
            "partner.work_package.read",
            workspace_id=workspace_id,
            portal_key=portal_key,
        ):
            return company_id
    raise HTTPException(status_code=403, detail="Partner work package grant required")


async def _partner_package(db, user, package_id: uuid.UUID) -> WorkPackage:
    package = await db.get(WorkPackage, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Partner work package not found")
    await _require_partner_work_package_access(
        db,
        user,
        workspace_id=package.workspace_id,
        partner_company_id=package.partner_company_id,
    )
    return package


async def _partner_task(db, user, task_id: uuid.UUID) -> tuple[FieldTask, WorkPackage]:
    row = (
        await db.execute(
            select(FieldTask, WorkPackage)
            .join(WorkPackage, WorkPackage.id == FieldTask.work_package_id)
            .where(FieldTask.id == task_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Partner field task not found")
    await _require_partner_work_package_access(
        db,
        user,
        workspace_id=row[1].workspace_id,
        partner_company_id=row[1].partner_company_id,
    )
    return row[0], row[1]


async def _package_detail(db, package: WorkPackage) -> dict:
    tasks = list(
        (
            await db.execute(
                select(FieldTask)
                .where(FieldTask.work_package_id == package.id)
                .order_by(FieldTask.schedule_start.asc().nullslast(), FieldTask.created_at.asc())
            )
        ).scalars()
    )
    task_ids = [task.id for task in tasks]
    assignments: dict[uuid.UUID, list[dict]] = {task_id: [] for task_id in task_ids}
    evidence_counts: dict[uuid.UUID, int] = {}
    if task_ids:
        assignment_rows = (
            await db.execute(
                select(TaskAssignment, User)
                .join(User, User.id == TaskAssignment.assignee_user_id)
                .where(TaskAssignment.field_task_id.in_(task_ids))
            )
        ).all()
        for assignment, worker in assignment_rows:
            assignments[assignment.field_task_id].append(
                {
                    **TaskAssignmentRead.model_validate(assignment).model_dump(mode="json"),
                    "worker_name": worker.full_name or worker.email,
                    "worker_email": worker.email,
                }
            )
        evidence_counts = dict(
            (
                await db.execute(
                    select(TaskEvidence.field_task_id, func.count())
                    .where(TaskEvidence.field_task_id.in_(task_ids))
                    .group_by(TaskEvidence.field_task_id)
                )
            ).all()
        )
    return {
        **WorkPackageRead.model_validate(package).model_dump(mode="json"),
        "tasks": [
            {
                **FieldTaskRead.model_validate(task).model_dump(mode="json"),
                "assignments": assignments[task.id],
                "evidence_count": evidence_counts.get(task.id, 0),
            }
            for task in tasks
        ],
    }


async def _ensure_crew_lead_access(db, user, *, workspace_id: uuid.UUID) -> None:
    if not await user_has_grant(
        db,
        user.id,
        "crew.task.manage",
        workspace_id=workspace_id,
        portal_key="crew_lead_h5",
    ):
        raise HTTPException(status_code=403, detail="Crew Lead workspace grant required")


async def _led_crews(db, user) -> list[PartnerCrew]:
    now = datetime.now(timezone.utc)
    rows = list(
        (
            await db.execute(
                select(PartnerCrew)
                .join(CrewMembership, CrewMembership.crew_id == PartnerCrew.id)
                .where(
                    CrewMembership.user_id == user.id,
                    CrewMembership.role_in_crew.in_(("lead", "supervisor")),
                    CrewMembership.status == "active",
                    (CrewMembership.valid_from.is_(None)) | (CrewMembership.valid_from <= now),
                    (CrewMembership.valid_until.is_(None)) | (CrewMembership.valid_until > now),
                    PartnerCrew.status == "active",
                )
                .order_by(PartnerCrew.name.asc())
            )
        ).scalars()
    )
    allowed = []
    for crew in rows:
        try:
            await _ensure_crew_lead_access(db, user, workspace_id=crew.workspace_id)
            allowed.append(crew)
        except HTTPException:
            continue
    return allowed


async def _crew_lead_task(db, user, task_id: uuid.UUID) -> tuple[FieldTask, WorkPackage, TaskAssignment]:
    crews = await _led_crews(db, user)
    crew_ids = [crew.id for crew in crews]
    if not crew_ids:
        raise HTTPException(status_code=404, detail="Crew task not found")
    row = (
        await db.execute(
            select(FieldTask, WorkPackage, TaskAssignment)
            .join(WorkPackage, WorkPackage.id == FieldTask.work_package_id)
            .join(TaskAssignment, TaskAssignment.field_task_id == FieldTask.id)
            .where(
                FieldTask.id == task_id,
                TaskAssignment.crew_id.in_(crew_ids),
                TaskAssignment.status == "active",
            )
            .limit(1)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Crew task not found")
    await _ensure_crew_lead_access(db, user, workspace_id=row[1].workspace_id)
    return row[0], row[1], row[2]


async def _record_crew_action(db, user, task: FieldTask, action: str, data: CrewTaskAction):
    row = await add_evidence(
        db,
        field_task_id=task.id,
        assignment_id=None,
        evidence_type=action,
        payload_json={
            **(data.payload_json or {}),
            "notes": data.notes,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        },
        captured_by=user.id,
        idempotency_key=None,
    )
    await db.commit()
    await db.refresh(row)
    return TaskEvidenceRead.model_validate(row)


@router.get("/tasks/today", response_model=dict)
async def field_worker_today(db: DB, user: CurrentUser):
    if not await user_has_grant_in_any_workspace(
        db, user.id, "field_task.read_assigned", portal_key="field_worker"
    ):
        raise HTTPException(status_code=403, detail="Field worker grant required")
    tasks = await list_assigned_tasks(db, user.id)
    allowed_tasks = []
    for task in tasks:
        if await user_has_grant(
            db,
            user.id,
            "field_task.read_assigned",
            workspace_id=await _task_workspace_id(db, task),
            portal_key="field_worker",
        ):
            allowed_tasks.append(task)
    return {
        "items": [FieldTaskRead.model_validate(t) for t in allowed_tasks],
        "total": len(allowed_tasks),
    }


@router.get("/tasks/{task_id}", response_model=FieldTaskDetailRead)
async def field_worker_task_detail(task_id: uuid.UUID, db: DB, user: CurrentUser):
    pair = await get_assigned_task(db, user.id, task_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Task not found or not assigned")
    task, assignment = pair
    await _require_field_worker(db, user, workspace_id=await _task_workspace_id(db, task))
    site = task.site_json or {}
    phone = site.get("contact_phone") if task.status in ("in_progress", "scheduled") else None
    data = FieldTaskRead.model_validate(task).model_dump()
    data["site_contact_phone"] = phone
    data["assignment_id"] = assignment.id
    return FieldTaskDetailRead.model_validate(data)


@router.patch("/tasks/{task_id}/status", response_model=FieldTaskRead)
async def field_worker_update_status(
    task_id: uuid.UUID, data: FieldTaskStatusUpdate, db: DB, user: CurrentUser
):
    pair = await get_assigned_task(db, user.id, task_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task, _ = pair
    await _require_field_worker(db, user, workspace_id=await _task_workspace_id(db, task))
    server_version = task.offline_version
    try:
        updated = await update_task_status(
            db, task=task, new_status=data.status, client_version=data.offline_version
        )
        await db.commit()
        await db.refresh(updated)
        return FieldTaskRead.model_validate(updated)
    except FieldServiceError as exc:
        await db.rollback()
        if str(exc) == "version_conflict":
            raise HTTPException(
                status_code=409,
                detail={"error": "version_conflict", "server_offline_version": server_version},
            ) from None
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.post("/sync", response_model=dict)
async def field_worker_offline_sync(data: OfflineSyncRequest, db: DB, user: CurrentUser):
    results: list[OfflineSyncResult] = []
    for item in data.items:
        pair = await get_assigned_task(db, user.id, item.task_id)
        if pair is None:
            results.append(
                OfflineSyncResult(
                    idempotency_key=item.idempotency_key,
                    status="rejected",
                    detail="assignment_revoked",
                )
            )
            continue
        task, assignment = pair
        if not await user_has_grant(
            db,
            user.id,
            "field_task.read_assigned",
            workspace_id=await _task_workspace_id(db, task),
            portal_key="field_worker",
        ):
            results.append(
                OfflineSyncResult(
                    idempotency_key=item.idempotency_key,
                    status="rejected",
                    detail="workspace_grant_revoked",
                )
            )
            continue
        try:
            if item.type == "status" and item.status:
                await update_task_status(
                    db,
                    task=task,
                    new_status=item.status,
                    client_version=item.offline_version or task.offline_version,
                )
            elif item.type == "evidence" and item.evidence_type:
                await add_evidence(
                    db,
                    field_task_id=item.task_id,
                    assignment_id=assignment.id,
                    evidence_type=item.evidence_type,
                    payload_json=item.payload_json,
                    captured_by=user.id,
                    idempotency_key=item.idempotency_key,
                )
            results.append(OfflineSyncResult(idempotency_key=item.idempotency_key, status="ok"))
        except FieldServiceError as exc:
            conflict = str(exc) == "version_conflict"
            results.append(
                OfflineSyncResult(
                    idempotency_key=item.idempotency_key,
                    status="conflict" if conflict else "error",
                    conflict=conflict,
                    server_offline_version=task.offline_version,
                    detail=str(exc),
                )
            )
    await db.commit()
    return {"items": [r.model_dump() for r in results], "total": len(results)}


async def _submit_assigned_evidence(
    db,
    user,
    task_id: uuid.UUID,
    *,
    evidence_type: str,
    payload_json: dict | None,
    idempotency_key: str | None,
) -> TaskEvidence:
    pair = await get_assigned_task(db, user.id, task_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Task not found or not assigned")
    task, assignment = pair
    await _require_field_worker(db, user, workspace_id=await _task_workspace_id(db, task))
    try:
        row = await add_evidence(
            db,
            field_task_id=task_id,
            assignment_id=assignment.id,
            evidence_type=evidence_type,
            payload_json=payload_json,
            captured_by=user.id,
            idempotency_key=idempotency_key,
        )
        await db.commit()
        await db.refresh(row)
        return row
    except FieldServiceError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.post("/tasks/{task_id}/evidence", response_model=TaskEvidenceRead)
async def submit_task_evidence(
    task_id: uuid.UUID, data: TaskEvidenceCreate, db: DB, user: CurrentUser
):
    row = await _submit_assigned_evidence(
        db,
        user,
        task_id,
        evidence_type=data.evidence_type,
        payload_json=data.payload_json,
        idempotency_key=data.idempotency_key,
    )
    return TaskEvidenceRead.model_validate(row)


@router.post("/tasks/{task_id}/bind-qr", response_model=TaskEvidenceRead)
async def bind_qr_device(task_id: uuid.UUID, data: QrBindRequest, db: DB, user: CurrentUser):
    """Scan QR / enter device serial — stored as structured evidence."""
    row = await _submit_assigned_evidence(
        db,
        user,
        task_id,
        evidence_type="qr",
        payload_json={
            "qr_code": data.qr_code.strip(),
            "device_label": data.device_label,
            "bound_at": datetime.now(timezone.utc).isoformat(),
        },
        idempotency_key=f"qr-{data.qr_code.strip()}-{task_id}",
    )
    return TaskEvidenceRead.model_validate(row)


@router.post("/tasks/{task_id}/signature", response_model=TaskEvidenceRead)
async def capture_customer_signature(
    task_id: uuid.UUID, data: SignatureCaptureRequest, db: DB, user: CurrentUser
):
    """On-site customer signature capture."""
    try:
        validate_signature_data_url(data.signature_data_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    row = await _submit_assigned_evidence(
        db,
        user,
        task_id,
        evidence_type="signature",
        payload_json={
            "signature_data_url": data.signature_data_url,
            "signer_name": data.signer_name,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
        idempotency_key=data.idempotency_key,
    )
    return TaskEvidenceRead.model_validate(row)


@admin_router.get("/work-packages")
async def admin_list_work_packages(
    db: DB, admin: CurrentUser, workspace_id: uuid.UUID | None = None
):
    if workspace_id is None and admin.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=400, detail="workspace_id is required")
    if workspace_id is not None:
        await _require_field_ops_admin(db, admin, workspace_id=workspace_id)
    items = await list_work_packages(db, workspace_id=workspace_id)
    return {"items": [WorkPackageRead.model_validate(i) for i in items], "total": len(items)}


@admin_router.post("/work-packages", response_model=WorkPackageRead, status_code=201)
async def admin_create_work_package(data: WorkPackageCreate, db: DB, admin: CurrentUser):
    from app.models.portal_access import Workspace

    ws = await db.get(Workspace, data.workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await _require_field_ops_admin(db, admin, workspace_id=data.workspace_id)
    if data.project_id is not None:
        project = await db.get(Project, data.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        await require_project_operator_access(db, admin, project)
        if project.workspace_id is None:
            project.workspace_id = data.workspace_id
            db.add(project)
        elif project.workspace_id != data.workspace_id:
            raise HTTPException(
                status_code=409,
                detail="WorkPackage and Project must belong to the same Workspace",
            )
    if data.partner_company_id is not None and await db.get(Company, data.partner_company_id) is None:
        raise HTTPException(status_code=404, detail="Partner company not found")
    row = await create_work_package(db, **data.model_dump())
    await db.commit()
    await db.refresh(row)
    return WorkPackageRead.model_validate(row)


@admin_router.post("/work-packages/{package_id}/tasks", response_model=FieldTaskRead, status_code=201)
async def admin_create_field_task(package_id: uuid.UUID, data: FieldTaskCreate, db: DB, admin: CurrentUser):
    pkg = await db.get(WorkPackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    await _require_field_ops_admin(db, admin, workspace_id=pkg.workspace_id)
    body = data.model_dump()
    body["work_package_id"] = package_id
    body["workspace_id"] = pkg.workspace_id
    row = FieldTask(**body)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return FieldTaskRead.model_validate(row)


@admin_router.post("/tasks/{task_id}/assignments", response_model=TaskAssignmentRead, status_code=201)
async def admin_assign_task(task_id: uuid.UUID, data: TaskAssignmentCreate, db: DB, admin: CurrentUser):
    task = await db.get(FieldTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    package = await db.get(WorkPackage, task.work_package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    workspace_id = package.workspace_id
    await _require_field_ops_admin(db, admin, workspace_id=workspace_id)
    worker = await db.get(User, data.assignee_user_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    membership = (
        await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == worker.id,
                WorkspaceMembership.status == "active",
            )
        )
    ).scalars().first()
    if membership is None:
        raise HTTPException(status_code=409, detail="Worker is not active in the task workspace")
    if package.partner_company_id is not None and worker.company_id != package.partner_company_id:
        raise HTTPException(status_code=409, detail="Worker is not part of the assigned partner company")
    if data.crew_id is not None:
        crew = await db.get(PartnerCrew, data.crew_id)
        if crew is None or crew.workspace_id != workspace_id:
            raise HTTPException(status_code=409, detail="Crew is not active in the task workspace")
        if package.partner_company_id is not None and crew.partner_company_id != package.partner_company_id:
            raise HTTPException(status_code=409, detail="Crew is not part of the assigned partner company")
    try:
        row = await assign_task(
            db,
            field_task_id=task_id,
            assignee_user_id=data.assignee_user_id,
            assigned_by=admin.id,
            crew_id=data.crew_id,
        )
        await db.commit()
        await db.refresh(row)
        return TaskAssignmentRead.model_validate(row)
    except FieldServiceError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@admin_router.post("/crews", response_model=PartnerCrewRead, status_code=201)
async def admin_create_crew(data: PartnerCrewCreate, db: DB, admin: CurrentUser):
    await _require_field_ops_admin(db, admin, workspace_id=data.workspace_id)
    if data.partner_company_id is not None and await db.get(Company, data.partner_company_id) is None:
        raise HTTPException(status_code=404, detail="Partner company not found")
    row = await create_crew(db, **data.model_dump())
    await db.commit()
    await db.refresh(row)
    return PartnerCrewRead.model_validate(row)


@admin_router.post("/crews/{crew_id}/members", response_model=CrewMembershipRead)
async def admin_add_crew_member(
    crew_id: uuid.UUID,
    db: DB,
    admin: CurrentUser,
    data: CrewMembershipCreate | None = None,
    user_id: uuid.UUID | None = None,
    role_in_crew: str = "worker",
):
    crew = await db.get(PartnerCrew, crew_id)
    if crew is None:
        raise HTTPException(status_code=404, detail="Crew not found")
    await _require_field_ops_admin(db, admin, workspace_id=crew.workspace_id)
    member_id = data.user_id if data else user_id
    member_role = data.role_in_crew if data else role_in_crew
    if member_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    member = await db.get(User, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    workspace_membership = (
        await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == crew.workspace_id,
                WorkspaceMembership.user_id == member.id,
                WorkspaceMembership.status == "active",
            )
        )
    ).scalars().first()
    if workspace_membership is None:
        raise HTTPException(status_code=409, detail="Worker is not active in the crew workspace")
    if crew.partner_company_id is not None and member.company_id != crew.partner_company_id:
        raise HTTPException(status_code=409, detail="Worker is not part of the crew company")
    row = await add_crew_member(
        db,
        crew_id=crew_id,
        user_id=member_id,
        role_in_crew=member_role,
    )
    if member_role in ("lead", "supervisor"):
        await ensure_membership(
            db,
            user_id=member.id,
            membership_type="crew_lead",
            workspace_id=crew.workspace_id,
            company_id=member.company_id,
        )
        await ensure_grant(
            db,
            user_id=member.id,
            grant_key="crew.task.manage",
            workspace_id=crew.workspace_id,
            portal_key="crew_lead_h5",
        )
    await db.commit()
    return CrewMembershipRead.model_validate(row)


@admin_router.get("/work-packages/{package_id}")
async def admin_get_work_package(package_id: uuid.UUID, db: DB, admin: CurrentUser):
    package = await db.get(WorkPackage, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    await _require_field_ops_admin(db, admin, workspace_id=package.workspace_id)
    return await _package_detail(db, package)


@admin_router.get("/crews")
async def admin_list_crews(db: DB, admin: CurrentUser, workspace_id: uuid.UUID):
    await _require_field_ops_admin(db, admin, workspace_id=workspace_id)
    items = list(
        (
            await db.execute(
                select(PartnerCrew)
                .where(PartnerCrew.workspace_id == workspace_id)
                .order_by(PartnerCrew.name.asc())
            )
        ).scalars()
    )
    return {"items": [PartnerCrewRead.model_validate(item) for item in items], "total": len(items)}


@admin_router.get("/workers")
async def admin_list_workers(db: DB, admin: CurrentUser, workspace_id: uuid.UUID):
    await _require_field_ops_admin(db, admin, workspace_id=workspace_id)
    rows = (
        await db.execute(
            select(User, WorkspaceMembership)
            .join(WorkspaceMembership, WorkspaceMembership.user_id == User.id)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.status == "active",
                WorkspaceMembership.membership_type.in_(("field_worker", "crew_lead")),
            )
            .order_by(User.full_name.asc().nullslast(), User.email.asc())
        )
    ).all()
    return {
        "items": [
            {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "company_id": str(user.company_id) if user.company_id else None,
                "membership_type": membership.membership_type,
            }
            for user, membership in rows
        ],
        "total": len(rows),
    }


@admin_router.get("/tasks/{task_id}/evidence")
async def admin_list_task_evidence(task_id: uuid.UUID, db: DB, admin: CurrentUser):
    task = await db.get(FieldTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_field_ops_admin(db, admin, workspace_id=await _task_workspace_id(db, task))
    items = list(
        (
            await db.execute(
                select(TaskEvidence)
                .where(TaskEvidence.field_task_id == task_id)
                .order_by(TaskEvidence.created_at.desc())
            )
        ).scalars()
    )
    return {"items": [TaskEvidenceRead.model_validate(item) for item in items], "total": len(items)}


@partner_router.get("/work-packages")
async def partner_list_work_packages(db: DB, user: ServicePartnerUser):
    company_id = await _partner_company_id(db, user)
    packages = await list_work_packages(db, partner_company_id=company_id, limit=100)
    items = []
    for package in packages:
        try:
            await _require_partner_work_package_access(
                db,
                user,
                workspace_id=package.workspace_id,
                partner_company_id=package.partner_company_id,
            )
            items.append(WorkPackageRead.model_validate(package))
        except HTTPException:
            continue
    return {"items": items, "total": len(items)}


@partner_router.get("/work-packages/{package_id}")
async def partner_get_work_package(package_id: uuid.UUID, db: DB, user: ServicePartnerUser):
    return await _package_detail(db, await _partner_package(db, user, package_id))


@partner_router.get("/crews")
async def partner_list_crews(db: DB, user: ServicePartnerUser):
    company_id = await _partner_company_id(db, user)
    memberships = list(
        (
            await db.execute(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.user_id == user.id,
                    WorkspaceMembership.status == "active",
                )
            )
        ).scalars()
    )
    workspace_ids = [membership.workspace_id for membership in memberships]
    items = list(
        (
            await db.execute(
                select(PartnerCrew)
                .where(
                    PartnerCrew.partner_company_id == company_id,
                    PartnerCrew.workspace_id.in_(workspace_ids),
                )
                .order_by(PartnerCrew.name.asc())
            )
        ).scalars()
    ) if workspace_ids else []
    allowed = []
    for crew in items:
        try:
            await _require_partner_work_package_access(
                db,
                user,
                workspace_id=crew.workspace_id,
                partner_company_id=crew.partner_company_id,
            )
            allowed.append(crew)
        except HTTPException:
            continue
    return {"items": [PartnerCrewRead.model_validate(item) for item in allowed], "total": len(allowed)}


@partner_router.post("/crews", response_model=PartnerCrewRead, status_code=201)
async def partner_create_crew(data: PartnerCrewCreate, db: DB, user: ServicePartnerUser):
    company_id = await _require_partner_work_package_access(
        db,
        user,
        workspace_id=data.workspace_id,
        partner_company_id=await _partner_company_id(db, user),
    )
    row = await create_crew(
        db,
        **{**data.model_dump(), "partner_company_id": company_id},
    )
    await db.commit()
    await db.refresh(row)
    return PartnerCrewRead.model_validate(row)


@partner_router.get("/workers")
async def partner_list_workers(db: DB, user: ServicePartnerUser):
    company_id = await _partner_company_id(db, user)
    rows = (
        await db.execute(
            select(User, WorkspaceMembership)
            .join(WorkspaceMembership, WorkspaceMembership.user_id == User.id)
            .where(
                User.company_id == company_id,
                WorkspaceMembership.status == "active",
                WorkspaceMembership.membership_type.in_(("field_worker", "crew_lead")),
            )
            .order_by(User.full_name.asc().nullslast(), User.email.asc())
        )
    ).all()
    items = []
    for worker, membership in rows:
        try:
            await _require_partner_work_package_access(
                db,
                user,
                workspace_id=membership.workspace_id,
                partner_company_id=company_id,
            )
            items.append(
                {
                    "id": str(worker.id),
                    "full_name": worker.full_name,
                    "email": worker.email,
                    "role": worker.role,
                    "workspace_id": str(membership.workspace_id),
                    "membership_type": membership.membership_type,
                }
            )
        except HTTPException:
            continue
    return {"items": items, "total": len(items)}


@partner_router.post("/crews/{crew_id}/members", response_model=CrewMembershipRead)
async def partner_add_crew_member(
    crew_id: uuid.UUID, data: CrewMembershipCreate, db: DB, user: ServicePartnerUser
):
    crew = await db.get(PartnerCrew, crew_id)
    if crew is None:
        raise HTTPException(status_code=404, detail="Partner crew not found")
    company_id = await _require_partner_work_package_access(
        db,
        user,
        workspace_id=crew.workspace_id,
        partner_company_id=crew.partner_company_id,
    )
    worker = await db.get(User, data.user_id)
    if worker is None or worker.company_id != company_id:
        raise HTTPException(status_code=404, detail="Partner worker not found")
    membership = (
        await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == crew.workspace_id,
                WorkspaceMembership.user_id == worker.id,
                WorkspaceMembership.status == "active",
            )
        )
    ).scalars().first()
    if membership is None:
        raise HTTPException(status_code=409, detail="Worker is not active in the crew workspace")
    row = await add_crew_member(
        db,
        crew_id=crew_id,
        user_id=worker.id,
        role_in_crew=data.role_in_crew,
    )
    if data.role_in_crew in ("lead", "supervisor"):
        await ensure_membership(
            db,
            user_id=worker.id,
            membership_type="crew_lead",
            workspace_id=crew.workspace_id,
            company_id=worker.company_id,
        )
        await ensure_grant(
            db,
            user_id=worker.id,
            grant_key="crew.task.manage",
            workspace_id=crew.workspace_id,
            portal_key="crew_lead_h5",
        )
    await db.commit()
    return CrewMembershipRead.model_validate(row)


@partner_router.post("/tasks/{task_id}/assignments", response_model=TaskAssignmentRead, status_code=201)
async def partner_assign_task(
    task_id: uuid.UUID, data: TaskAssignmentCreate, db: DB, user: ServicePartnerUser
):
    task, package = await _partner_task(db, user, task_id)
    company_id = await _partner_company_id(db, user)
    worker = await db.get(User, data.assignee_user_id)
    if worker is None or worker.company_id != company_id:
        raise HTTPException(status_code=404, detail="Partner worker not found")
    membership = (
        await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == package.workspace_id,
                WorkspaceMembership.user_id == worker.id,
                WorkspaceMembership.status == "active",
            )
        )
    ).scalars().first()
    if membership is None:
        raise HTTPException(status_code=409, detail="Worker is not active in the task workspace")
    if data.crew_id is not None:
        crew = await db.get(PartnerCrew, data.crew_id)
        if (
            crew is None
            or crew.workspace_id != package.workspace_id
            or crew.partner_company_id != company_id
        ):
            raise HTTPException(status_code=404, detail="Partner crew not found")
    row = await assign_task(
        db,
        field_task_id=task.id,
        assignee_user_id=worker.id,
        assigned_by=user.id,
        crew_id=data.crew_id,
    )
    await db.commit()
    await db.refresh(row)
    return TaskAssignmentRead.model_validate(row)


@partner_router.get("/tasks/{task_id}/evidence")
async def partner_list_task_evidence(task_id: uuid.UUID, db: DB, user: ServicePartnerUser):
    await _partner_task(db, user, task_id)
    items = list(
        (
            await db.execute(
                select(TaskEvidence)
                .where(TaskEvidence.field_task_id == task_id)
                .order_by(TaskEvidence.created_at.desc())
            )
        ).scalars()
    )
    return {"items": [TaskEvidenceRead.model_validate(item) for item in items], "total": len(items)}


@crew_router.get("")
async def crew_lead_dashboard(db: DB, user: CurrentUser):
    crews = await _led_crews(db, user)
    crew_ids = [crew.id for crew in crews]
    task_rows = (
        await db.execute(
            select(FieldTask.status, func.count())
            .join(TaskAssignment, TaskAssignment.field_task_id == FieldTask.id)
            .where(TaskAssignment.crew_id.in_(crew_ids), TaskAssignment.status == "active")
            .group_by(FieldTask.status)
        )
    ).all() if crew_ids else []
    member_total = (
        await db.execute(
            select(func.count())
            .select_from(CrewMembership)
            .where(CrewMembership.crew_id.in_(crew_ids), CrewMembership.status == "active")
        )
    ).scalar() if crew_ids else 0
    counts = dict(task_rows)
    return {
        "crews": [PartnerCrewRead.model_validate(crew) for crew in crews],
        "counts": {
            "crews": len(crews),
            "members": member_total or 0,
            "open_tasks": sum(value for key, value in counts.items() if key != "done"),
            "blocked_tasks": counts.get("blocked", 0),
            "done_tasks": counts.get("done", 0),
        },
    }


@crew_router.get("/tasks")
async def crew_lead_tasks(db: DB, user: CurrentUser):
    crews = await _led_crews(db, user)
    crew_ids = [crew.id for crew in crews]
    if not crew_ids:
        return {"items": [], "total": 0}
    rows = (
        await db.execute(
            select(FieldTask, WorkPackage, PartnerCrew)
            .join(TaskAssignment, TaskAssignment.field_task_id == FieldTask.id)
            .join(PartnerCrew, PartnerCrew.id == TaskAssignment.crew_id)
            .join(WorkPackage, WorkPackage.id == FieldTask.work_package_id)
            .where(TaskAssignment.crew_id.in_(crew_ids), TaskAssignment.status == "active")
            .order_by(FieldTask.schedule_start.asc().nullslast())
        )
    ).all()
    unique: dict[uuid.UUID, dict] = {}
    for task, package, crew in rows:
        unique[task.id] = {
            **FieldTaskRead.model_validate(task).model_dump(mode="json"),
            "work_package_title": package.title,
            "crew_id": str(crew.id),
            "crew_name": crew.name,
        }
    return {"items": list(unique.values()), "total": len(unique)}


@crew_router.get("/tasks/{task_id}")
async def crew_lead_task_detail(task_id: uuid.UUID, db: DB, user: CurrentUser):
    task, package, assignment = await _crew_lead_task(db, user, task_id)
    members = (
        await db.execute(
            select(User, CrewMembership)
            .join(CrewMembership, CrewMembership.user_id == User.id)
            .where(CrewMembership.crew_id == assignment.crew_id, CrewMembership.status == "active")
            .order_by(User.full_name.asc().nullslast(), User.email.asc())
        )
    ).all()
    evidence = list(
        (
            await db.execute(
                select(TaskEvidence)
                .where(TaskEvidence.field_task_id == task.id)
                .order_by(TaskEvidence.created_at.desc())
            )
        ).scalars()
    )
    return {
        **FieldTaskRead.model_validate(task).model_dump(mode="json"),
        "work_package": WorkPackageRead.model_validate(package).model_dump(mode="json"),
        "crew_id": str(assignment.crew_id),
        "members": [
            {
                "id": str(member.id),
                "full_name": member.full_name,
                "email": member.email,
                "role_in_crew": membership.role_in_crew,
            }
            for member, membership in members
        ],
        "evidence": [TaskEvidenceRead.model_validate(item).model_dump(mode="json") for item in evidence],
    }


@crew_router.patch("/tasks/{task_id}/status", response_model=FieldTaskRead)
async def crew_lead_update_task_status(
    task_id: uuid.UUID, data: CrewTaskStatusUpdate, db: DB, user: CurrentUser
):
    task, _, _ = await _crew_lead_task(db, user, task_id)
    try:
        await update_task_status(db, task=task, new_status=data.status, client_version=data.offline_version)
        await db.commit()
        await db.refresh(task)
        return FieldTaskRead.model_validate(task)
    except FieldServiceError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@crew_router.post("/tasks/{task_id}/exceptions", response_model=TaskEvidenceRead)
async def crew_lead_report_exception(
    task_id: uuid.UUID, data: CrewTaskAction, db: DB, user: CurrentUser
):
    task, _, _ = await _crew_lead_task(db, user, task_id)
    return await _record_crew_action(db, user, task, "exception", data)


@crew_router.post("/tasks/{task_id}/handover", response_model=TaskEvidenceRead)
async def crew_lead_submit_handover(
    task_id: uuid.UUID, data: CrewTaskAction, db: DB, user: CurrentUser
):
    task, _, _ = await _crew_lead_task(db, user, task_id)
    return await _record_crew_action(db, user, task, "handover", data)


@crew_router.post("/tasks/{task_id}/completion", response_model=TaskEvidenceRead)
async def crew_lead_submit_completion(
    task_id: uuid.UUID, data: CrewTaskAction, db: DB, user: CurrentUser
):
    task, _, _ = await _crew_lead_task(db, user, task_id)
    evidence = await _record_crew_action(db, user, task, "crew_completion", data)
    if task.status != "done":
        await update_task_status(
            db,
            task=task,
            new_status="done",
            client_version=task.offline_version,
        )
        await db.commit()
    return evidence


@crew_router.get("/members")
async def crew_lead_members(db: DB, user: CurrentUser):
    crews = await _led_crews(db, user)
    crew_ids = [crew.id for crew in crews]
    rows = (
        await db.execute(
            select(User, CrewMembership, PartnerCrew)
            .join(CrewMembership, CrewMembership.user_id == User.id)
            .join(PartnerCrew, PartnerCrew.id == CrewMembership.crew_id)
            .where(CrewMembership.crew_id.in_(crew_ids), CrewMembership.status == "active")
            .order_by(PartnerCrew.name.asc(), User.full_name.asc().nullslast(), User.email.asc())
        )
    ).all() if crew_ids else []
    return {
        "items": [
            {
                "id": str(member.id),
                "full_name": member.full_name,
                "email": member.email,
                "crew_id": str(crew.id),
                "crew_name": crew.name,
                "role_in_crew": membership.role_in_crew,
            }
            for member, membership, crew in rows
        ],
        "total": len(rows),
    }


@supplier_router.get("/dashboard")
async def supplier_dashboard(db: DB, user: CurrentUser):
    if not await user_has_grant_in_any_workspace(
        db, user.id, "supplier.rfq.read", portal_key="supplier"
    ):
        raise HTTPException(status_code=403, detail="Supplier grant required")
    return {
        "portal_key": "supplier",
        "capabilities": ["rfq", "quotes", "catalog", "orders"],
        "message": "Supplier H5 portal — RFQ and catalog modules",
    }

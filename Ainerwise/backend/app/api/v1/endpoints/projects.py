import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DB, ProjectOpsUser
from app.core.permissions import UserRole
from app.crud.project import crud_project
from app.models.lifecycle import MaintenanceSchedule
from app.models.service import ServicePartner
from app.schemas.project import (
    ProjectCreate,
    ProjectCustomerRead,
    ProjectRead,
    ProjectStatusUpdate,
    ProjectUpdate,
)
from app.services.audit import log_action
from app.services.partner_dispatch import dispatch_partner_task, partner_task_dict
from app.services.portal_access import list_memberships
from app.services.project_access import (
    project_operator_workspace_ids,
    require_customer_project_access,
    require_project_operator_access,
    resolve_project_workspace,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/my")
async def list_my_projects(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    from app.models.project import Project

    filters = []
    if current_user.company_id:
        filters.append(Project.buyer_company_id == current_user.company_id)
        memberships = await list_memberships(db, current_user.id)
        workspace_ids = {
            membership.workspace_id
            for membership in memberships
            if membership.company_id == current_user.company_id
        }
        filters.append(
            Project.workspace_id.in_(workspace_ids)
            if workspace_ids
            else Project.workspace_id.is_(None)
        )
    else:
        return {"items": [], "total": 0}
    items, total = await crud_project.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [ProjectCustomerRead.model_validate(i) for i in items], "total": total}


@router.get("")
async def list_projects(
    db: DB,
    admin: ProjectOpsUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    workspace_id: uuid.UUID | None = Query(None),
):
    from app.models.project import Project

    filters = []
    accessible_workspace_ids = await project_operator_workspace_ids(db, admin)
    if accessible_workspace_ids is not None:
        if workspace_id is not None and workspace_id not in accessible_workspace_ids:
            raise HTTPException(status_code=403, detail="Project Workspace access required")
        filters.append(
            Project.workspace_id == workspace_id
            if workspace_id is not None
            else Project.workspace_id.in_(accessible_workspace_ids)
        )
    elif workspace_id is not None:
        filters.append(Project.workspace_id == workspace_id)
    if status_filter:
        filters.append(Project.status == status_filter)
    items, total = await crud_project.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [ProjectRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=None)
async def get_project(id: uuid.UUID, db: DB, current_user: CurrentUser):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    is_project_operator = current_user.role in {
        UserRole.SUPER_ADMIN.value,
        UserRole.ADMIN.value,
        UserRole.PROJECT_MANAGER.value,
    }
    is_owning_customer = (
        current_user.company_id is not None
        and project.buyer_company_id is not None
        and project.buyer_company_id == current_user.company_id
    )
    if not is_project_operator and not is_owning_customer:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if is_project_operator:
        await require_project_operator_access(db, current_user, project)
        return ProjectRead.model_validate(project)
    await require_customer_project_access(db, current_user, project)
    return ProjectCustomerRead.model_validate(project)


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(data: ProjectCreate, db: DB, admin: ProjectOpsUser):
    obj = data.model_dump()
    obj["workspace_id"] = await resolve_project_workspace(db, admin, data.workspace_id)
    obj["status"] = "planning"
    return await crud_project.create(db, obj_in=obj)


@router.put("/{id}", response_model=ProjectRead)
async def update_project(id: uuid.UUID, data: ProjectUpdate, db: DB, admin: ProjectOpsUser):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    return await crud_project.update(db, db_obj=project, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=ProjectRead)
async def update_project_status(id: uuid.UUID, data: ProjectStatusUpdate, db: DB, admin: ProjectOpsUser):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    old_status = project.status
    result = await crud_project.update(db, db_obj=project, obj_in={"status": data.status})
    await log_action(
        db, actor_user_id=admin.id, action="status_change",
        entity_type="project", entity_id=id,
        before={"status": old_status}, after={"status": data.status},
    )
    return result


@router.patch("/{id}/notes", response_model=ProjectRead)
async def update_project_notes(id: uuid.UUID, data: dict, db: DB, admin: ProjectOpsUser):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    return await crud_project.update(db, db_obj=project, obj_in={"notes": data.get("notes", "")})


class AssignPartnerRequest(BaseModel):
    partner_id: uuid.UUID
    role: str = "installer"


@router.post("/{id}/assign-partner", response_model=ProjectRead)
async def assign_partner_to_project(
    id: uuid.UUID, data: AssignPartnerRequest, db: DB, admin: ProjectOpsUser
):
    """Add a service partner to the project's team_json list."""
    from app.crud.service_partner import crud_service_partner

    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    partner = await crud_service_partner.get(db, data.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Service partner not found")
    if partner.verification_status != "verified":
        raise HTTPException(status_code=400, detail="Only verified partners can be assigned")

    team = list(project.team_json or [])
    # Avoid duplicate assignment
    if any(m.get("partner_id") == str(data.partner_id) for m in team):
        raise HTTPException(status_code=400, detail="Partner already assigned to this project")

    team.append({
        "partner_id": str(partner.id),
        "partner_type": partner.partner_type,
        "name": f"{partner.partner_type} ({partner.city or partner.country or 'remote'})",
        "role": data.role,
        "skills": partner.skills_json or [],
    })
    result = await crud_project.update(db, db_obj=project, obj_in={"team_json": team})
    await log_action(
        db, actor_user_id=admin.id, action="assign_partner",
        entity_type="project", entity_id=id,
        after={"partner_id": str(partner.id), "role": data.role},
    )
    return result


@router.delete("/{id}/team/{partner_id}", response_model=ProjectRead)
async def remove_partner_from_project(
    id: uuid.UUID, partner_id: uuid.UUID, db: DB, admin: ProjectOpsUser
):
    """Remove a service partner from the project team."""
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)

    team = list(project.team_json or [])
    new_team = [m for m in team if m.get("partner_id") != str(partner_id)]
    if len(new_team) == len(team):
        raise HTTPException(status_code=404, detail="Partner not found in project team")

    return await crud_project.update(db, db_obj=project, obj_in={"team_json": new_team})


class DispatchPartnerTaskRequest(BaseModel):
    partner_id: uuid.UUID
    task_type: str = Field(min_length=1, max_length=50)
    due_date: date | None = None
    device_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    covered_by_amc: bool = False


@router.get("/{id}/dispatches")
async def list_project_dispatches(id: uuid.UUID, db: DB, admin: ProjectOpsUser):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    tasks = (
        await db.execute(
            select(MaintenanceSchedule)
            .where(MaintenanceSchedule.project_id == id, MaintenanceSchedule.assigned_to.is_not(None))
            .order_by(MaintenanceSchedule.due_date.asc().nullslast(), MaintenanceSchedule.created_at.desc())
        )
    ).scalars().all()
    return {"items": [partner_task_dict(task, project) for task in tasks], "total": len(tasks)}


@router.post("/{id}/dispatch", status_code=201)
async def dispatch_project_task(
    id: uuid.UUID,
    data: DispatchPartnerTaskRequest,
    db: DB,
    admin: ProjectOpsUser,
):
    project = await crud_project.get(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_operator_access(db, admin, project)
    partner = await db.get(ServicePartner, data.partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Service partner not found")
    if partner.verification_status != "verified":
        raise HTTPException(status_code=400, detail="Only verified partners can receive tasks")
    if not any(m.get("partner_id") == str(partner.id) for m in (project.team_json or [])):
        raise HTTPException(status_code=400, detail="Partner must be assigned to the project before dispatch")
    try:
        task = await dispatch_partner_task(
            db,
            project=project,
            partner=partner,
            task_type=data.task_type,
            due_date=data.due_date,
            device_name=data.device_name,
            notes=data.notes,
            covered_by_amc=data.covered_by_amc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    await log_action(
        db,
        actor_user_id=admin.id,
        action="dispatch_partner_task",
        entity_type="project",
        entity_id=project.id,
        after={"partner_id": str(partner.id), "task_id": str(task.id), "task_type": task.task_type},
    )
    await db.commit()
    await db.refresh(task)
    return partner_task_dict(task, project)


class CreateProjectFromLeadRequest(BaseModel):
    title: str | None = None


@router.post("/from-lead/{lead_id}", response_model=ProjectRead, status_code=201)
async def create_project_from_lead(
    lead_id: uuid.UUID,
    data: CreateProjectFromLeadRequest,
    db: DB,
    admin: ProjectOpsUser,
):
    """Create a project directly from a lead, pre-populating fields."""
    from app.crud.lead import crud_lead

    lead = await crud_lead.get(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    title = data.title or f"{lead.project_type or 'Project'} - {lead.contact_name or lead.contact_email or 'Unknown'}"
    obj = {
        "workspace_id": await resolve_project_workspace(db, admin, lead.workspace_id),
        "lead_id": lead.id,
        "buyer_company_id": lead.buyer_company_id,
        "title": title,
        "region": lead.country,
        "status": "planning",
        "notes": f"Created from lead {str(lead.id)[:8]}. {lead.description or ''}".strip(),
    }
    project = await crud_project.create(db, obj_in=obj)
    await log_action(
        db, actor_user_id=admin.id, action="create_from_lead",
        entity_type="project", entity_id=project.id,
        after={"lead_id": str(lead.id)},
    )
    return project

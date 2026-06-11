"""Phase H Project Space and structured Agent Mission endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.models.agent import Agent, AgentObjectGrant
from app.models.audit import AuditLog
from app.models.content import DesignRevision
from app.models.file import FileAsset
from app.models.mission import AgentMission, AgentMissionTask
from app.models.project import Project
from app.models.ticket import Ticket
from app.services.agent_team import approve_mission_plan, plan_mission, run_mission

router = APIRouter(tags=["agent-missions"])


class MissionCreate(BaseModel):
    goal: str = Field(min_length=10, max_length=3000)
    context_json: dict | None = None


class ObjectGrantUpdate(BaseModel):
    agent_slug: str
    granted: bool


async def _owned_project(db, project_id: uuid.UUID, user) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not user.company_id or project.buyer_company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Not your project")
    return project


def _mission_dict(mission: AgentMission, *, internal: bool = False) -> dict:
    data = {
        "id": str(mission.id),
        "project_id": str(mission.project_id),
        "goal": mission.goal,
        "status": mission.status,
        "agents": mission.agent_slugs_json or [],
        "created_at": mission.created_at.isoformat(),
        "updated_at": mission.updated_at.isoformat(),
    }
    if mission.status == "completed":
        data["final_report"] = mission.final_report_json
    if internal:
        data.update(
            {
                "context_json": mission.context_json,
                "plan_json": mission.plan_json,
                "final_report_json": mission.final_report_json,
                "review_id": str(mission.review_id) if mission.review_id else None,
            }
        )
    return data


def _task_dict(task: AgentMissionTask, *, internal: bool = False) -> dict:
    data = {
        "id": str(task.id),
        "mission_id": str(task.mission_id),
        "agent_slug": task.agent_slug,
        "sequence": task.sequence,
        "title": task.title,
        "status": task.status,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
    if internal:
        data["instructions"] = task.instructions
        data["output_json"] = task.output_json
        data["run_id"] = str(task.run_id) if task.run_id else None
    return data


@router.post("/portal/projects/{project_id}/missions", status_code=201)
async def request_project_mission(
    project_id: uuid.UUID,
    data: MissionCreate,
    db: DB,
    user: CurrentUser,
):
    await _owned_project(db, project_id, user)
    mission = AgentMission(
        project_id=project_id,
        requested_by=user.id,
        goal=data.goal.strip(),
        context_json=data.context_json,
        status="requested",
    )
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    return _mission_dict(mission)


@router.get("/portal/projects/{project_id}/space")
async def project_space(project_id: uuid.UUID, db: DB, user: CurrentUser):
    project = await _owned_project(db, project_id, user)
    missions = (
        await db.execute(
            select(AgentMission).where(AgentMission.project_id == project_id).order_by(AgentMission.created_at.desc())
        )
    ).scalars().all()
    mission_ids = [m.id for m in missions]
    tasks = []
    if mission_ids:
        tasks = (
            await db.execute(
                select(AgentMissionTask)
                .where(AgentMissionTask.mission_id.in_(mission_ids))
                .order_by(AgentMissionTask.created_at.desc())
            )
        ).scalars().all()

    grants = (
        await db.execute(
            select(AgentObjectGrant, Agent)
            .join(Agent, Agent.id == AgentObjectGrant.agent_id)
            .where(
                AgentObjectGrant.object_type == "project",
                AgentObjectGrant.object_id == project_id,
                AgentObjectGrant.scope == "project_data",
                AgentObjectGrant.granted.is_(True),
            )
            .order_by(Agent.name)
        )
    ).all()

    file_rows = (
        await db.execute(
            select(FileAsset)
            .where(FileAsset.entity_type == "project", FileAsset.entity_id == project_id)
            .order_by(FileAsset.created_at.desc())
        )
    ).scalars().all()
    designs = (
        await db.execute(
            select(DesignRevision).where(DesignRevision.project_id == project_id).order_by(DesignRevision.created_at.desc())
        )
    ).scalars().all()
    tickets = (
        await db.execute(select(Ticket).where(Ticket.project_id == project_id).order_by(Ticket.created_at.desc()).limit(20))
    ).scalars().all()

    timeline = [
        {
            "type": "project",
            "title": f"Project created: {project.title}",
            "status": project.status,
            "created_at": project.created_at.isoformat(),
        }
    ]
    timeline.extend(
        {
            "type": "mission",
            "title": mission.goal,
            "status": mission.status,
            "created_at": mission.created_at.isoformat(),
        }
        for mission in missions
    )
    timeline.extend(
        {
            "type": "ticket",
            "title": ticket.title,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
        }
        for ticket in tickets
    )
    timeline.sort(key=lambda item: item["created_at"], reverse=True)

    return {
        "agents": [
            {"slug": agent.slug, "name": agent.name, "role_title": agent.role_title, "status": agent.status}
            for _, agent in grants
        ],
        "missions": [_mission_dict(m) for m in missions],
        "tasks": [_task_dict(t) for t in tasks],
        "files": [
            {
                "id": str(f.id),
                "name": f.original_name,
                "kind": f.file_type or f.mime_type,
                "created_at": f.created_at.isoformat(),
            }
            for f in file_rows
        ]
        + [
            {
                "id": str(d.id),
                "name": d.title,
                "kind": d.file_kind or "design",
                "version": d.version,
                "created_at": d.created_at.isoformat(),
            }
            for d in designs
        ],
        "timeline": timeline[:50],
    }


@router.get("/admin/agent-missions")
async def list_agent_missions(
    db: DB,
    admin: AdminUser,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    query = select(AgentMission)
    if status:
        query = query.where(AgentMission.status == status)
    query = query.order_by(AgentMission.created_at.desc()).limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return {"items": [_mission_dict(m, internal=True) for m in rows], "total": len(rows)}


@router.get("/admin/agent-missions/{mission_id}")
async def get_agent_mission(mission_id: uuid.UUID, db: DB, admin: AdminUser):
    mission = await db.get(AgentMission, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    tasks = (
        await db.execute(
            select(AgentMissionTask)
            .where(AgentMissionTask.mission_id == mission_id)
            .order_by(AgentMissionTask.sequence)
        )
    ).scalars().all()
    return {**_mission_dict(mission, internal=True), "tasks": [_task_dict(t, internal=True) for t in tasks]}


@router.post("/admin/agent-missions/{mission_id}/plan")
async def create_mission_plan(mission_id: uuid.UUID, db: DB, admin: AdminUser):
    mission = await db.get(AgentMission, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        await plan_mission(db, mission)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(mission)
    return _mission_dict(mission, internal=True)


@router.post("/admin/agent-missions/{mission_id}/approve-plan")
async def approve_plan(mission_id: uuid.UUID, db: DB, admin: AdminUser):
    mission = await db.get(AgentMission, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        await approve_mission_plan(db, mission, admin_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(mission)
    return _mission_dict(mission, internal=True)


@router.post("/admin/agent-missions/{mission_id}/run")
async def execute_mission(mission_id: uuid.UUID, db: DB, admin: AdminUser):
    mission = await db.get(AgentMission, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        await run_mission(db, mission)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(mission)
    return _mission_dict(mission, internal=True)


@router.get("/admin/projects/{project_id}/agent-grants")
async def list_project_agent_grants(project_id: uuid.UUID, db: DB, admin: AdminUser):
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    agents = (await db.execute(select(Agent).order_by(Agent.name))).scalars().all()
    grants = (
        await db.execute(
            select(AgentObjectGrant).where(
                AgentObjectGrant.object_type == "project",
                AgentObjectGrant.object_id == project_id,
                AgentObjectGrant.scope == "project_data",
            )
        )
    ).scalars().all()
    values = {g.agent_id: g for g in grants}
    return {
        "items": [
            {
                "agent_slug": agent.slug,
                "name": agent.name,
                "status": agent.status,
                "granted": bool(values.get(agent.id) and values[agent.id].granted),
            }
            for agent in agents
        ]
    }


@router.post("/admin/projects/{project_id}/agent-grants")
async def update_project_agent_grant(
    project_id: uuid.UUID,
    data: ObjectGrantUpdate,
    db: DB,
    admin: AdminUser,
):
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    agent = (await db.execute(select(Agent).where(Agent.slug == data.agent_slug))).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    grant = (
        await db.execute(
            select(AgentObjectGrant).where(
                AgentObjectGrant.agent_id == agent.id,
                AgentObjectGrant.object_type == "project",
                AgentObjectGrant.object_id == project_id,
                AgentObjectGrant.scope == "project_data",
            )
        )
    ).scalar_one_or_none()
    if grant is None:
        grant = AgentObjectGrant(
            agent_id=agent.id,
            object_type="project",
            object_id=project_id,
            scope="project_data",
        )
    before = grant.granted
    grant.granted = data.granted
    grant.granted_by = admin.id
    grant.granted_at = datetime.now(timezone.utc) if data.granted else None
    db.add(grant)
    await db.flush()
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="agent_object_grant_update",
            entity_type="agent_object_grant",
            entity_id=grant.id,
            before_json={"granted": before, "scope": "project_data"},
            after_json={
                "granted": grant.granted,
                "scope": "project_data",
                "agent_slug": agent.slug,
                "object_type": "project",
                "object_id": str(project_id),
            },
        )
    )
    await db.commit()
    return {"agent_slug": agent.slug, "project_id": str(project_id), "granted": grant.granted}

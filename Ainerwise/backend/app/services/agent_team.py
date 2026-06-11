"""Structured Phase H Agent Team: Mission -> Tasks -> Workers -> Review."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentObjectGrant
from app.models.ai import AgentRun, AIReview
from app.models.audit import AuditLog
from app.models.file import FileAsset
from app.models.lifecycle import MaintenanceSchedule, MonitoringPoint
from app.models.mission import AgentMission, AgentMissionTask
from app.models.project import Project
from app.models.ticket import Ticket
from app.services.agent_runtime import require_agent


def _selected_agents(goal: str) -> list[str]:
    text = goal.lower()
    selected = ["business-brain"]
    rules = {
        "sales-agent": ("sales", "quote", "customer", "proposal", "预算", "报价", "客户"),
        "procurement-agent": ("partner", "supplier", "procure", "install", "采购", "伙伴", "安装"),
        "support-agent": ("support", "ticket", "maintenance", "fault", "运维", "工单", "故障"),
        "marketing-agent": ("marketing", "campaign", "content", "case study", "营销", "内容", "案例"),
    }
    for slug, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            selected.append(slug)
    if len(selected) == 1:
        selected.extend(["sales-agent", "procurement-agent", "support-agent"])
    return selected


TASK_TEMPLATES = {
    "business-brain": (
        "Project goal and risk review",
        "Summarize the current project state, risks, approvals and next decisions.",
    ),
    "sales-agent": (
        "Customer outcome and scope review",
        "Translate the goal into customer outcomes and identify missing commercial decisions.",
    ),
    "procurement-agent": (
        "Partner and delivery readiness review",
        "Review assigned partners, delivery readiness and procurement dependencies.",
    ),
    "support-agent": (
        "Support and lifecycle readiness review",
        "Review tickets, monitoring health and due maintenance without promising coverage.",
    ),
    "marketing-agent": (
        "Approved-story readiness review",
        "Assess whether the project can become a privacy-safe case study after customer approval.",
    ),
}


async def plan_mission(db: AsyncSession, mission: AgentMission) -> AgentMission:
    if mission.status not in ("requested", "plan_rejected"):
        raise ValueError(f"Mission cannot be planned from status {mission.status}")
    selected = _selected_agents(mission.goal)
    await db.execute(delete(AgentMissionTask).where(AgentMissionTask.mission_id == mission.id))
    tasks = []
    for sequence, slug in enumerate(selected, start=1):
        title, instructions = TASK_TEMPLATES[slug]
        task = AgentMissionTask(
            mission_id=mission.id,
            project_id=mission.project_id,
            agent_slug=slug,
            sequence=sequence,
            title=title,
            instructions=instructions,
            status="queued",
        )
        db.add(task)
        tasks.append({"sequence": sequence, "agent_slug": slug, "title": title, "instructions": instructions})
    mission.agent_slugs_json = selected
    mission.plan_json = {
        "goal": mission.goal,
        "flow": "Manager -> Workers -> Reviewer -> Final Report",
        "tasks": tasks,
        "human_gate": "Admin approval grants selected Agents access to this project only.",
    }
    review = AIReview(
        target_type="mission_plan",
        target_id=mission.id,
        draft_json=mission.plan_json,
        status="preliminary",
    )
    db.add(review)
    await db.flush()
    mission.review_id = review.id
    mission.status = "plan_review"
    db.add(mission)
    return mission


async def approve_mission_plan(
    db: AsyncSession,
    mission: AgentMission,
    *,
    admin_id: uuid.UUID,
) -> AgentMission:
    if mission.status != "plan_review":
        raise ValueError(f"Mission plan cannot be approved from status {mission.status}")
    review = await db.get(AIReview, mission.review_id) if mission.review_id else None
    if review is None or review.status != "preliminary":
        raise ValueError("Mission plan review is missing or already decided")
    review.status = "approved"
    review.reviewed_by = admin_id
    review.reviewed_at = datetime.now(timezone.utc)
    db.add(review)

    for slug in mission.agent_slugs_json or []:
        agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one()
        grant = (
            await db.execute(
                select(AgentObjectGrant).where(
                    AgentObjectGrant.agent_id == agent.id,
                    AgentObjectGrant.object_type == "project",
                    AgentObjectGrant.object_id == mission.project_id,
                    AgentObjectGrant.scope == "project_data",
                )
            )
        ).scalar_one_or_none()
        if grant is None:
            grant = AgentObjectGrant(
                agent_id=agent.id,
                object_type="project",
                object_id=mission.project_id,
                scope="project_data",
            )
        before = grant.granted
        grant.granted = True
        grant.granted_by = admin_id
        grant.granted_at = datetime.now(timezone.utc)
        db.add(grant)
        await db.flush()
        db.add(
            AuditLog(
                actor_user_id=admin_id,
                action="agent_object_grant_update",
                entity_type="agent_object_grant",
                entity_id=grant.id,
                before_json={"granted": before, "scope": "project_data"},
                after_json={
                    "granted": True,
                    "scope": "project_data",
                    "agent_slug": slug,
                    "object_type": "project",
                    "object_id": str(mission.project_id),
                },
            )
        )
    mission.status = "approved"
    mission.approved_by = admin_id
    mission.approved_at = datetime.now(timezone.utc)
    db.add(mission)
    return mission


async def _project_snapshot(db: AsyncSession, project: Project) -> dict:
    async def count(model, *where) -> int:
        return int((await db.execute(select(func.count()).select_from(model).where(*where))).scalar() or 0)

    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "status": project.status,
            "region": project.region,
            "expected_delivery_date": (
                project.expected_delivery_date.isoformat() if project.expected_delivery_date else None
            ),
        },
        "assigned_human_partners": len(project.team_json or []),
        "open_tickets": await count(Ticket, Ticket.project_id == project.id, Ticket.status != "resolved"),
        "monitoring_points": await count(MonitoringPoint, MonitoringPoint.project_id == project.id),
        "fault_points": await count(
            MonitoringPoint, MonitoringPoint.project_id == project.id, MonitoringPoint.status == "fault"
        ),
        "due_tasks": await count(
            MaintenanceSchedule,
            MaintenanceSchedule.project_id == project.id,
            MaintenanceSchedule.status.not_in(("done", "completed", "cancelled")),
        ),
        "files": await count(FileAsset, FileAsset.entity_type == "project", FileAsset.entity_id == project.id),
    }


def _worker_output(slug: str, goal: str, snapshot: dict) -> dict:
    project = snapshot["project"]
    common = {"agent_slug": slug, "goal": goal, "project_status": project["status"], "preliminary": True}
    if slug == "business-brain":
        return {
            **common,
            "summary": f"{project['title']} is currently {project['status']}.",
            "risks": [
                label for value, label in (
                    (snapshot["open_tickets"], f"{snapshot['open_tickets']} open support tickets"),
                    (snapshot["fault_points"], f"{snapshot['fault_points']} monitoring points in fault"),
                    (snapshot["due_tasks"], f"{snapshot['due_tasks']} open delivery/maintenance tasks"),
                ) if value
            ],
            "required_decisions": ["Confirm scope owner", "Review worker findings before external commitment"],
        }
    if slug == "sales-agent":
        return {
            **common,
            "customer_outcome": "Confirm the requested outcome, acceptance criteria and next commercial decision.",
            "missing_decisions": ["Approved scope", "Budget boundary", "Decision timeline"],
        }
    if slug == "procurement-agent":
        return {
            **common,
            "assigned_human_partners": snapshot["assigned_human_partners"],
            "delivery_readiness": "ready_for_review" if snapshot["assigned_human_partners"] else "partner_assignment_needed",
            "next_actions": ["Verify partner capacity", "Confirm procurement dependencies"],
        }
    if slug == "support-agent":
        return {
            **common,
            "open_tickets": snapshot["open_tickets"],
            "fault_points": snapshot["fault_points"],
            "due_tasks": snapshot["due_tasks"],
            "next_actions": ["Review open incidents", "Confirm coverage before promising on-site work"],
        }
    return {
        **common,
        "case_study_readiness": "needs_customer_consent",
        "available_project_files": snapshot["files"],
        "next_actions": ["Obtain customer consent", "Remove private and supplier-sensitive details"],
    }


async def run_mission(db: AsyncSession, mission: AgentMission) -> AgentMission:
    if mission.status not in ("approved", "report_rejected"):
        raise ValueError(f"Mission cannot run from status {mission.status}")
    project = await db.get(Project, mission.project_id)
    if project is None:
        raise ValueError("Project not found")
    snapshot = await _project_snapshot(db, project)
    tasks = (
        await db.execute(
            select(AgentMissionTask)
            .where(AgentMissionTask.mission_id == mission.id)
            .order_by(AgentMissionTask.sequence)
        )
    ).scalars().all()
    outputs = []
    for task in tasks:
        await require_agent(
            db,
            task.agent_slug,
            scopes=("project_data",),
            workflow="mission_task",
            object_type="project",
            object_id=mission.project_id,
        )
        output = _worker_output(task.agent_slug, mission.goal, snapshot)
        run = AgentRun(
            agent_slug=task.agent_slug,
            workflow="mission_task",
            input_json={"mission_id": str(mission.id), "project_id": str(mission.project_id), "goal": mission.goal},
            output_json=output,
            status="completed",
        )
        db.add(run)
        await db.flush()
        task.run_id = run.id
        task.output_json = output
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        db.add(task)
        outputs.append({"task_id": str(task.id), "title": task.title, **output})

    final_report = {
        "mission_id": str(mission.id),
        "project_id": str(mission.project_id),
        "goal": mission.goal,
        "worker_reports": outputs,
        "manager_summary": (
            "All assigned workers completed their structured review. "
            "Review the findings before making external commitments."
        ),
        "review_status": "preliminary_pending_human_approval",
        "reviewer_checks": {
            "all_tasks_completed": len(outputs) == len(tasks),
            "external_commitments_blocked": True,
            "human_approval_required": True,
        },
        "preliminary": True,
    }
    review = AIReview(
        target_type="mission_final_report",
        target_id=mission.id,
        draft_json=final_report,
        status="preliminary",
    )
    db.add(review)
    await db.flush()
    mission.final_report_json = final_report
    mission.review_id = review.id
    mission.status = "in_review"
    db.add(mission)
    return mission

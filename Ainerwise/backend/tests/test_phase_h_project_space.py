"""Phase H: Project Space, structured Agent Missions and project-scoped grants."""
import asyncio
import uuid

import pytest
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import Agent, AgentObjectGrant
from app.models.ai import AgentRun, AIReview
from app.models.audit import AuditLog
from app.models.mission import AgentMission, AgentMissionTask
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company, User
from app.tasks.celery_app import celery_app


def test_phase_h_routes_and_schedule_registered():
    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/portal/projects/{project_id}/missions",
        "/api/v1/portal/projects/{project_id}/space",
        "/api/v1/admin/agent-missions",
        "/api/v1/admin/agent-missions/{mission_id}/plan",
        "/api/v1/admin/agent-missions/{mission_id}/approve-plan",
        "/api/v1/admin/agent-missions/{mission_id}/run",
        "/api/v1/admin/projects/{project_id}/agent-grants",
        "/api/v1/admin/marketing/weekly-report/run",
    ):
        assert path in paths, path
    assert "generate-weekly-marketing-report" in celery_app.conf.beat_schedule
    assert celery_app.conf.task_routes["generate_weekly_marketing_report"]["queue"] == "automation"


def test_project_object_grant_is_enforced():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.agent_runtime import AgentAuthorizationError, require_agent

            project = Project(title="H object grant regression", status="planning")
            db.add(project)
            await db.flush()
            with pytest.raises(AgentAuthorizationError, match="lacks project"):
                await require_agent(
                    db,
                    "support-agent",
                    scopes=("project_data",),
                    workflow="ticket_triage",
                    object_type="project",
                    object_id=project.id,
                )
            support = (await db.execute(select(Agent).where(Agent.slug == "support-agent"))).scalar_one()
            db.add(
                AgentObjectGrant(
                    agent_id=support.id,
                    object_type="project",
                    object_id=project.id,
                    scope="project_data",
                    granted=True,
                )
            )
            await db.flush()
            authorized = await require_agent(
                db,
                "support-agent",
                scopes=("project_data",),
                workflow="ticket_triage",
                object_type="project",
                object_id=project.id,
            )
            assert authorized.slug == "support-agent"
            await db.rollback()

    asyncio.run(_run())


def test_structured_mission_plan_grant_run_and_review_gate():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.agent_team import approve_mission_plan, plan_mission, run_mission

            suffix = uuid.uuid4().hex[:10]
            company = Company(name=f"H Company {suffix}", type="buyer")
            admin = User(
                email=f"h-admin-{suffix}@test.local",
                password_hash="not-used",
                role="admin",
            )
            buyer = User(
                email=f"h-buyer-{suffix}@test.local",
                password_hash="not-used",
                role="buyer",
                company=company,
            )
            project = Project(
                title="H Mission Project",
                status="planning",
                buyer_company_id=company.id,
                team_json=[{"role": "installer"}],
            )
            db.add_all([company, admin, buyer, project])
            await db.flush()
            project.buyer_company_id = company.id
            mission = AgentMission(
                project_id=project.id,
                requested_by=buyer.id,
                goal="Review support readiness, partner installation risks and customer proposal.",
                status="requested",
            )
            db.add(mission)
            await db.flush()

            await plan_mission(db, mission)
            assert mission.status == "plan_review"
            assert {"business-brain", "sales-agent", "procurement-agent", "support-agent"} <= set(
                mission.agent_slugs_json
            )
            tasks = (
                await db.execute(select(AgentMissionTask).where(AgentMissionTask.mission_id == mission.id))
            ).scalars().all()
            assert len(tasks) == len(mission.agent_slugs_json)
            assert all(task.status == "queued" for task in tasks)

            await approve_mission_plan(db, mission, admin_id=admin.id)
            assert mission.status == "approved"
            grants = (
                await db.execute(
                    select(AgentObjectGrant).where(
                        AgentObjectGrant.object_type == "project",
                        AgentObjectGrant.object_id == project.id,
                        AgentObjectGrant.granted.is_(True),
                    )
                )
            ).scalars().all()
            assert len(grants) == len(mission.agent_slugs_json)
            audits = (
                await db.execute(
                    select(AuditLog).where(
                        AuditLog.action == "agent_object_grant_update",
                        AuditLog.actor_user_id == admin.id,
                    )
                )
            ).scalars().all()
            assert audits and all(audit.entity_id is not None for audit in audits)

            await run_mission(db, mission)
            assert mission.status == "in_review"
            assert mission.final_report_json["preliminary"] is True
            assert mission.final_report_json["reviewer_checks"]["human_approval_required"] is True
            tasks = (
                await db.execute(select(AgentMissionTask).where(AgentMissionTask.mission_id == mission.id))
            ).scalars().all()
            assert all(task.status == "completed" and task.run_id for task in tasks)
            runs = (
                await db.execute(
                    select(AgentRun).where(
                        AgentRun.workflow == "mission_task",
                        AgentRun.input_json["mission_id"].astext == str(mission.id),
                    )
                )
            ).scalars().all()
            assert {run.agent_slug for run in runs} == set(mission.agent_slugs_json)
            review = await db.get(AIReview, mission.review_id)
            assert review and review.target_type == "mission_final_report" and review.status == "preliminary"
            await db.rollback()

    asyncio.run(_run())


def test_support_triage_and_marketing_report_are_preliminary():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.marketing_reporting import generate_weekly_marketing_report
            from app.services.support_agent import create_ticket_triage

            project = Project(title="H support triage", status="maintenance")
            db.add(project)
            await db.flush()
            support = (await db.execute(select(Agent).where(Agent.slug == "support-agent"))).scalar_one()
            db.add(
                AgentObjectGrant(
                    agent_id=support.id,
                    object_type="project",
                    object_id=project.id,
                    scope="project_data",
                    granted=True,
                )
            )
            ticket = Ticket(
                project_id=project.id,
                issue_type="device_failure",
                priority="high",
                title="Gateway offline",
                status="open",
            )
            db.add(ticket)
            await db.flush()
            triage = await create_ticket_triage(db, ticket)
            assert triage and triage.target_type == "ticket_triage"
            assert triage.draft_json["preliminary"] is True
            assert "administrator" in triage.draft_json["coverage_note"]

            report_run = await generate_weekly_marketing_report(db)
            assert report_run.agent_slug == "marketing-agent"
            assert report_run.output_json["preliminary"] is True
            report_review = (
                await db.execute(
                    select(AIReview).where(
                        AIReview.run_id == report_run.id,
                        AIReview.target_type == "marketing_weekly_report",
                    )
                )
            ).scalar_one()
            assert report_review.status == "preliminary"
            await db.rollback()

    asyncio.run(_run())


def test_final_report_approval_updates_customer_visible_gate():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.api.v1.endpoints.ai_reviews import _decide

            suffix = uuid.uuid4().hex[:10]
            admin = User(
                email=f"h-review-{suffix}@test.local",
                password_hash="not-used",
                role="admin",
            )
            project = Project(title="H final review", status="planning")
            db.add_all([admin, project])
            await db.flush()
            mission = AgentMission(
                project_id=project.id,
                goal="Approve this structured final report.",
                status="in_review",
                final_report_json={
                    "preliminary": True,
                    "review_status": "preliminary_pending_human_approval",
                    "reviewer_checks": {"human_approval_required": True},
                },
            )
            db.add(mission)
            await db.flush()
            review = AIReview(
                target_type="mission_final_report",
                target_id=mission.id,
                draft_json=mission.final_report_json,
                status="preliminary",
            )
            db.add(review)
            await db.flush()
            mission.review_id = review.id
            db.add(mission)
            await db.commit()

            await _decide(db, admin, review.id, "approved", "Phase H gate regression")
            await db.refresh(mission)
            assert mission.status == "completed"
            assert mission.final_report_json["preliminary"] is False
            assert mission.final_report_json["review_status"] == "approved"
            assert mission.final_report_json["reviewer_checks"]["human_approval_required"] is False
            assert mission.final_report_json["reviewer_checks"]["human_approved"] is True

            await db.delete(mission)
            await db.flush()
            await db.delete(review)
            await db.delete(project)
            await db.delete(admin)
            await db.commit()

    asyncio.run(_run())


def test_customer_ticket_updates_cannot_set_coverage_decisions():
    from app.api.v1.endpoints.tickets import CUSTOMER_EDITABLE_FIELDS

    assert {
        "warranty_related",
        "amc_covered",
        "is_paid_service",
        "coverage_type",
        "estimated_cost",
        "resolution",
    }.isdisjoint(CUSTOMER_EDITABLE_FIELDS)

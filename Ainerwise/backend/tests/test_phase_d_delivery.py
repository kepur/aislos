"""Phase D first slice: channel gateway handoff + service-partner role view."""
import asyncio
import uuid

from app.main import app
from app.db.session import async_session_factory, engine
from app.models.integration import IntegrationEvent
from app.models.rfq import RFQ
from app.models.service import ServicePartner
from app.models.user import User
from app.services.partner_dispatch import change_partner_task_status, dispatch_partner_task
from datetime import date

from app.models.lifecycle import MaintenanceSchedule
from app.models.project import Project
from app.services.partner_dispatch import PARTNER_TASK_STATUS_TRANSITIONS, _task_message, partner_task_dict
from app.services.rfq import _invitation_text


def test_phase_d_partner_routes_registered():
    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/partner/dashboard",
        "/api/v1/partner/rfqs",
        "/api/v1/partner/rfqs/{id}",
        "/api/v1/partner/rfqs/{id}/decline",
        "/api/v1/partner/rfqs/{id}/bids",
        "/api/v1/partner/tasks",
        "/api/v1/partner/tasks/{id}",
        "/api/v1/partner/tasks/{id}/status",
        "/api/v1/partner/calendar",
        "/api/v1/projects/{id}/dispatch",
        "/api/v1/projects/{id}/dispatches",
        "/internal/v1/channel-config/{channel}",
        "/internal/v1/channels/inbound",
    ):
        assert path in paths


def test_rfq_invitation_points_partner_to_role_view():
    rfq_id = uuid.uuid4()
    rfq = RFQ(
        id=rfq_id,
        title="Hotel network upgrade",
        trade="network",
        status="bidding",
        scope_json={"city": "Belgrade", "country": "Serbia"},
    )
    text = _invitation_text(rfq)

    assert "Hotel network upgrade" in text
    assert f"/partner/rfqs/{rfq_id}" in text


def test_partner_task_payload_and_deep_link():
    project = Project(id=uuid.uuid4(), title="Hotel network delivery", region="Belgrade")
    task = MaintenanceSchedule(
        id=uuid.uuid4(),
        project_id=project.id,
        task_type="installation",
        device_name="Core switch",
        due_date=date(2026, 7, 15),
        status="scheduled",
        covered_by_amc=False,
    )

    payload = partner_task_dict(task, project)
    message = _task_message(project, task)

    assert payload["project_title"] == "Hotel network delivery"
    assert payload["due_date"] == "2026-07-15"
    assert f"/partner/tasks/{task.id}" in message
    assert "scheduled" in PARTNER_TASK_STATUS_TRANSITIONS
    assert "done" in PARTNER_TASK_STATUS_TRANSITIONS["in_progress"]


def test_partner_dispatch_service_status_flow():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            partner_user = User(
                email=f"d4-dispatch-{uuid.uuid4().hex[:10]}@test.local",
                password_hash="not-used",
                role="service_partner",
            )
            db.add(partner_user)
            await db.flush()
            partner = ServicePartner(
                user_id=partner_user.id,
                partner_type="installer",
                verification_status="verified",
                availability_status="available",
            )
            project = Project(title="Phase D dispatch regression", status="planning")
            db.add_all([partner, project])
            await db.flush()

            task = await dispatch_partner_task(
                db,
                project=project,
                partner=partner,
                task_type="installation",
                due_date=date(2026, 7, 15),
                device_name="Control cabinet",
                notes="Install and verify.",
                covered_by_amc=False,
            )
            assert task.assigned_to == partner_user.id
            await change_partner_task_status(db, task=task, status="in_progress")
            await change_partner_task_status(db, task=task, status="done")
            assert task.status == "done"

            from sqlalchemy import select

            events = (
                await db.execute(
                    select(IntegrationEvent.event_type).where(IntegrationEvent.aggregate_id == task.id)
                )
            ).scalars().all()
            assert "partner.task_dispatched" in events
            assert events.count("partner.task_status_changed") == 2
            await db.rollback()

    asyncio.run(_run())

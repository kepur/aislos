"""Support Agent ticket triage. Advice is preliminary and never changes coverage."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AgentRun, AIReview
from app.models.ticket import Ticket
from app.services.agent_runtime import AgentAuthorizationError, require_agent


def _triage(ticket: Ticket) -> dict:
    urgent_types = {"device_failure", "false_alarm", "network"}
    missing = []
    if not ticket.affected_device:
        missing.append("affected device")
    if not ticket.description:
        missing.append("issue description")
    return {
        "ticket_id": str(ticket.id),
        "severity": "high" if ticket.priority == "high" or ticket.issue_type in urgent_types else ticket.priority,
        "recommended_route": (
            "remote_diagnosis_first"
            if ticket.issue_type not in {"on_site_service", "calibration"}
            else "coverage_and_schedule_review"
        ),
        "missing_information": missing,
        "coverage_note": "Warranty, AMC and paid-service coverage must be confirmed by an administrator.",
        "safety_note": (
            "If there is immediate safety risk, stop using the affected system and contact local emergency services."
        ),
        "preliminary": True,
    }


async def create_ticket_triage(db: AsyncSession, ticket: Ticket) -> AIReview | None:
    if ticket.project_id is None:
        return None
    try:
        await require_agent(
            db,
            "support-agent",
            scopes=("project_data",),
            workflow="ticket_triage",
            object_type="project",
            object_id=ticket.project_id,
        )
    except AgentAuthorizationError:
        return None
    draft = _triage(ticket)
    run = AgentRun(
        agent_slug="support-agent",
        workflow="ticket_triage",
        input_json={"ticket_id": str(ticket.id), "project_id": str(ticket.project_id)},
        output_json=draft,
        status="completed",
    )
    db.add(run)
    await db.flush()
    review = AIReview(
        run_id=run.id,
        target_type="ticket_triage",
        target_id=ticket.id,
        draft_json=draft,
        status="preliminary",
    )
    db.add(review)
    await db.flush()
    return review

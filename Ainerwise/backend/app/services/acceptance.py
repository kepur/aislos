"""Acceptance closed loop — the contractor handshake:

partner completes task (photos/serials/tests)
  -> acceptance document auto-rendered and sent for signature to the customer
  -> customer signs on their phone (existing e-sign flow)
  -> document.signed consumer: release on_acceptance milestones, register
     assets from the serial list, draft the case study, emit project.completed

Everything is idempotent: re-running the signed handler on the same project
creates nothing twice.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, Site
from app.models.case_library import CaseStudy
from app.models.content import DocumentTemplate, GeneratedDocument
from app.models.lead import Lead
from app.models.lifecycle import MaintenanceSchedule
from app.models.payment import PaymentMilestone, PaymentPlan
from app.models.project import Project
from app.services.esign import send_for_signature, signing_url

DEFAULT_ACCEPTANCE_BODY = """# Acceptance Report

Project: {{project_title}}
Customer: {{customer_name}}
Date: {{date}}

## Completed work
{{work_summary}}

## Installed devices
{{device_list}}

By signing, the customer confirms the work above was delivered and accepted.
Warranty terms start on the signature date.
"""


def _render_acceptance(template_body: str, variables: dict) -> str:
    from app.services.documents import render_template

    rendered, _ = render_template(template_body, variables)
    return rendered


async def create_acceptance_request(
    db: AsyncSession, task: MaintenanceSchedule, project: Project, completion: dict
) -> tuple[GeneratedDocument, str]:
    """Build the acceptance document from the completion payload and send it
    for signature to the project's customer contact."""
    lead = await db.get(Lead, project.lead_id) if project.lead_id else None
    customer_name = (lead.contact_name if lead else None) or "Customer"
    customer_email = lead.contact_email if lead else None

    devices = completion.get("devices") or []
    device_lines = "\n".join(
        f"- {d.get('name', 'device')}"
        + (f" (SN: {d['serial']})" if d.get("serial") else "")
        + (f" — {d.get('room')}" if d.get("room") else "")
        for d in devices
    ) or "- (no devices recorded)"

    template = (
        await db.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.kind == "acceptance_report", DocumentTemplate.is_active.is_(True)
            ).limit(1)
        )
    ).scalars().first()
    template_body = template.body_md if template else DEFAULT_ACCEPTANCE_BODY
    body = _render_acceptance(
        template_body,
        {
            "project_title": project.title,
            "customer_name": customer_name,
            "date": date.today().isoformat(),
            "work_summary": completion.get("notes") or task.device_name or "Installation completed.",
            "device_list": device_lines,
        },
    )
    # custom templates without the placeholder still must show what was installed
    if "device_list" not in template_body and devices:
        body += f"\n\n## Installed devices\n{device_lines}"
    document = GeneratedDocument(
        template_id=template.id if template else None,
        kind="acceptance_report",
        subject_type="project",
        subject_id=project.id,
        title=f"Acceptance — {project.title}",
        body_md=body,
        status="final",
    )
    db.add(document)
    await db.flush()
    signature = await send_for_signature(
        db, document, signer_name=customer_name, signer_email=customer_email
    )
    return document, signing_url(signature.token)


async def handle_acceptance_signed(db: AsyncSession, document: GeneratedDocument) -> dict:
    """document.signed consumer logic for acceptance reports."""
    if document.subject_type != "project" or document.subject_id is None:
        return {"handled": False, "reason": "no project subject"}
    project = await db.get(Project, document.subject_id)
    if project is None:
        return {"handled": False, "reason": "project gone"}

    released = 0
    plans = (
        await db.execute(select(PaymentPlan).where(PaymentPlan.project_id == project.id))
    ).scalars().all()
    from app.services.payments import release_milestone

    for plan in plans:
        milestones = (
            await db.execute(
                select(PaymentMilestone).where(
                    PaymentMilestone.plan_id == plan.id,
                    PaymentMilestone.trigger == "on_acceptance",
                    PaymentMilestone.status == "funded",
                )
            )
        ).scalars().all()
        for milestone in milestones:
            await release_milestone(db, milestone, memo="customer acceptance signed")
            released += 1

    # assets from the completion record (idempotent: skip if project has assets)
    assets_created = 0
    existing_asset = (
        await db.execute(select(Asset).where(Asset.project_id == project.id).limit(1))
    ).scalars().first()
    task = (
        await db.execute(
            select(MaintenanceSchedule).where(
                MaintenanceSchedule.project_id == project.id,
                MaintenanceSchedule.completion_json.isnot(None),
            ).order_by(MaintenanceSchedule.updated_at.desc()).limit(1)
        )
    ).scalars().first()
    completion = (task.completion_json if task else None) or {}
    if existing_asset is None and completion.get("devices"):
        lead = await db.get(Lead, project.lead_id) if project.lead_id else None
        site = Site(
            name=project.title,
            city=lead.city if lead else None,
            country=lead.country if lead else None,
        )
        db.add(site)
        await db.flush()
        for device in completion["devices"]:
            if not device.get("name"):
                continue
            db.add(
                Asset(
                    site_id=site.id, project_id=project.id,
                    product_id=uuid.UUID(device["product_id"]) if device.get("product_id") else None,
                    name=device["name"], serial_no=device.get("serial"),
                    floor=device.get("floor"), room=device.get("room"),
                    installed_at=date.today(), status="active",
                )
            )
            assets_created += 1

    # case draft (idempotent by project)
    case_created = False
    embedding_document_id = None
    existing_case = (
        await db.execute(select(CaseStudy).where(CaseStudy.project_id == project.id).limit(1))
    ).scalars().first()
    if existing_case is None:
        lead = await db.get(Lead, project.lead_id) if project.lead_id else None
        case = CaseStudy(
            project_id=project.id,
            title=project.title,
            country=lead.country if lead else None,
            city=lead.city if lead else None,
            summary=completion.get("notes") or f"Delivered project: {project.title}",
            products_json=[{"name": d.get("name")} for d in (completion.get("devices") or []) if d.get("name")],
            public_visible=False,
        )
        db.add(case)
        await db.flush()
        from app.services.cases import embed_case

        embedding_document = await embed_case(db, case)
        embedding_document_id = str(embedding_document.id)
        case_created = True

    if task and task.status != "done":
        task.status = "done"
        db.add(task)
    if project.status not in ("maintenance", "closed"):
        project.status = "maintenance"
        db.add(project)
    await db.flush()

    from app.services.event_bus import EventType, emit_event

    await emit_event(
        db, EventType.PROJECT_COMPLETED,
        {"project_id": str(project.id), "released_milestones": released,
         "assets_created": assets_created, "case_created": case_created},
        aggregate_type="project", aggregate_id=project.id, target_channel="telegram_admin",
    )
    return {
        "handled": True,
        "released": released,
        "assets": assets_created,
        "case": case_created,
        "embedding_document_id": embedding_document_id,
    }

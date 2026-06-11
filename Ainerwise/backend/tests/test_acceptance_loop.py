"""The contractor handshake: completion -> acceptance signature -> milestone
release + asset registry + case draft, fully automated. Plus the 9-role RBAC."""
import asyncio
import base64
from decimal import Decimal

from app.core.permissions import (
    ADMIN_ROLES,
    CUSTOMER_ROLES,
    PARTNER_ROLES,
    STAFF_ROLES,
    UserRole,
)
from app.db.session import async_session_factory, engine
from app.main import app

TINY_PNG_DATA_URL = "data:image/png;base64," + base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
).decode()


def test_role_matrix():
    values = {r.value for r in UserRole}
    assert {
        "super_admin", "admin", "sales_manager", "project_manager", "finance",
        "buyer", "customer_user", "vendor", "developer",
        "service_partner", "partner_worker", "maintenance_worker",
    } == values
    assert UserRole.SALES_MANAGER in STAFF_ROLES
    assert UserRole.PARTNER_WORKER in PARTNER_ROLES
    assert UserRole.MAINTENANCE_WORKER in PARTNER_ROLES
    assert UserRole.CUSTOMER_USER in CUSTOMER_ROLES
    assert ADMIN_ROLES == {UserRole.SUPER_ADMIN, UserRole.ADMIN}


def test_completion_route_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/partner/tasks/{id}/complete" in paths


def test_acceptance_closed_loop():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.asset import Asset, Site
            from app.models.case_library import CaseStudy
            from app.models.integration import IntegrationEvent
            from app.models.lead import Lead
            from app.models.lifecycle import MaintenanceSchedule
            from app.models.payment import PaymentMilestone, PaymentPlan
            from app.models.project import Project
            from app.services.acceptance import create_acceptance_request, handle_acceptance_signed
            from app.services.esign import apply_signature

            lead = Lead(contact_name="Ana Petrović", contact_email="ana@e2e.local",
                        city="Novi Sad", country="Serbia", status="won")
            db.add(lead)
            await db.flush()
            project = Project(lead_id=lead.id, title="Novi Sad apartment — KNX retrofit",
                              status="installation")
            db.add(project)
            await db.flush()
            plan = PaymentPlan(project_id=project.id, currency="EUR",
                               total=Decimal("8000"), status="active")
            db.add(plan)
            await db.flush()
            milestone = PaymentMilestone(plan_id=plan.id, seq=3, label="acceptance",
                                         pct=Decimal("30"), amount=Decimal("2400"),
                                         trigger="on_acceptance", status="funded")
            db.add(milestone)
            task = MaintenanceSchedule(project_id=project.id, task_type="installation",
                                       status="in_progress")
            db.add(task)
            await db.flush()

            completion = {
                "notes": "KNX backbone installed, all scenes tested OK.",
                "photos": ["uploads/x/1.jpg"],
                "devices": [
                    {"name": "KNX gateway", "serial": "KNX-001", "room": "utility", "floor": "1"},
                    {"name": "Dimmer actuator", "serial": "DIM-042", "room": "living"},
                ],
            }
            task.completion_json = completion
            task.status = "completed_pending_acceptance"
            db.add(task)
            await db.flush()

            document, url = await create_acceptance_request(db, task, project, completion)
            await db.commit()
            assert "/sign/" in url
            assert document.kind == "acceptance_report"
            assert "KNX-001" in document.body_md

            # customer signs (token from the URL)
            token = url.rsplit("/", 1)[-1]
            await apply_signature(db, token, signature_data_url=TINY_PNG_DATA_URL,
                                  signer_name="Ana Petrović", signer_ip="198.51.100.1",
                                  user_agent="pytest")

            # consumer logic closes the loop
            result = await handle_acceptance_signed(db, document)
            await db.commit()
            assert result["handled"] is True
            assert result["released"] == 1
            assert result["assets"] == 2
            assert result["case"] is True

            refreshed_milestone = await db.get(PaymentMilestone, milestone.id)
            assert refreshed_milestone.status == "released"
            assets = (
                await db.execute(select(Asset).where(Asset.project_id == project.id))
            ).scalars().all()
            assert {a.serial_no for a in assets} == {"KNX-001", "DIM-042"}
            case = (
                await db.execute(select(CaseStudy).where(CaseStudy.project_id == project.id))
            ).scalar_one()
            assert case.country == "Serbia"
            assert case.embedding_document_id is not None
            refreshed_task = await db.get(MaintenanceSchedule, task.id)
            assert refreshed_task.status == "done"
            refreshed_project = await db.get(Project, project.id)
            assert refreshed_project.status == "maintenance"

            # idempotent re-run creates nothing new
            again = await handle_acceptance_signed(db, document)
            await db.commit()
            assert again["assets"] == 0 and again["case"] is False and again["released"] == 0

            # cleanup (FK order matters)
            from app.models.ai import KnowledgeDocument
            from app.models.content import DocumentSignature, GeneratedDocument

            for model, column, value in (
                (DocumentSignature, DocumentSignature.document_id, document.id),
                (Asset, Asset.project_id, project.id),
            ):
                for row in (await db.execute(select(model).where(column == value))).scalars().all():
                    await db.delete(row)
            site_ids = {a.site_id for a in assets}
            for site_id in site_ids:
                site = await db.get(Site, site_id)
                if site:
                    await db.delete(site)
            embedding_doc_id = case.embedding_document_id
            await db.delete(case)
            await db.flush()
            if embedding_doc_id:
                doc = await db.get(KnowledgeDocument, embedding_doc_id)
                if doc:
                    await db.delete(doc)
            generated = await db.get(GeneratedDocument, document.id)
            await db.delete(generated)
            for row in (
                await db.execute(
                    select(IntegrationEvent).where(IntegrationEvent.aggregate_id.in_([project.id, document.id]))
                )
            ).scalars().all():
                await db.delete(row)
            await db.delete(refreshed_task)
            from app.models.payment import LedgerEntry

            for row in (
                await db.execute(select(LedgerEntry).where(LedgerEntry.milestone_id == milestone.id))
            ).scalars().all():
                await db.delete(row)
            await db.flush()
            await db.delete(refreshed_milestone)
            await db.flush()
            await db.delete(plan)
            await db.flush()
            await db.delete(project)
            await db.flush()
            await db.delete(lead)
            await db.commit()

    asyncio.run(_run())

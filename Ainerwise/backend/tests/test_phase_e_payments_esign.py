"""Phase E tests: e-signature flow (fully offline-capable), Stripe degradation
paths, auto-dispatch consumer, briefing region metrics."""
import asyncio
import base64
import uuid

import httpx
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.main import app

# 1x1 transparent PNG
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
TINY_PNG_DATA_URL = "data:image/png;base64," + base64.b64encode(TINY_PNG).decode()


def test_phase_e_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/documents/{id}/send-for-signature",
        "/api/v1/admin/documents/{id}/signatures",
        "/api/v1/sign/{token}",
        "/api/v1/admin/payments/milestones/{id}/checkout-link",
        "/api/v1/admin/payments/milestones/{id}/transfer",
        "/api/v1/admin/payments/partner-deposits",
        "/api/v1/admin/payments/partners/{partner_id}/stripe-onboard",
        "/webhooks/stripe",
    ):
        assert p in paths, p


def test_esign_full_flow_and_tamper_protection():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.models.content import GeneratedDocument
            from app.services.esign import (
                apply_signature,
                document_hash,
                load_for_signing,
                send_for_signature,
            )

            document = GeneratedDocument(
                kind="acceptance_report", title="E2E acceptance report",
                body_md="# Acceptance\nProject completed.\nCustomer accepts the installation.",
                status="final",
            )
            db.add(document)
            await db.flush()

            signature = await send_for_signature(
                db, document, signer_name="Marko Petrovic", signer_email=None
            )
            await db.commit()
            assert signature.status == "sent"
            assert signature.document_sha256 == document_hash(document.body_md)
            assert document.status == "sent_for_signature"

            loaded_sig, loaded_doc = await load_for_signing(db, signature.token)
            assert loaded_sig.status == "viewed"

            signed = await apply_signature(
                db, signature.token,
                signature_data_url=TINY_PNG_DATA_URL,
                signer_name="Marko Petrović",
                signer_ip="203.0.113.7",
                user_agent="pytest",
            )
            assert signed.status == "signed"
            assert signed.signed_at is not None
            assert signed.signer_ip == "203.0.113.7"
            assert signed.signature_minio_key

            refreshed_doc = await db.get(GeneratedDocument, document.id)
            assert refreshed_doc.status == "signed"
            assert "Electronic signature" in refreshed_doc.body_md
            assert signed.document_sha256 in refreshed_doc.body_md
            assert refreshed_doc.pdf_minio_key  # signed PDF rendered

            # double-sign blocked
            try:
                await load_for_signing(db, signature.token)
                raise AssertionError("signed link must not be loadable")
            except ValueError:
                pass

            # cleanup
            await db.delete(signed)
            await db.delete(refreshed_doc)
            await db.commit()

    asyncio.run(_run())


def test_esign_tamper_detection():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.models.content import GeneratedDocument
            from app.services.esign import apply_signature, send_for_signature

            document = GeneratedDocument(kind="contract", title="Tamper test",
                                         body_md="original body", status="final")
            db.add(document)
            await db.flush()
            signature = await send_for_signature(db, document, signer_name="X", signer_email=None)
            document.body_md = "modified body after sending"
            db.add(document)
            await db.commit()

            try:
                await apply_signature(db, signature.token, signature_data_url=TINY_PNG_DATA_URL,
                                      signer_name=None, signer_ip=None, user_agent=None)
                raise AssertionError("tampered document must not be signable")
            except ValueError as exc:
                assert "changed" in str(exc)

            await db.delete(signature)
            refreshed = await db.get(GeneratedDocument, document.id)
            await db.delete(refreshed)
            await db.commit()

    asyncio.run(_run())


def test_stripe_unconfigured_degrades_cleanly():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from decimal import Decimal

            from app.models.payment import PaymentMilestone, PaymentPlan
            from app.services.stripe_payments import create_milestone_checkout

            plan = PaymentPlan(currency="EUR", total=Decimal("1000"), status="active")
            db.add(plan)
            await db.flush()
            milestone = PaymentMilestone(plan_id=plan.id, seq=1, label="deposit",
                                         pct=Decimal("30"), amount=Decimal("300"), status="pending")
            db.add(milestone)
            await db.flush()
            try:
                await create_milestone_checkout(db, milestone)
                raise AssertionError("must raise when stripe unconfigured")
            except ValueError as exc:
                assert "not configured" in str(exc)
            assert milestone.status == "pending"  # untouched
            await db.rollback()

        # public webhook returns 503 when unconfigured
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/webhooks/stripe", content=b"{}")
            assert response.status_code == 503

    asyncio.run(_run())


def test_rfq_awarded_consumer_skips_unlinked_partner():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.lead import Lead
            from app.models.lifecycle import MaintenanceSchedule
            from app.models.project import Project
            from app.models.rfq import RFQ
            from app.models.service import ServicePartner
            from app.tasks.event_consumers import _handle_rfq_awarded

            partner = ServicePartner(partner_type="installer", rating_internal=4.0)  # no user_id
            lead = Lead(contact_name="x", status="new")
            db.add_all([partner, lead])
            await db.flush()
            project = Project(lead_id=lead.id, title="dispatch test", status="planning")
            rfq = RFQ(title="dispatch test", trade="knx", status="awarded", lead_id=lead.id)
            db.add_all([project, rfq])
            await db.flush()

            await _handle_rfq_awarded(db, {
                "rfq_id": str(rfq.id), "partner_id": str(partner.id), "project_id": str(project.id),
            })
            tasks = (
                await db.execute(
                    select(MaintenanceSchedule).where(MaintenanceSchedule.project_id == project.id)
                )
            ).scalars().all()
            assert tasks == []  # graceful skip, no crash
            await db.rollback()

    asyncio.run(_run())


def test_briefing_includes_region_and_marketing_metrics_live():
    async def _run():
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/briefing",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            assert response.status_code == 200, response.text
            metrics = response.json()["metrics"]
            for key in ("region_margin", "leads_by_source_yesterday",
                        "posts_published_yesterday", "seo_pages_published"):
                assert key in metrics, key
            if metrics["region_margin"]:
                assert {"country", "avg_margin_pct", "cases"} <= set(metrics["region_margin"][0])

    asyncio.run(_run())

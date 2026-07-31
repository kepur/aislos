"""Cebu Admin shared configuration is admin-only, persisted and audited."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.admin_config import AdminNote, NotificationTemplate, PlatformSetting
from app.models.audit import AuditLog
from app.models.commerce import RiskFlag
from app.models.commerce_geo import CompanyBranch, ServiceArea
from app.modules.buyer_project.models import ProjectMetricTemplate
from app.modules.kyc.models import CompanyDocument


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_cebu_admin_shared_config_is_real_admin_only_and_audited():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        admin_email, password, _ = await _create_identity(role="admin", with_company=False)
        buyer_email, buyer_password, buyer_company = await _create_identity(role="buyer")
        admin = await _login(admin_email, password)
        buyer = await _login(buyer_email, buyer_password)
        entity_id = uuid.uuid4()
        template_key = f"order-awarded-{uuid.uuid4().hex[:8]}"
        setting_key = f"commerce.quote-expiry-{uuid.uuid4().hex[:8]}"
        metric_key = f"room-count-{uuid.uuid4().hex[:8]}"
        async with async_session_factory() as db:
            document = CompanyDocument(
                company_id=buyer_company,
                doc_type="BUSINESS_REGISTRATION",
                file_url="https://example.com/kyc-risk.pdf",
                status="PENDING",
            )
            db.add(document)
            await db.commit()
            document_id = document.id

        async with _client() as client:
            denied = await client.put(
                f"/api/v1/admin/cebu/settings/{setting_key}",
                headers=buyer,
                json={"value_json": {"days": 7}},
            )
            assert denied.status_code == 403

            note = await client.post(
                "/api/v1/admin/cebu/notes",
                headers=admin,
                json={
                    "entity_type": "commerce_order",
                    "entity_id": str(entity_id),
                    "visibility": "risk_team",
                    "note": "Manual risk evidence reviewed.",
                },
            )
            assert note.status_code == 201, note.text
            notes = await client.get(
                f"/api/v1/admin/cebu/notes/commerce_order/{entity_id}", headers=admin
            )
            assert notes.status_code == 200, notes.text
            assert notes.json()["items"][0]["note"] == "Manual risk evidence reviewed."

            template = await client.put(
                f"/api/v1/admin/cebu/notification-templates/{template_key}",
                headers=admin,
                json={
                    "channel": "EMAIL",
                    "language": "en",
                    "subject": "Order awarded",
                    "body": "Order {{ order_id }} has been awarded.",
                    "variables_hint": "order_id",
                    "active": True,
                },
            )
            assert template.status_code == 200, template.text
            templates = await client.get(
                "/api/v1/admin/cebu/notification-templates", headers=admin
            )
            assert templates.status_code == 200, templates.text
            assert any(row["template_key"] == template_key for row in templates.json()["items"])

            setting = await client.put(
                f"/api/v1/admin/cebu/settings/{setting_key}",
                headers=admin,
                json={
                    "value_json": {"days": 7, "regions": ["PH"]},
                    "description": "Default quote expiry policy.",
                },
            )
            assert setting.status_code == 200, setting.text
            settings = await client.get("/api/v1/admin/cebu/settings", headers=admin)
            assert settings.status_code == 200, settings.text
            assert any(row["key"] == setting_key for row in settings.json()["items"])

            rejected_secret = await client.put(
                "/api/v1/admin/cebu/settings/provider_api_token",
                headers=admin,
                json={"value_json": {"value": "must-not-be-saved"}},
            )
            assert rejected_secret.status_code == 422

            branch = await client.post(
                "/api/v1/admin/cebu/branches",
                headers=admin,
                json={
                    "company_id": str(buyer_company),
                    "name": "Cebu Operations Branch",
                    "country": "Philippines",
                    "city": "Cebu",
                    "radius_km": 30,
                    "delivery_methods_json": ["installation", "delivery"],
                },
            )
            assert branch.status_code == 201, branch.text
            branch_id = branch.json()["id"]
            branch_updated = await client.patch(
                f"/api/v1/admin/cebu/branches/{branch_id}",
                headers=admin,
                json={"radius_km": 45},
            )
            assert branch_updated.status_code == 200, branch_updated.text
            assert branch_updated.json()["radius_km"] == 45
            area = await client.post(
                "/api/v1/admin/cebu/service-areas",
                headers=admin,
                json={
                    "name": "Metro Cebu Coverage",
                    "company_id": str(buyer_company),
                    "coverage_type": "RADIUS",
                    "center_lat": 10.3157,
                    "center_lng": 123.8854,
                    "radius_km": 40,
                },
            )
            assert area.status_code == 201, area.text
            area_id = area.json()["id"]
            area_updated = await client.patch(
                f"/api/v1/admin/cebu/service-areas/{area_id}",
                headers=admin,
                json={"notes": "Includes Mandaue and Lapu-Lapu."},
            )
            assert area_updated.status_code == 200, area_updated.text

            denied_metric = await client.post(
                "/api/v1/admin/cebu/project-metric-templates",
                headers=buyer,
                json={"project_type": "RENOVATION", "key": metric_key, "label": "Room count"},
            )
            assert denied_metric.status_code == 403
            metric = await client.post(
                "/api/v1/admin/cebu/project-metric-templates",
                headers=admin,
                json={
                    "project_type": "RENOVATION",
                    "key": metric_key,
                    "label": "Room count",
                    "data_type": "number",
                    "required": True,
                    "sort_order": 10,
                },
            )
            assert metric.status_code == 201, metric.text
            metric_id = metric.json()["id"]
            metric_updated = await client.patch(
                f"/api/v1/admin/cebu/project-metric-templates/{metric_id}",
                headers=admin,
                json={"prompt": "How many rooms need upgrading?", "active": False},
            )
            assert metric_updated.status_code == 200, metric_updated.text
            assert metric_updated.json()["active"] is False

            flagged = await client.post(
                f"/api/v1/admin/cebu/kyc-media/files/{document_id}/flag-risk",
                headers=admin,
                json={"note": "Document image appears altered.", "severity": "high"},
            )
            assert flagged.status_code == 200, flagged.text
            assert flagged.json()["status"] == "REJECTED"
            detail = await client.get(
                f"/api/v1/admin/cebu/kyc-media/files/{document_id}", headers=admin
            )
            assert detail.status_code == 200, detail.text
            assert detail.json()["reviewer_note"] == "Document image appears altered."

        async with async_session_factory() as db:
            assert (
                await db.execute(select(AdminNote).where(AdminNote.entity_id == entity_id))
            ).scalar_one()
            assert (
                await db.execute(
                    select(NotificationTemplate).where(
                        NotificationTemplate.template_key == template_key
                    )
                )
            ).scalar_one()
            assert (
                await db.execute(select(PlatformSetting).where(PlatformSetting.key == setting_key))
            ).scalar_one()
            assert (
                await db.execute(select(ProjectMetricTemplate).where(ProjectMetricTemplate.key == metric_key))
            ).scalar_one()
            assert await db.get(CompanyBranch, uuid.UUID(branch_id))
            assert await db.get(ServiceArea, uuid.UUID(area_id))
            assert (
                await db.execute(
                    select(RiskFlag).where(
                        RiskFlag.subject_type == "company_document",
                        RiskFlag.subject_id == document_id,
                    )
                )
            ).scalar_one()
            actions = set(
                (
                    await db.execute(
                        select(AuditLog.action).where(AuditLog.portal_key == "admin_cebu")
                    )
                ).scalars()
            )
            assert {
                "cebu.admin.note_created",
                "cebu.admin.notification_template_created",
                "cebu.admin.platform_setting_created",
                "cebu.admin.project_metric_template_created",
                "cebu.admin.project_metric_template_updated",
                "cebu.admin.kyc_media_flagged",
                "cebu.admin.branch_created",
                "cebu.admin.branch_updated",
                "cebu.admin.service_area_created",
                "cebu.admin.service_area_updated",
            }.issubset(actions)

    asyncio.run(_run())

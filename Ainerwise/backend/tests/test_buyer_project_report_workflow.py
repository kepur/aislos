"""Buyer Project metrics, estimates, reports and freeze are real and owner-scoped."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.modules.buyer_project.models import ProjectLineItem, ProjectMetricTemplate


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_buyer_project_report_workflow_is_versioned_audited_and_owner_scoped():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        buyer_email, password, _ = await _create_identity(role="buyer")
        stranger_email, stranger_password, _ = await _create_identity(role="buyer")
        buyer = await _login(buyer_email, password)
        stranger = await _login(stranger_email, stranger_password)
        metric_key = f"room_count_{uuid.uuid4().hex[:8]}"

        async with _client() as client:
            created = await client.post(
                "/api/v1/buyer/projects",
                headers=buyer,
                json={"title": "Villa smart upgrade", "project_type": "RENOVATION"},
            )
            assert created.status_code == 201, created.text
            project_id = created.json()["id"]

        async with async_session_factory() as db:
            template = ProjectMetricTemplate(
                project_type="RENOVATION",
                key=metric_key,
                label="Room count",
                data_type="number",
                required=True,
            )
            item = ProjectLineItem(
                project_id=project_id,
                name="Smart lock",
                qty=2,
                unit="pcs",
                quality_tier="MID_RANGE",
                estimated_unit_price=10000,
                estimated_total_price=20000,
                currency="PHP",
            )
            db.add_all([template, item])
            await db.commit()

        async with _client() as client:
            metrics = await client.get(f"/api/v1/buyer/projects/{project_id}/metrics", headers=buyer)
            assert metrics.status_code == 200, metrics.text
            assert metric_key in {row["key"] for row in metrics.json()["missing_required"]}

            denied_metric = await client.patch(
                f"/api/v1/buyer/projects/{project_id}/metrics",
                headers=stranger,
                json={"metrics": [{"key": metric_key, "value": 99}]},
            )
            assert denied_metric.status_code == 404

            updated = await client.patch(
                f"/api/v1/buyer/projects/{project_id}/metrics",
                headers=buyer,
                json={"metrics": [{"key": metric_key, "value": 4, "confidence": 0.95}]},
            )
            assert updated.status_code == 200, updated.text
            assert metric_key not in {row["key"] for row in updated.json()["missing_required"]}

            estimate = await client.post(
                f"/api/v1/buyer/projects/{project_id}/price-estimate", headers=buyer
            )
            assert estimate.status_code == 200, estimate.text
            assert len(estimate.json()["items"]) == 1

            report = await client.get(f"/api/v1/buyer/projects/{project_id}/report", headers=buyer)
            assert report.status_code == 200, report.text
            assert report.json()["current_version"]["version_number"] == 1
            assert len(report.json()["rows"]) == 1
            row_id = report.json()["rows"][0]["id"]

            edited = await client.patch(
                f"/api/v1/buyer/projects/{project_id}/report/rows/{row_id}",
                headers=buyer,
                json={"selected_tier": "PREMIUM", "notes": "Customer preference"},
            )
            assert edited.status_code == 200, edited.text
            assert edited.json()["rows"][0]["selected_tier"] == "PREMIUM"

            recalculated = await client.post(
                f"/api/v1/buyer/projects/{project_id}/report/recalculate", headers=buyer
            )
            assert recalculated.status_code == 200, recalculated.text
            assert recalculated.json()["current_version"]["version_number"] == 2
            frozen_row_id = recalculated.json()["rows"][0]["id"]

            frozen = await client.post(
                f"/api/v1/buyer/projects/{project_id}/report/freeze", headers=buyer
            )
            assert frozen.status_code == 200, frozen.text
            assert frozen.json()["current_version"]["status"] == "FROZEN"
            assert frozen.json()["frozen_version_id"] == frozen.json()["current_version_id"]

            frozen_edit = await client.patch(
                f"/api/v1/buyer/projects/{project_id}/report/rows/{frozen_row_id}",
                headers=buyer,
                json={"notes": "Must not mutate frozen commercial record"},
            )
            assert frozen_edit.status_code == 409

            versions = await client.get(
                f"/api/v1/buyer/projects/{project_id}/report/versions", headers=buyer
            )
            assert versions.status_code == 200, versions.text
            assert [row["version_number"] for row in versions.json()["items"]][:2] == [2, 1]

            denied_report = await client.get(
                f"/api/v1/buyer/projects/{project_id}/report", headers=stranger
            )
            assert denied_report.status_code == 404

        async with async_session_factory() as db:
            actions = set(
                (
                    await db.execute(
                        select(AuditLog.action).where(AuditLog.entity_id == project_id)
                    )
                ).scalars()
            )
            assert {
                "buyer_project.report_recalculated",
                "buyer_project.report_frozen",
            }.issubset(actions)

    asyncio.run(_run())

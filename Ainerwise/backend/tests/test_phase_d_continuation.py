"""Phase D continuation tests: Business Brain, SEO engine, document center,
publish jobs, similar-case retrieval. Live services where it matters."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.main import app
from app.services.documents import markdown_to_pdf_bytes, render_template
from app.tasks.celery_app import celery_app


def test_phase_d_continuation_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/business-brain/latest",
        "/api/v1/admin/business-brain/run",
        "/api/v1/admin/seo/pages/generate",
        "/api/v1/admin/seo/pages/{id}/publish",
        "/api/v1/seo/pages/{slug}",
        "/api/v1/admin/documents/templates",
        "/api/v1/admin/documents/generate",
        "/api/v1/admin/documents/{id}/finalize",
        "/api/v1/admin/marketing/assets/{id}/schedule",
        "/api/v1/admin/marketing/publish-jobs",
        "/api/v1/admin/marketing/generate-image",
        "/api/v1/admin/design-revisions",
        "/api/v1/admin/cases/similar",
    ):
        assert p in paths, p


def test_phase_d_celery_wiring():
    beat = celery_app.conf.beat_schedule
    assert "send-daily-briefing" in beat
    assert "dispatch-publish-jobs" in beat
    routes = celery_app.conf.task_routes
    assert routes["send_daily_briefing"]["queue"] == "automation"
    assert routes["dispatch_publish_jobs"]["queue"] == "automation"


def test_template_rendering():
    body = "# Report\nProject: {{project_title}}\nCustomer: {{customer_name}}\nNote: {{missing_var}}"
    rendered, missing = render_template(body, {"project_title": "Villa BG", "customer_name": "Marko"})
    assert "Villa BG" in rendered and "Marko" in rendered
    assert "[missing_var]" in rendered
    assert missing == ["missing_var"]


def test_markdown_pdf_generation():
    pdf = markdown_to_pdf_bytes("Acceptance Report", "# Done\n- KNX installed\n- Solar commissioned\n\nSigned.")
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 500


def test_publish_job_without_aggregator_goes_manual():
    from app.models.content import PublishJob
    from app.models.marketing import MarketingAsset

    async def _setup():
        await engine.dispose()
        async with async_session_factory() as db:
            asset = MarketingAsset(kind="post", channel="linkedin", lang="en",
                                   title="t", content="c", status="approved")
            db.add(asset)
            await db.flush()
            job = PublishJob(asset_id=asset.id, platform="linkedin",
                             scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                             status="scheduled")
            db.add(job)
            await db.commit()
            return job.id, asset.id

    job_id, asset_id = asyncio.run(_setup())

    # the celery task runs its own event loop — call it at sync level
    from app.tasks.publishing_tasks import dispatch_publish_jobs

    dispatch_publish_jobs()

    async def _verify_and_cleanup():
        await engine.dispose()
        async with async_session_factory() as db:
            refreshed = await db.get(PublishJob, job_id)
            assert refreshed.status == "manual_required"
            assert "aggregator" in (refreshed.error_message or "")
            await db.delete(refreshed)
            asset = await db.get(MarketingAsset, asset_id)
            await db.delete(asset)
            await db.commit()

    asyncio.run(_verify_and_cleanup())


def test_briefing_live_via_orchestrator():
    async def _run():
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/briefing",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert "text" in body and "metrics" in body
            assert "leads_yesterday" in body["metrics"]
            assert isinstance(body["metrics"]["partner_risk"], list)

    asyncio.run(_run())


def test_consult_returns_similar_cases_live():
    """Relies on the embedded Belgrade case from the Phase C e2e demo data."""

    async def _run():
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/chat",
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
                json={"message": "Have you delivered KNX and solar villa projects in Belgrade?",
                      "visitor_id": f"phase-d-test-{uuid.uuid4().hex[:6]}"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert "similar_cases" in body
            if body["similar_cases"]:  # demo case present
                top = body["similar_cases"][0]
                assert {"title", "similarity", "budget"} <= set(top)
                assert "gross_margin_pct" not in top  # internal economics never leak

    asyncio.run(_run())

"""MI01: Creative Brief, immutable versions, human review gate and Media Requests."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.integration import IntegrationEvent
from app.models.marketing import MarketingCreativeBrief, MarketingMediaRequest
from app.services.marketing_briefs import build_export_payload, compute_content_hash

SAMPLE_DELIVERABLE = {
    "key": "instagram-square-en-v1",
    "media_type": "image",
    "channel": "instagram",
    "language": "en",
    "format": "png",
    "width": 1080,
    "height": 1080,
    "duration_seconds": None,
    "variant_count": 3,
    "required_text": [],
    "notes": None,
}

BRIEF_BODY = {
    "title": "Villa launch Q3",
    "objective": "Drive showroom visits",
    "version": {
        "copy_json": {"headline": "Smart living starts here"},
        "audience_json": {"segment": "luxury homeowners"},
        "brand_constraints_json": {"tone": "premium"},
        "channel_specs_json": {"instagram": {"aspect": "1:1"}},
        "deliverables_json": [SAMPLE_DELIVERABLE],
        "compliance_json": {"disclaimer": "Preliminary creative direction"},
    },
}


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _buyer_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@ainerwise.com", "password": "demo123"},
        )
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _create_brief(headers: dict) -> dict:
    async with _client() as client:
        resp = await client.post("/api/v1/admin/marketing/creative-briefs", headers=headers, json=BRIEF_BODY)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _approve_brief(headers: dict, version_id: str) -> dict:
    async with _client() as client:
        submitted = await client.post(
            f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/submit-review",
            headers=headers,
        )
        assert submitted.status_code == 200, submitted.text
        approved = await client.post(
            f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/approve",
            headers=headers,
            json={"notes": "Looks good"},
        )
        assert approved.status_code == 200, approved.text
        return approved.json()


def test_creative_brief_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/marketing/creative-briefs",
        "/api/v1/admin/marketing/creative-briefs/{brief_id}",
        "/api/v1/admin/marketing/creative-briefs/{brief_id}/versions",
        "/api/v1/admin/marketing/creative-brief-versions/{version_id}/submit-review",
        "/api/v1/admin/marketing/creative-brief-versions/{version_id}/approve",
        "/api/v1/admin/marketing/creative-brief-versions/{version_id}/reject",
        "/api/v1/admin/marketing/creative-brief-versions/{version_id}/media-requests",
        "/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
    ):
        assert p in paths, p


def test_create_submit_approve_and_media_requests():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        assert brief["status"] == "draft"
        assert brief["current_version"]["status"] == "draft"
        assert brief["current_version"]["content_hash"]

        approved = await _approve_brief(headers, version_id)
        assert approved["status"] == "approved"

        async with _client() as client:
            media = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
                headers=headers,
            )
        assert media.status_code == 201, media.text
        items = media.json()
        assert len(items) == 1
        assert items[0]["deliverable_key"] == SAMPLE_DELIVERABLE["key"]
        assert items[0]["status"] == "available"

    asyncio.run(_run())


def test_unapproved_brief_cannot_create_media_requests():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        async with _client() as client:
            resp = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
                headers=headers,
            )
        assert resp.status_code == 409

    asyncio.run(_run())


def test_in_review_version_cannot_be_edited():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        async with _client() as client:
            submitted = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/submit-review",
                headers=headers,
            )
            assert submitted.status_code == 200
            edited = await client.put(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}",
                headers=headers,
                json={"copy_json": {"headline": "changed"}},
            )
        assert edited.status_code == 409

    asyncio.run(_run())


def test_approved_brief_requires_new_version_for_changes():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        await _approve_brief(headers, version_id)

        new_version_body = {
            "copy_json": {"headline": "Revised headline"},
            "audience_json": BRIEF_BODY["version"]["audience_json"],
            "brand_constraints_json": BRIEF_BODY["version"]["brand_constraints_json"],
            "channel_specs_json": BRIEF_BODY["version"]["channel_specs_json"],
            "deliverables_json": [SAMPLE_DELIVERABLE],
            "compliance_json": BRIEF_BODY["version"]["compliance_json"],
        }
        async with _client() as client:
            resp = await client.post(
                f"/api/v1/admin/marketing/creative-briefs/{brief['id']}/versions",
                headers=headers,
                json=new_version_body,
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["version"] == 2
        assert resp.json()["status"] == "draft"

        async with _client() as client:
            detail = await client.get(
                f"/api/v1/admin/marketing/creative-briefs/{brief['id']}",
                headers=headers,
            )
        assert detail.json()["status"] == "draft"

    asyncio.run(_run())


def test_rejected_version_can_copy_to_new_draft():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        async with _client() as client:
            await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/submit-review",
                headers=headers,
            )
            rejected = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/reject",
                headers=headers,
                json={"reason": "Needs stronger CTA"},
            )
            assert rejected.status_code == 200
            copied = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/copy-draft",
                headers=headers,
            )
        assert copied.status_code == 201, copied.text
        assert copied.json()["version"] == 2
        assert copied.json()["status"] == "draft"

    asyncio.run(_run())


def test_non_admin_cannot_approve_brief():
    async def _run():
        await engine.dispose()
        admin_headers = await _admin_headers()
        buyer_headers = await _buyer_headers()
        brief = await _create_brief(admin_headers)
        version_id = brief["current_version"]["id"]
        async with _client() as client:
            await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/submit-review",
                headers=admin_headers,
            )
            resp = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/approve",
                headers=buyer_headers,
                json={"notes": "auto"},
            )
        assert resp.status_code == 403

    asyncio.run(_run())


def test_external_export_excludes_internal_fields():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        async with _client() as client:
            resp = await client.get(
                f"/api/v1/admin/marketing/creative-briefs/{brief['id']}/export",
                headers=headers,
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        text = resp.text.lower()
        assert "review_id" not in body
        assert "created_by" not in body
        assert "source_refs" not in body
        assert "crm" not in text
        assert "margin" not in text
        assert "cost" not in text
        assert body["deliverables"][0]["key"] == SAMPLE_DELIVERABLE["key"]

    asyncio.run(_run())


def test_content_hash_is_stable_for_same_payload():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            brief = MarketingCreativeBrief(
                id=uuid.uuid4(),
                title="t",
                objective="o",
                status="draft",
            )
            from app.models.marketing import MarketingCreativeBriefVersion

            version = MarketingCreativeBriefVersion(
                id=uuid.uuid4(),
                brief_id=brief.id,
                version=1,
                status="draft",
                copy_json=BRIEF_BODY["version"]["copy_json"],
                audience_json=BRIEF_BODY["version"]["audience_json"],
                brand_constraints_json=BRIEF_BODY["version"]["brand_constraints_json"],
                channel_specs_json=BRIEF_BODY["version"]["channel_specs_json"],
                deliverables_json=[SAMPLE_DELIVERABLE],
                compliance_json=BRIEF_BODY["version"]["compliance_json"],
            )
            payload = build_export_payload(brief, version)
            h1 = compute_content_hash(payload)
            h2 = compute_content_hash(payload)
            assert h1 == h2
            assert len(h1) == 64

    asyncio.run(_run())


def test_audit_and_outbox_on_brief_creation():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        async with async_session_factory() as db:
            audits = (
                await db.execute(
                    select(AuditLog).where(
                        AuditLog.entity_id == uuid.UUID(brief["id"]),
                        AuditLog.action == "marketing.creative_brief.created",
                    )
                )
            ).scalars().all()
            events = (
                await db.execute(
                    select(IntegrationEvent).where(
                        IntegrationEvent.event_type == "marketing.creative_brief.created",
                    )
                )
            ).scalars().all()
        assert audits
        assert any(e.payload_json.get("brief_id") == brief["id"] for e in events)

    asyncio.run(_run())


def test_duplicate_media_request_rejected():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        await _approve_brief(headers, version_id)
        async with _client() as client:
            first = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
                headers=headers,
            )
            second = await client.post(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}/create-media-requests",
                headers=headers,
            )
        assert first.status_code == 201
        assert second.status_code == 409

    asyncio.run(_run())


def test_draft_version_can_be_updated_before_submit():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        brief = await _create_brief(headers)
        version_id = brief["current_version"]["id"]
        async with _client() as client:
            resp = await client.put(
                f"/api/v1/admin/marketing/creative-brief-versions/{version_id}",
                headers=headers,
                json={"copy_json": {"headline": "Updated headline"}},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["copy_json"]["headline"] == "Updated headline"

    asyncio.run(_run())

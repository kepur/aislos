"""Public intake must not write server-owned CRM fields or bypass AI limits."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from fastapi import HTTPException

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.lead import Lead
from app.models.inquiry import Inquiry


def test_public_lead_intake_ignores_internal_crm_fields(monkeypatch):
    async def no_analysis(*args, **kwargs):
        return None

    async def _run():
        await engine.dispose()
        monkeypatch.setattr("app.api.v1.endpoints.leads.analyze_lead", no_analysis)
        monkeypatch.setattr("app.api.v1.endpoints.leads.ensure_lead_follow_up", no_analysis)
        marker = uuid.uuid4().hex
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/leads",
                json={
                    "contact_email": f"{marker}@example.com",
                    "description": "Public requirement",
                    "lead_score": 100,
                    "lead_stage": "won",
                    "proposal_tiers_json": {"premium": {"price": 1}},
                    "source_channel": "trusted_partner",
                    "source_detail": "forged",
                    "campaign_id": str(uuid.uuid4()),
                },
            )
            assert response.status_code == 201, response.text
            lead_id = uuid.UUID(response.json()["id"])

        async with async_session_factory() as db:
            lead = await db.get(Lead, lead_id)
            assert lead is not None
            assert lead.lead_score is None
            assert lead.lead_stage is None
            assert lead.proposal_tiers_json is None
            assert lead.source_channel == "website"
            assert lead.source_detail is None
            assert lead.campaign_id is None

    asyncio.run(_run())


def test_public_ai_assessment_is_rate_limited(monkeypatch):
    async def limited(**kwargs):
        return True

    async def _run():
        await engine.dispose()
        monkeypatch.setattr(
            "app.api.v1.endpoints.integrations.redis_fixed_window_limited",
            limited,
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/ai/assistant",
                json={
                    "category": "villa",
                    "messages": [{"role": "user", "content": "Help me plan it"}],
                },
            )
            assert response.status_code == 429, response.text

    asyncio.run(_run())


def test_public_inquiry_ignores_internal_attribution_fields(monkeypatch):
    async def no_limit(*args, **kwargs):
        return None

    async def _run():
        await engine.dispose()
        monkeypatch.setattr(
            "app.api.v1.endpoints.inquiries.enforce_public_rate_limit", no_limit
        )
        marker = uuid.uuid4().hex
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/inquiries/public",
                json={
                    "contact_email": f"{marker}@example.com",
                    "message": "Public inquiry",
                    "campaign_id": str(uuid.uuid4()),
                    "source_channel": "trusted_partner",
                    "source_detail": "forged",
                },
            )
            assert response.status_code == 201, response.text
            inquiry_id = uuid.UUID(response.json()["id"])

        async with async_session_factory() as db:
            inquiry = await db.get(Inquiry, inquiry_id)
            assert inquiry is not None
            assert inquiry.campaign_id is None
            assert inquiry.source_channel == "website"
            assert inquiry.source_detail is None

    asyncio.run(_run())


def test_public_intake_endpoints_are_rate_limited(monkeypatch):
    async def limited(*args, **kwargs):
        raise HTTPException(status_code=429, detail="limited")

    async def _run():
        await engine.dispose()
        monkeypatch.setattr(
            "app.api.v1.endpoints.leads.enforce_public_rate_limit", limited
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.inquiries.enforce_public_rate_limit", limited
        )
        monkeypatch.setattr(
            "app.api.v1.endpoints.vendors.enforce_public_rate_limit", limited
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            lead = await client.post("/api/v1/leads", json={})
            inquiry = await client.post("/api/v1/inquiries/public", json={})
            vendor = await client.post(
                "/api/v1/vendors/apply",
                json={"company_name": "Limited", "email": "limited@example.com"},
            )
            assert lead.status_code == 429
            assert inquiry.status_code == 429
            assert vendor.status_code == 429

    asyncio.run(_run())


def test_login_only_uses_rate_limit_buckets_for_invalid_credentials(monkeypatch):
    calls: list[dict] = []

    async def record_limit(request, **kwargs):
        calls.append(kwargs)

    async def _run():
        await engine.dispose()
        monkeypatch.setattr(
            "app.api.v1.endpoints.auth.enforce_public_rate_limit", record_limit
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            successful = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@ainerwise.com", "password": "admin123456"},
            )
            assert successful.status_code == 200, successful.text
            assert calls == []

            calls.clear()
            failed = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@ainerwise.com", "password": "wrong-password"},
            )
            assert failed.status_code == 401, failed.text
            assert [item["bucket"] for item in calls] == [
                "auth-login-failed-ip",
                "auth-login-failed-account",
            ]
            assert calls[1]["subject_suffix"] == "admin@ainerwise.com"

    asyncio.run(_run())

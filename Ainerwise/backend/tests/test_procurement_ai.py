"""C05: procurement analyze API, validation and concurrency."""
import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.services.portal_policy import ensure_default_policies

BASE = "/api/v1/procurement"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register_buyer() -> str:
    email = f"buyer-{uuid.uuid4().hex[:8]}@test.local"
    async with async_session_factory() as db:
        from app.models.user import User

        user = User(
            email=email,
            password_hash=hash_password("testpass123"),
            full_name="Buyer",
            role="buyer",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return create_access_token(str(user.id), "buyer")


def _auth(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: "aislos",
    }


async def _confirm_all_facts(pid: str, token: str) -> None:
    async with _client() as ac:
        facts = await ac.get(f"{BASE}/projects/{pid}/facts", headers=_auth(token))
        for fact in facts.json():
            await ac.patch(
                f"{BASE}/projects/{pid}/facts/{fact['id']}",
                json={"value_json": "ok", "user_confirmed": True},
                headers=_auth(token),
            )


def _orch_response(scenario: str) -> dict:
    conf_map = {
        "low": 0.55,
        "edge_600": 0.6,
        "edge_800": 0.8,
        "edge_801": 0.801,
        "high": 0.85,
    }
    conf = conf_map.get(scenario, 0.85)
    tiers = ["budget", "standard", "premium"]
    options = [
        {
            "tier": t,
            "capability": t,
            "unit_price_min": 100,
            "unit_price_max": 150,
            "currency": "USD",
        }
        for t in tiers
    ]
    data = {
        "project_summary": "Test",
        "extracted_facts": [
            {"key": "property_area_sqm", "value": 300, "source": "ai", "confidence": conf}
        ],
        "missing_questions": [{"key": "target_budget", "importance": "critical", "reason": "x"}]
        if scenario == "low"
        else [],
        "boq_items": [
            {
                "category": "lighting",
                "name": "Lights",
                "qty": "2",
                "unit": "lot",
                "quantity_basis": "2 floors",
                "confidence": conf,
                "included": True,
                "options": options,
            }
        ]
        if conf >= 0.6
        else [],
        "risks": [],
        "exclusions": [],
    }
    return {"workflow": "procurement_analyze", "status": "completed", "data": data}


def test_analyze_route_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/procurement/projects/{project_id}/analyze" in paths


def test_analyze_high_confidence_review_ready():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await ensure_default_policies(db)
            await db.commit()
        token = await _register_buyer()
        async with _client() as ac:
            project = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "AI Villa"},
                headers=_auth(token),
            )
            assert project.status_code == 201
            pid = project.json()["id"]
            await _confirm_all_facts(pid, token)

            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=_orch_response("high")),
            ):
                resp = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "high"},
                    headers=_auth(token),
                )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "review_ready"
        assert body["boq_version_id"] is not None
        assert body["review_id"] is not None

    asyncio.run(_run())


def test_analyze_low_confidence_needs_information():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await ensure_default_policies(db)
            await db.commit()
        token = await _register_buyer()
        async with _client() as ac:
            project = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Low"},
                headers=_auth(token),
            )
            pid = project.json()["id"]
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=_orch_response("low")),
            ):
                resp = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "low"},
                    headers=_auth(token),
                )
        assert resp.status_code == 200
        assert resp.json()["status"] == "needs_information"
        assert resp.json()["boq_version_id"] is None

    asyncio.run(_run())


def test_analyze_invalid_output_fail_closed():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await ensure_default_policies(db)
            await db.commit()
        token = await _register_buyer()
        async with _client() as ac:
            project = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Bad"},
                headers=_auth(token),
            )
            pid = project.json()["id"]
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value={"status": "completed", "data": {"broken": True}}),
            ):
                resp = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={},
                    headers=_auth(token),
                )
        assert resp.status_code == 400

    asyncio.run(_run())


def test_analyze_edge_confidence_branches():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await ensure_default_policies(db)
            await db.commit()
        token = await _register_buyer()
        for scenario, expected in (
            ("edge_600", "estimate_ready"),
            ("edge_800", "estimate_ready"),
            ("edge_801", "review_ready"),
        ):
            async with _client() as ac:
                project = await ac.post(
                    f"{BASE}/projects",
                    json={"project_type": "villa_smart_home", "title": scenario},
                    headers=_auth(token),
                )
                pid = project.json()["id"]
                await _confirm_all_facts(pid, token)
                with patch(
                    "app.services.procurement_ai._call_orchestrator",
                    new=AsyncMock(return_value=_orch_response(scenario)),
                ):
                    resp = await ac.post(
                        f"{BASE}/projects/{pid}/analyze",
                        json={"test_scenario": scenario},
                        headers=_auth(token),
                    )
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == expected

    asyncio.run(_run())

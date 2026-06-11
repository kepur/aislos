"""C03: procurement project facts — list, patch, user_confirmed."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.integration import IntegrationEvent
from app.models.user import User
from app.services.portal_policy import ensure_default_policies

BASE = "/api/v1/procurement"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register_buyer() -> tuple[User, str]:
    email = f"buyer-{uuid.uuid4().hex[:8]}@test.local"
    async with async_session_factory() as db:
        user = User(
            email=email,
            password_hash=hash_password("testpass123"),
            full_name="Test Buyer",
            role=UserRole.BUYER.value,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token(str(user.id), user.role)
    return user, token


def _auth(token: str, portal_key: str = "aislos") -> dict:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: portal_key,
    }


async def _seed_and_create_project(token: str, project_type: str = "villa_smart_home") -> dict:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()
    async with _client() as ac:
        r = await ac.post(
            f"{BASE}/projects",
            json={
                "project_type": project_type,
                "title": "Facts Test Project",
            },
            headers=_auth(token),
        )
    assert r.status_code == 201, r.text
    return r.json()


def test_list_facts_returns_required_template_keys():
    async def _t():
        await engine.dispose()
        _, token = await _register_buyer()
        project = await _seed_and_create_project(token)

        async with _client() as ac:
            r = await ac.get(
                f"{BASE}/projects/{project['id']}/facts",
                headers=_auth(token),
            )
        assert r.status_code == 200
        facts = r.json()
        assert len(facts) >= 7
        for f in facts:
            assert f["required"] is True
            assert f["user_confirmed"] is False
            assert f["confidence"] == "0.000"

    asyncio.run(_t())


def test_patch_fact_value_and_confirm():
    async def _t():
        await engine.dispose()
        _, token = await _register_buyer()
        project = await _seed_and_create_project(token)

        async with _client() as ac:
            facts = await ac.get(
                f"{BASE}/projects/{project['id']}/facts",
                headers=_auth(token),
            )
        fact = next(f for f in facts.json() if f["template_key"] == "room_count")
        original_confidence = fact["confidence"]

        async with _client() as ac:
            updated = await ac.patch(
                f"{BASE}/projects/{project['id']}/facts/{fact['id']}",
                json={"value_json": 12},
                headers=_auth(token),
            )
        assert updated.status_code == 200
        assert updated.json()["value_json"] == 12
        assert updated.json()["source"] == "user"
        assert updated.json()["confidence"] == original_confidence

        async with _client() as ac:
            confirmed = await ac.patch(
                f"{BASE}/projects/{project['id']}/facts/{fact['id']}",
                json={"user_confirmed": True},
                headers=_auth(token),
            )
        assert confirmed.status_code == 200
        body = confirmed.json()
        assert body["user_confirmed"] is True
        assert body["confidence"] == original_confidence  # original AI confidence preserved

        async with async_session_factory() as db:
            audit_confirmed = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(
                        AuditLog.action == "procurement.fact.confirmed",
                        AuditLog.entity_id == uuid.UUID(fact["id"]),
                    )
                )
            ).scalar()
            event_confirmed = (
                await db.execute(
                    select(func.count()).select_from(IntegrationEvent).where(
                        IntegrationEvent.event_type == "procurement.fact.confirmed",
                    )
                )
            ).scalar()
        assert audit_confirmed == 1
        assert event_confirmed >= 1

    asyncio.run(_t())


def test_hotel_template_initializes_distinct_facts():
    async def _t():
        await engine.dispose()
        _, token = await _register_buyer()
        project = await _seed_and_create_project(token, "small_hotel_smart_upgrade")

        async with _client() as ac:
            r = await ac.get(
                f"{BASE}/projects/{project['id']}/facts",
                headers=_auth(token),
            )
        keys = {f["template_key"] for f in r.json()}
        for key in (
            "room_count",
            "property_area_sqm",
            "star_rating",
            "target_budget",
            "public_area_coverage",
            "back_of_house_systems",
            "installation_timeline",
            "brand_standards",
        ):
            assert key in keys

    asyncio.run(_t())


def test_patch_fact_not_found_wrong_portal():
    async def _t():
        await engine.dispose()
        _, token = await _register_buyer()
        project = await _seed_and_create_project(token)

        async with _client() as ac:
            facts = await ac.get(
                f"{BASE}/projects/{project['id']}/facts",
                headers=_auth(token),
            )
        fact_id = facts.json()[0]["id"]

        async with _client() as ac:
            r = await ac.patch(
                f"{BASE}/projects/{project['id']}/facts/{fact_id}",
                json={"value_json": 99},
                headers=_auth(token, "cebu"),
            )
        assert r.status_code == 404

    asyncio.run(_t())

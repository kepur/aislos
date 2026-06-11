"""C07: RFQ publish, idempotency, privacy serializers and transactional integrity."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.integration import IntegrationEvent
from app.models.procurement import CommercialSnapshot
from app.models.rfq import RFQ
from app.services.portal_policy import ensure_default_policies

BASE = "/api/v1/procurement"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register_user(role: str = UserRole.BUYER.value) -> tuple[str, str]:
    email = f"user-{uuid.uuid4().hex[:8]}@test.local"
    async with async_session_factory() as db:
        from app.models.user import User

        user = User(
            email=email,
            password_hash=hash_password("testpass123"),
            full_name="Test User",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return str(user.id), create_access_token(str(user.id), role)


def _auth(token: str, portal: str = "aislos") -> dict:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: portal,
    }


def _commercial_terms() -> dict:
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    return {
        "currency": "USD",
        "exchange_rate_snapshot_json": {"base": "USD", "quote": "PHP", "rate": "56.5"},
        "tax_mode": "exclusive",
        "margin_rule_json": {"type": "percent", "value": "0.15"},
        "service_fee_json": {"platform_fee_percent": "0.05"},
        "warranty_rule_json": {"months": 12},
        "delivery_region_json": {"country": "PH"},
        "quote_expiry": expiry,
        "payment_terms_json": {"net_days": 30},
    }


def _item_payload() -> dict:
    tiers = []
    for tier, price in (("budget", 100), ("standard", 200), ("premium", 300)):
        tiers.append(
            {
                "tier": tier,
                "capability": f"{tier} kit",
                "unit_price_min": str(price),
                "unit_price_max": str(price + 50),
                "currency": "USD",
            }
        )
    return {
        "category": "lighting",
        "name": "Lighting kit",
        "qty": "1",
        "unit": "lot",
        "quantity_basis": "per scope",
        "confidence": "0.95",
        "included": True,
        "options": tiers,
    }


async def _seed() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


async def _create_project(token: str) -> dict:
    async with _client() as ac:
        resp = await ac.post(
            f"{BASE}/projects",
            json={
                "project_type": "villa_smart_home",
                "title": "RFQ Publish Test",
                "country": "PH",
            },
            headers=_auth(token),
        )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _confirm_facts(project_id: str, token: str) -> None:
    async with _client() as ac:
        facts = await ac.get(f"{BASE}/projects/{project_id}/facts", headers=_auth(token))
        for fact in facts.json():
            await ac.patch(
                f"{BASE}/projects/{project_id}/facts/{fact['id']}",
                json={"value_json": "ok", "user_confirmed": True},
                headers=_auth(token),
            )


async def _ready_package(project_id: str, buyer: str, admin: str) -> str:
    await _confirm_facts(project_id, buyer)
    async with _client() as ac:
        draft = await ac.post(
            f"{BASE}/projects/{project_id}/boq/draft",
            json={"items": [_item_payload()]},
            headers=_auth(admin),
        )
        version_id = draft.json()["version_id"]
        review = await ac.post(
            f"{BASE}/projects/{project_id}/boq/review",
            json={"boq_version_id": version_id},
            headers=_auth(buyer),
        )
        review_id = review.json()["review_id"]
        await ac.post(
            f"/api/v1/admin/ai-reviews/{review_id}/approve",
            json={"notes": "ok"},
            headers={"Authorization": f"Bearer {admin}"},
        )
        await ac.post(
            f"{BASE}/projects/{project_id}/boq/freeze",
            json={"boq_version_id": version_id},
            headers=_auth(buyer),
        )
        gen = await ac.post(
            f"{BASE}/projects/{project_id}/packages/generate",
            headers=_auth(buyer),
        )
        package_id = gen.json()["packages"][0]["id"]
        ready = await ac.patch(
            f"{BASE}/projects/{project_id}/packages/{package_id}",
            json={"status": "ready"},
            headers=_auth(buyer),
        )
        assert ready.status_code == 200, ready.text
        return package_id


def test_publish_route_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/procurement/projects/{project_id}/packages/{package_id}/publish-rfq" in paths


def test_publish_fails_with_incomplete_commercial_terms():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        package_id = await _ready_package(project["id"], buyer, admin)
        bad = _commercial_terms()
        bad.pop("tax_mode")
        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=bad,
                headers=_auth(buyer),
            )
        assert resp.status_code == 422
        async with async_session_factory() as db:
            pkg_snaps = (
                await db.execute(
                    select(func.count())
                    .select_from(CommercialSnapshot)
                    .where(CommercialSnapshot.package_id == uuid.UUID(package_id))
                )
            ).scalar_one()
            pkg_rfqs = (
                await db.execute(
                    select(func.count())
                    .select_from(RFQ)
                    .where(RFQ.procurement_package_id == uuid.UUID(package_id))
                )
            ).scalar_one()
        assert pkg_snaps == 0
        assert pkg_rfqs == 0

    asyncio.run(_run())


def test_successful_publish_and_project_status():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        package_id = await _ready_package(project["id"], buyer, admin)
        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=_commercial_terms(),
                headers=_auth(buyer),
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["created"] is True
        assert body["package_status"] == "published"
        assert body["project_status"] == "rfq_published"
        assert "margin_rule_json" not in body["rfq"]["commercial_snapshot"]
        assert "margin_rule_json" not in body["supplier_view"]["commercial_snapshot"]
        assert "service_fee_json" not in body["supplier_view"]["commercial_snapshot"]

    asyncio.run(_run())


def test_publish_is_idempotent_per_package_revision():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        package_id = await _ready_package(project["id"], buyer, admin)
        async with _client() as ac:
            first = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=_commercial_terms(),
                headers=_auth(buyer),
            )
            second = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=_commercial_terms(),
                headers=_auth(buyer),
            )
        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["created"] is False
        assert first.json()["rfq"]["id"] == second.json()["rfq"]["id"]
        async with async_session_factory() as db:
            count = (
                await db.execute(
                    select(func.count()).select_from(RFQ).where(
                        RFQ.procurement_package_id == uuid.UUID(package_id)
                    )
                )
            ).scalar_one()
        assert count == 1

    asyncio.run(_run())


def test_outbox_payload_includes_portal_branding():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        package_id = await _ready_package(project["id"], buyer, admin)
        async with _client() as ac:
            await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=_commercial_terms(),
                headers=_auth(buyer),
            )
        async with async_session_factory() as db:
            row = (
                await db.execute(
                    select(IntegrationEvent)
                    .where(IntegrationEvent.event_type == "procurement.rfq.published")
                    .order_by(IntegrationEvent.created_at.desc())
                    .limit(1)
                )
            ).scalar_one()
        payload = row.payload_json
        assert payload["portal_key"] == "aislos"
        assert "price_visibility_rule" in payload
        assert "rfq_id" in payload

    asyncio.run(_run())


def test_publish_fails_when_package_not_ready():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_facts(project["id"], buyer)
        async with _client() as ac:
            draft = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/draft",
                json={"items": [_item_payload()]},
                headers=_auth(admin),
            )
            version_id = draft.json()["version_id"]
            review = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/review",
                json={"boq_version_id": version_id},
                headers=_auth(buyer),
            )
            review_id = review.json()["review_id"]
            await ac.post(
                f"/api/v1/admin/ai-reviews/{review_id}/approve",
                json={"notes": "ok"},
                headers={"Authorization": f"Bearer {admin}"},
            )
            await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={"boq_version_id": version_id},
                headers=_auth(buyer),
            )
            gen = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer),
            )
            package_id = gen.json()["packages"][0]["id"]
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/{package_id}/publish-rfq",
                json=_commercial_terms(),
                headers=_auth(buyer),
            )
        assert resp.status_code == 409
        assert "ready" in resp.json()["detail"].lower()

    asyncio.run(_run())

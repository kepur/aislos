"""C04: BOQ versions, tier derivation, review gate and freeze rules."""
import asyncio
import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.procurement import BoqItem, BoqVersion
from app.services.portal_policy import ensure_default_policies
from app.services.procurement_boq import derive_solution_plan_totals

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


def _auth(token: str, portal_key: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: portal_key,
    }


async def _seed() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


async def _create_project(token: str, portal: str = "aislos") -> dict:
    async with _client() as ac:
        resp = await ac.post(
            f"{BASE}/projects",
            json={
                "project_type": "villa_smart_home",
                "title": "BOQ Test Villa",
                "country": "PH",
            },
            headers=_auth(token, portal),
        )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _confirm_all_facts(project_id: str, token: str, portal: str) -> None:
    async with _client() as ac:
        facts = await ac.get(
            f"{BASE}/projects/{project_id}/facts",
            headers=_auth(token, portal),
        )
        assert facts.status_code == 200
        for fact in facts.json():
            patch = await ac.patch(
                f"{BASE}/projects/{project_id}/facts/{fact['id']}",
                json={"value_json": "confirmed", "user_confirmed": True},
                headers=_auth(token, portal),
            )
            assert patch.status_code == 200, patch.text


def _sample_item_payload() -> dict:
    tiers = []
    for tier, price in (("budget", 100), ("standard", 200), ("premium", 300)):
        tiers.append(
            {
                "tier": tier,
                "capability": f"{tier} lighting package",
                "unit_price_min": str(price),
                "unit_price_max": str(price + 50),
                "currency": "USD",
            }
        )
    return {
        "category": "lighting",
        "name": "Smart lighting package",
        "qty": "2",
        "unit": "lot",
        "quantity_basis": "2 floors x 1 lot per floor",
        "confidence": "0.95",
        "critical": False,
        "included": True,
        "options": tiers,
    }


async def _create_draft(project_id: str, admin_token: str) -> dict:
    async with _client() as ac:
        resp = await ac.post(
            f"{BASE}/projects/{project_id}/boq/draft",
            json={"items": [_sample_item_payload()]},
            headers=_auth(admin_token, "aislos"),
        )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_boq_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/procurement/projects/{project_id}/boq",
        "/api/v1/procurement/projects/{project_id}/boq/review",
        "/api/v1/procurement/projects/{project_id}/boq/freeze",
        "/api/v1/procurement/projects/{project_id}/boq/draft",
    ):
        assert p in paths


def test_solution_plan_totals_match_options():
    from app.models.procurement import BoqItem, BoqItemOption

    item = BoqItem(
        id=uuid.uuid4(),
        boq_version_id=uuid.uuid4(),
        category="x",
        name="item",
        qty=Decimal("2"),
        unit="ea",
        included=True,
        confidence=Decimal("0.9"),
    )
    options = []
    for tier, total in (("budget", Decimal("250")), ("standard", Decimal("500")), ("premium", Decimal("700"))):
        options.append(
            BoqItemOption(
                id=uuid.uuid4(),
                boq_item_id=item.id,
                tier=tier,
                capability="c",
                unit_price_min=Decimal("100"),
                unit_price_max=Decimal("150"),
                total_price_min=total,
                total_price_max=total + Decimal("50"),
                currency="USD",
            )
        )
    t_min, t_max, _ = derive_solution_plan_totals([item], options, "standard")
    assert t_min == Decimal("500.00")
    assert t_max == Decimal("550.00")


def test_draft_boq_derives_three_tier_totals():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        admin_id, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        body = await _create_draft(project["id"], admin)
        plans = {p["tier"]: p for p in body["solution_plans"]}
        assert set(plans) == {"budget", "standard", "premium"}
        # qty=2: budget 100-150 per unit -> 200-300 per item
        assert plans["budget"]["total_min"] == "200.00"
        assert plans["budget"]["total_max"] == "300.00"
        assert "source_ref" not in str(body).lower()

    asyncio.run(_run())


def test_freeze_fails_without_approved_review():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        await _create_draft(project["id"], admin)
        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={},
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 400
        assert "review" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_freeze_fails_with_unconfirmed_required_fact():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _create_draft(project["id"], admin)
        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={},
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 400
        assert "required fact" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_freeze_fails_missing_quantity_basis():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        item = _sample_item_payload()
        item.pop("quantity_basis")
        async with _client() as ac:
            await ac.post(
                f"{BASE}/projects/{project['id']}/boq/draft",
                json={"items": [item]},
                headers=_auth(admin, "aislos"),
            )
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={},
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 400
        assert "quantity_basis" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_admin_cannot_bypass_freeze_rules():
    async def _run():
        await engine.dispose()
        await _seed()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(admin)
        await _confirm_all_facts(project["id"], admin, "aislos")
        await _create_draft(project["id"], admin)
        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={},
                headers=_auth(admin, "aislos"),
            )
        assert resp.status_code == 400
        assert "review" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_successful_freeze_after_review_approval():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        boq = await _create_draft(project["id"], admin)
        version_id = boq["version_id"]

        async with _client() as ac:
            review_resp = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/review",
                json={"boq_version_id": version_id},
                headers=_auth(buyer, "aislos"),
            )
            assert review_resp.status_code == 200, review_resp.text
            review_id = review_resp.json()["review_id"]

            approve = await ac.post(
                f"/api/v1/admin/ai-reviews/{review_id}/approve",
                json={"notes": "approved for freeze test"},
                headers={"Authorization": f"Bearer {admin}"},
            )
            assert approve.status_code == 200, approve.text

            frozen = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/freeze",
                json={"boq_version_id": version_id},
                headers=_auth(buyer, "aislos"),
            )
        assert frozen.status_code == 200, frozen.text
        assert frozen.json()["project_status"] == "boq_frozen"
        assert frozen.json()["boq"]["status"] == "frozen"

    asyncio.run(_run())


def test_new_draft_does_not_mutate_frozen_version():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        boq_v1 = await _create_draft(project["id"], admin)
        version_id = boq_v1["version_id"]

        async with _client() as ac:
            review = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/review",
                json={"boq_version_id": version_id},
                headers=_auth(buyer, "aislos"),
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
                headers=_auth(buyer, "aislos"),
            )
            frozen_snapshot = (
                await ac.get(
                    f"{BASE}/projects/{project['id']}/boq",
                    headers=_auth(buyer, "aislos"),
                )
            ).json()
            assert frozen_snapshot["status"] == "frozen"
            assert frozen_snapshot["version"] == 1

            item = _sample_item_payload()
            item["name"] = "Mutated item name"
            await ac.post(
                f"{BASE}/projects/{project['id']}/boq/draft",
                json={"items": [item]},
                headers=_auth(admin, "aislos"),
            )
            refetch = await ac.get(
                f"{BASE}/projects/{project['id']}/boq",
                headers=_auth(buyer, "aislos"),
            )
        # Current pointer moves to new draft; frozen v1 unchanged in DB
        assert refetch.json()["version"] == 2
        assert refetch.json()["status"] == "draft"
        async with async_session_factory() as db:
            v1 = await db.get(BoqVersion, uuid.UUID(version_id))
            assert v1 is not None
            assert v1.status == "frozen"
            items = (
                await db.execute(select(BoqItem).where(BoqItem.boq_version_id == v1.id))
            ).scalars().all()
            assert items[0].name == "Smart lighting package"

    asyncio.run(_run())

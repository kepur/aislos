"""C06: auto package split from frozen BOQ and partner capability matching."""
import asyncio
import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.service import PartnerCapability, ServicePartner
from app.models.portal_policy import PHASE1_PROJECT_TYPES
from app.services.portal_policy import (
    activate_policy,
    create_policy_version,
    ensure_default_policies,
    retire_active_policy,
)
from app.services.procurement_packages import classify_commercial_type, resolve_trade

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


async def _ensure_portal_policy(portal_key: str, mode: str) -> None:
    async with async_session_factory() as db:
        await retire_active_policy(db, portal_key)
        policy = await create_policy_version(
            db,
            portal_key,
            default_procurement_mode=mode,
            allowed_project_types_json=list(PHASE1_PROJECT_TYPES),
            price_visibility_rule="customer_totals_only"
            if mode == "managed"
            else "line_estimates",
            supplier_visibility_rule="hidden"
            if mode == "managed"
            else "visible_when_self_service",
        )
        await activate_policy(db, policy)
        await db.commit()


def _item_payload(
    *,
    category: str,
    name: str,
    trade: str | None = None,
    supply: bool = True,
    install: bool = False,
    maintain: bool = False,
) -> dict:
    tiers = []
    for tier, price in (("budget", 100), ("standard", 200), ("premium", 300)):
        tiers.append(
            {
                "tier": tier,
                "capability": f"{tier} {name}",
                "unit_price_min": str(price),
                "unit_price_max": str(price + 50),
                "currency": "USD",
                "supply_included": supply,
                "install_included": install,
                "maintain_included": maintain,
            }
        )
    payload = {
        "category": category,
        "name": name,
        "qty": "1",
        "unit": "lot",
        "quantity_basis": "per scope",
        "confidence": "0.95",
        "critical": False,
        "included": True,
        "options": tiers,
    }
    if trade:
        payload["trade"] = trade
    return payload


async def _create_project(token: str, portal: str = "aislos") -> dict:
    async with _client() as ac:
        resp = await ac.post(
            f"{BASE}/projects",
            json={
                "project_type": "villa_smart_home",
                "title": "Package Test Villa",
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
        for fact in facts.json():
            await ac.patch(
                f"{BASE}/projects/{project_id}/facts/{fact['id']}",
                json={"value_json": "confirmed", "user_confirmed": True},
                headers=_auth(token, portal),
            )


async def _freeze_boq(project_id: str, buyer_token: str, admin_token: str, portal: str) -> dict:
    async with _client() as ac:
        draft = await ac.post(
            f"{BASE}/projects/{project_id}/boq/draft",
            json={"items": [_item_payload(category="lighting", name="Lighting kit")]},
            headers=_auth(admin_token, portal),
        )
        assert draft.status_code == 201, draft.text
        version_id = draft.json()["version_id"]
        review = await ac.post(
            f"{BASE}/projects/{project_id}/boq/review",
            json={"boq_version_id": version_id},
            headers=_auth(buyer_token, portal),
        )
        assert review.status_code == 200, review.text
        review_id = review.json()["review_id"]
        approve = await ac.post(
            f"/api/v1/admin/ai-reviews/{review_id}/approve",
            json={"notes": "ok"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve.status_code == 200, approve.text
        frozen = await ac.post(
            f"{BASE}/projects/{project_id}/boq/freeze",
            json={"boq_version_id": version_id},
            headers=_auth(buyer_token, portal),
        )
        assert frozen.status_code == 200, frozen.text
        return frozen.json()


async def _freeze_multi_item_boq(
    project_id: str, buyer_token: str, admin_token: str, portal: str
) -> dict:
    items = [
        _item_payload(category="lighting", name="Lighting supply", supply=True),
        _item_payload(
            category="network",
            name="Network install",
            trade="network",
            supply=True,
            install=True,
        ),
        _item_payload(
            category="hvac",
            name="HVAC maintenance",
            trade="hvac",
            supply=False,
            maintain=True,
        ),
    ]
    async with _client() as ac:
        draft = await ac.post(
            f"{BASE}/projects/{project_id}/boq/draft",
            json={"items": items},
            headers=_auth(admin_token, portal),
        )
        assert draft.status_code == 201, draft.text
        version_id = draft.json()["version_id"]
        review = await ac.post(
            f"{BASE}/projects/{project_id}/boq/review",
            json={"boq_version_id": version_id},
            headers=_auth(buyer_token, portal),
        )
        review_id = review.json()["review_id"]
        await ac.post(
            f"/api/v1/admin/ai-reviews/{review_id}/approve",
            json={"notes": "ok"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        frozen = await ac.post(
            f"{BASE}/projects/{project_id}/boq/freeze",
            json={"boq_version_id": version_id},
            headers=_auth(buyer_token, portal),
        )
        assert frozen.status_code == 200, frozen.text
        return frozen.json()


async def _seed_partner(
    *,
    trade: str,
    supply: bool = False,
    install: bool = False,
    maintain: bool = False,
    regions: list[str] | None = None,
    verified: bool = True,
    active: bool = True,
) -> uuid.UUID:
    async with async_session_factory() as db:
        partner = ServicePartner(
            partner_type="contractor",
            country="PH",
            verification_status="verified" if verified else "pending",
        )
        db.add(partner)
        await db.flush()
        cap = PartnerCapability(
            partner_id=partner.id,
            trade=trade,
            supported_regions_json=regions or ["PH"],
            supply=supply,
            install=install,
            maintain=maintain,
            active=active,
            verification_status="verified" if verified else "pending",
        )
        db.add(cap)
        await db.commit()
        return partner.id


def test_package_routes_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/procurement/projects/{project_id}/packages/generate" in paths
    assert "/api/v1/procurement/projects/{project_id}/packages/{package_id}" in paths


def test_classify_and_resolve_helpers():
    from app.models.procurement import BoqItem, BoqItemOption

    item = BoqItem(
        id=uuid.uuid4(),
        boq_version_id=uuid.uuid4(),
        category="lighting",
        name="x",
        qty=Decimal("1"),
        unit="ea",
        included=True,
        confidence=Decimal("0.9"),
    )
    assert resolve_trade(item) == "lighting"

    install_opt = BoqItemOption(
        id=uuid.uuid4(),
        boq_item_id=item.id,
        tier="standard",
        capability="c",
        unit_price_min=Decimal("1"),
        unit_price_max=Decimal("2"),
        total_price_min=Decimal("1"),
        total_price_max=Decimal("2"),
        install_included=True,
    )
    assert classify_commercial_type(install_opt) == "installation"

    maintain_opt = BoqItemOption(
        id=uuid.uuid4(),
        boq_item_id=item.id,
        tier="standard",
        capability="c",
        unit_price_min=Decimal("1"),
        unit_price_max=Decimal("2"),
        total_price_min=Decimal("1"),
        total_price_max=Decimal("2"),
        maintain_included=True,
    )
    assert classify_commercial_type(maintain_opt) == "maintenance"


def test_generate_fails_without_frozen_boq():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        async with _client() as ac:
            draft = await ac.post(
                f"{BASE}/projects/{project['id']}/boq/draft",
                json={"items": [_item_payload(category="lighting", name="x")]},
                headers=_auth(admin, "aislos"),
            )
            assert draft.status_code == 201
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 400
        assert "frozen" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_generate_splits_without_duplicate_items():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        await _freeze_multi_item_boq(project["id"], buyer, admin, "aislos")

        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["project_status"] == "packaged"
        packages = body["packages"]
        assert len(packages) == 3

        keys = {(p["trade"], p["commercial_type"]) for p in packages}
        assert ("lighting", "equipment") in keys
        assert ("network", "installation") in keys
        assert ("hvac", "maintenance") in keys

        seen_items: set[str] = set()
        for pkg in packages:
            for row in pkg["items"]:
                assert row["boq_item_id"] not in seen_items
                seen_items.add(row["boq_item_id"])
        assert len(seen_items) == 3

    asyncio.run(_run())


def test_portal_default_procurement_mode():
    async def _run():
        await engine.dispose()
        await _seed()
        await _ensure_portal_policy("aislos", "managed")
        await _ensure_portal_policy("cebu", "self_service")
        _, buyer_a = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project_a = await _create_project(buyer_a, "aislos")
        await _confirm_all_facts(project_a["id"], buyer_a, "aislos")
        await _freeze_boq(project_a["id"], buyer_a, admin, "aislos")

        _, buyer_c = await _register_user()
        project_c = await _create_project(buyer_c, "cebu")
        await _confirm_all_facts(project_c["id"], buyer_c, "cebu")
        await _freeze_boq(project_c["id"], buyer_c, admin, "cebu")

        async with _client() as ac:
            a_resp = await ac.post(
                f"{BASE}/projects/{project_a['id']}/packages/generate",
                headers=_auth(buyer_a, "aislos"),
            )
            c_resp = await ac.post(
                f"{BASE}/projects/{project_c['id']}/packages/generate",
                headers=_auth(buyer_c, "cebu"),
            )
        a_pkg = a_resp.json()["packages"][0]
        c_pkg = c_resp.json()["packages"][0]
        assert a_pkg["commercial_type"] == "equipment"
        assert a_pkg["procurement_mode"] == "managed"
        assert c_pkg["procurement_mode"] == "self_service"

    asyncio.run(_run())


def test_installation_and_maintenance_force_managed():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer, "cebu")
        await _confirm_all_facts(project["id"], buyer, "cebu")
        await _freeze_multi_item_boq(project["id"], buyer, admin, "cebu")

        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "cebu"),
            )
        modes = {p["commercial_type"]: p["procurement_mode"] for p in resp.json()["packages"]}
        assert modes["installation"] == "managed"
        assert modes["maintenance"] == "managed"
        assert modes["equipment"] == "self_service"

    asyncio.run(_run())


def test_published_package_cannot_be_patched():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        await _freeze_boq(project["id"], buyer, admin, "aislos")

        async with _client() as ac:
            gen = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "aislos"),
            )
            package_id = gen.json()["packages"][0]["id"]

        async with async_session_factory() as db:
            from app.models.procurement import ProcurementPackage

            pkg = await db.get(ProcurementPackage, uuid.UUID(package_id))
            pkg.status = "published"
            await db.commit()

        async with _client() as ac:
            resp = await ac.patch(
                f"{BASE}/projects/{project['id']}/packages/{package_id}",
                json={"title": "Renamed"},
                headers=_auth(buyer, "aislos"),
            )
        assert resp.status_code == 400
        assert "cannot be modified" in resp.json()["detail"].lower()

    asyncio.run(_run())


def test_partner_matching_filters_verification_and_region():
    async def _run():
        await engine.dispose()
        await _seed()
        good = await _seed_partner(trade="lighting", supply=True, regions=["PH"])
        unverified = await _seed_partner(
            trade="lighting", supply=True, regions=["PH"], verified=False
        )
        wrong_region = await _seed_partner(trade="lighting", supply=True, regions=["US"])

        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        await _freeze_boq(project["id"], buyer, admin, "aislos")

        async with _client() as ac:
            resp = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "aislos"),
            )
        pkg = resp.json()["packages"][0]
        partner_ids = {c["partner_id"] for c in pkg["candidate_partners"]}
        assert str(good) in partner_ids
        assert str(unverified) not in partner_ids
        assert str(wrong_region) not in partner_ids

    asyncio.run(_run())


def test_patch_package_mode_is_audited():
    async def _run():
        await engine.dispose()
        await _seed()
        _, buyer = await _register_user()
        _, admin = await _register_user(UserRole.ADMIN.value)
        project = await _create_project(buyer)
        await _confirm_all_facts(project["id"], buyer, "aislos")
        await _freeze_boq(project["id"], buyer, admin, "aislos")

        async with _client() as ac:
            gen = await ac.post(
                f"{BASE}/projects/{project['id']}/packages/generate",
                headers=_auth(buyer, "aislos"),
            )
            package_id = gen.json()["packages"][0]["id"]
            patch = await ac.patch(
                f"{BASE}/projects/{project['id']}/packages/{package_id}",
                json={"procurement_mode": "self_service", "status": "ready"},
                headers=_auth(buyer, "aislos"),
            )
        assert patch.status_code == 200, patch.text
        assert patch.json()["procurement_mode"] == "self_service"
        assert patch.json()["status"] == "ready"

    asyncio.run(_run())

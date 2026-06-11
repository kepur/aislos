"""C09: Phase 1 end-to-end release gates — Villa (AISLOS) and Small Hotel (Cebu)."""
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.permissions import UserRole
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.integration import IntegrationEvent
from app.models.procurement import CommercialSnapshot, ProcurementPackage
from app.models.rfq import RFQ
from app.services.procurement_rfq import (
    CommercialSnapshotImmutableError,
    assert_snapshot_immutable,
    compute_terms_hash,
    serialize_rfq_for_customer,
    serialize_rfq_for_supplier,
)
from tests.fixtures.procurement_e2e import (
    BASE,
    auth,
    boq_item,
    client,
    commercial_terms,
    confirm_all_facts,
    ensure_portal_policy,
    freeze_reviewed_boq,
    orch_response,
    register_user,
    seed_policies,
)

VILLA_ITEMS = [
    boq_item(category="lighting", name="Villa lighting supply", supply=True),
    boq_item(
        category="network",
        name="Network installation",
        trade="network",
        supply=True,
        install=True,
    ),
    boq_item(
        category="hvac",
        name="HVAC maintenance contract",
        trade="hvac",
        supply=False,
        maintain=True,
    ),
]

HOTEL_ITEMS = [
    boq_item(category="lighting", name="Guest room lighting", supply=True),
    boq_item(
        category="network",
        name="Hotel Wi-Fi install",
        trade="network",
        supply=True,
        install=True,
    ),
    boq_item(
        category="access",
        name="Access control maintenance",
        trade="access",
        supply=False,
        maintain=True,
    ),
]


async def _publish_all_packages(
    project_id: str,
    buyer_token: str,
    portal: str,
    *,
    terms: dict | None = None,
) -> list[dict]:
    payload = terms if terms is not None else commercial_terms()
    published = []
    async with client() as ac:
        packages = await ac.get(
            f"{BASE}/projects/{project_id}/packages",
            headers=auth(buyer_token, portal),
        )
        assert packages.status_code == 200
        for pkg in packages.json():
            if pkg["status"] != "published":
                await ac.patch(
                    f"{BASE}/projects/{project_id}/packages/{pkg['id']}",
                    json={"status": "ready"},
                    headers=auth(buyer_token, portal),
                )
                resp = await ac.post(
                    f"{BASE}/projects/{project_id}/packages/{pkg['id']}/publish-rfq",
                    json=payload,
                    headers=auth(buyer_token, portal),
                )
                assert resp.status_code == 200, resp.text
                published.append(resp.json())
    return published


def test_e2e_aislos_villa_managed_full_flow():
    """Scenario A: AISLOS 300㎡ Villa — low confidence → facts → review → 3 packages → RFQ."""

    async def _run():
        await engine.dispose()
        await seed_policies()
        await ensure_portal_policy("aislos", "managed")
        _, buyer = await register_user()
        _, admin = await register_user(UserRole.ADMIN.value)

        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={
                    "project_type": "villa_smart_home",
                    "title": "300㎡ Villa Smart Home",
                    "country": "PH",
                    "description": "AISLOS managed villa E2E",
                },
                headers=auth(buyer, "aislos"),
            )
            assert created.status_code == 201
            pid = created.json()["id"]
            assert created.json()["policy_snapshot_json"]["default_procurement_mode"] == "managed"

            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="low")),
            ):
                low = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "low"},
                    headers=auth(buyer, "aislos"),
                )
            assert low.status_code == 200
            assert low.json()["status"] == "needs_information"

            await confirm_all_facts(pid, buyer, "aislos")

            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="high", items=VILLA_ITEMS)),
            ):
                high = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "high"},
                    headers=auth(buyer, "aislos"),
                )
            assert high.status_code == 200
            assert high.json()["status"] == "review_ready"
            assert len(high.json()["solution_plans"]) == 3

            version_id = high.json()["boq_version_id"]
            await freeze_reviewed_boq(pid, buyer, admin, "aislos", version_id=version_id)

            gen = await ac.post(
                f"{BASE}/projects/{pid}/packages/generate",
                headers=auth(buyer, "aislos"),
            )
            assert gen.status_code == 201
            packages = gen.json()["packages"]
            assert len(packages) == 3
            types = {(p["trade"], p["commercial_type"]) for p in packages}
            assert ("lighting", "equipment") in types
            assert ("network", "installation") in types
            assert ("hvac", "maintenance") in types
            assert all(p["procurement_mode"] == "managed" for p in packages)

            item_ids: set[str] = set()
            for pkg in packages:
                for row in pkg["items"]:
                    assert row["boq_item_id"] not in item_ids
                    item_ids.add(row["boq_item_id"])

            published = await _publish_all_packages(pid, buyer, "aislos")
            assert len(published) == 3
            assert all(p["project_status"] == "rfq_published" for p in published[-1:])
            assert published[0]["rfq"]["portal_key"] == "aislos"
            assert "margin_rule_json" not in published[0]["rfq"]["commercial_snapshot"]
            assert "margin_rule_json" not in published[0]["supplier_view"]["commercial_snapshot"]

            event = (
                await ac.get(f"{BASE}/projects/{pid}", headers=auth(buyer, "aislos"))
            ).json()
            assert event["status"] == "rfq_published"

        async with async_session_factory() as db:
            rfqs = (
                await db.execute(select(RFQ).where(RFQ.portal_key == "aislos"))
            ).scalars().all()
            assert len([r for r in rfqs if r.procurement_package_id]) >= 3

    asyncio.run(_run())


def test_e2e_cebu_small_hotel_self_service_full_flow():
    """Scenario B: Cebu 30-room hotel — line estimate → self_service equipment + managed install/maint."""

    async def _run():
        await engine.dispose()
        await seed_policies()
        await ensure_portal_policy("cebu", "self_service")
        _, buyer = await register_user()
        _, admin = await register_user(UserRole.ADMIN.value)

        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={
                    "project_type": "small_hotel_smart_upgrade",
                    "title": "30-room Small Hotel Smart Upgrade",
                    "country": "PH",
                },
                headers=auth(buyer, "cebu"),
            )
            assert created.status_code == 201
            pid = created.json()["id"]
            assert created.json()["portal_key"] == "cebu"
            snap = created.json()["policy_snapshot_json"]
            assert snap["default_procurement_mode"] == "self_service"
            assert snap["price_visibility_rule"] == "line_estimates"

            await confirm_all_facts(pid, buyer, "cebu")

            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(
                    return_value=orch_response(scenario="edge_600", items=HOTEL_ITEMS)
                ),
            ):
                analyzed = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "edge_600"},
                    headers=auth(buyer, "cebu"),
                )
            assert analyzed.status_code == 200
            assert analyzed.json()["status"] in ("estimate_ready", "review_ready")
            assert analyzed.json()["boq_version_id"] is not None

            version_id = analyzed.json()["boq_version_id"]
            await freeze_reviewed_boq(pid, buyer, admin, "cebu", version_id=version_id)

            gen = await ac.post(
                f"{BASE}/projects/{pid}/packages/generate",
                headers=auth(buyer, "cebu"),
            )
            packages = gen.json()["packages"]
            modes = {p["commercial_type"]: p["procurement_mode"] for p in packages}
            assert modes["equipment"] == "self_service"
            assert modes["installation"] == "managed"
            assert modes["maintenance"] == "managed"

            terms = commercial_terms()
            published = await _publish_all_packages(pid, buyer, "cebu", terms=terms)
            assert published[0]["rfq"]["portal_key"] == "cebu"

        async with async_session_factory() as db:
            snap = (
                await db.execute(
                    select(CommercialSnapshot).where(
                        CommercialSnapshot.procurement_project_id == uuid.UUID(pid)
                    )
                )
            ).scalars().first()
            assert snap is not None
            terms_for_hash = dict(terms)
            terms_for_hash["quote_expiry"] = datetime.fromisoformat(
                terms_for_hash["quote_expiry"].replace("Z", "+00:00")
            )
            assert snap.terms_hash == compute_terms_hash(terms_for_hash)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Failure paths (release gate)
# ---------------------------------------------------------------------------


def test_e2e_cross_portal_read_forbidden():
    async def _run():
        await engine.dispose()
        await seed_policies()
        _, buyer_a = await register_user()
        _, buyer_c = await register_user()
        async with client() as ac:
            a = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "A", "country": "PH"},
                headers=auth(buyer_a, "aislos"),
            )
            pid = a.json()["id"]
            cross = await ac.get(
                f"{BASE}/projects/{pid}",
                headers=auth(buyer_c, "cebu"),
            )
        assert cross.status_code == 404

    asyncio.run(_run())


def test_e2e_freeze_gates_enforced():
    async def _run():
        await engine.dispose()
        await seed_policies()
        _, buyer = await register_user()
        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Gates", "country": "PH"},
                headers=auth(buyer, "aislos"),
            )
            pid = created.json()["id"]
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="low")),
            ):
                await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={"test_scenario": "low"},
                    headers=auth(buyer, "aislos"),
                )
            freeze = await ac.post(
                f"{BASE}/projects/{pid}/boq/freeze",
                json={},
                headers=auth(buyer, "aislos"),
            )
            assert freeze.status_code in (400, 404)

    asyncio.run(_run())


def test_e2e_frozen_boq_immutable_via_new_draft():
    async def _run():
        await engine.dispose()
        await seed_policies()
        _, buyer = await register_user()
        _, admin = await register_user(UserRole.ADMIN.value)
        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Frozen", "country": "PH"},
                headers=auth(buyer, "aislos"),
            )
            pid = created.json()["id"]
            await confirm_all_facts(pid, buyer, "aislos")
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="high")),
            ):
                analyzed = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={},
                    headers=auth(buyer, "aislos"),
                )
            vid = analyzed.json()["boq_version_id"]
            await freeze_reviewed_boq(pid, buyer, admin, "aislos", version_id=vid)
            before = await ac.get(f"{BASE}/projects/{pid}/boq", headers=auth(buyer, "aislos"))
            v1_name = before.json()["items"][0]["name"]
            await ac.post(
                f"{BASE}/projects/{pid}/boq/draft",
                json={"items": [boq_item(category="x", name="Mutated")]},
                headers=auth(admin, "aislos"),
            )
            after = await ac.get(f"{BASE}/projects/{pid}/boq", headers=auth(buyer, "aislos"))
            assert after.json()["version"] == 2
        async with async_session_factory() as db:
            from app.models.procurement import BoqItem, BoqVersion

            v1 = await db.get(BoqVersion, uuid.UUID(vid))
            items = (
                await db.execute(select(BoqItem).where(BoqItem.boq_version_id == v1.id))
            ).scalars().all()
            assert items[0].name == v1_name
            assert v1.status == "frozen"

    asyncio.run(_run())


def test_e2e_commercial_snapshot_immutable_and_no_leak():
    async def _run():
        await engine.dispose()
        await seed_policies()
        from app.models.portal_policy import PortalPolicy
        from app.models.procurement import BoqVersion, ProcurementProject
        from app.models.user import User
        from app.core.security import hash_password
        from app.services.procurement_rfq import create_commercial_snapshot

        terms = commercial_terms()
        terms["quote_expiry"] = datetime.fromisoformat(
            terms["quote_expiry"].replace("Z", "+00:00")
        )
        async with async_session_factory() as db:
            policy = (
                await db.execute(
                    select(PortalPolicy).where(
                        PortalPolicy.portal_key == "aislos",
                        PortalPolicy.status == "active",
                    )
                )
            ).scalar_one()
            user = User(
                email=f"snap-{uuid.uuid4().hex[:8]}@t.local",
                password_hash=hash_password("x"),
                full_name="x",
                role="buyer",
                is_active=True,
            )
            db.add(user)
            await db.flush()
            project = ProcurementProject(
                owner_user_id=user.id,
                portal_key="aislos",
                portal_policy_id=policy.id,
                policy_snapshot_json={"default_procurement_mode": "managed"},
                project_type="villa_smart_home",
                title="snap",
                status="packaged",
                created_by=user.id,
            )
            db.add(project)
            await db.flush()
            boq = BoqVersion(project_id=project.id, version=1, status="frozen")
            db.add(boq)
            await db.flush()
            pkg = ProcurementPackage(
                project_id=project.id,
                boq_version_id=boq.id,
                title="P",
                trade="lighting",
                commercial_type="equipment",
                procurement_mode="managed",
                status="ready",
                revision=1,
            )
            db.add(pkg)
            await db.flush()
            snap = await create_commercial_snapshot(
                db,
                project=project,
                package=pkg,
                boq_version=boq,
                terms=terms,
                created_by=user.id,
            )
            await db.commit()
            customer = serialize_rfq_for_customer(
                RFQ(
                    trade="general",
                    title="t",
                    currency="USD",
                    status="inviting",
                    portal_key="aislos",
                    revision=1,
                ),
                snap,
                project,
            )
            supplier = serialize_rfq_for_supplier(
                RFQ(trade="general", title="t", currency="USD", status="inviting"),
                snap,
            )
            assert "margin_rule_json" not in str(customer)
            assert "margin_rule_json" not in str(supplier)
            assert "service_fee_json" not in str(supplier)

    asyncio.run(_run())
    with pytest.raises(CommercialSnapshotImmutableError):
        assert_snapshot_immutable()


def test_e2e_publish_without_commercial_terms_rolls_back():
    async def _run():
        await engine.dispose()
        await seed_policies()
        _, buyer = await register_user()
        _, admin = await register_user(UserRole.ADMIN.value)
        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Pub", "country": "PH"},
                headers=auth(buyer, "aislos"),
            )
            pid = created.json()["id"]
            await confirm_all_facts(pid, buyer, "aislos")
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="high", items=VILLA_ITEMS[:1])),
            ):
                analyzed = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={},
                    headers=auth(buyer, "aislos"),
                )
            await freeze_reviewed_boq(
                pid, buyer, admin, "aislos", version_id=analyzed.json()["boq_version_id"]
            )
            gen = await ac.post(
                f"{BASE}/projects/{pid}/packages/generate",
                headers=auth(buyer, "aislos"),
            )
            pkg_id = gen.json()["packages"][0]["id"]
            await ac.patch(
                f"{BASE}/projects/{pid}/packages/{pkg_id}",
                json={"status": "ready"},
                headers=auth(buyer, "aislos"),
            )
            bad = commercial_terms()
            bad.pop("tax_mode")
            resp = await ac.post(
                f"{BASE}/projects/{pid}/packages/{pkg_id}/publish-rfq",
                json=bad,
                headers=auth(buyer, "aislos"),
            )
            assert resp.status_code == 422

        async with async_session_factory() as db:
            count = (
                await db.execute(
                    select(func.count())
                    .select_from(RFQ)
                    .where(RFQ.procurement_package_id == uuid.UUID(pkg_id))
                )
            ).scalar_one()
            assert count == 0

    asyncio.run(_run())


def test_e2e_outbox_branding_on_publish():
    async def _run():
        await engine.dispose()
        await seed_policies()
        await ensure_portal_policy("aislos", "managed")
        _, buyer = await register_user()
        _, admin = await register_user(UserRole.ADMIN.value)
        async with client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json={"project_type": "villa_smart_home", "title": "Outbox", "country": "PH"},
                headers=auth(buyer, "aislos"),
            )
            pid = created.json()["id"]
            await confirm_all_facts(pid, buyer, "aislos")
            with patch(
                "app.services.procurement_ai._call_orchestrator",
                new=AsyncMock(return_value=orch_response(scenario="high", items=VILLA_ITEMS[:1])),
            ):
                analyzed = await ac.post(
                    f"{BASE}/projects/{pid}/analyze",
                    json={},
                    headers=auth(buyer, "aislos"),
                )
            await freeze_reviewed_boq(
                pid, buyer, admin, "aislos", version_id=analyzed.json()["boq_version_id"]
            )
            gen = await ac.post(
                f"{BASE}/projects/{pid}/packages/generate",
                headers=auth(buyer, "aislos"),
            )
            pkg_id = gen.json()["packages"][0]["id"]
            await ac.patch(
                f"{BASE}/projects/{pid}/packages/{pkg_id}",
                json={"status": "ready"},
                headers=auth(buyer, "aislos"),
            )
            await ac.post(
                f"{BASE}/projects/{pid}/packages/{pkg_id}/publish-rfq",
                json=commercial_terms(),
                headers=auth(buyer, "aislos"),
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
            assert row.payload_json["portal_key"] == "aislos"
            assert "price_visibility_rule" in row.payload_json

    asyncio.run(_run())

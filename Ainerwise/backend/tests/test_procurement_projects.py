"""C03: procurement projects, portal isolation, transfer and file attach."""
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.portal_context import PortalContext, get_portal_context
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.integration import IntegrationEvent
from app.models.procurement import ProcurementProject
from app.models.user import User
from app.services.portal_policy import (
    activate_policy,
    create_policy_version,
    ensure_default_policies,
    get_active_policy,
    retire_active_policy,
)

BASE = "/api/v1/procurement"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register_buyer(email: str | None = None) -> tuple[User, str]:
    email = email or f"buyer-{uuid.uuid4().hex[:8]}@test.local"
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


async def _register_admin() -> tuple[User, str]:
    email = f"admin-{uuid.uuid4().hex[:8]}@test.local"
    async with async_session_factory() as db:
        user = User(
            email=email,
            password_hash=hash_password("testpass123"),
            full_name="Test Admin",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token(str(user.id), user.role)
    return user, token


def _auth(token: str, portal_key: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: portal_key,
    }


async def _seed_defaults() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


async def _ensure_aislos_managed_policy() -> None:
    """Reset aislos to a known managed policy (prior tests may leave self_service active)."""
    from app.models.portal_policy import PHASE1_PROJECT_TYPES

    async with async_session_factory() as db:
        await retire_active_policy(db, "aislos")
        policy = await create_policy_version(
            db,
            "aislos",
            default_procurement_mode="managed",
            allowed_project_types_json=list(PHASE1_PROJECT_TYPES),
            price_visibility_rule="customer_totals_only",
            supplier_visibility_rule="hidden",
        )
        await activate_policy(db, policy)
        await db.commit()


def _project_payload(project_type: str = "villa_smart_home") -> dict:
    return {
        "project_type": project_type,
        "title": "Test Villa Project",
        "description": "Phase 1 test",
        "country": "PH",
        "city": "Cebu",
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def test_procurement_project_routes_registered():
    paths = {r.path for r in app.routes}
    for sub in (
        f"{BASE}/projects",
        f"{BASE}/projects/{{project_id}}",
        f"{BASE}/projects/{{project_id}}/transfer-portal",
        f"{BASE}/projects/{{project_id}}/files",
        f"{BASE}/projects/{{project_id}}/facts",
        f"{BASE}/projects/{{project_id}}/facts/{{fact_id}}",
    ):
        assert sub in paths, sub


# ---------------------------------------------------------------------------
# Create + portal isolation
# ---------------------------------------------------------------------------

def test_create_project_sets_portal_and_initializes_facts():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()
        async with _client() as ac:
            r = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["portal_key"] == "aislos"
        assert body["status"] == "draft"
        assert body["owner_user_id"] == str(user.id)
        assert body["facts_score"] == "0.000"
        assert body["policy_snapshot_json"]["portal_key"] == "aislos"
        assert "villa_smart_home" in body["policy_snapshot_json"]["allowed_project_types"]

        async with _client() as ac:
            facts = await ac.get(
                f"{BASE}/projects/{body['id']}/facts",
                headers=_auth(token, "aislos"),
            )
        assert facts.status_code == 200
        keys = {f["template_key"] for f in facts.json()}
        for required_key in (
            "property_area_sqm",
            "floor_count",
            "room_count",
            "target_budget",
            "installation_timeline",
            "existing_network_infra",
            "primary_use_case",
        ):
            assert required_key in keys
        assert "preferred_brands" not in keys  # optional in template

    asyncio.run(_t())


def test_portal_isolation_same_user_different_portals():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()

        async with _client() as ac:
            ra = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
            rc = await ac.post(
                f"{BASE}/projects",
                json={**_project_payload(), "title": "Cebu Hotel"},
                headers=_auth(token, "cebu"),
            )
        assert ra.status_code == 201 and rc.status_code == 201
        aislos_id = ra.json()["id"]
        cebu_id = rc.json()["id"]

        async with _client() as ac:
            list_a = await ac.get(f"{BASE}/projects", headers=_auth(token, "aislos"))
            list_c = await ac.get(f"{BASE}/projects", headers=_auth(token, "cebu"))
            cross = await ac.get(
                f"{BASE}/projects/{cebu_id}",
                headers=_auth(token, "aislos"),
            )
        assert list_a.status_code == 200
        assert list_c.status_code == 200
        assert len(list_a.json()["items"]) == 1
        assert len(list_c.json()["items"]) == 1
        assert list_a.json()["items"][0]["id"] == aislos_id
        assert list_c.json()["items"][0]["id"] == cebu_id
        assert cross.status_code == 404

    asyncio.run(_t())


def test_reject_disallowed_project_type():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:8]}"
        async with async_session_factory() as db:
            policy = await create_policy_version(
                db,
                portal_key,
                default_procurement_mode="managed",
                allowed_project_types_json=["villa_smart_home"],
                price_visibility_rule="customer_totals_only",
                supplier_visibility_rule="hidden",
            )
            await activate_policy(db, policy)
            await db.commit()

        user, token = await _register_buyer()
        async with _client() as ac:
            r = await ac.post(
                f"{BASE}/projects",
                json=_project_payload("small_hotel_smart_upgrade"),
                headers=_auth(token, portal_key),
            )
        assert r.status_code == 400
        assert "not allowed" in r.json()["detail"].lower()

    asyncio.run(_t())


def test_policy_snapshot_unchanged_after_policy_update():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        await _ensure_aislos_managed_policy()
        user, token = await _register_buyer()

        async with _client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        assert created.status_code == 201
        project = created.json()
        snapshot_v1 = dict(project["policy_snapshot_json"])

        async with async_session_factory() as db:
            active = await get_active_policy(db, "aislos")
            assert active is not None
            await retire_active_policy(db, "aislos")
            new_policy = await create_policy_version(
                db,
                "aislos",
                default_procurement_mode="self_service",
                allowed_project_types_json=["villa_smart_home", "small_hotel_smart_upgrade"],
                price_visibility_rule="line_estimates",
                supplier_visibility_rule="hidden",
            )
            await activate_policy(db, new_policy)
            await db.commit()

        async with _client() as ac:
            fetched = await ac.get(
                f"{BASE}/projects/{project['id']}",
                headers=_auth(token, "aislos"),
            )
        assert fetched.status_code == 200
        assert fetched.json()["policy_snapshot_json"] == snapshot_v1
        assert fetched.json()["policy_snapshot_json"]["default_procurement_mode"] == "managed"

        # Restore defaults so later portal-policy tests see frozen seed state.
        await _ensure_aislos_managed_policy()

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# Transfer portal
# ---------------------------------------------------------------------------

def test_transfer_portal_admin_requires_reason():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()
        _, admin_token = await _register_admin()

        async with _client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        project_id = created.json()["id"]

        async with _client() as ac:
            no_reason = await ac.post(
                f"{BASE}/projects/{project_id}/transfer-portal",
                json={"target_portal_key": "cebu"},
                headers=_auth(admin_token, "aislos"),
            )
            not_admin = await ac.post(
                f"{BASE}/projects/{project_id}/transfer-portal",
                json={"target_portal_key": "cebu", "reason": "customer request"},
                headers=_auth(token, "aislos"),
            )
        assert no_reason.status_code == 422
        assert not_admin.status_code == 403

    asyncio.run(_t())


def test_transfer_portal_success_with_audit_and_outbox():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()
        _, admin_token = await _register_admin()

        async with _client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        project_id = created.json()["id"]
        old_snapshot = created.json()["policy_snapshot_json"]

        async with _client() as ac:
            transferred = await ac.post(
                f"{BASE}/projects/{project_id}/transfer-portal",
                json={"target_portal_key": "cebu", "reason": "customer moved to Cebu portal"},
                headers=_auth(admin_token, "aislos"),
            )
        assert transferred.status_code == 200, transferred.text
        body = transferred.json()
        assert body["portal_key"] == "cebu"
        assert body["policy_snapshot_json"]["portal_key"] == "cebu"
        assert body["policy_snapshot_json"] != old_snapshot

        async with async_session_factory() as db:
            audits = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(
                        AuditLog.action == "procurement.project.portal_transferred",
                        AuditLog.entity_id == uuid.UUID(project_id),
                    )
                )
            ).scalar()
            events = (
                await db.execute(
                    select(func.count()).select_from(IntegrationEvent).where(
                        IntegrationEvent.event_type == "procurement.project.portal_transferred",
                        IntegrationEvent.aggregate_id == uuid.UUID(project_id),
                    )
                )
            ).scalar()
        assert audits == 1
        assert events == 1

    asyncio.run(_t())


def test_transfer_fails_without_target_active_policy():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()
        _, admin_token = await _register_admin()

        async with _client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        project_id = created.json()["id"]

        async with _client() as ac:
            r = await ac.post(
                f"{BASE}/projects/{project_id}/transfer-portal",
                json={"target_portal_key": "no-such-portal", "reason": "test"},
                headers=_auth(admin_token, "aislos"),
            )
        assert r.status_code == 400

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# File attach
# ---------------------------------------------------------------------------

def test_file_attach_creates_asset_and_audit():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()

        async with _client() as ac:
            created = await ac.post(
                f"{BASE}/projects",
                json=_project_payload(),
                headers=_auth(token, "aislos"),
            )
        project_id = created.json()["id"]

        async with _client() as ac:
            attached = await ac.post(
                f"{BASE}/projects/{project_id}/files",
                json={
                    "original_name": "floorplan.pdf",
                    "storage_path": "uploads/test/floorplan.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 1024,
                },
                headers=_auth(token, "aislos"),
            )
            cross = await ac.post(
                f"{BASE}/projects/{project_id}/files",
                json={
                    "original_name": "hack.pdf",
                    "storage_path": "uploads/hack.pdf",
                },
                headers=_auth(token, "cebu"),
            )
        assert attached.status_code == 201, attached.text
        assert attached.json()["entity_type"] == "procurement_project"
        assert attached.json()["entity_id"] == project_id
        assert cross.status_code == 404

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# Transaction atomicity
# ---------------------------------------------------------------------------

def test_create_rolls_back_audit_on_commit_failure():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        user, token = await _register_buyer()

        async with async_session_factory() as db:
            before_projects = (
                await db.execute(select(func.count()).select_from(ProcurementProject))
            ).scalar()
            before_audits = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(
                        AuditLog.action == "procurement.project.created"
                    )
                )
            ).scalar()
            try:
                from app.core.portal_context import PortalContext
                from app.services.procurement_projects import create_project

                policy = await get_active_policy(db, "aislos")
                ctx = PortalContext(portal_key="aislos", policy=policy)
                project, _ = await create_project(
                    db,
                    user=user,
                    ctx=ctx,
                    project_type="villa_smart_home",
                    title="rollback test",
                )
                from app.services.audit import append_audit_event

                await append_audit_event(
                    db,
                    actor_type="user",
                    actor_user_id=user.id,
                    portal_key="aislos",
                    action="procurement.project.created",
                    entity_type="procurement_project",
                    entity_id=project.id,
                    require_procurement_action=True,
                )
                await db.flush()
                raise RuntimeError("business failure")
            except RuntimeError:
                await db.rollback()

            after_projects = (
                await db.execute(select(func.count()).select_from(ProcurementProject))
            ).scalar()
            after_audits = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(
                        AuditLog.action == "procurement.project.created"
                    )
                )
            ).scalar()
            assert after_projects == before_projects
            assert after_audits == before_audits

    asyncio.run(_t())

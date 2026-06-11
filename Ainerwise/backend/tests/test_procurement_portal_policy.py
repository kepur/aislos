"""C01: trusted Portal Context + versioned Portal Policy.

Conventions follow existing integration tests: sync test functions drive a
fresh event loop via asyncio.run() and dispose the module-level engine first.
Constraint tests never commit, so the live database is left unchanged except
for the idempotent aislos/cebu default policies (also seeded by migration 024).
"""
import asyncio
import uuid
from pathlib import Path

import pytest
import sqlalchemy.exc
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.portal_context import PortalContext, get_portal_context
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_policy import FROZEN_CONFIDENCE_GATE, PHASE1_PROJECT_TYPES, PortalPolicy
from app.services.portal_policy import (
    PortalPolicyError,
    activate_policy,
    create_policy_version,
    ensure_default_policies,
    get_active_policy,
    retire_active_policy,
    validate_policy,
)

POLICY_URL = "/api/v1/procurement/portal-policy"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _seed_defaults() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


def _default_kwargs() -> dict:
    return dict(
        default_procurement_mode="managed",
        allowed_project_types_json=list(PHASE1_PROJECT_TYPES),
        price_visibility_rule="customer_totals_only",
        supplier_visibility_rule="hidden",
        lead_routing_rule_json={"queue": "test_queue"},
    )


# ---------------------------------------------------------------------------
# Routing / wiring
# ---------------------------------------------------------------------------

def test_portal_policy_route_registered():
    paths = {r.path for r in app.routes}
    assert POLICY_URL in paths


def test_nginx_injects_trusted_portal_header():
    """Forged external X-Portal-Key headers must be overwritten at the gateway."""
    conf = Path(__file__).resolve().parents[2] / "nginx" / "default.conf"
    if not conf.exists():
        # Backend container only mounts backend/; the gateway config is
        # checked when tests run from the full repository checkout.
        pytest.skip("nginx config not available in this environment")
    text = conf.read_text()
    assert 'proxy_set_header X-Portal-Key "aislos";' in text
    assert 'proxy_set_header X-Portal-Key "cebu";' in text


# ---------------------------------------------------------------------------
# Default policies
# ---------------------------------------------------------------------------

def test_default_policies_seeded_and_differ():
    async def _t():
        await engine.dispose()
        async with async_session_factory() as db:
            policies = await ensure_default_policies(db)
            await db.commit()
            a, c = policies["aislos"], policies["cebu"]
            assert a.status == "active" and c.status == "active"
            assert a.default_procurement_mode == "managed"
            assert c.default_procurement_mode == "self_service"
            assert a.price_visibility_rule == "customer_totals_only"
            assert c.price_visibility_rule == "line_estimates"
            assert a.supplier_visibility_rule == "hidden"
            assert c.supplier_visibility_rule == "visible_when_self_service"
            assert a.allowed_project_types_json == list(PHASE1_PROJECT_TYPES)
            assert c.allowed_project_types_json == list(PHASE1_PROJECT_TYPES)
            # Both portals share the frozen confidence gate.
            assert a.confidence_gate_json == FROZEN_CONFIDENCE_GATE
            assert c.confidence_gate_json == FROZEN_CONFIDENCE_GATE
            assert validate_policy(a) == [] and validate_policy(c) == []

            # Idempotent: a second call keeps the same active versions.
            again = await ensure_default_policies(db)
            assert again["aislos"].id == a.id and again["cebu"].id == c.id

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# API behavior
# ---------------------------------------------------------------------------

def test_api_returns_different_policies_per_portal():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        async with _client() as ac:
            ra = await ac.get(POLICY_URL, headers={"X-Portal-Key": "aislos"})
            rc = await ac.get(POLICY_URL, headers={"X-Portal-Key": "cebu"})
        assert ra.status_code == 200, ra.text
        assert rc.status_code == 200, rc.text
        a, c = ra.json(), rc.json()
        assert a["portal_key"] == "aislos" and c["portal_key"] == "cebu"
        assert a["default_procurement_mode"] == "managed"
        assert c["default_procurement_mode"] == "self_service"
        assert a["price_visibility_rule"] == "customer_totals_only"
        assert c["price_visibility_rule"] == "line_estimates"
        assert a != c

    asyncio.run(_t())


def test_api_supports_dependency_override():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        async with async_session_factory() as db:
            policy = await get_active_policy(db, "cebu")
        assert policy is not None

        async def _override() -> PortalContext:
            return PortalContext(portal_key="cebu", policy=policy)

        app.dependency_overrides[get_portal_context] = _override
        try:
            async with _client() as ac:
                r = await ac.get(POLICY_URL)
        finally:
            app.dependency_overrides.pop(get_portal_context, None)
        assert r.status_code == 200
        assert r.json()["portal_key"] == "cebu"

    asyncio.run(_t())


def test_api_hides_internal_lead_routing():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        async with _client() as ac:
            r = await ac.get(POLICY_URL, headers={"X-Portal-Key": "aislos"})
        assert r.status_code == 200
        body = r.json()
        assert "lead_routing_rule" not in r.text
        assert "lead_routing_rule_json" not in body
        assert "aislos_sales" not in r.text
        assert "created_by" not in body

    asyncio.run(_t())


def test_api_fails_closed_without_portal():
    async def _t():
        await engine.dispose()
        original = settings.PROCUREMENT_DEFAULT_PORTAL_KEY
        settings.PROCUREMENT_DEFAULT_PORTAL_KEY = ""
        try:
            async with _client() as ac:
                r = await ac.get(POLICY_URL)
        finally:
            settings.PROCUREMENT_DEFAULT_PORTAL_KEY = original
        assert r.status_code == 400

    asyncio.run(_t())


def test_api_fails_closed_when_no_active_policy():
    async def _t():
        await engine.dispose()
        async with _client() as ac:
            r = await ac.get(POLICY_URL, headers={"X-Portal-Key": "no-such-portal"})
        assert r.status_code == 503

    asyncio.run(_t())


def test_api_rejects_malformed_portal_key():
    async def _t():
        await engine.dispose()
        async with _client() as ac:
            r = await ac.get(POLICY_URL, headers={"X-Portal-Key": "'; DROP TABLE x; --"})
        assert r.status_code == 400

    asyncio.run(_t())


def test_client_cannot_switch_portal_via_query():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        async with _client() as ac:
            r = await ac.get(
                POLICY_URL,
                headers={"X-Portal-Key": "aislos"},
                params={"portal_key": "cebu", "portal": "cebu"},
            )
        assert r.status_code == 200
        assert r.json()["portal_key"] == "aislos"

    asyncio.run(_t())


def test_local_dev_default_portal_fallback():
    async def _t():
        await engine.dispose()
        await _seed_defaults()
        original = settings.PROCUREMENT_DEFAULT_PORTAL_KEY
        settings.PROCUREMENT_DEFAULT_PORTAL_KEY = "aislos"
        try:
            async with _client() as ac:
                r = await ac.get(POLICY_URL)
        finally:
            settings.PROCUREMENT_DEFAULT_PORTAL_KEY = original
        assert r.status_code == 200
        assert r.json()["portal_key"] == "aislos"

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# Versioning / activation constraints (no commit: DB state is rolled back)
# ---------------------------------------------------------------------------

def test_second_active_policy_rejected_by_service_and_db():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:10]}"
        async with async_session_factory() as db:
            try:
                p1 = await create_policy_version(db, portal_key, **_default_kwargs())
                await activate_policy(db, p1)
                p2 = await create_policy_version(db, portal_key, **_default_kwargs())
                assert p2.version == 2

                # Service refuses to activate without retiring the old version.
                service_raised = False
                try:
                    await activate_policy(db, p2)
                except PortalPolicyError:
                    service_raised = True
                assert service_raised

                # The partial unique index also blocks a raw bypass.
                p2.status = "active"
                db_raised = False
                try:
                    await db.flush()
                except sqlalchemy.exc.IntegrityError:
                    db_raised = True
                assert db_raised
            finally:
                await db.rollback()

    asyncio.run(_t())


def test_retire_then_activate_new_version():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:10]}"
        async with async_session_factory() as db:
            try:
                p1 = await create_policy_version(db, portal_key, **_default_kwargs())
                await activate_policy(db, p1)
                retired = await retire_active_policy(db, portal_key)
                assert retired is not None and retired.id == p1.id
                assert retired.status == "retired"

                p2 = await create_policy_version(db, portal_key, **_default_kwargs())
                await activate_policy(db, p2)
                active = await get_active_policy(db, portal_key)
                assert active is not None and active.id == p2.id and active.version == 2

                # A retired policy can never come back.
                raised = False
                try:
                    await activate_policy(db, p1)
                except PortalPolicyError:
                    raised = True
                assert raised
            finally:
                await db.rollback()

    asyncio.run(_t())


def test_unique_portal_key_version_constraint():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:10]}"
        async with async_session_factory() as db:
            try:
                kwargs = _default_kwargs()
                db.add(PortalPolicy(portal_key=portal_key, version=1, status="draft", **kwargs))
                db.add(PortalPolicy(portal_key=portal_key, version=1, status="draft", **kwargs))
                raised = False
                try:
                    await db.flush()
                except sqlalchemy.exc.IntegrityError:
                    raised = True
                assert raised
            finally:
                await db.rollback()

    asyncio.run(_t())


# ---------------------------------------------------------------------------
# Policy legality (fail closed)
# ---------------------------------------------------------------------------

def test_confidence_gate_cannot_be_loosened():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:10]}"
        async with async_session_factory() as db:
            try:
                loosened = dict(FROZEN_CONFIDENCE_GATE)
                loosened["ask_below"] = "0.300"
                raised = False
                try:
                    await create_policy_version(
                        db, portal_key, **_default_kwargs(), confidence_gate_json=loosened
                    )
                except PortalPolicyError:
                    raised = True
                assert raised
            finally:
                await db.rollback()

    asyncio.run(_t())


def test_project_types_outside_phase1_rejected():
    async def _t():
        await engine.dispose()
        portal_key = f"tp{uuid.uuid4().hex[:10]}"
        async with async_session_factory() as db:
            try:
                kwargs = _default_kwargs()
                kwargs["allowed_project_types_json"] = ["villa_smart_home", "office"]
                raised = False
                try:
                    await create_policy_version(db, portal_key, **kwargs)
                except PortalPolicyError:
                    raised = True
                assert raised
            finally:
                await db.rollback()

    asyncio.run(_t())


def test_validate_policy_flags_illegal_active_policy():
    policy = PortalPolicy(
        portal_key="broken",
        version=1,
        status="active",
        default_procurement_mode="free_for_all",
        allowed_project_types_json=[],
        price_visibility_rule="",
        supplier_visibility_rule="hidden",
        confidence_gate_json={},
    )
    problems = validate_policy(policy)
    assert problems  # fail closed in get_portal_context

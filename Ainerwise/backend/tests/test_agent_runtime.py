"""V3 Phase G: agent registry, enforceable grants, explicit run identity."""
import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import AGENT_GRANT_SCOPES
from tests.route_utils import registered_route_paths


def test_agent_routes_registered():
    paths = registered_route_paths(app)
    for p in ("/api/v1/admin/agents", "/api/v1/admin/agents/{slug}", "/api/v1/admin/agents/{slug}/grants"):
        assert p in paths, p


def test_official_agents_seeded_with_grants():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.agent import Agent, AgentGrant

            agents = (await db.execute(select(Agent).where(Agent.vendor == "official"))).scalars().all()
            slugs = {a.slug for a in agents}
            assert {"marketing-agent", "sales-agent", "procurement-agent",
                    "business-brain", "support-agent"} <= slugs

            marketing = next(a for a in agents if a.slug == "marketing-agent")
            assert "content_gen" in (marketing.workflows_json or [])
            grants = (
                await db.execute(select(AgentGrant).where(AgentGrant.agent_id == marketing.id))
            ).scalars().all()
            assert {g.scope for g in grants} == set(AGENT_GRANT_SCOPES)
            granted = {g.scope for g in grants if g.granted}
            assert "ads" in granted
            assert "payment" not in granted  # money actions never default-on

            support = next(a for a in agents if a.slug == "support-agent")
            assert support.status == "active"
            support_grants = (
                await db.execute(select(AgentGrant).where(AgentGrant.agent_id == support.id, AgentGrant.granted))
            ).scalars().all()
            assert {g.scope for g in support_grants} == {"project_data"}

    asyncio.run(_run())


def test_agent_runtime_enforces_status_and_grants():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.agent_runtime import AgentAuthorizationError, require_agent

            agent = await require_agent(
                db,
                "marketing-agent",
                scopes=("product_data", "project_data"),
                workflow="content_gen",
            )
            assert agent.slug == "marketing-agent"

            with pytest.raises(AgentAuthorizationError, match="lacks required grants: payment"):
                await require_agent(db, "marketing-agent", scopes=("payment",))

            with pytest.raises(AgentAuthorizationError, match="not allowed to run workflow"):
                await require_agent(db, "marketing-agent", workflow="quote_draft")

            support = await require_agent(
                db,
                "support-agent",
                scopes=("project_data",),
                workflow="ticket_triage",
            )
            assert support.slug == "support-agent"

    asyncio.run(_run())


def test_agent_stats_use_explicit_identity_not_shared_workflow_names():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.api.v1.endpoints.agents import _agent_stats
            from app.models.ai import AgentRun

            before = await _agent_stats(db, "support-agent")
            db.add(
                AgentRun(
                    agent_slug="support-agent",
                    workflow="consult",
                    status="completed",
                    tokens_in=2,
                    tokens_out=3,
                )
            )
            await db.flush()
            after = await _agent_stats(db, "support-agent")
            assert after["runs_30d"] == before["runs_30d"] + 1
            assert after["tokens_30d"] == before["tokens_30d"] + 5
            await db.rollback()

    asyncio.run(_run())


def test_third_party_runtime_requires_exact_workspace_installation_and_grants():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.agent import Agent, AgentGrant, AgentObjectGrant
            from app.models.ecosystem import AgentInstallation, MarketplaceListing
            from app.models.portal_access import Workspace
            from app.models.user import User
            from app.services.agent_runtime import AgentAuthorizationError, require_agent

            suffix = uuid.uuid4().hex[:10]
            user = User(
                email=f"third-party-runtime-{suffix}@example.com",
                password_hash="unused",
                role="buyer",
            )
            workspace_a = Workspace(name=f"Runtime A {suffix}", slug=f"runtime-a-{suffix}")
            workspace_b = Workspace(name=f"Runtime B {suffix}", slug=f"runtime-b-{suffix}")
            agent = Agent(
                slug=f"runtime-third-party-{suffix}",
                name="Runtime Third Party",
                vendor="third_party",
                workflows_json=["inspect"],
                status="active",
            )
            db.add_all([user, workspace_a, workspace_b, agent])
            await db.flush()
            listing = MarketplaceListing(
                agent_id=agent.id,
                developer_user_id=user.id,
                slug=agent.slug,
                name=agent.name,
                status="approved",
            )
            db.add(listing)
            await db.flush()
            project_id = uuid.uuid4()
            db.add_all(
                [
                    AgentInstallation(
                        listing_id=listing.id,
                        agent_id=agent.id,
                        installed_by=user.id,
                        workspace_id=workspace_a.id,
                        status="installed",
                        installed_at=datetime.now(timezone.utc),
                    ),
                    AgentInstallation(
                        listing_id=listing.id,
                        agent_id=agent.id,
                        installed_by=user.id,
                        workspace_id=workspace_b.id,
                        status="installed",
                        installed_at=datetime.now(timezone.utc),
                    ),
                    AgentGrant(
                        agent_id=agent.id,
                        workspace_id=None,
                        scope="project_data",
                        granted=True,
                    ),
                    AgentGrant(
                        agent_id=agent.id,
                        workspace_id=workspace_a.id,
                        scope="project_data",
                        granted=True,
                    ),
                    AgentGrant(
                        agent_id=agent.id,
                        workspace_id=workspace_b.id,
                        scope="project_data",
                        granted=False,
                    ),
                    AgentObjectGrant(
                        agent_id=agent.id,
                        workspace_id=workspace_a.id,
                        object_type="project",
                        object_id=project_id,
                        scope="project_data",
                        granted=True,
                    ),
                ]
            )
            await db.flush()

            with pytest.raises(AgentAuthorizationError, match="explicit Workspace"):
                await require_agent(db, agent.slug, scopes=("project_data",), workflow="inspect")
            with pytest.raises(AgentAuthorizationError, match="lacks required grants"):
                await require_agent(
                    db,
                    agent.slug,
                    scopes=("project_data",),
                    workflow="inspect",
                    workspace_id=workspace_b.id,
                )
            authorized = await require_agent(
                db,
                agent.slug,
                scopes=("project_data",),
                workflow="inspect",
                object_type="project",
                object_id=project_id,
                workspace_id=workspace_a.id,
            )
            assert authorized.id == agent.id
            await db.rollback()

    asyncio.run(_run())


def test_third_party_agent_cannot_be_activated_before_sandbox_release_gate():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.api.v1.endpoints.agents import AgentConfigUpdate, update_agent
            from app.models.agent import Agent
            from app.models.user import User

            suffix = uuid.uuid4().hex[:10]
            admin = User(
                email=f"sandbox-admin-{suffix}@example.com",
                password_hash="unused",
                role="super_admin",
            )
            agent = Agent(
                slug=f"sandbox-gate-{suffix}",
                name="Sandbox Gate",
                vendor="third_party",
                status="paused",
            )
            db.add_all([admin, agent])
            await db.flush()
            with pytest.raises(HTTPException) as exc:
                await update_agent(
                    agent.slug,
                    AgentConfigUpdate(status="active"),
                    db,
                    admin,
                )
            assert exc.value.status_code == 409
            assert agent.status == "paused"
            await db.rollback()

    asyncio.run(_run())

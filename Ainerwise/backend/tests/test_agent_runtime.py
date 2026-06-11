"""V3 Phase G: agent registry, enforceable grants, explicit run identity."""
import asyncio

import pytest

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import AGENT_GRANT_SCOPES


def test_agent_routes_registered():
    paths = {r.path for r in app.routes}
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

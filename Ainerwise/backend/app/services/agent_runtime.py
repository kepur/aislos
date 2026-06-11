"""Runtime authorization for registered digital employees.

Agents are role-oriented callers of business capabilities. This gate makes
their active/paused state and explicit data grants enforceable at execution
time instead of treating the Agent Console as descriptive metadata.
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from app.models.agent import Agent, AgentGrant, AgentObjectGrant


class AgentAuthorizationError(RuntimeError):
    pass


async def require_agent(
    db: AsyncSession,
    slug: str,
    *,
    scopes: Iterable[str] = (),
    workflow: str | None = None,
    object_type: str | None = None,
    object_id: uuid.UUID | None = None,
) -> Agent:
    agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one_or_none()
    if agent is None:
        raise AgentAuthorizationError(f"Agent '{slug}' is not registered")
    if agent.status != "active":
        raise AgentAuthorizationError(f"Agent '{slug}' is {agent.status}")
    if workflow is not None and workflow not in (agent.workflows_json or []):
        raise AgentAuthorizationError(
            f"Agent '{slug}' is not allowed to run workflow '{workflow}'"
        )

    required = set(scopes)
    if required:
        granted = set(
            (
                await db.execute(
                    select(AgentGrant.scope).where(
                        AgentGrant.agent_id == agent.id,
                        AgentGrant.granted.is_(True),
                    )
                )
            ).scalars()
        )
        missing = sorted(required - granted)
        if missing:
            raise AgentAuthorizationError(
                f"Agent '{slug}' lacks required grants: {', '.join(missing)}"
            )
        if object_type is not None and object_id is not None:
            object_grants = set(
                (
                    await db.execute(
                        select(AgentObjectGrant.scope).where(
                            AgentObjectGrant.agent_id == agent.id,
                            AgentObjectGrant.object_type == object_type,
                            AgentObjectGrant.object_id == object_id,
                            AgentObjectGrant.granted.is_(True),
                        )
                    )
                ).scalars()
            )
            missing_object = sorted(required - object_grants)
            if missing_object:
                raise AgentAuthorizationError(
                    f"Agent '{slug}' lacks {object_type} {object_id} grants: "
                    f"{', '.join(missing_object)}"
                )
    return agent

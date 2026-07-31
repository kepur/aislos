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
from app.models.ecosystem import AgentInstallation


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
    workspace_id: uuid.UUID | None = None,
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
    if agent.vendor == "third_party":
        if workspace_id is None:
            raise AgentAuthorizationError(
                f"Third-party Agent '{slug}' requires an explicit Workspace"
            )
        installation = (
            await db.execute(
                select(AgentInstallation.id).where(
                    AgentInstallation.agent_id == agent.id,
                    AgentInstallation.workspace_id == workspace_id,
                    AgentInstallation.status == "installed",
                )
            )
        ).scalar_one_or_none()
        if installation is None:
            raise AgentAuthorizationError(
                f"Third-party Agent '{slug}' is not installed in Workspace {workspace_id}"
            )

    required = set(scopes)
    if required:
        grant_workspace_scope = (
            AgentGrant.workspace_id == workspace_id
            if agent.vendor == "third_party"
            else AgentGrant.workspace_id.is_(None)
        )
        granted = set(
            (
                await db.execute(
                    select(AgentGrant.scope).where(
                        AgentGrant.agent_id == agent.id,
                        AgentGrant.granted.is_(True),
                        grant_workspace_scope,
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
            object_workspace_scope = (
                AgentObjectGrant.workspace_id == workspace_id
                if workspace_id is not None
                else AgentObjectGrant.workspace_id.is_(None)
            )
            object_grants = set(
                (
                    await db.execute(
                        select(AgentObjectGrant.scope).where(
                            AgentObjectGrant.agent_id == agent.id,
                            AgentObjectGrant.object_type == object_type,
                            AgentObjectGrant.object_id == object_id,
                            AgentObjectGrant.granted.is_(True),
                            object_workspace_scope,
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

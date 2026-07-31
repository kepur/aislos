"""Agent Console API: digital-employee directory and per-agent control."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.agent import AGENT_GRANT_SCOPES, Agent, AgentGrant
from app.models.ecosystem import AgentInstallation
from app.models.ai import AgentRun
from app.services.audit import log_action
from app.services.portal_access import resolve_workspace_scope

router = APIRouter(prefix="/admin/agents", tags=["agents"])


class AgentConfigUpdate(BaseModel):
    config_json: dict | None = None
    status: str | None = None


class GrantUpdate(BaseModel):
    scope: str
    granted: bool
    workspace_id: uuid.UUID | None = None


async def _agent_grant_workspace(db: DB, admin: AdminUser, agent: Agent, workspace_id: uuid.UUID | None):
    if agent.vendor != "third_party":
        return None
    try:
        resolved = await resolve_workspace_scope(
            db,
            user_id=admin.id,
            requested_workspace_id=workspace_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if resolved is None:
        raise HTTPException(status_code=400, detail="workspace_id is required for third-party Agents")
    installed = (
        await db.execute(
            select(AgentInstallation.id).where(
                AgentInstallation.agent_id == agent.id,
                AgentInstallation.workspace_id == resolved,
                AgentInstallation.status == "installed",
            )
        )
    ).scalar_one_or_none()
    if installed is None:
        raise HTTPException(status_code=409, detail="Agent is not installed in the selected Workspace")
    return resolved


async def _agent_stats(db, agent_slug: str) -> dict:
    from sqlalchemy import text as sql_text

    row = (
        await db.execute(
            select(
                func.count(AgentRun.id),
                func.coalesce(func.sum(func.coalesce(AgentRun.tokens_in, 0) + func.coalesce(AgentRun.tokens_out, 0)), 0),
                func.max(AgentRun.created_at),
            ).where(
                AgentRun.agent_slug == agent_slug,
                AgentRun.created_at >= sql_text("now() - interval '30 days'"),
            )
        )
    ).first()
    return {
        "runs_30d": int(row[0] or 0),
        "tokens_30d": int(row[1] or 0),
        "last_run_at": row[2].isoformat() if row[2] else None,
    }


def _agent_dict(agent: Agent) -> dict:
    return {
        "id": str(agent.id), "slug": agent.slug, "name": agent.name,
        "role_title": agent.role_title, "description": agent.description,
        "vendor": agent.vendor, "workflows": agent.workflows_json or [],
        "config_json": agent.config_json, "status": agent.status,
        "price_monthly": float(agent.price_monthly) if agent.price_monthly is not None else None,
    }


@router.get("")
async def list_agents(db: DB, admin: AdminUser):
    agents = (await db.execute(select(Agent).order_by(Agent.vendor, Agent.name))).scalars().all()
    items = []
    for agent in agents:
        data = _agent_dict(agent)
        data["stats"] = await _agent_stats(db, agent.slug)
        items.append(data)
    return {"items": items}


@router.get("/{slug}")
async def get_agent(slug: str, db: DB, admin: AdminUser, workspace_id: uuid.UUID | None = None):
    agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    grant_workspace_id = await _agent_grant_workspace(db, admin, agent, workspace_id)
    grants = (
        await db.execute(
            select(AgentGrant)
            .where(
                AgentGrant.agent_id == agent.id,
                (
                    AgentGrant.workspace_id == grant_workspace_id
                    if grant_workspace_id is not None
                    else AgentGrant.workspace_id.is_(None)
                ),
            )
            .order_by(AgentGrant.scope)
        )
    ).scalars().all()
    grants_by_scope = {grant.scope: grant for grant in grants}
    runs = (
        await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_slug == agent.slug)
            .order_by(AgentRun.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    return {
        **_agent_dict(agent),
        "stats": await _agent_stats(db, agent.slug),
        "grants": [
            {
                "scope": scope,
                "workspace_id": str(grant_workspace_id) if grant_workspace_id else None,
                "granted": bool(grants_by_scope.get(scope) and grants_by_scope[scope].granted),
                "granted_at": (
                    grants_by_scope[scope].granted_at.isoformat()
                    if grants_by_scope.get(scope) and grants_by_scope[scope].granted_at
                    else None
                ),
            }
            for scope in AGENT_GRANT_SCOPES
        ],
        "recent_runs": [
            {"workflow": r.workflow, "status": r.status, "latency_ms": r.latency_ms,
             "tokens": (r.tokens_in or 0) + (r.tokens_out or 0),
             "created_at": r.created_at.isoformat()}
            for r in runs
        ],
    }


@router.patch("/{slug}")
async def update_agent(slug: str, data: AgentConfigUpdate, db: DB, admin: AdminUser):
    agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    before = {"config_json": agent.config_json, "status": agent.status}
    if data.config_json is not None:
        agent.config_json = data.config_json
    if data.status is not None:
        if data.status not in ("active", "paused"):
            raise HTTPException(status_code=400, detail="status must be active|paused")
        if agent.vendor == "third_party" and data.status == "active":
            raise HTTPException(
                status_code=409,
                detail="Third-party Agent execution remains blocked until the sandbox release gate is complete",
            )
        agent.status = data.status
    db.add(agent)
    await log_action(
        db,
        actor_user_id=admin.id,
        action="agent_update",
        entity_type="agent",
        entity_id=agent.id,
        before=before,
        after={"config_json": agent.config_json, "status": agent.status},
    )
    await db.refresh(agent)
    return _agent_dict(agent)


@router.post("/{slug}/grants")
async def update_grant(slug: str, data: GrantUpdate, db: DB, admin: AdminUser):
    if data.scope not in AGENT_GRANT_SCOPES:
        raise HTTPException(status_code=400, detail=f"Unknown scope. Valid: {AGENT_GRANT_SCOPES}")
    agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    grant_workspace_id = await _agent_grant_workspace(db, admin, agent, data.workspace_id)
    grant = (
        await db.execute(
            select(AgentGrant).where(
                AgentGrant.agent_id == agent.id,
                AgentGrant.scope == data.scope,
                (
                    AgentGrant.workspace_id == grant_workspace_id
                    if grant_workspace_id is not None
                    else AgentGrant.workspace_id.is_(None)
                ),
            )
        )
    ).scalar_one_or_none()
    if grant is None:
        grant = AgentGrant(agent_id=agent.id, workspace_id=grant_workspace_id, scope=data.scope)
    before = {
        "scope": data.scope,
        "workspace_id": str(grant_workspace_id) if grant_workspace_id else None,
        "granted": grant.granted,
    }
    grant.granted = data.granted
    grant.granted_by = admin.id
    grant.granted_at = datetime.now(timezone.utc) if data.granted else None
    db.add(grant)
    await db.flush()
    await log_action(
        db,
        actor_user_id=admin.id,
        action="agent_grant_update",
        entity_type="agent_grant",
        entity_id=grant.id,
        before=before,
        after={
            "scope": grant.scope,
            "workspace_id": str(grant_workspace_id) if grant_workspace_id else None,
            "granted": grant.granted,
        },
    )
    return {
        "scope": grant.scope,
        "workspace_id": str(grant_workspace_id) if grant_workspace_id else None,
        "granted": grant.granted,
    }

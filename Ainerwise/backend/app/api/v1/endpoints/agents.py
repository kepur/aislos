"""Agent Console API: digital-employee directory and per-agent control."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.agent import AGENT_GRANT_SCOPES, Agent, AgentGrant
from app.models.ai import AgentRun
from app.services.audit import log_action

router = APIRouter(prefix="/admin/agents", tags=["agents"])


class AgentConfigUpdate(BaseModel):
    config_json: dict | None = None
    status: str | None = None


class GrantUpdate(BaseModel):
    scope: str
    granted: bool


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
async def get_agent(slug: str, db: DB, admin: AdminUser):
    agent = (await db.execute(select(Agent).where(Agent.slug == slug))).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    grants = (
        await db.execute(select(AgentGrant).where(AgentGrant.agent_id == agent.id).order_by(AgentGrant.scope))
    ).scalars().all()
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
            {"scope": g.scope, "granted": g.granted,
             "granted_at": g.granted_at.isoformat() if g.granted_at else None}
            for g in grants
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
    grant = (
        await db.execute(
            select(AgentGrant).where(AgentGrant.agent_id == agent.id, AgentGrant.scope == data.scope)
        )
    ).scalar_one_or_none()
    if grant is None:
        grant = AgentGrant(agent_id=agent.id, scope=data.scope)
    before = {"scope": data.scope, "granted": grant.granted}
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
        after={"scope": grant.scope, "granted": grant.granted},
    )
    return {"scope": grant.scope, "granted": grant.granted}

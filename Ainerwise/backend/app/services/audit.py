"""Audit logging service.

- ``append_audit_event()`` — procurement-grade, flush-only, participates in caller transaction.
- ``log_action()`` — legacy helper; commits immediately (existing endpoints only).
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

ActorType = Literal["user", "agent", "system"]

PROCUREMENT_AUDIT_ACTIONS = frozenset(
    {
        "procurement.project.created",
        "procurement.project.portal_transferred",
        "procurement.file.attached",
        "procurement.fact.created",
        "procurement.fact.updated",
        "procurement.fact.confirmed",
        "procurement.ai.started",
        "procurement.ai.completed",
        "procurement.ai.failed",
        "procurement.boq.generated",
        "procurement.boq.reviewed",
        "procurement.boq.frozen",
        "procurement.package.generated",
        "procurement.package.updated",
        "procurement.commercial_snapshot.created",
        "procurement.rfq.published",
    }
)

_ACTION_RE = re.compile(r"^[a-z][a-z0-9_.]{2,119}$")


class AuditEventError(ValueError):
    pass


def _validate_audit_fields(
    *,
    actor_type: ActorType,
    action: str,
    entity_type: str,
    actor_user_id: uuid.UUID | None,
    agent_slug: str | None,
) -> None:
    if actor_type not in ("user", "agent", "system"):
        raise AuditEventError(f"invalid actor_type: {actor_type!r}")
    if not _ACTION_RE.match(action):
        raise AuditEventError(f"invalid action: {action!r}")
    if not entity_type or len(entity_type) > 50:
        raise AuditEventError("entity_type required (max 50 chars)")
    if actor_type == "user" and actor_user_id is None:
        raise AuditEventError("actor_user_id required when actor_type is user")
    if actor_type == "agent" and not agent_slug:
        raise AuditEventError("agent_slug required when actor_type is agent")


async def append_audit_event(
    db: AsyncSession,
    *,
    actor_type: ActorType,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    agent_slug: str | None = None,
    portal_key: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
    source: str | None = None,
    correlation_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    require_procurement_action: bool = False,
) -> AuditLog:
    """Record an immutable audit row without committing the session."""
    if require_procurement_action and action not in PROCUREMENT_AUDIT_ACTIONS:
        raise AuditEventError(f"action not in procurement allowlist: {action!r}")

    _validate_audit_fields(
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        actor_user_id=actor_user_id,
        agent_slug=agent_slug,
    )

    entry = AuditLog(
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        agent_slug=agent_slug,
        portal_key=portal_key,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
        reason=reason,
        source=source,
        correlation_id=correlation_id,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


async def log_action(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Legacy audit helper — commits immediately. Do not use in new procurement flows."""
    entry = await append_audit_event(
        db,
        actor_type="user" if actor_user_id else "system",
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        ip=ip,
        source="legacy.log_action",
    )
    await db.commit()
    await db.refresh(entry)
    return entry

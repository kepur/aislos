import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, RiskLevel


async def create_audit_log(
    db: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    actor_role: str | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    risk_level: RiskLevel = RiskLevel.LOW,
) -> AuditLog:
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        actor_role=actor_role,
        before_json=before_json,
        after_json=after_json,
        ip_address=ip_address,
        user_agent=user_agent,
        risk_level=risk_level,
    )
    db.add(log)
    await db.flush()
    return log

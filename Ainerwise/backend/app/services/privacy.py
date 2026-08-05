from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.agent import AgentObjectGrant
from app.models.ai import Conversation
from app.models.audit import AuditLog
from app.models.commerce import BuyerWatchlistItem, CommerceMessage, OrderDispute, ProcurementRequest
from app.models.ecosystem import AgentInstallation
from app.models.field_service import CrewMembership, TaskAssignment, TaskEvidence
from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.notification import NotificationPreference, PortalNotification
from app.models.portal_access import PortalGrant, WorkspaceMembership
from app.models.privacy import PrivacyRequest
from app.models.procurement import ProcurementProject
from app.models.service import ServicePartner
from app.models.ticket import Ticket
from app.models.user import PasswordResetToken, User


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _row_dict(row: Any, *, exclude: set[str] | None = None) -> dict[str, Any]:
    excluded = exclude or set()
    return {
        column.name: _json_value(getattr(row, column.name))
        for column in row.__table__.columns
        if column.name not in excluded
    }


async def _collect(
    db: AsyncSession,
    model: Any,
    criterion: Any,
    *,
    exclude: set[str] | None = None,
) -> list[dict[str, Any]]:
    rows = (await db.execute(select(model).where(criterion).order_by(model.created_at.asc()))).scalars().all()
    return [_row_dict(row, exclude=exclude) for row in rows]


async def build_user_export(db: AsyncSession, user: User) -> dict[str, Any]:
    """Build a current, user-owned export without persisting another PII snapshot."""
    data = {
        "profile": _row_dict(
            user,
            exclude={"password_hash", "last_login_at"},
        ),
        "workspace_memberships": await _collect(db, WorkspaceMembership, WorkspaceMembership.user_id == user.id),
        "portal_grants": await _collect(db, PortalGrant, PortalGrant.user_id == user.id),
        "notification_preferences": await _collect(db, NotificationPreference, NotificationPreference.user_id == user.id),
        "portal_notifications": await _collect(db, PortalNotification, PortalNotification.user_id == user.id),
        "leads": await _collect(db, Lead, Lead.buyer_user_id == user.id),
        "inquiries": await _collect(db, Inquiry, Inquiry.buyer_user_id == user.id),
        "tickets": await _collect(db, Ticket, Ticket.buyer_user_id == user.id),
        "procurement_projects": await _collect(db, ProcurementProject, ProcurementProject.owner_user_id == user.id),
        "procurement_requests": await _collect(db, ProcurementRequest, ProcurementRequest.buyer_user_id == user.id),
        "watchlist": await _collect(db, BuyerWatchlistItem, BuyerWatchlistItem.buyer_user_id == user.id),
        "commerce_messages": await _collect(db, CommerceMessage, CommerceMessage.sender_user_id == user.id),
        "order_disputes": await _collect(db, OrderDispute, OrderDispute.opened_by_user_id == user.id),
        "service_partner_profiles": await _collect(db, ServicePartner, ServicePartner.user_id == user.id),
        "crew_memberships": await _collect(db, CrewMembership, CrewMembership.user_id == user.id),
        "task_assignments": await _collect(db, TaskAssignment, TaskAssignment.assignee_user_id == user.id),
        "task_evidence": await _collect(db, TaskEvidence, TaskEvidence.captured_by == user.id),
        "agent_installations": await _collect(db, AgentInstallation, AgentInstallation.installed_by == user.id),
        "conversations": await _collect(db, Conversation, Conversation.user_id == user.id),
        "agent_object_grants": await _collect(db, AgentObjectGrant, AgentObjectGrant.granted_by == user.id),
        "audit_activity": await _collect(
            db,
            AuditLog,
            AuditLog.actor_user_id == user.id,
            exclude={"before_json", "after_json"},
        ),
    }
    return {
        "schema_version": "privacy-export-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user.id),
        "data": data,
    }


async def anonymize_user(db: AsyncSession, user: User) -> None:
    """Deactivate personal access while retaining immutable business evidence."""
    now = datetime.now(timezone.utc)
    await db.execute(
        update(WorkspaceMembership)
        .where(WorkspaceMembership.user_id == user.id)
        .values(status="inactive", valid_until=now)
    )
    await db.execute(
        update(PortalGrant)
        .where(PortalGrant.user_id == user.id)
        .values(granted=False, revoked_at=now)
    )
    await db.execute(
        update(CrewMembership)
        .where(CrewMembership.user_id == user.id)
        .values(status="inactive", valid_until=now)
    )
    await db.execute(
        update(TaskAssignment)
        .where(TaskAssignment.assignee_user_id == user.id, TaskAssignment.status == "active")
        .values(status="revoked", valid_until=now, reason="privacy deletion completed")
    )
    await db.execute(
        update(NotificationPreference)
        .where(NotificationPreference.user_id == user.id)
        .values(
            telegram_enabled=False,
            email_enabled=False,
            whatsapp_enabled=False,
            viber_enabled=False,
            telegram_chat_id=None,
            email=None,
            whatsapp_number=None,
            viber_number=None,
        )
    )
    await db.execute(delete(PortalNotification).where(PortalNotification.user_id == user.id))
    await db.execute(delete(BuyerWatchlistItem).where(BuyerWatchlistItem.buyer_user_id == user.id))
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

    user.email = f"deleted+{user.id}@privacy.invalid"
    user.phone = None
    user.full_name = "Deleted User"
    user.country = None
    user.company_id = None
    user.password_hash = hash_password(secrets.token_urlsafe(48))
    user.is_active = False
    user.last_login_at = None
    db.add(user)

"""Phase 2: commerce in-app notifications and buyer–supplier threads."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import (
    CommerceMessage,
    CommerceOrder,
    CommerceThread,
    ProcurementRequest,
)
from app.models.notification import PortalNotification
from app.models.user import User
from app.modules.commerce.access import (
    customer_commerce_workspace_ids,
    user_is_order_party,
    user_owns_procurement_request,
)
from app.services.event_bus import emit_event

COMMERCE_NOTIFY_TEMPLATES: dict[str, tuple[str, str]] = {
    "procurement.offer.submitted": ("New supplier offer", "A supplier submitted an offer on your request."),
    "procurement.offer.awarded": ("Offer awarded", "Your offer was awarded — order confirmed."),
    "commerce.order.awarded": ("Order confirmed", "An order was created from your procurement request."),
    "commerce.delivery.shipped": ("Shipment dispatched", "Your order has been shipped."),
    "commerce.delivery.delivered": ("Delivery arrived", "Your order was marked as delivered."),
    "commerce.dispute.opened": ("Dispute opened", "A dispute was opened on the order."),
    "commerce.order.completed": ("Order completed", "The commerce order was completed."),
}


class CommerceMessagingError(ValueError):
    pass


class CommerceMessagingAccessDenied(CommerceMessagingError):
    pass


async def _company_user_ids(db: AsyncSession, company_id: uuid.UUID | None) -> list[uuid.UUID]:
    if not company_id:
        return []
    rows = await db.execute(
        select(User.id).where(User.company_id == company_id, User.is_active.is_(True))
    )
    return [r[0] for r in rows.all()]


async def notify_company_users(
    db: AsyncSession,
    *,
    company_ids: list[uuid.UUID],
    portal_key: str,
    event_type: str,
    title: str,
    body: str | None,
    link_path: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: uuid.UUID | None = None,
    exclude_user_id: uuid.UUID | None = None,
) -> list[PortalNotification]:
    created: list[PortalNotification] = []
    seen_users: set[uuid.UUID] = set()
    for company_id in company_ids:
        for user_id in await _company_user_ids(db, company_id):
            if user_id in seen_users or user_id == exclude_user_id:
                continue
            seen_users.add(user_id)
            row = PortalNotification(
                user_id=user_id,
                portal_key=portal_key,
                domain="commerce",
                event_type=event_type,
                title=title,
                body=body,
                link_path=link_path,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
            )
            db.add(row)
            created.append(row)
    if created:
        await db.flush()
        await emit_event(
            db,
            "commerce.notification.created",
            {
                "event_type": event_type,
                "recipient_count": len(created),
                "aggregate_type": aggregate_type,
                "aggregate_id": str(aggregate_id) if aggregate_id else None,
            },
            aggregate_type=aggregate_type or "portal_notification",
            aggregate_id=aggregate_id or created[0].id,
        )
    return created


async def notify_from_template(
    db: AsyncSession,
    *,
    event_type: str,
    company_ids: list[uuid.UUID],
    portal_key: str,
    link_path: str | None = None,
    aggregate_type: str | None = None,
    aggregate_id: uuid.UUID | None = None,
    title: str | None = None,
    body: str | None = None,
    exclude_user_id: uuid.UUID | None = None,
) -> list[PortalNotification]:
    default_title, default_body = COMMERCE_NOTIFY_TEMPLATES.get(event_type, (event_type, ""))
    return await notify_company_users(
        db,
        company_ids=company_ids,
        portal_key=portal_key,
        event_type=event_type,
        title=title or default_title,
        body=body or default_body,
        link_path=link_path,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        exclude_user_id=exclude_user_id,
    )


async def get_or_create_thread_for_request(
    db: AsyncSession, req: ProcurementRequest, *, supplier_company_id: uuid.UUID | None = None
) -> CommerceThread:
    q = select(CommerceThread).where(CommerceThread.procurement_request_id == req.id)
    if supplier_company_id:
        q = q.where(CommerceThread.supplier_company_id == supplier_company_id)
    row = (await db.execute(q)).scalar_one_or_none()
    if row:
        if row.workspace_id != req.workspace_id:
            raise CommerceMessagingError("thread and request belong to different Workspaces")
        return row
    if req.workspace_id is None:
        raise CommerceMessagingError("procurement request requires a Workspace")
    row = CommerceThread(
        workspace_id=req.workspace_id,
        portal_key=req.portal_key,
        procurement_request_id=req.id,
        buyer_company_id=req.buyer_company_id,
        supplier_company_id=supplier_company_id,
        subject=req.title,
    )
    db.add(row)
    await db.flush()
    return row


async def get_or_create_thread_for_order(db: AsyncSession, order: CommerceOrder) -> CommerceThread:
    row = (
        await db.execute(
            select(CommerceThread).where(CommerceThread.commerce_order_id == order.id)
        )
    ).scalar_one_or_none()
    if row:
        if row.workspace_id != order.workspace_id:
            raise CommerceMessagingError("thread and order belong to different Workspaces")
        return row
    req = await db.get(ProcurementRequest, order.procurement_request_id)
    subject = req.title if req else f"Order {order.id}"
    if order.workspace_id is None:
        raise CommerceMessagingError("commerce order requires a Workspace")
    if req is not None and req.workspace_id != order.workspace_id:
        raise CommerceMessagingError("request and order belong to different Workspaces")
    row = CommerceThread(
        workspace_id=order.workspace_id or (req.workspace_id if req else None),
        portal_key=req.portal_key if req else "cebu",
        procurement_request_id=order.procurement_request_id,
        commerce_order_id=order.id,
        buyer_company_id=order.buyer_company_id,
        supplier_company_id=order.supplier_company_id,
        subject=subject,
    )
    db.add(row)
    await db.flush()
    return row


async def _thread_party(db: AsyncSession, user: User, thread: CommerceThread) -> str | None:
    if user.role in ("admin", "super_admin"):
        return "admin"
    if thread.supplier_company_id and user.company_id == thread.supplier_company_id:
        return "supplier"
    if thread.buyer_company_id and user.company_id == thread.buyer_company_id:
        if thread.procurement_request_id:
            request = await db.get(ProcurementRequest, thread.procurement_request_id)
            if request and await user_owns_procurement_request(db, user, request):
                return "buyer"
            return None
        if thread.commerce_order_id:
            order = await db.get(CommerceOrder, thread.commerce_order_id)
            if order and await user_is_order_party(db, user, order) == "buyer":
                return "buyer"
            return None
        if thread.workspace_id is None:
            return "buyer"
        if thread.workspace_id in await customer_commerce_workspace_ids(db, user):
            return "buyer"
    return None


async def post_thread_message(
    db: AsyncSession,
    *,
    thread_id: uuid.UUID,
    user: User,
    body: str,
    attachments_json: dict | None = None,
) -> CommerceMessage:
    thread = await db.get(CommerceThread, thread_id)
    if thread is None:
        raise CommerceMessagingError("thread not found")
    if thread.status != "open":
        raise CommerceMessagingError("thread is closed")
    if thread.workspace_id is None:
        raise CommerceMessagingError("commerce thread requires a Workspace")
    party = await _thread_party(db, user, thread)
    if party is None:
        raise CommerceMessagingAccessDenied("not a participant")
    row = CommerceMessage(
        workspace_id=thread.workspace_id,
        thread_id=thread_id,
        sender_user_id=user.id,
        sender_role=party,
        body=body,
        attachments_json=attachments_json,
    )
    db.add(row)
    await db.flush()
    other_company = (
        thread.supplier_company_id if party == "buyer" else thread.buyer_company_id
    )
    if other_company:
        await notify_company_users(
            db,
            company_ids=[other_company],
            portal_key=thread.portal_key,
            event_type="commerce.message.received",
            title="New message",
            body=body[:200],
            link_path=f"/commerce/threads/{thread_id}",
            aggregate_type="commerce_thread",
            aggregate_id=thread_id,
            exclude_user_id=user.id,
        )
    await emit_event(
        db,
        "commerce.message.posted",
        {"thread_id": str(thread_id), "message_id": str(row.id)},
        aggregate_type="commerce_thread",
        aggregate_id=thread_id,
    )
    return row


async def list_thread_messages(
    db: AsyncSession, thread: CommerceThread
) -> list[CommerceMessage]:
    result = await db.execute(
        select(CommerceMessage)
        .where(
            CommerceMessage.thread_id == thread.id,
            CommerceMessage.workspace_id == thread.workspace_id,
        )
        .order_by(CommerceMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def list_user_notifications(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    portal_key: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[PortalNotification]:
    q = (
        select(PortalNotification)
        .where(PortalNotification.user_id == user_id, PortalNotification.domain == "commerce")
        .order_by(PortalNotification.created_at.desc())
        .limit(limit)
    )
    if portal_key:
        q = q.where(PortalNotification.portal_key == portal_key)
    if status:
        q = q.where(PortalNotification.status == status)
    return list((await db.execute(q)).scalars())


async def unread_notification_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    return (
        await db.execute(
            select(func.count())
            .select_from(PortalNotification)
            .where(
                PortalNotification.user_id == user_id,
                PortalNotification.domain == "commerce",
                PortalNotification.status == "unread",
            )
        )
    ).scalar_one()


async def mark_notification_read(
    db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> PortalNotification:
    row = await db.get(PortalNotification, notification_id)
    if row is None or row.user_id != user_id:
        raise CommerceMessagingError("notification not found")
    if row.status == "unread":
        row.status = "read"
        row.read_at = datetime.now(timezone.utc)
        await db.flush()
    return row


async def mark_all_notifications_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    rows = list(
        (
            await db.execute(
                select(PortalNotification).where(
                    PortalNotification.user_id == user_id,
                    PortalNotification.domain == "commerce",
                    PortalNotification.status == "unread",
                )
            )
        ).scalars()
    )
    for row in rows:
        row.status = "read"
        row.read_at = now
    await db.flush()
    return len(rows)

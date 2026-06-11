from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.message import Message
from app.models.offer import Offer
from app.models.order import Order
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.notification_service import notify_user

router = APIRouter(tags=["Messages"])


async def resolve_message_recipient(
    db: AsyncSession,
    *,
    thread_type: str,
    thread_id: str,
    sender: User,
):
    normalized = thread_type.lower()
    if normalized in {"order", "orders"}:
        result = await db.execute(select(Order).where(Order.id == thread_id))
        order = result.scalar_one_or_none()
        if not order:
            return None
        if order.buyer_id == sender.id:
            offer_result = await db.execute(select(Offer).where(Offer.id == order.offer_id))
            offer = offer_result.scalar_one_or_none()
            return offer.supplier_user_id if offer else None
        return order.buyer_id

    if normalized in {"offer", "offers"}:
        result = await db.execute(select(Offer).where(Offer.id == thread_id))
        offer = result.scalar_one_or_none()
        if not offer:
            return None
        if offer.supplier_user_id == sender.id:
            order_result = await db.execute(select(Order).where(Order.offer_id == offer.id))
            order = order_result.scalar_one_or_none()
            return order.buyer_id if order else None
        return offer.supplier_user_id

    return None


@router.post("/threads/{thread_type}/{thread_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    thread_type: str,
    thread_id: str,
    req: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = Message(thread_type=thread_type, thread_id=thread_id, sender_id=user.id, body=req.body, attachments=req.attachments)
    db.add(msg)
    recipient_user_id = await resolve_message_recipient(db, thread_type=thread_type, thread_id=thread_id, sender=user)
    if recipient_user_id and recipient_user_id != user.id:
        await notify_user(
            db,
            user_id=recipient_user_id,
            notification_type="MESSAGE_RECEIVED",
            subject="New in-site message",
            body=f"{user.full_name} sent you a new message in the {thread_type} thread.",
        )
    await db.commit()
    await db.refresh(msg)
    return msg


@router.get("/threads/{thread_type}/{thread_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    thread_type: str,
    thread_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message).where(Message.thread_type == thread_type, Message.thread_id == thread_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()

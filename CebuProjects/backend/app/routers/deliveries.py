from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.company import Company
from app.models.delivery import Delivery, DeliveryStatus
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.delivery import DeliveryCreate, DeliveryResponse
from app.services.audit_service import create_audit_log
from app.services.notification_service import notify_user

router = APIRouter(tags=["Deliveries"])


@router.post("/orders/{order_id}/delivery", response_model=DeliveryResponse, status_code=201)
async def create_delivery(
    order_id: str,
    req: DeliveryCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.execute(select(Company).where(Company.id == order.company_id, Company.owner_user_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not your order")

    delivery = Delivery(order_id=order.id, actor_id=user.id, **req.model_dump())
    db.add(delivery)

    status_map = {
        DeliveryStatus.READY_FOR_PICKUP: OrderStatus.IN_PROGRESS,
        DeliveryStatus.DISPATCHED: OrderStatus.IN_PROGRESS,
        DeliveryStatus.DELIVERED: OrderStatus.DELIVERED,
    }
    if req.status in status_map:
        order.status = status_map[req.status]

    await db.flush()
    await create_audit_log(db, action="DELIVERY_PROOF_UPLOADED" if req.proofs else "ORDER_STATUS_CHANGED", entity_type="Delivery", entity_id=delivery.id, actor_id=user.id, actor_role=user.role.value)
    await notify_user(
        db,
        user_id=order.buyer_id,
        notification_type="DELIVERY_UPDATED_BUYER",
        subject="Delivery update",
        body=f"Delivery update: {req.status.value}",
    )

    await db.commit()
    await db.refresh(delivery)
    return delivery


@router.get("/orders/{order_id}/delivery", response_model=list[DeliveryResponse])
async def get_deliveries(order_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Delivery).where(Delivery.order_id == order_id).order_by(Delivery.created_at.desc()))
    return result.scalars().all()

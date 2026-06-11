from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.audit_log import RiskLevel
from app.models.delivery import Delivery, DeliveryStatus
from app.models.escrow import EscrowTransaction, EscrowStatus
from app.models.notification import NotificationChannel
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.models.catalog import CatalogItem
from app.models.company import Company
from app.models.intent import Intent, IntentStatus
from app.models.offer import Offer, OfferStatus, OfferTier, StockConfidence
from app.models.wallet import Wallet, WalletTransaction, WalletTransactionType
from app.schemas.order import OrderCreateFromCatalog, OrderResponse, OrderStatusUpdate
from app.services.audit_service import create_audit_log
from app.services.escrow_service import create_escrow, release_escrow
from app.services.notification_service import create_notification

router = APIRouter(tags=["Orders"])


class PayFromWalletRequest(BaseModel):
    currency: str | None = None
    quote_id: UUID | None = None


async def _enrich_order(order: Order, db: AsyncSession) -> OrderResponse:
    escrow_row = (await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == order.id))).scalar_one_or_none()
    delivery_row = (await db.execute(select(Delivery).where(Delivery.order_id == order.id).order_by(Delivery.created_at.desc()))).scalar_one_or_none()
    data = {
        "id": order.id,
        "offer_id": order.offer_id,
        "intent_id": order.intent_id,
        "buyer_id": order.buyer_id,
        "company_id": order.company_id,
        "branch_id": order.branch_id,
        "total_amount_minor": order.total_amount_minor,
        "currency": order.currency,
        "status": order.status,
        "notes": None,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "escrow": escrow_row,
        "delivery": delivery_row,
    }
    return OrderResponse.model_validate(data)


@router.get("/orders/my", response_model=list[OrderResponse])
async def list_my_orders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.company import Company

    if user.role == UserRole.BUYER:
        q = select(Order).where(Order.buyer_id == user.id)
    elif user.role in (UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT):
        company_result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
        company = company_result.scalar_one_or_none()
        if not company:
            return []
        q = select(Order).where(Order.company_id == company.id)
    else:
        q = select(Order)

    orders = (await db.execute(q.order_by(Order.created_at.desc()))).scalars().all()
    return [await _enrich_order(o, db) for o in orders]


@router.post("/orders", response_model=OrderResponse)
async def create_b2c_order(
    req: OrderCreateFromCatalog,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db)
):
    import uuid as _uuid
    # 1. Fetch catalog item & company
    item = (await db.execute(select(CatalogItem).where(CatalogItem.id == req.catalog_item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Catalog item not found")
    if item.status.value != "ACTIVE":
        raise HTTPException(400, "Item is not active")
    if req.qty < (item.min_order_qty or 1):
        raise HTTPException(400, f"Minimum order quantity is {item.min_order_qty}")
    if item.stock_qty < req.qty:
        raise HTTPException(400, f"Insufficient stock. Available: {item.stock_qty}")

    company = (await db.execute(select(Company).where(Company.id == item.company_id))).scalar_one_or_none()
    if not company or not company.owner_user_id:
        raise HTTPException(400, "Supplier company invalid")

    # 2. Deduct stock
    item.stock_qty -= req.qty
    item.order_count = (item.order_count or 0) + 1

    # 3. Create dummy intent
    intent = Intent(
        id=_uuid.uuid4(),
        buyer_id=user.id,
        category_id=item.category_id,
        title=f"B2C Direct Order: {item.title}",
        qty=req.qty,
        unit=item.unit,
        currency=item.currency,
        status=IntentStatus.AWARDED,
        attrs_jsonb={"b2c_direct_buy": True, "catalog_item_id": str(item.id)}
    )
    db.add(intent)

    total_minor = item.price_minor * req.qty

    # 4. Create dummy offer
    offer = Offer(
        id=_uuid.uuid4(),
        intent_id=intent.id,
        company_id=item.company_id,
        catalog_item_id=item.id,
        supplier_user_id=company.owner_user_id,
        unit_price_minor=item.price_minor,
        qty_available=req.qty,
        total_price_minor=total_minor,
        currency=item.currency,
        tier=OfferTier.GOOD,
        stock_confidence=StockConfidence.FIRM,
        status=OfferStatus.AWARDED,
        message="Auto-generated offer for B2C checkout"
    )
    db.add(offer)

    # 5. Create order
    order = Order(
        id=_uuid.uuid4(),
        offer_id=offer.id,
        intent_id=intent.id,
        buyer_id=user.id,
        company_id=item.company_id,
        branch_id=None,
        total_amount_minor=total_minor,
        currency=item.currency,
        status=OrderStatus.AWAITING_PAYMENT,
    )
    db.add(order)

    # 6. Optionally create delivery record if address provided
    if req.delivery_address_id or req.delivery_city:
        delivery = Delivery(
            id=_uuid.uuid4(),
            order_id=order.id,
            actor_id=user.id,
            tracking_number=None,
            carrier=None,
            status=DeliveryStatus.PENDING,
        )
        db.add(delivery)

    await db.commit()
    await db.refresh(order)
    return await _enrich_order(order, db)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await _enrich_order(order, db)


@router.post("/orders/{order_id}/accept", response_model=OrderResponse)
async def accept_order(
    order_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id, Order.buyer_id == user.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Order must be in DELIVERED status")

    order.status = OrderStatus.ACCEPTED

    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == order.id))
    escrow = result.scalar_one_or_none()
    if escrow:
        await release_escrow(db, escrow)

    order.status = OrderStatus.PAYOUT_RELEASED

    await create_audit_log(db, action="ORDER_ACCEPTED", entity_type="Order", entity_id=order.id, actor_id=user.id, actor_role=user.role.value, risk_level=RiskLevel.MEDIUM)
    await create_audit_log(db, action="ESCROW_STATUS_CHANGED", entity_type="EscrowTransaction", entity_id=escrow.id if escrow else None, actor_id=user.id, risk_level=RiskLevel.HIGH)

    await db.commit()
    await db.refresh(order)
    return await _enrich_order(order, db)


@router.post("/admin/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: str,
    req: OrderStatusUpdate,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    order.status = req.status

    await create_audit_log(
        db, action="ORDER_STATUS_CHANGED", entity_type="Order", entity_id=order.id,
        actor_id=user.id, actor_role=user.role.value,
        before_json={"status": old_status.value}, after_json={"status": req.status.value},
        risk_level=RiskLevel.HIGH,
    )
    await create_audit_log(db, action="ADMIN_MANUAL_ACTION", entity_type="Order", entity_id=order.id, actor_id=user.id, actor_role=user.role.value, risk_level=RiskLevel.CRITICAL)

    await db.commit()
    await db.refresh(order)
    return await _enrich_order(order, db)


@router.post("/orders/{order_id}/pay-from-wallet", response_model=OrderResponse)
async def pay_order_from_wallet(
    order_id: str,
    req: PayFromWalletRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deduct from the buyer's configured currency wallet and fund order escrow."""
    # Fetch order
    result = await db.execute(select(Order).where(Order.id == order_id, Order.buyer_id == user.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.AWAITING_PAYMENT:
        raise HTTPException(400, f"Order is not awaiting payment (current status: {order.status.value})")

    amount_needed = order.total_amount_minor
    if not amount_needed or amount_needed <= 0:
        raise HTTPException(400, "Order has no payable amount")

    payment_currency = (req.currency if req and req.currency else order.currency or "PHP").upper()

    # Find buyer's wallet in the payable currency.
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.owner_user_id == user.id, Wallet.currency == payment_currency)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(400, f"No {payment_currency} wallet found. Please deposit first.")
    if wallet.available_balance_minor < amount_needed:
        raise HTTPException(400, (
            f"Insufficient balance. Need {amount_needed / 100:.2f} {payment_currency}, "
            f"have {wallet.available_balance_minor / 100:.2f} {payment_currency}."
        ))

    # Deduct from wallet
    balance_before = wallet.available_balance_minor
    wallet.available_balance_minor -= amount_needed
    wallet.locked_balance_minor = getattr(wallet, 'locked_balance_minor', 0) + amount_needed

    # Record wallet transaction
    import uuid as _uuid
    tx = WalletTransaction(
        id=_uuid.uuid4(),
        owner_user_id=user.id,
        wallet_id=wallet.id,
        tx_type=WalletTransactionType.ESCROW_LOCK,
        amount_delta_minor=-amount_needed,
        available_balance_after_minor=wallet.available_balance_minor,
        locked_balance_after_minor=wallet.locked_balance_minor,
        currency=payment_currency,
        reference_type="Order",
        reference_id=order.id,
        note=f"Escrow payment for order #{str(order.id)[:8]}",
    )
    db.add(tx)

    # Create or update escrow
    existing_escrow = (await db.execute(
        select(EscrowTransaction).where(EscrowTransaction.order_id == order.id)
    )).scalar_one_or_none()
    if existing_escrow:
        existing_escrow.status = EscrowStatus.CAPTURED
        existing_escrow.auth_amount_minor = amount_needed
        existing_escrow.captured_amount_minor = amount_needed
        existing_escrow.currency = payment_currency
    else:
        escrow = await create_escrow(db, order_id=order.id, amount_minor=amount_needed, currency=payment_currency)
        escrow.status = EscrowStatus.CAPTURED
        escrow.captured_amount_minor = amount_needed

    # Advance order status
    order.status = OrderStatus.PAID_IN_ESCROW

    await create_audit_log(
        db,
        action="ORDER_PAID_FROM_WALLET",
        entity_type="Order",
        entity_id=order.id,
        actor_id=user.id,
        before_json={"balance": balance_before, "status": "AWAITING_PAYMENT"},
        after_json={"balance": wallet.available_balance_minor, "status": "PAID_IN_ESCROW"},
        risk_level=RiskLevel.HIGH,
    )

    await db.commit()
    await db.refresh(order)
    return await _enrich_order(order, db)

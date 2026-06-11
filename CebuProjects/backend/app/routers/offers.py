from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.audit_log import RiskLevel
from app.models.company import Company
from app.models.escrow import EscrowStatus
from app.models.intent import Intent, IntentStatus
from app.models.offer import Offer, OfferStatus
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.offer import OfferCreate, OfferResponse
from app.services.audit_service import create_audit_log
from app.services.escrow_service import create_escrow
from app.services.notification_service import notify_user

router = APIRouter(tags=["Offers"])


@router.post("/intents/{intent_id}/offers", response_model=OfferResponse, status_code=201)
async def submit_offer(
    intent_id: str,
    req: OfferCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = result.scalar_one_or_none()
    if not intent or intent.status != IntentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Intent not available for offers")

    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=400, detail="No company found")

    total = req.unit_price_minor * req.qty_available + req.delivery_fee_minor
    offer = Offer(
        intent_id=intent.id,
        company_id=company.id,
        supplier_user_id=user.id,
        total_price_minor=total,
        **req.model_dump(),
    )
    db.add(offer)
    await db.flush()

    await create_audit_log(db, action="OFFER_SUBMITTED", entity_type="Offer", entity_id=offer.id, actor_id=user.id, actor_role=user.role.value)
    await notify_user(
        db,
        user_id=intent.buyer_id,
        notification_type="NEW_OFFER_FOR_BUYER",
        subject="New offer received",
        body=f"A supplier submitted a new offer for: {intent.title}",
    )

    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("/intents/{intent_id}/offers", response_model=list[OfferResponse])
async def list_offers_for_intent(intent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Offer).where(Offer.intent_id == intent_id).order_by(Offer.created_at.desc()))
    return result.scalars().all()


@router.get("/supplier/offers", response_model=list[OfferResponse])
async def list_my_offers(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Offer).where(Offer.supplier_user_id == user.id).order_by(Offer.created_at.desc()))
    return result.scalars().all()


@router.post("/offers/{offer_id}/withdraw", response_model=OfferResponse)
async def withdraw_offer(
    offer_id: str,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Offer).where(Offer.id == offer_id, Offer.supplier_user_id == user.id))
    offer = result.scalar_one_or_none()
    if not offer or offer.status != OfferStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Cannot withdraw this offer")
    offer.status = OfferStatus.WITHDRAWN
    await db.commit()
    await db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/award", response_model=dict)
async def award_offer(
    offer_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer or offer.status != OfferStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Offer not available")

    result = await db.execute(select(Intent).where(Intent.id == offer.intent_id))
    intent = result.scalar_one_or_none()
    if not intent or intent.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Not your intent")
    if intent.status != IntentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Intent not active")

    offer.status = OfferStatus.AWARDED
    intent.status = IntentStatus.AWARDED

    await db.execute(
        update(Offer)
        .where(Offer.intent_id == intent.id, Offer.id != offer.id, Offer.status == OfferStatus.SUBMITTED)
        .values(status=OfferStatus.REJECTED)
    )

    order = Order(
        offer_id=offer.id,
        intent_id=intent.id,
        buyer_id=user.id,
        company_id=offer.company_id,
        branch_id=offer.branch_id,
        total_amount_minor=offer.total_price_minor,
        currency=offer.currency,
        status=OrderStatus.PAID_IN_ESCROW,
    )
    db.add(order)
    await db.flush()

    escrow = await create_escrow(db, order_id=order.id, amount_minor=offer.total_price_minor, currency=offer.currency)

    await create_audit_log(db, action="OFFER_AWARDED", entity_type="Offer", entity_id=offer.id, actor_id=user.id, actor_role=user.role.value, risk_level=RiskLevel.MEDIUM)
    await create_audit_log(db, action="ORDER_CREATED", entity_type="Order", entity_id=order.id, actor_id=user.id, actor_role=user.role.value)
    await create_audit_log(db, action="ESCROW_STATUS_CHANGED", entity_type="EscrowTransaction", entity_id=escrow.id, actor_id=user.id, risk_level=RiskLevel.HIGH)

    await notify_user(
        db,
        user_id=offer.supplier_user_id,
        notification_type="OFFER_AWARDED_SUPPLIER",
        subject="Offer awarded",
        body="Your offer has been awarded. Review the linked order in your dashboard.",
    )

    await db.commit()
    return {"order_id": str(order.id), "escrow_status": escrow.status.value}

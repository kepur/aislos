from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.audit_log import RiskLevel
from app.models.dispute import Dispute, DisputeStatus
from app.models.escrow import EscrowTransaction
from app.models.notification import NotificationChannel
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeCreate, DisputeResolve, DisputeResponse
from app.services.audit_service import create_audit_log
from app.services.escrow_service import refund_escrow, release_escrow
from app.services.notification_service import create_notification

router = APIRouter(tags=["Disputes"])


@router.post("/orders/{order_id}/dispute", response_model=DisputeResponse, status_code=201)
async def open_dispute(
    order_id: str,
    req: DisputeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in (OrderStatus.DISPUTED, OrderStatus.REFUNDED, OrderStatus.PAYOUT_RELEASED, OrderStatus.CANCELED):
        raise HTTPException(status_code=400, detail="Cannot dispute this order")

    order.status = OrderStatus.DISPUTED

    dispute = Dispute(order_id=order.id, opened_by_user_id=user.id, reason=req.reason, evidence_json=req.evidence)
    db.add(dispute)
    await db.flush()

    await create_audit_log(db, action="DISPUTE_OPENED", entity_type="Dispute", entity_id=dispute.id, actor_id=user.id, actor_role=user.role.value, risk_level=RiskLevel.HIGH)
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.get("/disputes/my", response_model=list[DisputeResponse])
async def list_my_disputes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dispute).where(Dispute.opened_by_user_id == user.id).order_by(Dispute.created_at.desc()))
    return result.scalars().all()


@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(dispute_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@router.post("/disputes/{dispute_id}/evidence", response_model=DisputeResponse)
async def add_evidence(
    dispute_id: str,
    evidence: list[dict],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    existing = dispute.evidence_json or []
    dispute.evidence_json = existing + evidence
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.post("/admin/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: str,
    req: DisputeResolve,
    user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    result = await db.execute(select(Order).where(Order.id == dispute.order_id))
    order = result.scalar_one_or_none()

    result = await db.execute(select(EscrowTransaction).where(EscrowTransaction.order_id == dispute.order_id))
    escrow = result.scalar_one_or_none()

    dispute.resolution = req.resolution
    dispute.refund_amount_minor = req.refund_amount_minor

    if req.decision == "FULL_REFUND":
        dispute.status = DisputeStatus.RESOLVED_REFUND
        if order:
            order.status = OrderStatus.REFUNDED
        if escrow:
            await refund_escrow(db, escrow)
    elif req.decision == "PARTIAL_REFUND":
        dispute.status = DisputeStatus.RESOLVED_PARTIAL_REFUND
        if escrow and req.refund_amount_minor:
            await refund_escrow(db, escrow, req.refund_amount_minor)
        if order:
            order.status = OrderStatus.REFUNDED
    elif req.decision == "RELEASE_TO_SUPPLIER":
        dispute.status = DisputeStatus.RESOLVED_RELEASE
        if order:
            order.status = OrderStatus.PAYOUT_RELEASED
        if escrow:
            await release_escrow(db, escrow)
    elif req.decision == "ESCALATE":
        dispute.status = DisputeStatus.ESCALATED

    await create_audit_log(
        db, action="DISPUTE_RESOLVED", entity_type="Dispute", entity_id=dispute.id,
        actor_id=user.id, actor_role=user.role.value,
        after_json={"decision": req.decision},
        risk_level=RiskLevel.CRITICAL,
    )

    await db.commit()
    await db.refresh(dispute)
    return dispute

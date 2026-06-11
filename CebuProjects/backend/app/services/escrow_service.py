import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.escrow import EscrowProvider, EscrowStatus, EscrowTransaction


async def create_escrow(db: AsyncSession, *, order_id: uuid.UUID, amount_minor: int, currency: str) -> EscrowTransaction:
    status = EscrowStatus.CAPTURED if settings.ESCROW_AUTO_CAPTURE else EscrowStatus.AUTH_HELD
    tx = EscrowTransaction(
        order_id=order_id,
        provider=EscrowProvider.SIMULATED,
        auth_amount_minor=amount_minor,
        captured_amount_minor=amount_minor if settings.ESCROW_AUTO_CAPTURE else 0,
        currency=currency,
        status=status,
    )
    db.add(tx)
    await db.flush()
    return tx


async def release_escrow(db: AsyncSession, tx: EscrowTransaction) -> EscrowTransaction:
    tx.released_amount_minor = tx.captured_amount_minor
    tx.status = EscrowStatus.RELEASED
    await db.flush()
    return tx


async def refund_escrow(db: AsyncSession, tx: EscrowTransaction, amount: int | None = None) -> EscrowTransaction:
    tx.refunded_amount_minor = amount or tx.captured_amount_minor
    if tx.refunded_amount_minor >= tx.captured_amount_minor:
        tx.status = EscrowStatus.REFUNDED
    tx.released_amount_minor = max(0, tx.captured_amount_minor - tx.refunded_amount_minor)
    await db.flush()
    return tx

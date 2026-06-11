import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import (
    DepositStatus,
    Wallet,
    WalletDeposit,
    WalletTransaction,
    WalletTransactionType,
)


async def get_or_create_wallet(db: AsyncSession, *, owner_user_id: uuid.UUID, currency: str = "PHP") -> Wallet:
    normalized = currency.upper()
    result = await db.execute(
        select(Wallet).where(Wallet.owner_user_id == owner_user_id, Wallet.currency == normalized)
    )
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet

    wallet = Wallet(owner_user_id=owner_user_id, currency=normalized)
    db.add(wallet)
    await db.flush()
    return wallet


def make_deposit_address(*, user_id: uuid.UUID, currency: str, network: str) -> str:
    if currency.upper() in {"PHP", "USD", "JPY", "SGD"} or network.upper() in {"LOCAL_BANK", "MANUAL_BANK"}:
        digest = uuid.uuid5(uuid.NAMESPACE_URL, f"{user_id}:{currency}:{network}").hex[:12].upper()
        return f"MANUAL_BANK:{currency.upper()}:{digest}"
    prefix = "T" if network.upper() == "TRC20" else "0x"
    digest = uuid.uuid5(uuid.NAMESPACE_URL, f"{user_id}:{currency}:{network}").hex
    return f"{prefix}{digest[:33]}"


async def add_wallet_tx(
    db: AsyncSession,
    *,
    wallet: Wallet,
    tx_type: WalletTransactionType,
    amount_delta_minor: int,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    note: str | None = None,
    metadata_json: dict | None = None,
) -> WalletTransaction:
    tx = WalletTransaction(
        wallet_id=wallet.id,
        owner_user_id=wallet.owner_user_id,
        tx_type=tx_type,
        amount_delta_minor=amount_delta_minor,
        available_balance_after_minor=wallet.available_balance_minor,
        locked_balance_after_minor=wallet.locked_balance_minor,
        currency=wallet.currency,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        metadata_json=metadata_json or {},
    )
    db.add(tx)
    await db.flush()
    return tx


async def verify_deposit(
    db: AsyncSession,
    *,
    deposit: WalletDeposit,
    wallet: Wallet,
    admin_id: uuid.UUID,
    confirmations: int,
    admin_note: str | None = None,
) -> WalletDeposit:
    deposit.status = DepositStatus.VERIFIED
    deposit.confirmations = confirmations
    deposit.admin_note = admin_note
    deposit.verified_by = admin_id
    deposit.verified_at = datetime.now(timezone.utc)
    wallet.available_balance_minor += deposit.amount_minor
    wallet.total_deposited_minor += deposit.amount_minor
    await add_wallet_tx(
        db,
        wallet=wallet,
        tx_type=WalletTransactionType.DEPOSIT_VERIFIED,
        amount_delta_minor=deposit.amount_minor,
        reference_type="WalletDeposit",
        reference_id=deposit.id,
        note=admin_note,
        metadata_json={"network": deposit.network, "tx_hash": deposit.tx_hash, "confirmations": confirmations},
    )
    return deposit


async def reject_deposit(
    db: AsyncSession,
    *,
    deposit: WalletDeposit,
    wallet: Wallet,
    admin_id: uuid.UUID,
    admin_note: str | None = None,
) -> WalletDeposit:
    deposit.status = DepositStatus.REJECTED
    deposit.admin_note = admin_note
    deposit.rejected_by = admin_id
    deposit.rejected_at = datetime.now(timezone.utc)
    await add_wallet_tx(
        db,
        wallet=wallet,
        tx_type=WalletTransactionType.DEPOSIT_REJECTED,
        amount_delta_minor=0,
        reference_type="WalletDeposit",
        reference_id=deposit.id,
        note=admin_note,
        metadata_json={"network": deposit.network, "tx_hash": deposit.tx_hash},
    )
    return deposit

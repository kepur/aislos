from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.audit_log import RiskLevel
from app.models.payment_event import PaymentEvent
from app.models.user import User, UserRole
from app.models.wallet import DepositStatus, Wallet, WalletDeposit, WalletTransaction, WalletTransactionType
from app.schemas.wallet import (
    DepositAdminDecisionRequest,
    DepositCreateRequest,
    DepositSubmitTxRequest,
    WalletDepositResponse,
    WalletMeResponse,
    WalletResponse,
    WalletTransactionResponse,
)
from app.services.audit_service import create_audit_log
from app.services.payment_service import ensure_currency_enabled
from app.services.trust_service import recalculate_trust_profile
from app.models.trust import TrustEntityType
from app.services.wallet_service import (
    add_wallet_tx,
    get_or_create_wallet,
    make_deposit_address,
    reject_deposit,
    verify_deposit,
)

router = APIRouter(tags=["Wallets"])


@router.get("/wallets/me", response_model=WalletMeResponse)
async def my_wallets(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await get_or_create_wallet(db, owner_user_id=user.id, currency="PHP")
    await db.commit()
    result = await db.execute(select(Wallet).where(Wallet.owner_user_id == user.id).order_by(Wallet.currency.asc()))
    return WalletMeResponse(wallets=[WalletResponse.model_validate(w) for w in result.scalars().all()])


@router.get("/wallets/transactions", response_model=list[WalletTransactionResponse])
async def wallet_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    currency: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(WalletTransaction).where(WalletTransaction.owner_user_id == user.id)
    if currency:
        q = q.where(WalletTransaction.currency == currency.upper())
    result = await db.execute(q.order_by(WalletTransaction.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.post("/wallets/deposits", response_model=WalletDepositResponse, status_code=201)
async def create_deposit(
    req: DepositCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    currency = req.currency.upper()
    network = req.network.upper()
    await ensure_currency_enabled(db, "PH", currency)
    wallet = await get_or_create_wallet(db, owner_user_id=user.id, currency=currency)
    deposit = WalletDeposit(
        wallet_id=wallet.id,
        owner_user_id=user.id,
        amount_minor=req.amount_minor,
        currency=currency,
        network=network,
        provider=req.provider.upper(),
        payment_method=req.payment_method.upper(),
        quote_id=req.quote_id,
        source_currency=(req.source_currency or currency).upper(),
        target_currency=(req.target_currency or currency).upper(),
        deposit_address=make_deposit_address(user_id=user.id, currency=currency, network=network),
    )
    db.add(deposit)
    await db.flush()
    await add_wallet_tx(
        db,
        wallet=wallet,
        tx_type=WalletTransactionType.DEPOSIT_INTENT_CREATED,
        amount_delta_minor=0,
        reference_type="WalletDeposit",
        reference_id=deposit.id,
        metadata_json={"amount_minor": req.amount_minor, "network": deposit.network, "provider": deposit.provider, "payment_method": deposit.payment_method},
    )
    await create_audit_log(
        db,
        action="WALLET_DEPOSIT_CREATED",
        entity_type="WalletDeposit",
        entity_id=deposit.id,
        actor_id=user.id,
        actor_role=user.role.value,
        after_json={"amount_minor": req.amount_minor, "currency": deposit.currency, "network": deposit.network, "provider": deposit.provider, "payment_method": deposit.payment_method},
        risk_level=RiskLevel.MEDIUM,
    )
    await db.commit()
    await db.refresh(deposit)
    return deposit


@router.get("/wallets/deposits/{deposit_id}", response_model=WalletDepositResponse)
async def get_deposit(
    deposit_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deposit = (await db.execute(select(WalletDeposit).where(WalletDeposit.id == deposit_id))).scalar_one_or_none()
    if not deposit or deposit.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Deposit not found")
    return deposit


@router.post("/wallets/deposits/{deposit_id}/submit-tx", response_model=WalletDepositResponse)
async def submit_deposit_tx(
    deposit_id: UUID,
    req: DepositSubmitTxRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deposit = (await db.execute(select(WalletDeposit).where(WalletDeposit.id == deposit_id))).scalar_one_or_none()
    if not deposit or deposit.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Deposit not found")
    if deposit.status not in (DepositStatus.PENDING_TX, DepositStatus.SUBMITTED, DepositStatus.UNDER_REVIEW):
        raise HTTPException(status_code=400, detail=f"Deposit is {deposit.status.value}")
    wallet = (await db.execute(select(Wallet).where(Wallet.id == deposit.wallet_id))).scalar_one()
    deposit.tx_hash = req.tx_hash
    deposit.confirmations = req.confirmations
    deposit.submitter_note = req.submitter_note
    deposit.status = DepositStatus.UNDER_REVIEW
    await add_wallet_tx(
        db,
        wallet=wallet,
        tx_type=WalletTransactionType.DEPOSIT_TX_SUBMITTED,
        amount_delta_minor=0,
        reference_type="WalletDeposit",
        reference_id=deposit.id,
        note=req.submitter_note,
        metadata_json={"tx_hash": req.tx_hash, "confirmations": req.confirmations},
    )
    db.add(PaymentEvent(
        provider=deposit.provider,
        provider_event_id=req.tx_hash,
        event_type="DEPOSIT_TX_SUBMITTED",
        amount_minor=deposit.amount_minor,
        currency=deposit.currency,
        status="UNDER_REVIEW",
        raw_payload={"deposit_id": str(deposit.id), "network": deposit.network, "tx_hash": req.tx_hash, "payment_method": deposit.payment_method},
    ))
    await db.commit()
    await db.refresh(deposit)
    return deposit


@router.get("/admin/deposits", response_model=list[WalletDepositResponse])
async def admin_list_deposits(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.FINANCE_OFFICER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
    status: DepositStatus | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    q = select(WalletDeposit)
    if status:
        q = q.where(WalletDeposit.status == status)
    result = await db.execute(q.order_by(WalletDeposit.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@router.post("/admin/deposits/{deposit_id}/verify", response_model=WalletDepositResponse)
async def admin_verify_deposit(
    deposit_id: UUID,
    req: DepositAdminDecisionRequest,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.FINANCE_OFFICER)),
    db: AsyncSession = Depends(get_db),
):
    deposit = (await db.execute(select(WalletDeposit).where(WalletDeposit.id == deposit_id))).scalar_one_or_none()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    if deposit.status == DepositStatus.VERIFIED:
        raise HTTPException(status_code=400, detail="Deposit already verified")
    wallet = (await db.execute(select(Wallet).where(Wallet.id == deposit.wallet_id))).scalar_one()
    await verify_deposit(db, deposit=deposit, wallet=wallet, admin_id=admin.id, confirmations=req.confirmations, admin_note=req.admin_note)
    db.add(PaymentEvent(
        provider=deposit.provider,
        provider_event_id=deposit.tx_hash,
        event_type="DEPOSIT_VERIFIED",
        amount_minor=deposit.amount_minor,
        currency=deposit.currency,
        status="PROCESSED",
        processed_at=datetime.now(timezone.utc),
        raw_payload={"deposit_id": str(deposit.id), "network": deposit.network, "payment_method": deposit.payment_method},
    ))
    await create_audit_log(
        db,
        action="WALLET_DEPOSIT_VERIFIED",
        entity_type="WalletDeposit",
        entity_id=deposit.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"amount_minor": deposit.amount_minor, "currency": deposit.currency, "confirmations": req.confirmations},
        risk_level=RiskLevel.HIGH,
    )
    await recalculate_trust_profile(db, entity_type=TrustEntityType.USER, entity_id=deposit.owner_user_id)
    await db.commit()
    await db.refresh(deposit)
    return deposit


@router.post("/admin/deposits/{deposit_id}/reject", response_model=WalletDepositResponse)
async def admin_reject_deposit(
    deposit_id: UUID,
    req: DepositAdminDecisionRequest,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.FINANCE_OFFICER, UserRole.RISK_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    deposit = (await db.execute(select(WalletDeposit).where(WalletDeposit.id == deposit_id))).scalar_one_or_none()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    if deposit.status == DepositStatus.VERIFIED:
        raise HTTPException(status_code=400, detail="Verified deposits cannot be rejected")
    wallet = (await db.execute(select(Wallet).where(Wallet.id == deposit.wallet_id))).scalar_one()
    await reject_deposit(db, deposit=deposit, wallet=wallet, admin_id=admin.id, admin_note=req.admin_note)
    db.add(PaymentEvent(
        provider=deposit.provider,
        provider_event_id=deposit.tx_hash,
        event_type="DEPOSIT_REJECTED",
        amount_minor=deposit.amount_minor,
        currency=deposit.currency,
        status="REJECTED",
        processed_at=datetime.now(timezone.utc),
        raw_payload={"deposit_id": str(deposit.id), "network": deposit.network, "payment_method": deposit.payment_method, "admin_note": req.admin_note},
    ))
    await create_audit_log(
        db,
        action="WALLET_DEPOSIT_REJECTED",
        entity_type="WalletDeposit",
        entity_id=deposit.id,
        actor_id=admin.id,
        actor_role=admin.role.value,
        after_json={"reason": req.admin_note},
        risk_level=RiskLevel.HIGH,
    )
    await db.commit()
    await db.refresh(deposit)
    return deposit

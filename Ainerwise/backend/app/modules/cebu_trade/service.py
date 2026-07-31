"""Cebu zero-loss migration services — Wallet, Address, Shipping, Ads, Escrow, Payout."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import CommerceOrder, ProcurementRequest
from app.modules.cebu_trade.models import (
    AdCampaign,
    Address,
    EscrowTransaction,
    OrderShipping,
    Payout,
    ShippingRate,
    ShippingRoute,
    Wallet,
    WalletDeposit,
    WalletTransaction,
)
from app.services.portal_access import get_default_workspace


class CebuTradeError(ValueError):
    pass


async def _ensure_order_workspace(db: AsyncSession, order_id: uuid.UUID) -> uuid.UUID:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CebuTradeError("Order not found")
    if order.workspace_id is None and order.procurement_request_id is not None:
        request = await db.get(ProcurementRequest, order.procurement_request_id)
        if request is not None and request.workspace_id is not None:
            order.workspace_id = request.workspace_id
            await db.flush()
    if order.workspace_id is None:
        workspace = await get_default_workspace(db)
        if workspace is not None and workspace.status == "active":
            order.workspace_id = workspace.id
            await db.flush()
    if order.workspace_id is None:
        raise CebuTradeError("Order has no Workspace")
    return order.workspace_id


async def _ensure_escrow_workspace(db: AsyncSession, escrow: EscrowTransaction) -> uuid.UUID:
    workspace_id = await _ensure_order_workspace(db, escrow.order_id)
    if escrow.workspace_id is None:
        escrow.workspace_id = workspace_id
        await db.flush()
    if escrow.workspace_id != workspace_id:
        raise CebuTradeError("Escrow and order belong to different Workspaces")
    return workspace_id


async def _ensure_payout_workspace(db: AsyncSession, payout: Payout) -> uuid.UUID:
    workspace_id = await _ensure_order_workspace(db, payout.order_id)
    if payout.escrow_id is not None:
        escrow = await db.get(EscrowTransaction, payout.escrow_id)
        if escrow is None:
            raise CebuTradeError("Escrow not found")
        escrow_workspace_id = await _ensure_escrow_workspace(db, escrow)
        if escrow_workspace_id != workspace_id:
            raise CebuTradeError("Payout escrow and order belong to different Workspaces")
    if payout.workspace_id is None:
        payout.workspace_id = workspace_id
        await db.flush()
    if payout.workspace_id != workspace_id:
        raise CebuTradeError("Payout and order belong to different Workspaces")
    return workspace_id


async def ensure_escrow_workspace(db: AsyncSession, escrow: EscrowTransaction) -> uuid.UUID:
    return await _ensure_escrow_workspace(db, escrow)


async def ensure_payout_workspace(db: AsyncSession, payout: Payout) -> uuid.UUID:
    return await _ensure_payout_workspace(db, payout)


async def ensure_order_workspace(db: AsyncSession, order_id: uuid.UUID) -> uuid.UUID:
    return await _ensure_order_workspace(db, order_id)


# ── Wallet ──────────────────────────────────────────────────────────


async def get_or_create_wallet(
    db: AsyncSession, user_id: uuid.UUID, currency: str = "USDT"
) -> Wallet:
    existing = (
        await db.execute(
            select(Wallet).where(
                Wallet.owner_user_id == user_id,
                Wallet.currency == currency,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    wallet = Wallet(
        owner_user_id=user_id,
        currency=currency,
        status="ACTIVE",
    )
    db.add(wallet)
    await db.flush()
    return wallet


async def wallet_balance(db: AsyncSession, user_id: uuid.UUID) -> list[Wallet]:
    result = await db.execute(
        select(Wallet).where(Wallet.owner_user_id == user_id)
    )
    return list(result.scalars().all())


async def create_deposit(
    db: AsyncSession,
    *,
    wallet_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    **fields,
) -> WalletDeposit:
    deposit = WalletDeposit(
        wallet_id=wallet_id,
        owner_user_id=owner_user_id,
        **fields,
    )
    db.add(deposit)
    _record_tx(
        db,
        wallet_id=wallet_id,
        owner_user_id=owner_user_id,
        tx_type="DEPOSIT_INTENT_CREATED",
        amount_delta_minor=0,
        currency=fields.get("currency", "USDT"),
        reference_type="wallet_deposit",
        reference_id=None,
        note="Deposit intent created",
    )
    await db.flush()
    return deposit


async def verify_deposit(
    db: AsyncSession,
    deposit_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    admin_note: str | None = None,
) -> WalletDeposit:
    deposit = await db.get(WalletDeposit, deposit_id)
    if deposit is None:
        raise CebuTradeError("Deposit not found")
    if deposit.status not in ("PENDING_TX", "SUBMITTED", "UNDER_REVIEW"):
        raise CebuTradeError(f"Cannot verify deposit in status {deposit.status}")
    deposit.status = "VERIFIED"
    deposit.verified_by = admin_user_id
    deposit.verified_at = datetime.now(timezone.utc)
    deposit.admin_note = admin_note

    wallet = await db.get(Wallet, deposit.wallet_id)
    if wallet is None:
        raise CebuTradeError("Wallet not found")
    wallet.available_balance_minor += deposit.amount_minor
    wallet.total_deposited_minor += deposit.amount_minor
    _record_tx(
        db,
        wallet_id=wallet.id,
        owner_user_id=wallet.owner_user_id,
        tx_type="DEPOSIT_VERIFIED",
        amount_delta_minor=deposit.amount_minor,
        currency=wallet.currency,
        reference_type="wallet_deposit",
        reference_id=deposit.id,
        note=f"Deposit verified by admin",
        available_after=wallet.available_balance_minor,
        locked_after=wallet.locked_balance_minor,
    )
    await db.flush()
    return deposit


async def reject_deposit(
    db: AsyncSession,
    deposit_id: uuid.UUID,
    admin_user_id: uuid.UUID,
    admin_note: str | None = None,
) -> WalletDeposit:
    deposit = await db.get(WalletDeposit, deposit_id)
    if deposit is None:
        raise CebuTradeError("Deposit not found")
    if deposit.status not in ("PENDING_TX", "SUBMITTED", "UNDER_REVIEW"):
        raise CebuTradeError(f"Cannot reject deposit in status {deposit.status}")
    deposit.status = "REJECTED"
    deposit.rejected_by = admin_user_id
    deposit.rejected_at = datetime.now(timezone.utc)
    deposit.admin_note = admin_note
    await db.flush()
    return deposit


async def list_deposits(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[WalletDeposit]:
    q = select(WalletDeposit).order_by(WalletDeposit.created_at.desc()).limit(limit)
    if user_id:
        q = q.where(WalletDeposit.owner_user_id == user_id)
    if status:
        q = q.where(WalletDeposit.status == status)
    return list((await db.execute(q)).scalars().all())


async def list_wallet_transactions(
    db: AsyncSession,
    wallet_id: uuid.UUID,
    limit: int = 50,
) -> list[WalletTransaction]:
    return list(
        (
            await db.execute(
                select(WalletTransaction)
                .where(WalletTransaction.wallet_id == wallet_id)
                .order_by(WalletTransaction.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
    )


def _record_tx(
    db: AsyncSession,
    *,
    wallet_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    tx_type: str,
    amount_delta_minor: int,
    currency: str,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    note: str | None = None,
    available_after: int = 0,
    locked_after: int = 0,
) -> None:
    db.add(
        WalletTransaction(
            wallet_id=wallet_id,
            owner_user_id=owner_user_id,
            tx_type=tx_type,
            amount_delta_minor=amount_delta_minor,
            available_balance_after_minor=available_after,
            locked_balance_after_minor=locked_after,
            currency=currency,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )
    )


# ── Address ─────────────────────────────────────────────────────────


async def create_address(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
    **fields,
) -> Address:
    if fields.get("is_default"):
        await _unset_defaults(db, user_id, fields.get("address_type", "DELIVERY_TO"))
    addr = Address(user_id=user_id, company_id=company_id, **fields)
    db.add(addr)
    await db.flush()
    return addr


async def list_addresses(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Address]:
    return list(
        (
            await db.execute(
                select(Address)
                .where(Address.user_id == user_id, Address.status == "ACTIVE")
                .order_by(Address.is_default.desc(), Address.created_at.desc())
            )
        ).scalars().all()
    )


async def update_address(
    db: AsyncSession,
    address_id: uuid.UUID,
    user_id: uuid.UUID,
    **fields,
) -> Address:
    addr = await db.get(Address, address_id)
    if addr is None or addr.user_id != user_id:
        raise CebuTradeError("Address not found")
    if fields.get("is_default"):
        await _unset_defaults(db, user_id, addr.address_type)
    for k, v in fields.items():
        if v is not None:
            setattr(addr, k, v)
    await db.flush()
    return addr


async def delete_address(
    db: AsyncSession, address_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    addr = await db.get(Address, address_id)
    if addr is None or addr.user_id != user_id:
        raise CebuTradeError("Address not found")
    addr.status = "DELETED"
    await db.flush()


async def _unset_defaults(
    db: AsyncSession, user_id: uuid.UUID, address_type: str
) -> None:
    from sqlalchemy import update

    await db.execute(
        update(Address)
        .where(
            Address.user_id == user_id,
            Address.address_type == address_type,
            Address.is_default.is_(True),
        )
        .values(is_default=False)
    )


# ── Shipping ────────────────────────────────────────────────────────


async def create_shipping_route(db: AsyncSession, **fields) -> ShippingRoute:
    route = ShippingRoute(**fields)
    db.add(route)
    await db.flush()
    return route


async def list_shipping_routes(
    db: AsyncSession, origin: str | None = None, dest: str | None = None
) -> list[ShippingRoute]:
    q = select(ShippingRoute).where(ShippingRoute.status == "ACTIVE")
    if origin:
        q = q.where(ShippingRoute.origin_country == origin)
    if dest:
        q = q.where(ShippingRoute.dest_country == dest)
    return list((await db.execute(q.order_by(ShippingRoute.created_at.desc()))).scalars().all())


async def create_shipping_rate(db: AsyncSession, **fields) -> ShippingRate:
    rate = ShippingRate(**fields)
    db.add(rate)
    await db.flush()
    return rate


async def list_shipping_rates(
    db: AsyncSession, route_id: uuid.UUID | None = None, *, include_inactive: bool = True
) -> list[ShippingRate]:
    q = select(ShippingRate)
    if route_id:
        q = q.where(ShippingRate.route_id == route_id)
    if not include_inactive:
        q = q.where(ShippingRate.status == "ACTIVE")
    return list((await db.execute(q.order_by(ShippingRate.weight_min_kg))).scalars().all())


async def update_shipping_route(
    db: AsyncSession, route_id: uuid.UUID, **fields
) -> ShippingRoute:
    row = await db.get(ShippingRoute, route_id)
    if row is None:
        raise CebuTradeError("Shipping route not found")
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def update_shipping_rate(
    db: AsyncSession, rate_id: uuid.UUID, **fields
) -> ShippingRate:
    row = await db.get(ShippingRate, rate_id)
    if row is None:
        raise CebuTradeError("Shipping rate not found")
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    await db.flush()
    return row


async def estimate_shipping(
    db: AsyncSession,
    *,
    origin_country: str,
    dest_country: str,
    weight_kg: float,
    shipping_method: str | None = None,
) -> list[dict]:
    q = (
        select(ShippingRoute, ShippingRate)
        .join(ShippingRate, ShippingRate.route_id == ShippingRoute.id)
        .where(
            ShippingRoute.origin_country == origin_country,
            ShippingRoute.dest_country == dest_country,
            ShippingRoute.status == "ACTIVE",
            ShippingRate.status == "ACTIVE",
            ShippingRate.weight_min_kg <= weight_kg,
            ShippingRate.weight_max_kg >= weight_kg,
        )
    )
    if shipping_method:
        q = q.where(ShippingRoute.shipping_method == shipping_method)
    rows = (await db.execute(q)).all()
    estimates = []
    for route, rate in rows:
        cost = max(
            int(weight_kg * rate.price_per_kg_minor),
            rate.min_charge_minor,
        )
        estimates.append(
            {
                "route_id": route.id,
                "shipping_method": route.shipping_method,
                "cost_minor": cost,
                "currency": rate.currency,
                "estimated_days_min": rate.estimated_days_min,
                "estimated_days_max": rate.estimated_days_max,
            }
        )
    return estimates


# ── Ads ─────────────────────────────────────────────────────────────


async def create_ad_campaign(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    **fields,
) -> AdCampaign:
    campaign = AdCampaign(company_id=company_id, **fields)
    db.add(campaign)
    await db.flush()
    return campaign


async def list_ad_campaigns(
    db: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[AdCampaign]:
    q = select(AdCampaign).order_by(AdCampaign.created_at.desc()).limit(limit)
    if company_id:
        q = q.where(AdCampaign.company_id == company_id)
    if status:
        q = q.where(AdCampaign.status == status)
    return list((await db.execute(q)).scalars().all())


async def update_ad_campaign_status(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    new_status: str,
    rejection_reason: str | None = None,
    company_id: uuid.UUID | None = None,
) -> AdCampaign:
    campaign = await db.get(AdCampaign, campaign_id)
    if campaign is None:
        raise CebuTradeError("Campaign not found")
    if company_id and campaign.company_id != company_id:
        raise CebuTradeError("Not your campaign")
    campaign.status = new_status
    if rejection_reason:
        campaign.rejection_reason = rejection_reason
    await db.flush()
    return campaign


# ── Escrow ──────────────────────────────────────────────────────────


async def create_escrow(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    auth_amount_minor: int,
    currency: str = "PHP",
    provider: str = "SIMULATED",
) -> EscrowTransaction:
    workspace_id = await _ensure_order_workspace(db, order_id)
    existing = (
        await db.execute(
            select(EscrowTransaction).where(EscrowTransaction.order_id == order_id)
        )
    ).scalar_one_or_none()
    if existing:
        await _ensure_escrow_workspace(db, existing)
        raise CebuTradeError("Escrow already exists for this order")
    escrow = EscrowTransaction(
        workspace_id=workspace_id,
        order_id=order_id,
        auth_amount_minor=auth_amount_minor,
        currency=currency,
        provider=provider,
    )
    db.add(escrow)
    await db.flush()
    return escrow


async def capture_escrow(
    db: AsyncSession, escrow_id: uuid.UUID, amount_minor: int | None = None
) -> EscrowTransaction:
    escrow = await db.get(EscrowTransaction, escrow_id)
    if escrow is None:
        raise CebuTradeError("Escrow not found")
    await _ensure_escrow_workspace(db, escrow)
    if escrow.status != "AUTH_HELD":
        raise CebuTradeError(f"Cannot capture escrow in {escrow.status}")
    capture = amount_minor or escrow.auth_amount_minor
    if capture <= 0 or capture > escrow.auth_amount_minor:
        raise CebuTradeError("Invalid escrow capture amount")
    escrow.captured_amount_minor = capture
    escrow.status = "CAPTURED"
    await db.flush()
    return escrow


async def release_escrow(
    db: AsyncSession, escrow_id: uuid.UUID, amount_minor: int | None = None
) -> EscrowTransaction:
    escrow = await db.get(EscrowTransaction, escrow_id)
    if escrow is None:
        raise CebuTradeError("Escrow not found")
    await _ensure_escrow_workspace(db, escrow)
    if escrow.status not in ("CAPTURED", "AUTH_HELD"):
        raise CebuTradeError(f"Cannot release escrow in {escrow.status}")
    available = escrow.captured_amount_minor or escrow.auth_amount_minor
    release = amount_minor or available
    if release <= 0 or release > available - escrow.refunded_amount_minor:
        raise CebuTradeError("Invalid escrow release amount")
    escrow.released_amount_minor = release
    escrow.status = "RELEASED"
    await db.flush()
    return escrow


async def refund_escrow(
    db: AsyncSession,
    escrow_id: uuid.UUID,
    amount_minor: int | None = None,
    reason: str | None = None,
) -> EscrowTransaction:
    escrow = await db.get(EscrowTransaction, escrow_id)
    if escrow is None:
        raise CebuTradeError("Escrow not found")
    await _ensure_escrow_workspace(db, escrow)
    if escrow.status not in ("AUTH_HELD", "CAPTURED", "RELEASED", "PARTIALLY_REFUNDED"):
        raise CebuTradeError(f"Cannot refund escrow in {escrow.status}")
    refundable = (escrow.captured_amount_minor or escrow.auth_amount_minor) - escrow.refunded_amount_minor
    refund = amount_minor or refundable
    if refund <= 0 or refund > refundable:
        raise CebuTradeError("Invalid escrow refund amount")
    escrow.refunded_amount_minor += refund
    escrow.status = "REFUNDED" if escrow.refunded_amount_minor == (escrow.captured_amount_minor or escrow.auth_amount_minor) else "PARTIALLY_REFUNDED"
    raw = dict(escrow.raw_event_json or {})
    raw["last_refund_reason"] = reason
    raw["last_refund_amount_minor"] = refund
    escrow.raw_event_json = raw
    await db.flush()
    return escrow


async def get_escrow_for_order(
    db: AsyncSession, order_id: uuid.UUID
) -> EscrowTransaction | None:
    workspace_id = await _ensure_order_workspace(db, order_id)
    escrow = (
        await db.execute(
            select(EscrowTransaction).where(EscrowTransaction.order_id == order_id)
        )
    ).scalar_one_or_none()
    if escrow is not None:
        await _ensure_escrow_workspace(db, escrow)
        if escrow.workspace_id != workspace_id:
            raise CebuTradeError("Escrow and order belong to different Workspaces")
    return escrow


# ── Payout ──────────────────────────────────────────────────────────


async def create_payout(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    order_id: uuid.UUID,
    amount_minor: int,
    currency: str = "PHP",
    escrow_id: uuid.UUID | None = None,
) -> Payout:
    workspace_id = await _ensure_order_workspace(db, order_id)
    if escrow_id is not None:
        escrow = await db.get(EscrowTransaction, escrow_id)
        if escrow is None:
            raise CebuTradeError("Escrow not found")
        escrow_workspace_id = await _ensure_escrow_workspace(db, escrow)
        if escrow_workspace_id != workspace_id:
            raise CebuTradeError("Payout escrow and order belong to different Workspaces")
    payout = Payout(
        workspace_id=workspace_id,
        company_id=company_id,
        order_id=order_id,
        amount_minor=amount_minor,
        currency=currency,
        escrow_id=escrow_id,
    )
    db.add(payout)
    await db.flush()
    return payout


async def list_payouts(
    db: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    workspace_ids: set[uuid.UUID] | None = None,
    include_unscoped: bool = False,
    status: str | None = None,
    limit: int = 50,
) -> list[Payout]:
    q = select(Payout).order_by(Payout.created_at.desc()).limit(limit)
    if company_id:
        q = q.where(Payout.company_id == company_id)
    if workspace_ids is not None:
        workspace_filter = Payout.workspace_id.in_(workspace_ids)
        if include_unscoped:
            workspace_filter = or_(workspace_filter, Payout.workspace_id.is_(None))
        q = q.where(workspace_filter)
    if status:
        q = q.where(Payout.status == status)
    return list((await db.execute(q)).scalars().all())


async def process_payout(
    db: AsyncSession,
    payout_id: uuid.UUID,
    *,
    new_status: str,
    provider_reference: str | None = None,
    failure_reason: str | None = None,
) -> Payout:
    payout = await db.get(Payout, payout_id)
    if payout is None:
        raise CebuTradeError("Payout not found")
    await _ensure_payout_workspace(db, payout)
    payout.status = new_status
    if provider_reference:
        payout.provider_reference = provider_reference
    if failure_reason:
        payout.failure_reason = failure_reason
    if new_status == "PAID":
        payout.paid_at = datetime.now(timezone.utc)
    await db.flush()
    return payout

"""Cebu zero-loss API routes — Wallet, Address, Shipping, Ads, Escrow, Payout.

Ownership rules:
- Wallet: only the owner sees/modifies their wallet.  Admin verifies deposits.
- Address: only the owner CRUDs their addresses.
- Ads: supplier sees own company campaigns.  Admin manages status.
- Escrow/Payout: admin-only management; parties can view their own.
- Shipping routes/rates: admin-managed; public read for estimates.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB, FinanceUser
from app.modules.cebu_trade.access import (
    CebuTradeAccessDenied,
    cebu_trade_admin_workspace_ids,
    require_cebu_trade_admin_workspace,
)
from app.modules.cebu_trade.models import (
    AdCampaign,
    EscrowTransaction,
    Payout,
    ShippingRate,
    ShippingRoute,
    Wallet,
    WalletDeposit,
)
from app.modules.cebu_trade.schemas import (
    AdCampaignCreate,
    AdCampaignRead,
    AdCampaignStatusUpdate,
    AddressCreate,
    AddressRead,
    AddressUpdate,
    DepositRejectRequest,
    DepositVerifyRequest,
    EscrowCaptureRequest,
    EscrowRefundRequest,
    EscrowReleaseRequest,
    EscrowTransactionRead,
    PayoutRead,
    ShippingEstimateRead,
    ShippingEstimateRequest,
    ShippingRateCreate,
    ShippingRateRead,
    ShippingRateUpdate,
    ShippingRouteCreate,
    ShippingRouteRead,
    ShippingRouteUpdate,
    WalletDepositCreate,
    WalletDepositRead,
    WalletRead,
    WalletTransactionRead,
)
from app.modules.cebu_trade.service import (
    CebuTradeError,
    capture_escrow,
    create_ad_campaign,
    create_address,
    create_deposit,
    create_escrow,
    create_payout,
    create_shipping_rate,
    create_shipping_route,
    delete_address,
    estimate_shipping,
    ensure_escrow_workspace,
    ensure_order_workspace,
    ensure_payout_workspace,
    get_escrow_for_order,
    get_or_create_wallet,
    list_ad_campaigns,
    list_addresses,
    list_deposits,
    list_payouts,
    list_shipping_rates,
    list_shipping_routes,
    list_wallet_transactions,
    process_payout,
    reject_deposit,
    refund_escrow,
    release_escrow,
    update_shipping_rate,
    update_shipping_route,
    update_ad_campaign_status,
    update_address,
    verify_deposit,
    wallet_balance,
)
from app.services.audit import append_audit_event
from app.services.portal_access import list_memberships

router = APIRouter(prefix="/cebu-trade", tags=["cebu-trade-migration"])
admin_router = APIRouter(prefix="/admin/cebu-trade", tags=["cebu-trade-admin"])


async def _admin_audit(
    db: DB,
    admin,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
    reason: str | None = None,
) -> None:
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        portal_key="admin_cebu",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        reason=reason,
        source="admin.cebu_trade",
    )


# ── Wallet ──────────────────────────────────────────────────────────


@router.get("/wallet", response_model=dict)
async def get_my_wallet(db: DB, user: CurrentUser, currency: str = "USDT"):
    wallet = await get_or_create_wallet(db, user.id, currency)
    await db.commit()
    return WalletRead.model_validate(wallet).model_dump()


@router.get("/wallet/balances")
async def get_my_balances(db: DB, user: CurrentUser):
    wallets = await wallet_balance(db, user.id)
    return {"items": [WalletRead.model_validate(w).model_dump() for w in wallets], "total": len(wallets)}


@router.get("/wallet/{wallet_id}/transactions")
async def get_wallet_transactions(wallet_id: uuid.UUID, db: DB, user: CurrentUser):
    wallet = await db.get(Wallet, wallet_id)
    if wallet is None or wallet.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Wallet not found")
    txs = await list_wallet_transactions(db, wallet_id)
    return {
        "items": [WalletTransactionRead.model_validate(t).model_dump() for t in txs],
        "total": len(txs),
    }


@router.post("/wallet/deposits", response_model=WalletDepositRead, status_code=201)
async def create_wallet_deposit(data: WalletDepositCreate, db: DB, user: CurrentUser):
    wallet = await get_or_create_wallet(db, user.id, data.currency)
    deposit = await create_deposit(
        db,
        wallet_id=wallet.id,
        owner_user_id=user.id,
        **data.model_dump(),
    )
    await db.commit()
    await db.refresh(deposit)
    return WalletDepositRead.model_validate(deposit)


@router.get("/wallet/deposits")
async def list_my_deposits(db: DB, user: CurrentUser, status: str | None = None):
    items = await list_deposits(db, user_id=user.id, status=status)
    return {"items": [WalletDepositRead.model_validate(d).model_dump() for d in items], "total": len(items)}


@admin_router.get("/deposits")
async def admin_list_deposits(db: DB, admin: FinanceUser, status: str | None = Query(default=None)):
    items = await list_deposits(db, status=status)
    return {"items": [WalletDepositRead.model_validate(d).model_dump() for d in items], "total": len(items)}


@admin_router.post("/deposits/{deposit_id}/verify", response_model=WalletDepositRead)
async def admin_verify_deposit(deposit_id: uuid.UUID, data: DepositVerifyRequest, db: DB, admin: FinanceUser):
    try:
        current = await db.get(WalletDeposit, deposit_id)
        before_status = current.status if current else None
        row = await verify_deposit(db, deposit_id, admin.id, data.admin_note)
        await _admin_audit(
            db, admin, action="cebu.admin.deposit_verified", entity_type="wallet_deposit",
            entity_id=row.id, before={"status": before_status},
            after={"status": row.status, "amount_minor": row.amount_minor}, reason=data.admin_note,
        )
        await db.commit()
        await db.refresh(row)
        return WalletDepositRead.model_validate(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@admin_router.post("/deposits/{deposit_id}/reject", response_model=WalletDepositRead)
async def admin_reject_deposit(deposit_id: uuid.UUID, data: DepositRejectRequest, db: DB, admin: FinanceUser):
    try:
        current = await db.get(WalletDeposit, deposit_id)
        before_status = current.status if current else None
        row = await reject_deposit(db, deposit_id, admin.id, data.admin_note)
        await _admin_audit(
            db, admin, action="cebu.admin.deposit_rejected", entity_type="wallet_deposit",
            entity_id=row.id, before={"status": before_status},
            after={"status": row.status}, reason=data.admin_note,
        )
        await db.commit()
        await db.refresh(row)
        return WalletDepositRead.model_validate(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


# ── Address ─────────────────────────────────────────────────────────


@router.get("/addresses")
async def list_my_addresses(db: DB, user: CurrentUser):
    items = await list_addresses(db, user.id)
    return {"items": [AddressRead.model_validate(a).model_dump() for a in items], "total": len(items)}


@router.post("/addresses", response_model=AddressRead, status_code=201)
async def create_my_address(data: AddressCreate, db: DB, user: CurrentUser):
    addr = await create_address(db, user_id=user.id, company_id=user.company_id, **data.model_dump())
    await db.commit()
    await db.refresh(addr)
    return AddressRead.model_validate(addr)


@router.patch("/addresses/{address_id}", response_model=AddressRead)
async def update_my_address(address_id: uuid.UUID, data: AddressUpdate, db: DB, user: CurrentUser):
    try:
        addr = await update_address(db, address_id, user.id, **data.model_dump(exclude_unset=True))
        await db.commit()
        await db.refresh(addr)
        return AddressRead.model_validate(addr)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.delete("/addresses/{address_id}", status_code=204)
async def delete_my_address(address_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        await delete_address(db, address_id, user.id)
        await db.commit()
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


# ── Shipping ────────────────────────────────────────────────────────


@router.get("/shipping/routes")
async def list_routes(
    db: DB,
    user: CurrentUser,
    origin: str | None = None,
    dest: str | None = None,
):
    items = await list_shipping_routes(db, origin=origin, dest=dest)
    return {"items": [ShippingRouteRead.model_validate(r).model_dump() for r in items], "total": len(items)}


@router.post("/shipping/estimate")
async def get_shipping_estimate(data: ShippingEstimateRequest, db: DB, user: CurrentUser):
    estimates = await estimate_shipping(
        db,
        origin_country=data.origin_country,
        dest_country=data.dest_country,
        weight_kg=data.weight_kg,
        shipping_method=data.shipping_method,
    )
    return {
        "items": [ShippingEstimateRead.model_validate(e).model_dump() for e in estimates],
        "total": len(estimates),
    }


@admin_router.post("/shipping/routes", response_model=ShippingRouteRead, status_code=201)
async def admin_create_route(data: ShippingRouteCreate, db: DB, admin: AdminUser):
    route = await create_shipping_route(db, **data.model_dump())
    await _admin_audit(
        db, admin, action="cebu.admin.shipping_route_created", entity_type="shipping_route",
        entity_id=route.id, after={"status": route.status},
    )
    await db.commit()
    await db.refresh(route)
    return ShippingRouteRead.model_validate(route)


@admin_router.get("/shipping/routes")
async def admin_list_routes(db: DB, admin: AdminUser):
    rows = list(
        (await db.execute(select(ShippingRoute).order_by(ShippingRoute.created_at.desc()))).scalars()
    )
    return {"items": [ShippingRouteRead.model_validate(row) for row in rows], "total": len(rows)}


@admin_router.patch("/shipping/routes/{route_id}", response_model=ShippingRouteRead)
async def admin_update_route(route_id: uuid.UUID, data: ShippingRouteUpdate, db: DB, admin: AdminUser):
    try:
        current = await db.get(ShippingRoute, route_id)
        before = {"status": current.status} if current else None
        row = await update_shipping_route(db, route_id, **data.model_dump(exclude_unset=True))
        await _admin_audit(
            db, admin, action="cebu.admin.shipping_route_updated", entity_type="shipping_route",
            entity_id=row.id, before=before, after={"status": row.status},
        )
        await db.commit()
        await db.refresh(row)
        return ShippingRouteRead.model_validate(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@admin_router.delete("/shipping/routes/{route_id}", status_code=204)
async def admin_deactivate_route(route_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        row = await update_shipping_route(db, route_id, status="INACTIVE")
        await _admin_audit(
            db, admin, action="cebu.admin.shipping_route_deactivated", entity_type="shipping_route",
            entity_id=row.id, before={"status": "ACTIVE"}, after={"status": row.status},
        )
        await db.commit()
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@admin_router.post("/shipping/rates", response_model=ShippingRateRead, status_code=201)
async def admin_create_rate(data: ShippingRateCreate, db: DB, admin: AdminUser):
    rate = await create_shipping_rate(db, **data.model_dump())
    await _admin_audit(
        db, admin, action="cebu.admin.shipping_rate_created", entity_type="shipping_rate",
        entity_id=rate.id, after={"status": rate.status, "price_per_kg_minor": rate.price_per_kg_minor},
    )
    await db.commit()
    await db.refresh(rate)
    return ShippingRateRead.model_validate(rate)


@admin_router.get("/shipping/rates")
async def admin_list_rates(db: DB, admin: AdminUser, route_id: uuid.UUID | None = None):
    rows = await list_shipping_rates(db, route_id)
    return {"items": [ShippingRateRead.model_validate(row) for row in rows], "total": len(rows)}


@admin_router.patch("/shipping/rates/{rate_id}", response_model=ShippingRateRead)
async def admin_update_rate(rate_id: uuid.UUID, data: ShippingRateUpdate, db: DB, admin: AdminUser):
    try:
        current = await db.get(ShippingRate, rate_id)
        before = {"status": current.status, "price_per_kg_minor": current.price_per_kg_minor} if current else None
        row = await update_shipping_rate(db, rate_id, **data.model_dump(exclude_unset=True))
        await _admin_audit(
            db, admin, action="cebu.admin.shipping_rate_updated", entity_type="shipping_rate",
            entity_id=row.id, before=before,
            after={"status": row.status, "price_per_kg_minor": row.price_per_kg_minor},
        )
        await db.commit()
        await db.refresh(row)
        return ShippingRateRead.model_validate(row)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@admin_router.delete("/shipping/rates/{rate_id}", status_code=204)
async def admin_deactivate_rate(rate_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        row = await update_shipping_rate(db, rate_id, status="INACTIVE")
        await _admin_audit(
            db, admin, action="cebu.admin.shipping_rate_deactivated", entity_type="shipping_rate",
            entity_id=row.id, before={"status": "ACTIVE"}, after={"status": row.status},
        )
        await db.commit()
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


# ── Ads ─────────────────────────────────────────────────────────────


@router.get("/ads/campaigns")
async def list_my_campaigns(db: DB, user: CurrentUser):
    if user.company_id is None:
        return {"items": [], "total": 0}
    items = await list_ad_campaigns(db, company_id=user.company_id)
    return {"items": [AdCampaignRead.model_validate(c).model_dump() for c in items], "total": len(items)}


@router.post("/ads/campaigns", response_model=AdCampaignRead, status_code=201)
async def create_my_campaign(data: AdCampaignCreate, db: DB, user: CurrentUser):
    if user.company_id is None:
        raise HTTPException(status_code=403, detail="Company required to create ad campaigns")
    campaign = await create_ad_campaign(db, company_id=user.company_id, **data.model_dump())
    await db.commit()
    await db.refresh(campaign)
    return AdCampaignRead.model_validate(campaign)


@router.patch("/ads/campaigns/{campaign_id}/status", response_model=AdCampaignRead)
async def update_my_campaign_status(campaign_id: uuid.UUID, data: AdCampaignStatusUpdate, db: DB, user: CurrentUser):
    if user.company_id is None:
        raise HTTPException(status_code=403, detail="Company required")
    allowed_self = {"PAUSED", "DRAFT"}
    if data.status not in allowed_self:
        raise HTTPException(status_code=403, detail="Only admin can change to this status")
    try:
        campaign = await update_ad_campaign_status(
            db, campaign_id, new_status=data.status, company_id=user.company_id
        )
        await db.commit()
        await db.refresh(campaign)
        return AdCampaignRead.model_validate(campaign)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@admin_router.get("/ads/campaigns")
async def admin_list_all_campaigns(
    db: DB, admin: AdminUser, status: str | None = Query(default=None)
):
    items = await list_ad_campaigns(db, status=status)
    return {"items": [AdCampaignRead.model_validate(c).model_dump() for c in items], "total": len(items)}


@admin_router.patch("/ads/campaigns/{campaign_id}/status", response_model=AdCampaignRead)
async def admin_update_campaign_status(
    campaign_id: uuid.UUID, data: AdCampaignStatusUpdate, db: DB, admin: AdminUser
):
    try:
        current = await db.get(AdCampaign, campaign_id)
        before = {"status": current.status} if current else None
        campaign = await update_ad_campaign_status(
            db, campaign_id, new_status=data.status, rejection_reason=data.rejection_reason
        )
        await _admin_audit(
            db, admin, action="cebu.admin.ad_campaign_status_changed", entity_type="ad_campaign",
            entity_id=campaign.id, before=before, after={"status": campaign.status},
            reason=data.rejection_reason,
        )
        await db.commit()
        await db.refresh(campaign)
        return AdCampaignRead.model_validate(campaign)
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


# ── Escrow ──────────────────────────────────────────────────────────


@router.get("/orders/{order_id}/escrow", response_model=EscrowTransactionRead)
async def get_order_escrow(order_id: uuid.UUID, db: DB, user: CurrentUser):
    from app.modules.commerce.access import require_order_party, CommerceAccessDenied, CommerceResourceNotFound

    try:
        await require_order_party(db, user=user, order_id=order_id)
    except CommerceResourceNotFound:
        raise HTTPException(status_code=404, detail="Order not found") from None
    except CommerceAccessDenied:
        raise HTTPException(status_code=403, detail="Not a party to this order") from None
    try:
        escrow = await get_escrow_for_order(db, order_id)
        if escrow is None:
            raise HTTPException(status_code=404, detail="No escrow for this order")
    except CebuTradeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return EscrowTransactionRead.model_validate(escrow)


@admin_router.post("/escrow", response_model=EscrowTransactionRead, status_code=201)
async def admin_create_escrow(
    order_id: uuid.UUID,
    auth_amount_minor: int,
    currency: str = "PHP",
    db: DB = None,
    admin: FinanceUser = None,
):
    try:
        workspace_id = await ensure_order_workspace(db, order_id)
        await require_cebu_trade_admin_workspace(db, admin, workspace_id)
        escrow = await create_escrow(db, order_id=order_id, auth_amount_minor=auth_amount_minor, currency=currency)
        await _admin_audit(
            db, admin, action="cebu.admin.escrow_created", entity_type="escrow_transaction",
            entity_id=escrow.id, after={"status": escrow.status, "auth_amount_minor": escrow.auth_amount_minor},
        )
        await db.commit()
        await db.refresh(escrow)
        return EscrowTransactionRead.model_validate(escrow)
    except CebuTradeAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@admin_router.post("/escrow/{escrow_id}/capture", response_model=EscrowTransactionRead)
async def admin_capture_escrow(escrow_id: uuid.UUID, data: EscrowCaptureRequest, db: DB, admin: FinanceUser):
    try:
        current = await db.get(EscrowTransaction, escrow_id)
        if current is not None:
            await ensure_escrow_workspace(db, current)
            await require_cebu_trade_admin_workspace(db, admin, current.workspace_id)
        before = {"status": current.status, "captured_amount_minor": current.captured_amount_minor} if current else None
        row = await capture_escrow(db, escrow_id, data.amount_minor)
        await _admin_audit(
            db, admin, action="cebu.admin.escrow_captured", entity_type="escrow_transaction",
            entity_id=row.id, before=before, after={"status": row.status, "captured_amount_minor": row.captured_amount_minor},
        )
        await db.commit()
        await db.refresh(row)
        return EscrowTransactionRead.model_validate(row)
    except CebuTradeAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@admin_router.post("/escrow/{escrow_id}/release", response_model=EscrowTransactionRead)
async def admin_release_escrow(escrow_id: uuid.UUID, data: EscrowReleaseRequest, db: DB, admin: FinanceUser):
    try:
        current = await db.get(EscrowTransaction, escrow_id)
        if current is not None:
            await ensure_escrow_workspace(db, current)
            await require_cebu_trade_admin_workspace(db, admin, current.workspace_id)
        before = {"status": current.status, "released_amount_minor": current.released_amount_minor} if current else None
        row = await release_escrow(db, escrow_id, data.amount_minor)
        await _admin_audit(
            db, admin, action="cebu.admin.escrow_released", entity_type="escrow_transaction",
            entity_id=row.id, before=before, after={"status": row.status, "released_amount_minor": row.released_amount_minor},
        )
        await db.commit()
        await db.refresh(row)
        return EscrowTransactionRead.model_validate(row)
    except CebuTradeAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@admin_router.post("/escrow/{escrow_id}/refund", response_model=EscrowTransactionRead)
async def admin_refund_escrow(
    escrow_id: uuid.UUID, data: EscrowRefundRequest, db: DB, admin: FinanceUser
):
    try:
        current = await db.get(EscrowTransaction, escrow_id)
        if current is not None:
            await ensure_escrow_workspace(db, current)
            await require_cebu_trade_admin_workspace(db, admin, current.workspace_id)
        before = {"status": current.status, "refunded_amount_minor": current.refunded_amount_minor} if current else None
        row = await refund_escrow(db, escrow_id, data.amount_minor, data.reason)
        await _admin_audit(
            db, admin, action="cebu.admin.escrow_refunded", entity_type="escrow_transaction",
            entity_id=row.id, before=before,
            after={"status": row.status, "refunded_amount_minor": row.refunded_amount_minor},
            reason=data.reason,
        )
        await db.commit()
        await db.refresh(row)
        return EscrowTransactionRead.model_validate(row)
    except CebuTradeAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


# ── Payout ──────────────────────────────────────────────────────────


@router.get("/payouts")
async def list_my_payouts(db: DB, user: CurrentUser, status: str | None = None):
    if user.company_id is None:
        return {"items": [], "total": 0}
    memberships = await list_memberships(db, user.id)
    workspace_ids = {
        membership.workspace_id
        for membership in memberships
        if membership.company_id == user.company_id
    }
    items = await list_payouts(
        db,
        company_id=user.company_id,
        workspace_ids=workspace_ids,
        include_unscoped=True,
        status=status,
    )
    return {"items": [PayoutRead.model_validate(p).model_dump() for p in items], "total": len(items)}


@admin_router.get("/payouts")
async def admin_list_payouts(db: DB, admin: FinanceUser, status: str | None = Query(default=None)):
    workspace_ids = await cebu_trade_admin_workspace_ids(db, admin)
    items = await list_payouts(
        db,
        workspace_ids=workspace_ids,
        include_unscoped=True,
        status=status,
    )
    return {"items": [PayoutRead.model_validate(p).model_dump() for p in items], "total": len(items)}


@admin_router.post("/payouts/{payout_id}/process", response_model=PayoutRead)
async def admin_process_payout(
    payout_id: uuid.UUID,
    new_status: str,
    db: DB,
    admin: FinanceUser,
    provider_reference: str | None = None,
    failure_reason: str | None = None,
):
    try:
        current = await db.get(Payout, payout_id)
        if current is not None:
            await ensure_payout_workspace(db, current)
            await require_cebu_trade_admin_workspace(db, admin, current.workspace_id)
        before = {"status": current.status} if current else None
        row = await process_payout(
            db, payout_id,
            new_status=new_status,
            provider_reference=provider_reference,
            failure_reason=failure_reason,
        )
        await _admin_audit(
            db, admin, action="cebu.admin.payout_processed", entity_type="payout",
            entity_id=row.id, before=before, after={"status": row.status},
            reason=failure_reason,
        )
        await db.commit()
        await db.refresh(row)
        return PayoutRead.model_validate(row)
    except CebuTradeAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CebuTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None

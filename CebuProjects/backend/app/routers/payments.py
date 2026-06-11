import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.payment_config import PaymentIntent, PaymentMethodConfig, RegionPaymentConfig, SettlementEvent
from app.models.payment_event import PaymentEvent as LegacyPaymentEvent
from app.models.payout import Payout, PayoutStatus
from app.models.user import User, UserRole
from app.schemas.payments import (
    PaymentIntentCreateRequest,
    PaymentIntentResponse,
    PaymentMethodResponse,
    PaymentQuoteCreateRequest,
    PaymentQuoteResponse,
    PayoutQuoteCreateRequest,
    PayoutQuoteResponse,
    RegionPaymentConfigPatch,
    RegionPaymentConfigResponse,
    RegionPaymentConfigUpsert,
    SettlementEventResponse,
)
from app.services.payment_service import (
    create_payment_intent_from_quote,
    create_payment_quote,
    fee_lines_for,
    fx_rate,
    get_or_seed_region_config,
    quote_with_lines,
)

router = APIRouter(tags=["Payments"])


def _admin_finance():
    return require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FINANCE_OFFICER, UserRole.OPS_MANAGER)


def _quote_response(quote, lines) -> PaymentQuoteResponse:
    payload = PaymentQuoteResponse.model_validate(quote).model_dump()
    payload["fee_line_items"] = lines
    return PaymentQuoteResponse.model_validate(payload)


@router.get("/payments/region-config", response_model=RegionPaymentConfigResponse)
async def get_region_payment_config(country: str = Query(default="PH", min_length=2, max_length=2), db: AsyncSession = Depends(get_db)):
    config = await get_or_seed_region_config(db, country)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/payments/methods", response_model=list[PaymentMethodResponse])
async def payment_methods(country: str = "PH", currency: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(PaymentMethodConfig).where(
        PaymentMethodConfig.country_code == country.upper()[:2],
        PaymentMethodConfig.is_enabled.is_(True),
    )
    if currency:
        q = q.where(PaymentMethodConfig.currency == currency.upper())
    result = await db.execute(q.order_by(PaymentMethodConfig.method_code.asc()))
    return result.scalars().all()


@router.post("/payments/quotes", response_model=PaymentQuoteResponse, status_code=201)
async def create_quote(req: PaymentQuoteCreateRequest, db: AsyncSession = Depends(get_db)):
    quote = await create_payment_quote(db, req)
    await db.commit()
    quote, lines = await quote_with_lines(db, quote.id)
    return _quote_response(quote, lines)


@router.get("/payments/quotes/{quote_id}", response_model=PaymentQuoteResponse)
async def get_quote(quote_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    quote, lines = await quote_with_lines(db, quote_id)
    return _quote_response(quote, lines)


@router.post("/payments/quotes/{quote_id}/confirm", response_model=PaymentIntentResponse, status_code=201)
async def confirm_quote(
    quote_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote, _ = await quote_with_lines(db, quote_id)
    intent = await create_payment_intent_from_quote(db, quote=quote)
    db.add(LegacyPaymentEvent(
        provider=intent.provider,
        provider_event_id=intent.provider_reference,
        event_type="PAYMENT_INTENT_SUCCEEDED",
        order_id=intent.order_id,
        amount_minor=intent.amount_minor,
        currency=intent.currency,
        status="PROCESSED",
        processed_at=datetime.now(timezone.utc),
        raw_payload={"quote_id": str(quote.id), "actor_id": str(user.id)},
    ))
    await db.commit()
    await db.refresh(intent)
    return intent


@router.post("/payments/intents", response_model=PaymentIntentResponse, status_code=201)
async def create_intent(
    req: PaymentIntentCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quote, _ = await quote_with_lines(db, req.quote_id)
    intent = await create_payment_intent_from_quote(db, quote=quote, order_id=req.order_id, provider=req.provider)
    db.add(LegacyPaymentEvent(
        provider=intent.provider,
        provider_event_id=intent.provider_reference,
        event_type="PAYMENT_INTENT_SUCCEEDED",
        order_id=intent.order_id,
        amount_minor=intent.amount_minor,
        currency=intent.currency,
        status="PROCESSED",
        processed_at=datetime.now(timezone.utc),
        raw_payload={"quote_id": str(quote.id), "actor_id": str(user.id)},
    ))
    await db.commit()
    await db.refresh(intent)
    return intent


@router.get("/payments/intents/{intent_id}", response_model=PaymentIntentResponse)
async def get_intent(intent_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    intent = (await db.execute(select(PaymentIntent).where(PaymentIntent.id == intent_id))).scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    return intent


@router.post("/payments/webhooks/{provider}")
async def payment_webhook(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    event_id = str(payload.get("id") or payload.get("event_id") or uuid.uuid4())
    amount = payload.get("amount_minor") or payload.get("amount")
    currency = payload.get("currency")
    db.add(LegacyPaymentEvent(
        provider=provider.upper(),
        provider_event_id=event_id,
        event_type=str(payload.get("type") or "WEBHOOK_RECEIVED"),
        amount_minor=int(amount) if amount is not None else None,
        currency=currency.upper() if isinstance(currency, str) else currency,
        status="RECEIVED",
        raw_payload=payload,
    ))
    await db.commit()
    return {"ok": True}


@router.post("/payouts/quotes", response_model=PayoutQuoteResponse)
async def payout_quote(req: PayoutQuoteCreateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rate = fx_rate(req.source_currency, req.payout_currency)
    gross = int(round(req.amount_minor * float(rate)))
    fee_lines = await fee_lines_for(
        db,
        amount_minor=gross,
        country_code=req.supplier_country,
        payment_method=req.payout_method,
        currency=req.payout_currency,
    )
    settlement_fee = round(gross * 50 / 10000)
    fee_lines.append({
        "fee_type": "SETTLEMENT_FEE",
        "label": "Payout settlement fee",
        "amount_minor": settlement_fee,
        "currency": req.payout_currency.upper(),
        "refundable": False,
        "metadata_json": {"variable_bps": 50},
    })
    return PayoutQuoteResponse(
        source_currency=req.source_currency.upper(),
        payout_currency=req.payout_currency.upper(),
        amount_minor=req.amount_minor,
        rate=float(rate),
        fee_line_items=fee_lines,
        supplier_estimated_net_minor=max(0, gross - sum(line["amount_minor"] for line in fee_lines)),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )


@router.post("/supplier/payouts", status_code=201)
async def supplier_payout(req: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company_id = req.get("company_id")
    order_id = req.get("order_id")
    if not company_id or not order_id:
        return {"status": "PENDING_CONFIGURATION", "message": "company_id and order_id are required once real payout execution is enabled"}
    payout = Payout(
        company_id=company_id,
        order_id=order_id,
        amount_minor=int(req.get("amount_minor", 0)),
        currency=str(req.get("currency", "PHP")).upper(),
        provider=str(req.get("provider", "SIMULATED")).upper(),
        destination=req.get("destination"),
        status=PayoutStatus.PENDING,
    )
    db.add(payout)
    await db.commit()
    await db.refresh(payout)
    return {"id": str(payout.id), "status": payout.status.value}


@router.get("/admin/payment-region-configs", response_model=list[RegionPaymentConfigResponse])
async def admin_region_configs(
    admin: User = Depends(_admin_finance()),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RegionPaymentConfig).order_by(RegionPaymentConfig.country_code.asc()))
    return result.scalars().all()


@router.post("/admin/payment-region-configs", response_model=RegionPaymentConfigResponse, status_code=201)
async def admin_create_region_config(
    req: RegionPaymentConfigUpsert,
    admin: User = Depends(_admin_finance()),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == req.country_code.upper()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="REGION_CONFIG_EXISTS")
    config = RegionPaymentConfig(
        country_code=req.country_code.upper(),
        country_name=req.country_name,
        local_currency=req.local_currency.upper(),
        default_settlement_currency=req.default_settlement_currency.upper(),
        default_transaction_mode=req.default_transaction_mode,
        enabled_currencies=[c.upper() for c in req.enabled_currencies],
        enabled_payment_methods=[m.upper() for m in req.enabled_payment_methods],
        cross_border_currencies=[c.upper() for c in req.cross_border_currencies],
        force_usd_bridge=req.force_usd_bridge,
        allow_supplier_payout_currency=req.allow_supplier_payout_currency,
        is_active=req.is_active,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.patch("/admin/payment-region-configs/{config_id}", response_model=RegionPaymentConfigResponse)
async def admin_update_region_config(
    config_id: uuid.UUID,
    req: RegionPaymentConfigPatch,
    admin: User = Depends(_admin_finance()),
    db: AsyncSession = Depends(get_db),
):
    config = (await db.execute(select(RegionPaymentConfig).where(RegionPaymentConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Region config not found")
    payload = req.model_dump(exclude_unset=True)
    for key, value in payload.items():
        if key in {"local_currency", "default_settlement_currency"} and isinstance(value, str):
            value = value.upper()
        if key in {"enabled_currencies", "cross_border_currencies"} and isinstance(value, list):
            value = [str(c).upper() for c in value]
        if key == "enabled_payment_methods" and isinstance(value, list):
            value = [str(m).upper() for m in value]
        setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/admin/settlement-events", response_model=list[SettlementEventResponse])
async def admin_settlement_events(
    admin: User = Depends(_admin_finance()),
    db: AsyncSession = Depends(get_db),
    provider: str | None = None,
    limit: int = Query(default=100, le=500),
):
    q = select(SettlementEvent)
    if provider:
        q = q.where(SettlementEvent.provider == provider.upper())
    result = await db.execute(q.order_by(SettlementEvent.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/admin/reconciliation/payment-events")
async def admin_reconciliation_payment_events(
    admin: User = Depends(_admin_finance()),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=500),
):
    payments = (await db.execute(select(LegacyPaymentEvent).order_by(LegacyPaymentEvent.received_at.desc()).limit(limit))).scalars().all()
    settlements = (await db.execute(select(SettlementEvent).order_by(SettlementEvent.created_at.desc()).limit(limit))).scalars().all()
    return {
        "payment_events": payments,
        "settlement_events": settlements,
        "summary": {
            "payment_event_count": len(payments),
            "settlement_event_count": len(settlements),
            "unmatched_payment_events": max(0, len(payments) - len(settlements)),
        },
    }

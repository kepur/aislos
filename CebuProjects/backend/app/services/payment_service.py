import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_config import (
    CurrencyConfig,
    FeeLineItem,
    FeeRule,
    FeeType,
    FxQuote,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentQuote,
    PaymentMethodConfig,
    QuoteStatus,
    RegionPaymentConfig,
    SettlementEvent,
    SettlementEventStatus,
    TransactionCurrencyMode,
)
from app.schemas.payments import PaymentQuoteCreateRequest

DEFAULT_COUNTRIES = {
    "PH": ("Philippines", "PHP"),
    "US": ("United States", "USD"),
    "JP": ("Japan", "JPY"),
    "SG": ("Singapore", "SGD"),
}

STATIC_RATES = {
    ("PHP", "USD"): Decimal("0.0172"),
    ("USD", "PHP"): Decimal("58.00"),
    ("PHP", "JPY"): Decimal("2.65"),
    ("JPY", "PHP"): Decimal("0.377"),
    ("PHP", "SGD"): Decimal("0.0231"),
    ("SGD", "PHP"): Decimal("43.20"),
    ("USD", "JPY"): Decimal("154.00"),
    ("JPY", "USD"): Decimal("0.0065"),
    ("USD", "SGD"): Decimal("1.34"),
    ("SGD", "USD"): Decimal("0.746"),
}


def _norm(value: str) -> str:
    return value.strip().upper()


def _money_minor(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fx_rate(source: str, target: str) -> Decimal:
    source = _norm(source)
    target = _norm(target)
    if source == target:
        return Decimal("1")
    rate = STATIC_RATES.get((source, target))
    if rate:
        return rate
    usd_source = STATIC_RATES.get((source, "USD"))
    usd_target = STATIC_RATES.get(("USD", target))
    if usd_source and usd_target:
        return usd_source * usd_target
    raise HTTPException(status_code=400, detail="FX_PAIR_UNSUPPORTED")


async def get_or_seed_region_config(db: AsyncSession, country_code: str) -> RegionPaymentConfig:
    country = _norm(country_code)[:2]
    config = (await db.execute(select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == country))).scalar_one_or_none()
    if config:
        return config

    country_name, currency = DEFAULT_COUNTRIES.get(country, (country, "USD"))
    config = RegionPaymentConfig(
        country_code=country,
        country_name=country_name,
        local_currency=currency,
        default_settlement_currency=currency,
        default_transaction_mode=TransactionCurrencyMode.LOCAL_ONLY,
        enabled_currencies=[currency],
        enabled_payment_methods=[
            f"{currency}_CARD",
            f"{currency}_BANK_TRANSFER",
            f"{currency}_MANUAL_BANK",
            f"{currency}_WALLET_BALANCE",
        ],
        cross_border_currencies=["USD"] if currency != "USD" else ["USD"],
        force_usd_bridge=False,
        allow_supplier_payout_currency=False,
        is_active=True,
    )
    db.add(config)
    await db.flush()
    return config


async def ensure_currency_enabled(db: AsyncSession, country_code: str, currency: str) -> RegionPaymentConfig:
    config = await get_or_seed_region_config(db, country_code)
    currency = _norm(currency)
    enabled = set(config.enabled_currencies or [])
    cross_border = set(config.cross_border_currencies or [])
    if not config.is_active or currency not in enabled | cross_border:
        raise HTTPException(status_code=400, detail="CURRENCY_DISABLED")
    global_currency = (await db.execute(select(CurrencyConfig).where(CurrencyConfig.code == currency))).scalar_one_or_none()
    if global_currency and not global_currency.is_enabled:
        raise HTTPException(status_code=400, detail="CURRENCY_DISABLED")
    return config


async def fee_lines_for(
    db: AsyncSession,
    *,
    amount_minor: int,
    country_code: str,
    payment_method: str | None,
    currency: str,
    include_cross_border: bool = False,
    include_fx: bool = False,
) -> list[dict]:
    country = _norm(country_code)[:2]
    method = _norm(payment_method or "")
    rules = (await db.execute(
        select(FeeRule).where(
            FeeRule.is_enabled.is_(True),
            FeeRule.currency == _norm(currency),
        )
    )).scalars().all()

    selected: list[FeeRule] = []
    for rule in rules:
        if rule.country_code and rule.country_code != country:
            continue
        if rule.payment_method and _norm(rule.payment_method) != method:
            continue
        selected.append(rule)

    lines: list[dict] = []
    for rule in selected:
        amount = rule.fixed_fee_minor + round(amount_minor * rule.variable_bps / 10000)
        amount = max(amount, rule.min_fee_minor or 0)
        if rule.max_fee_minor is not None:
            amount = min(amount, rule.max_fee_minor)
        if amount:
            lines.append({
                "fee_type": rule.fee_type,
                "label": rule.name,
                "amount_minor": amount,
                "currency": _norm(currency),
                "refundable": False,
                "metadata_json": {"rule_id": str(rule.id), "variable_bps": rule.variable_bps},
            })

    if include_cross_border:
        lines.append({
            "fee_type": FeeType.CROSS_BORDER_FEE,
            "label": "Cross-border service fee",
            "amount_minor": round(amount_minor * 100 / 10000),
            "currency": _norm(currency),
            "refundable": False,
            "metadata_json": {"variable_bps": 100},
        })
    if include_fx:
        lines.append({
            "fee_type": FeeType.FX_FEE,
            "label": "FX processing cost",
            "amount_minor": round(amount_minor * 50 / 10000),
            "currency": _norm(currency),
            "refundable": False,
            "metadata_json": {"variable_bps": 50, "markup_bps": 0},
        })
    return lines


async def create_payment_quote(db: AsyncSession, req: PaymentQuoteCreateRequest) -> PaymentQuote:
    buyer_country = _norm(req.buyer_country)[:2]
    supplier_country = _norm(req.supplier_country)[:2]
    order_currency = _norm(req.order_currency)
    payer_currency = _norm(req.payer_currency)
    settlement_currency = _norm(req.settlement_currency)
    payment_method = _norm(req.payment_method)

    buyer_config = await ensure_currency_enabled(db, buyer_country, payer_currency)
    await ensure_currency_enabled(db, supplier_country, settlement_currency)

    same_country = buyer_country == supplier_country
    same_currency = order_currency == payer_currency == settlement_currency
    if same_country and same_currency:
        mode = TransactionCurrencyMode.LOCAL_ONLY
    elif order_currency == "USD" or settlement_currency == "USD" or buyer_config.force_usd_bridge:
        mode = TransactionCurrencyMode.USD_BRIDGE
    elif payer_currency != settlement_currency:
        mode = TransactionCurrencyMode.BUYER_LOCAL_TO_SUPPLIER_LOCAL
    else:
        mode = TransactionCurrencyMode.ORDER_CURRENCY_FIXED

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    rate: Decimal | None = None
    rate_source: str | None = None
    fx_quote_id: uuid.UUID | None = None
    payer_base_minor = req.amount_minor
    if payer_currency != order_currency:
        rate = fx_rate(order_currency, payer_currency)
        rate_source = "SIMULATED_RATE_TABLE"
        payer_base_minor = _money_minor(Decimal(req.amount_minor) * rate)
        fx_quote = FxQuote(
            source_currency=order_currency,
            target_currency=payer_currency,
            rate=rate,
            rate_source=rate_source,
            expires_at=expires_at,
            raw_payload={"locked_minutes": 10},
        )
        db.add(fx_quote)
        await db.flush()
        fx_quote_id = fx_quote.id

    cross_border = buyer_country != supplier_country
    has_fx = payer_currency != order_currency or order_currency != settlement_currency
    lines = await fee_lines_for(
        db,
        amount_minor=payer_base_minor,
        country_code=buyer_country,
        payment_method=payment_method,
        currency=payer_currency,
        include_cross_border=cross_border,
        include_fx=has_fx,
    )
    fee_total = sum(line["amount_minor"] for line in lines)
    platform_revenue = sum(
        line["amount_minor"]
        for line in lines
        if line["fee_type"] in (FeeType.PLATFORM_SERVICE_FEE, FeeType.CROSS_BORDER_FEE, FeeType.PLATFORM_FX_MARKUP)
    )

    supplier_gross = req.amount_minor
    settlement_rate: Decimal | None = None
    if order_currency != settlement_currency:
        settlement_rate = fx_rate(order_currency, settlement_currency)
        supplier_gross = _money_minor(Decimal(req.amount_minor) * settlement_rate)

    settlement_fee = 0
    supplier_net = max(0, supplier_gross - settlement_fee)

    quote = PaymentQuote(
        buyer_country=buyer_country,
        supplier_country=supplier_country,
        mode=mode,
        payment_method=payment_method,
        order_currency=order_currency,
        payer_currency=payer_currency,
        settlement_currency=settlement_currency,
        amount_minor=req.amount_minor,
        payer_total_minor=payer_base_minor + fee_total,
        escrow_amount_minor=req.amount_minor,
        supplier_estimated_net_minor=supplier_net,
        platform_revenue_minor=platform_revenue,
        rate=rate,
        rate_source=rate_source,
        fx_quote_id=fx_quote_id,
        expires_at=expires_at,
        status=QuoteStatus.ACTIVE,
        metadata_json={
            "order_id": str(req.order_id) if req.order_id else None,
            "quote_valid_minutes": 10,
            "settlement_rate": str(settlement_rate) if settlement_rate else None,
            "platform_fx_markup_bps": 0,
        },
    )
    db.add(quote)
    await db.flush()
    for line in lines:
        db.add(FeeLineItem(quote_id=quote.id, **line))
    await db.flush()
    return quote


async def quote_with_lines(db: AsyncSession, quote_id: uuid.UUID) -> tuple[PaymentQuote, list[FeeLineItem]]:
    quote = (await db.execute(select(PaymentQuote).where(PaymentQuote.id == quote_id))).scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    lines = (await db.execute(select(FeeLineItem).where(FeeLineItem.quote_id == quote_id).order_by(FeeLineItem.created_at.asc()))).scalars().all()
    return quote, lines


async def create_payment_intent_from_quote(
    db: AsyncSession,
    *,
    quote: PaymentQuote,
    order_id: uuid.UUID | None = None,
    provider: str = "SIMULATED",
) -> PaymentIntent:
    now = datetime.now(timezone.utc)
    if quote.status != QuoteStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"QUOTE_{quote.status.value}")
    if quote.expires_at < now:
        quote.status = QuoteStatus.EXPIRED
        await db.flush()
        raise HTTPException(status_code=400, detail="QUOTE_EXPIRED")

    intent = PaymentIntent(
        quote_id=quote.id,
        order_id=order_id or (uuid.UUID(quote.metadata_json["order_id"]) if quote.metadata_json and quote.metadata_json.get("order_id") else None),
        provider=provider,
        provider_reference=f"SIM-{quote.id.hex[:16]}",
        payment_method=quote.payment_method,
        amount_minor=quote.payer_total_minor,
        currency=quote.payer_currency,
        status=PaymentIntentStatus.SUCCEEDED,
        raw_payload={"simulated": True, "quote_id": str(quote.id)},
    )
    quote.status = QuoteStatus.CONFIRMED
    db.add(intent)
    await db.flush()

    db.add(SettlementEvent(
        payment_intent_id=intent.id,
        provider=provider,
        provider_reference=intent.provider_reference,
        gross_amount_minor=intent.amount_minor,
        fee_amount_minor=max(0, intent.amount_minor - quote.escrow_amount_minor),
        net_amount_minor=min(intent.amount_minor, quote.escrow_amount_minor),
        currency=intent.currency,
        status=SettlementEventStatus.MATCHED,
        raw_payload={"source": "simulated_intent"},
    ))
    await db.flush()
    return intent

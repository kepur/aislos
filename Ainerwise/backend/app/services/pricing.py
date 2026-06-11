"""Cost Engine + Pricing Engine.

Chain: product_costs (landed cost, pre-quote estimate) -> price_lists
(region price, tier-aware) -> VAT from Region.tax_rules_json -> margin.
Quote building should call `quote_price` instead of reading
product.list_price directly. Project-level actuals stay in ProjectFinance.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.costing import ExchangeRate, PriceList, ProductCost
from app.models.region import Region

TWO_PLACES = Decimal("0.01")


def compute_landed_cost(cost: ProductCost) -> Decimal:
    base = Decimal(cost.purchase_cost)
    total = base
    if cost.freight_fixed is not None:
        total += Decimal(cost.freight_fixed)
    elif cost.freight_pct is not None:
        total += base * Decimal(cost.freight_pct) / 100
    if cost.customs_fixed is not None:
        total += Decimal(cost.customs_fixed)
    elif cost.customs_pct is not None:
        total += base * Decimal(cost.customs_pct) / 100
    if cost.warehousing_pct is not None:
        total += base * Decimal(cost.warehousing_pct) / 100
    if cost.labor_estimate is not None:
        total += Decimal(cost.labor_estimate)
    return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


async def _effective_row(db: AsyncSession, model, region_id: uuid.UUID, product_id: uuid.UUID, on: date):
    result = await db.execute(
        select(model)
        .where(
            model.region_id == region_id,
            model.product_id == product_id,
            model.valid_from <= on,
            (model.valid_to.is_(None)) | (model.valid_to >= on),
        )
        .order_by(model.valid_from.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def convert_amount(db: AsyncSession, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    if from_currency == to_currency:
        return amount
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.base == from_currency, ExchangeRate.quote == to_currency)
        .order_by(ExchangeRate.as_of.desc())
        .limit(1)
    )
    rate = result.scalar_one_or_none()
    if rate is None:
        raise ValueError(f"No exchange rate {from_currency}->{to_currency}")
    return (amount * Decimal(rate.rate)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def vat_rate(region: Region | None, *, solution_line: str | None = None) -> Decimal:
    """Region.tax_rules_json: {"vat_default": 20, "overrides": [{"solution_line": "energyguard", "vat": 8}]}"""
    if region is None or not region.tax_rules_json:
        return Decimal("0")
    rules = region.tax_rules_json
    rate = Decimal(str(rules.get("vat_default", 0)))
    for override in rules.get("overrides", []):
        if solution_line and override.get("solution_line") == solution_line and "vat" in override:
            rate = Decimal(str(override["vat"]))
    return rate


async def quote_price(
    db: AsyncSession,
    region_id: uuid.UUID,
    product_id: uuid.UUID,
    qty: int = 1,
    tier: str = "list",
    on: date | None = None,
) -> dict:
    """Unit price + landed cost + margin + VAT for one product line.

    Margin fields are internal-only — callers must never expose them on
    customer-facing reads (same boundary as Quote internal economics).
    """
    on = on or date.today()
    price_row = await _effective_row(db, PriceList, region_id, product_id, on)
    if price_row is None:
        raise ValueError("No price list entry for this region/product")
    unit_price = Decimal(price_row.list_price)
    if tier == "partner" and price_row.partner_price is not None:
        unit_price = Decimal(price_row.partner_price)
    elif tier == "vip" and price_row.vip_price is not None:
        unit_price = Decimal(price_row.vip_price)

    cost_row = await _effective_row(db, ProductCost, region_id, product_id, on)
    unit_cost = None
    if cost_row is not None:
        unit_cost = Decimal(cost_row.landed_cost) if cost_row.landed_cost is not None else compute_landed_cost(cost_row)
        if cost_row.currency != price_row.currency:
            unit_cost = await convert_amount(db, unit_cost, cost_row.currency, price_row.currency)

    region = await db.get(Region, region_id)
    from app.models.product import Product

    product = await db.get(Product, product_id)
    solution_line = getattr(product, "solution_line", None)
    vat = vat_rate(region, solution_line=solution_line)

    net = (unit_price * qty).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    tax = (net * vat / 100).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    unit_margin = (unit_price - unit_cost).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if unit_cost is not None else None
    margin_pct = (
        (unit_margin / unit_price * 100).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if unit_margin is not None and unit_price
        else None
    )
    return {
        "product_id": str(product_id),
        "region_id": str(region_id),
        "tier": tier,
        "qty": qty,
        "currency": price_row.currency,
        "unit_price": float(unit_price),
        "unit_landed_cost": float(unit_cost) if unit_cost is not None else None,
        "unit_margin": float(unit_margin) if unit_margin is not None else None,
        "margin_pct": float(margin_pct) if margin_pct is not None else None,
        "vat_pct": float(vat),
        "total_net": float(net),
        "total_tax": float(tax),
        "total_gross": float(net + tax),
    }

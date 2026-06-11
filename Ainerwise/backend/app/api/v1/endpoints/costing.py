import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.costing import ExchangeRate, PriceList, ProductCost
from app.services.pricing import compute_landed_cost, quote_price

router = APIRouter(prefix="/admin/costing", tags=["costing"])


class ProductCostUpsert(BaseModel):
    region_id: uuid.UUID
    product_id: uuid.UUID
    supplier_id: uuid.UUID | None = None
    purchase_cost: float
    currency: str = "EUR"
    freight_pct: float | None = None
    freight_fixed: float | None = None
    customs_pct: float | None = None
    customs_fixed: float | None = None
    warehousing_pct: float | None = None
    labor_estimate: float | None = None
    valid_from: date
    valid_to: date | None = None


class PriceListUpsert(BaseModel):
    region_id: uuid.UUID
    product_id: uuid.UUID
    list_price: float
    currency: str = "EUR"
    partner_price: float | None = None
    vip_price: float | None = None
    valid_from: date
    valid_to: date | None = None


class ExchangeRateUpsert(BaseModel):
    base: str
    quote: str
    rate: float
    as_of: date


def _row_to_dict(row) -> dict:
    return {
        c.name: (str(v) if isinstance(v, uuid.UUID) else (float(v) if hasattr(v, "quantize") else (v.isoformat() if hasattr(v, "isoformat") else v)))
        for c in row.__table__.columns
        if (v := getattr(row, c.name)) is not None or True
    }


@router.post("/product-costs")
async def upsert_product_cost(data: ProductCostUpsert, db: DB, admin: AdminUser):
    existing = (
        await db.execute(
            select(ProductCost).where(
                ProductCost.region_id == data.region_id,
                ProductCost.product_id == data.product_id,
                ProductCost.valid_from == data.valid_from,
            )
        )
    ).scalar_one_or_none()
    row = existing or ProductCost()
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    row.landed_cost = compute_landed_cost(row)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.get("/product-costs")
async def list_product_costs(
    db: DB, admin: AdminUser,
    region_id: uuid.UUID | None = None, product_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    query = select(ProductCost).order_by(ProductCost.valid_from.desc())
    count_query = select(func.count()).select_from(ProductCost)
    if region_id:
        query = query.where(ProductCost.region_id == region_id)
        count_query = count_query.where(ProductCost.region_id == region_id)
    if product_id:
        query = query.where(ProductCost.product_id == product_id)
        count_query = count_query.where(ProductCost.product_id == product_id)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_row_to_dict(r) for r in rows], "total": total}


@router.post("/price-lists")
async def upsert_price_list(data: PriceListUpsert, db: DB, admin: AdminUser):
    existing = (
        await db.execute(
            select(PriceList).where(
                PriceList.region_id == data.region_id,
                PriceList.product_id == data.product_id,
                PriceList.valid_from == data.valid_from,
            )
        )
    ).scalar_one_or_none()
    row = existing or PriceList()
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.get("/price-lists")
async def list_price_lists(
    db: DB, admin: AdminUser,
    region_id: uuid.UUID | None = None, product_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    query = select(PriceList).order_by(PriceList.valid_from.desc())
    count_query = select(func.count()).select_from(PriceList)
    if region_id:
        query = query.where(PriceList.region_id == region_id)
        count_query = count_query.where(PriceList.region_id == region_id)
    if product_id:
        query = query.where(PriceList.product_id == product_id)
        count_query = count_query.where(PriceList.product_id == product_id)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_row_to_dict(r) for r in rows], "total": total}


@router.post("/exchange-rates")
async def upsert_exchange_rate(data: ExchangeRateUpsert, db: DB, admin: AdminUser):
    existing = (
        await db.execute(
            select(ExchangeRate).where(
                ExchangeRate.base == data.base, ExchangeRate.quote == data.quote, ExchangeRate.as_of == data.as_of
            )
        )
    ).scalar_one_or_none()
    row = existing or ExchangeRate()
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.get("/quote-price")
async def get_quote_price(
    db: DB, admin: AdminUser,
    region_id: uuid.UUID, product_id: uuid.UUID,
    qty: int = Query(1, ge=1), tier: str = Query("list"),
):
    try:
        return await quote_price(db, region_id, product_id, qty=qty, tier=tier)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None

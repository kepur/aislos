"""Shipping estimation for users + admin shipping management."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.shipping import (
    ShippingMethod,
    ShippingRate,
    ShippingRateStatus,
    ShippingRoute,
    ShippingRouteStatus,
)
from app.models.user import User
from app.models.user import UserRole
from app.schemas.shipping import (
    ShippingEstimateRequest,
    ShippingEstimateResponse,
    ShippingRateCreate,
    ShippingRateResponse,
    ShippingRateUpdate,
    ShippingRouteCreate,
    ShippingRouteResponse,
    ShippingStatisticsResponse,
    ShippingRouteUpdate,
)
from app.services.shipping_service import estimate_shipping

router = APIRouter(tags=["shipping"])


# ──────────────── User-facing endpoints ────────────────

@router.get("/shipping/methods")
async def list_shipping_methods():
    return [{"value": m.value, "label": m.value.replace("_", " ").title()} for m in ShippingMethod]


@router.get("/shipping/routes", response_model=list[ShippingRouteResponse])
async def list_available_routes(
    origin: str | None = None,
    dest: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(ShippingRoute).where(ShippingRoute.status == ShippingRouteStatus.ACTIVE)
    if origin:
        q = q.where(ShippingRoute.origin_country == origin.upper())
    if dest:
        q = q.where(ShippingRoute.dest_country == dest.upper())
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("/shipping/estimate", response_model=ShippingEstimateResponse)
async def get_shipping_estimate(
    body: ShippingEstimateRequest,
    db: AsyncSession = Depends(get_db),
):
    estimates = await estimate_shipping(
        db,
        origin_country=body.origin_country,
        dest_country=body.dest_country,
        weight_kg=body.weight_kg,
        length_cm=body.length_cm,
        width_cm=body.width_cm,
        height_cm=body.height_cm,
        shipping_method=body.shipping_method,
        declared_value_minor=body.declared_value_minor,
        currency=body.currency,
    )
    return ShippingEstimateResponse(
        estimates=estimates,
        origin_country=body.origin_country,
        dest_country=body.dest_country,
    )


# ──────────────── Admin endpoints ────────────────

# --- Routes ---
@router.get("/admin/shipping/routes", response_model=list[ShippingRouteResponse])
async def admin_list_routes(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    q = select(ShippingRoute).order_by(ShippingRoute.origin_country, ShippingRoute.dest_country)
    return (await db.execute(q)).scalars().all()


@router.post("/admin/shipping/routes", response_model=ShippingRouteResponse, status_code=201)
async def admin_create_route(
    body: ShippingRouteCreate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    route = ShippingRoute(**body.model_dump())
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


@router.patch("/admin/shipping/routes/{route_id}", response_model=ShippingRouteResponse)
async def admin_update_route(
    route_id: UUID,
    body: ShippingRouteUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    route = (await db.execute(select(ShippingRoute).where(ShippingRoute.id == route_id))).scalars().first()
    if not route:
        raise HTTPException(404, "Route not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(route, k, v)
    await db.commit()
    await db.refresh(route)
    return route


@router.delete("/admin/shipping/routes/{route_id}", status_code=204)
async def admin_delete_route(
    route_id: UUID,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    route = (await db.execute(select(ShippingRoute).where(ShippingRoute.id == route_id))).scalars().first()
    if not route:
        raise HTTPException(404, "Route not found")
    route.status = ShippingRouteStatus.INACTIVE
    await db.commit()


# --- Rates ---
@router.get("/admin/shipping/rates", response_model=list[ShippingRateResponse])
async def admin_list_rates(
    route_id: UUID | None = None,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    q = select(ShippingRate).order_by(ShippingRate.weight_min_kg)
    if route_id:
        q = q.where(ShippingRate.route_id == route_id)
    return (await db.execute(q)).scalars().all()


@router.post("/admin/shipping/rates", response_model=ShippingRateResponse, status_code=201)
async def admin_create_rate(
    body: ShippingRateCreate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rate = ShippingRate(**body.model_dump(exclude_unset=True))
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return rate


@router.patch("/admin/shipping/rates/{rate_id}", response_model=ShippingRateResponse)
async def admin_update_rate(
    rate_id: UUID,
    body: ShippingRateUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rate = (await db.execute(select(ShippingRate).where(ShippingRate.id == rate_id))).scalars().first()
    if not rate:
        raise HTTPException(404, "Rate not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rate, k, v)
    await db.commit()
    await db.refresh(rate)
    return rate


@router.delete("/admin/shipping/rates/{rate_id}", status_code=204)
async def admin_delete_rate(
    rate_id: UUID,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    rate = (await db.execute(select(ShippingRate).where(ShippingRate.id == rate_id))).scalars().first()
    if not rate:
        raise HTTPException(404, "Rate not found")
    rate.status = ShippingRateStatus.INACTIVE
    await db.commit()


@router.get("/admin/shipping/statistics", response_model=ShippingStatisticsResponse)
async def admin_shipping_statistics(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    total_routes = await db.scalar(select(func.count()).select_from(ShippingRoute))
    active_routes = await db.scalar(
        select(func.count()).select_from(ShippingRoute).where(ShippingRoute.status == ShippingRouteStatus.ACTIVE)
    )
    total_rates = await db.scalar(select(func.count()).select_from(ShippingRate))
    active_rates = await db.scalar(
        select(func.count()).select_from(ShippingRate).where(ShippingRate.status == ShippingRateStatus.ACTIVE)
    )
    avg_price_per_kg_minor = await db.scalar(
        select(func.avg(ShippingRate.price_per_kg_minor)).where(ShippingRate.status == ShippingRateStatus.ACTIVE)
    )
    last_route_updated_at = await db.scalar(select(func.max(ShippingRoute.updated_at)))
    last_rate_updated_at = await db.scalar(select(func.max(ShippingRate.updated_at)))
    by_method_rows = (
        await db.execute(
            select(ShippingRoute.shipping_method, func.count())
            .where(ShippingRoute.status == ShippingRouteStatus.ACTIVE)
            .group_by(ShippingRoute.shipping_method)
        )
    ).all()
    top_expensive_rows = (
        await db.execute(
            select(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
                func.avg(ShippingRate.price_per_kg_minor).label("avg_price_per_kg_minor"),
                func.avg(ShippingRate.estimated_days_max).label("avg_eta_max_days"),
            )
            .join(ShippingRate, ShippingRate.route_id == ShippingRoute.id)
            .where(ShippingRoute.status == ShippingRouteStatus.ACTIVE, ShippingRate.status == ShippingRateStatus.ACTIVE)
            .group_by(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
            )
            .order_by(func.avg(ShippingRate.price_per_kg_minor).desc())
            .limit(5)
        )
    ).all()
    top_cheapest_rows = (
        await db.execute(
            select(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
                func.avg(ShippingRate.price_per_kg_minor).label("avg_price_per_kg_minor"),
                func.avg(ShippingRate.estimated_days_max).label("avg_eta_max_days"),
            )
            .join(ShippingRate, ShippingRate.route_id == ShippingRoute.id)
            .where(ShippingRoute.status == ShippingRouteStatus.ACTIVE, ShippingRate.status == ShippingRateStatus.ACTIVE)
            .group_by(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
            )
            .order_by(func.avg(ShippingRate.price_per_kg_minor).asc())
            .limit(5)
        )
    ).all()
    top_slowest_rows = (
        await db.execute(
            select(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
                func.avg(ShippingRate.price_per_kg_minor).label("avg_price_per_kg_minor"),
                func.avg(ShippingRate.estimated_days_max).label("avg_eta_max_days"),
            )
            .join(ShippingRate, ShippingRate.route_id == ShippingRoute.id)
            .where(ShippingRoute.status == ShippingRouteStatus.ACTIVE, ShippingRate.status == ShippingRateStatus.ACTIVE)
            .group_by(
                ShippingRoute.id,
                ShippingRoute.origin_country,
                ShippingRoute.dest_country,
                ShippingRoute.shipping_method,
            )
            .order_by(func.avg(ShippingRate.estimated_days_max).desc())
            .limit(5)
        )
    ).all()

    total_routes = int(total_routes or 0)
    active_routes = int(active_routes or 0)
    total_rates = int(total_rates or 0)
    active_rates = int(active_rates or 0)
    routes_by_method = {str(method.value if hasattr(method, "value") else method): int(count) for method, count in by_method_rows}
    def _rows_to_items(rows):
        return [
            {
                "route_id": str(route_id),
                "route_label": f"{origin_country}->{dest_country}",
                "shipping_method": str(shipping_method.value if hasattr(shipping_method, "value") else shipping_method),
                "avg_price_per_kg_minor": int(avg_price_per_kg_minor_value or 0),
                "avg_eta_max_days": float(avg_eta_max_days or 0),
            }
            for route_id, origin_country, dest_country, shipping_method, avg_price_per_kg_minor_value, avg_eta_max_days in rows
        ]

    return ShippingStatisticsResponse(
        total_routes=total_routes,
        active_routes=active_routes,
        inactive_routes=max(total_routes - active_routes, 0),
        total_rates=total_rates,
        active_rates=active_rates,
        inactive_rates=max(total_rates - active_rates, 0),
        avg_price_per_kg_minor=int(avg_price_per_kg_minor or 0),
        last_route_updated_at=last_route_updated_at,
        last_rate_updated_at=last_rate_updated_at,
        routes_by_method=routes_by_method,
        top_expensive_routes=_rows_to_items(top_expensive_rows),
        top_cheapest_routes=_rows_to_items(top_cheapest_rows),
        top_slowest_routes=_rows_to_items(top_slowest_rows),
    )

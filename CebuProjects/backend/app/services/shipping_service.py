"""Shipping cost estimation service."""
import math
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping import ShippingMethod, ShippingRate, ShippingRoute, ShippingRouteStatus, ShippingRateStatus
from app.schemas.shipping import ShippingEstimateItem


INSURANCE_RATE = 0.005   # 0.5% of declared value


def calc_volumetric_weight(length_cm: float, width_cm: float, height_cm: float, volume_factor: float) -> float:
    """Calculate volumetric weight: (L * W * H) / factor.  Air=5000, Sea=1000."""
    return (length_cm * width_cm * height_cm) / volume_factor


async def estimate_shipping(
    db: AsyncSession,
    origin_country: str,
    dest_country: str,
    weight_kg: float,
    length_cm: float | None = None,
    width_cm: float | None = None,
    height_cm: float | None = None,
    shipping_method: ShippingMethod | None = None,
    declared_value_minor: int | None = None,
    currency: str = "USD",
) -> list[ShippingEstimateItem]:
    """Return shipping estimates for all matching routes."""

    # Find matching active routes
    route_q = select(ShippingRoute).where(
        ShippingRoute.origin_country == origin_country.upper(),
        ShippingRoute.dest_country == dest_country.upper(),
        ShippingRoute.status == ShippingRouteStatus.ACTIVE,
    )
    if shipping_method:
        route_q = route_q.where(ShippingRoute.shipping_method == shipping_method)

    routes = (await db.execute(route_q)).scalars().all()
    if not routes:
        return []

    today = date.today()
    estimates: list[ShippingEstimateItem] = []

    for route in routes:
        # Find the best matching rate for this weight
        rate_q = select(ShippingRate).where(
            ShippingRate.route_id == route.id,
            ShippingRate.status == ShippingRateStatus.ACTIVE,
            ShippingRate.weight_min_kg <= weight_kg,
            ShippingRate.weight_max_kg >= weight_kg,
            ShippingRate.valid_from <= today,
        ).order_by(ShippingRate.price_per_kg_minor.asc())

        rate = (await db.execute(rate_q)).scalars().first()
        if not rate:
            continue

        # Calculate volumetric weight if dimensions provided
        vol_weight = None
        if length_cm and width_cm and height_cm:
            vol_weight = calc_volumetric_weight(length_cm, width_cm, height_cm, rate.volume_factor)

        chargeable = max(weight_kg, vol_weight or 0)

        # Base cost
        base_cost = max(
            int(math.ceil(chargeable * rate.price_per_kg_minor)),
            rate.min_charge_minor,
        )

        # Surcharges
        surcharges = []
        surcharge_total = 0
        if rate.surcharges_json:
            for name, amount in rate.surcharges_json.items():
                surcharges.append({"name": name, "amount_minor": amount})
                surcharge_total += amount

        # Insurance
        insurance = 0
        if declared_value_minor:
            insurance = int(math.ceil(declared_value_minor * INSURANCE_RATE))

        total = base_cost + surcharge_total + insurance

        estimates.append(ShippingEstimateItem(
            route_id=route.id,
            shipping_method=route.shipping_method.value,
            actual_weight_kg=weight_kg,
            volumetric_weight_kg=round(vol_weight, 2) if vol_weight else None,
            chargeable_weight_kg=round(chargeable, 2),
            base_cost_minor=base_cost,
            surcharges=surcharges,
            insurance_minor=insurance,
            total_shipping_minor=total,
            currency=rate.currency,
            estimated_days_min=rate.estimated_days_min,
            estimated_days_max=rate.estimated_days_max,
        ))

    # Sort by total cost ascending
    estimates.sort(key=lambda e: e.total_shipping_minor)
    return estimates

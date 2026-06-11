from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.shipping import ShippingMethod


# --- Shipping Route ---
class ShippingRouteCreate(BaseModel):
    origin_country: str = Field(..., max_length=5)
    origin_region: str | None = None
    dest_country: str = Field(..., max_length=5)
    dest_region: str | None = None
    shipping_method: ShippingMethod
    description: str | None = None


class ShippingRouteUpdate(BaseModel):
    origin_region: str | None = None
    dest_region: str | None = None
    description: str | None = None
    status: str | None = None


class ShippingRouteResponse(BaseModel):
    id: UUID
    origin_country: str
    origin_region: str | None = None
    dest_country: str
    dest_region: str | None = None
    shipping_method: str
    description: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Shipping Rate ---
class ShippingRateCreate(BaseModel):
    route_id: UUID
    weight_min_kg: float = 0
    weight_max_kg: float = 99999
    price_per_kg_minor: int
    currency: str = "USD"
    min_charge_minor: int = 0
    volume_factor: float = 5000
    estimated_days_min: int = 1
    estimated_days_max: int = 7
    surcharges_json: dict | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None


class ShippingRateUpdate(BaseModel):
    weight_min_kg: float | None = None
    weight_max_kg: float | None = None
    price_per_kg_minor: int | None = None
    currency: str | None = None
    min_charge_minor: int | None = None
    volume_factor: float | None = None
    estimated_days_min: int | None = None
    estimated_days_max: int | None = None
    surcharges_json: dict | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    status: str | None = None


class ShippingRateResponse(BaseModel):
    id: UUID
    route_id: UUID
    weight_min_kg: float
    weight_max_kg: float
    price_per_kg_minor: int
    currency: str
    min_charge_minor: int
    volume_factor: float
    estimated_days_min: int
    estimated_days_max: int
    surcharges_json: dict | None = None
    valid_from: date
    valid_until: date | None = None
    notes: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Shipping Estimate ---
class ShippingEstimateRequest(BaseModel):
    origin_country: str = Field(..., max_length=5)
    dest_country: str = Field(..., max_length=5)
    weight_kg: float = Field(..., gt=0)
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    shipping_method: ShippingMethod | None = None   # None = return all methods
    declared_value_minor: int | None = None
    currency: str = "USD"


class ShippingEstimateItem(BaseModel):
    route_id: UUID
    shipping_method: str
    actual_weight_kg: float
    volumetric_weight_kg: float | None = None
    chargeable_weight_kg: float
    base_cost_minor: int
    surcharges: list[dict] = []
    insurance_minor: int = 0
    total_shipping_minor: int
    currency: str
    estimated_days_min: int
    estimated_days_max: int


class ShippingEstimateResponse(BaseModel):
    estimates: list[ShippingEstimateItem]
    origin_country: str
    dest_country: str


# --- Admin shipping statistics ---
class ShippingStatisticsResponse(BaseModel):
    total_routes: int
    active_routes: int
    inactive_routes: int
    total_rates: int
    active_rates: int
    inactive_rates: int
    avg_price_per_kg_minor: int
    last_route_updated_at: datetime | None = None
    last_rate_updated_at: datetime | None = None
    routes_by_method: dict[str, int]
    top_expensive_routes: list[dict]
    top_cheapest_routes: list[dict]
    top_slowest_routes: list[dict]


# --- Order Shipping ---
class OrderShippingResponse(BaseModel):
    id: UUID
    order_id: UUID
    shipping_method: str
    origin_address_id: UUID | None = None
    dest_address_id: UUID | None = None
    chargeable_weight_kg: float | None = None
    shipping_cost_minor: int
    currency: str
    estimated_days_min: int | None = None
    estimated_days_max: int | None = None
    tracking_number: str | None = None
    carrier_name: str | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

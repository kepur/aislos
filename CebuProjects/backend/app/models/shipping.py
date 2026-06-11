import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ShippingMethod(str, enum.Enum):
    SEA_FREIGHT = "SEA_FREIGHT"
    AIR_FREIGHT = "AIR_FREIGHT"
    EXPRESS = "EXPRESS"
    LAND_FREIGHT = "LAND_FREIGHT"
    LOCAL_DELIVERY = "LOCAL_DELIVERY"
    SELF_PICKUP = "SELF_PICKUP"


class ShippingRouteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ShippingRateStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class OrderShippingStatus(str, enum.Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"


class ShippingRoute(Base):
    """International shipping routes: origin country → destination country + method."""
    __tablename__ = "shipping_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_country: Mapped[str] = mapped_column(String(5), index=True)       # ISO code
    origin_region: Mapped[str | None] = mapped_column(String(100))
    dest_country: Mapped[str] = mapped_column(String(5), index=True)
    dest_region: Mapped[str | None] = mapped_column(String(100))
    shipping_method: Mapped[ShippingMethod] = mapped_column(Enum(ShippingMethod, name="shipping_method", create_type=False))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ShippingRouteStatus] = mapped_column(Enum(ShippingRouteStatus, name="shipping_route_status", create_type=False), default=ShippingRouteStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ShippingRate(Base):
    """Weight-tiered pricing for a shipping route."""
    __tablename__ = "shipping_rates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    weight_min_kg: Mapped[float] = mapped_column(Float, default=0)
    weight_max_kg: Mapped[float] = mapped_column(Float, default=99999)
    price_per_kg_minor: Mapped[int] = mapped_column(Integer)              # cents/centavos per kg
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    min_charge_minor: Mapped[int] = mapped_column(Integer, default=0)      # minimum charge
    volume_factor: Mapped[float] = mapped_column(Float, default=5000)      # air=5000, sea=1000
    estimated_days_min: Mapped[int] = mapped_column(Integer, default=1)
    estimated_days_max: Mapped[int] = mapped_column(Integer, default=7)
    surcharges_json: Mapped[dict | None] = mapped_column(JSON)             # { fuel: 500, peak: 300 }
    valid_from: Mapped[date] = mapped_column(Date, default=lambda: date.today())
    valid_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ShippingRateStatus] = mapped_column(Enum(ShippingRateStatus, name="shipping_rate_status", create_type=False), default=ShippingRateStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class OrderShipping(Base):
    """Shipping details attached to an order after confirmation."""
    __tablename__ = "order_shipping"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    shipping_method: Mapped[ShippingMethod] = mapped_column(Enum(ShippingMethod, name="shipping_method", create_type=False))
    origin_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    dest_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    chargeable_weight_kg: Mapped[float | None] = mapped_column(Float)
    shipping_cost_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    estimated_days_min: Mapped[int | None] = mapped_column(Integer)
    estimated_days_max: Mapped[int | None] = mapped_column(Integer)
    tracking_number: Mapped[str | None] = mapped_column(String(200))
    carrier_name: Mapped[str | None] = mapped_column(String(200))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[OrderShippingStatus] = mapped_column(Enum(OrderShippingStatus, name="order_shipping_status", create_type=False), default=OrderShippingStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class RegionType(str, enum.Enum):
    COUNTRY = "COUNTRY"
    CITY = "CITY"
    DISTRICT = "DISTRICT"
    BUSINESS_AREA = "BUSINESS_AREA"


class CoverageType(str, enum.Enum):
    RADIUS = "RADIUS"
    POLYGON = "POLYGON"
    ADMIN_REGION = "ADMIN_REGION"


class ServiceAreaStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(100), default="Philippines")
    city: Mapped[str | None] = mapped_column(String(100))
    region_type: Mapped[RegionType] = mapped_column(Enum(RegionType, name="region_type", create_type=False), default=RegionType.CITY)
    center_lat: Mapped[float | None] = mapped_column(Float)
    center_lng: Mapped[float | None] = mapped_column(Float)
    default_radius_km: Mapped[int] = mapped_column(Integer, default=15)
    polygon_json: Mapped[dict | None] = mapped_column(JSON)
    provider_place_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[RegionStatus] = mapped_column(Enum(RegionStatus, name="region_status", create_type=False), default=RegionStatus.ACTIVE)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ServiceArea(Base):
    __tablename__ = "service_areas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    coverage_type: Mapped[CoverageType] = mapped_column(Enum(CoverageType, name="coverage_type", create_type=False), default=CoverageType.RADIUS)
    center_lat: Mapped[float | None] = mapped_column(Float)
    center_lng: Mapped[float | None] = mapped_column(Float)
    radius_km: Mapped[int | None] = mapped_column(Integer)
    polygon_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[ServiceAreaStatus] = mapped_column(Enum(ServiceAreaStatus, name="service_area_status", create_type=False), default=ServiceAreaStatus.ACTIVE)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

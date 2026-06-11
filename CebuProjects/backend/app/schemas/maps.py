import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.maps import CoverageType, RegionStatus, RegionType, ServiceAreaStatus


class MapPlaceResponse(BaseModel):
    label: str
    place_id: str | None = None
    country: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    provider: str = "local"


class GeocodeResponse(BaseModel):
    address: str
    country: str | None = None
    city: str | None = None
    lat: float
    lng: float
    provider: str = "local"


class CoverageEstimateResponse(BaseModel):
    lat: float
    lng: float
    radius_km: int
    matching_branches: int
    matching_companies: int
    active_regions: list[str]


class RegionCreate(BaseModel):
    name: str
    slug: str
    country: str = "Philippines"
    city: str | None = None
    region_type: RegionType = RegionType.CITY
    center_lat: float | None = None
    center_lng: float | None = None
    default_radius_km: int = Field(default=15, ge=1, le=500)
    polygon_json: dict | None = None
    provider_place_id: str | None = None
    status: RegionStatus = RegionStatus.ACTIVE
    notes: str | None = None


class RegionUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    city: str | None = None
    region_type: RegionType | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    default_radius_km: int | None = Field(default=None, ge=1, le=500)
    polygon_json: dict | None = None
    provider_place_id: str | None = None
    status: RegionStatus | None = None
    notes: str | None = None


class RegionResponse(RegionCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceAreaCreate(BaseModel):
    name: str
    region_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    coverage_type: CoverageType = CoverageType.RADIUS
    center_lat: float | None = None
    center_lng: float | None = None
    radius_km: int | None = Field(default=15, ge=1, le=500)
    polygon_json: dict | None = None
    status: ServiceAreaStatus = ServiceAreaStatus.ACTIVE
    notes: str | None = None


class ServiceAreaUpdate(BaseModel):
    name: str | None = None
    region_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    coverage_type: CoverageType | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    radius_km: int | None = Field(default=None, ge=1, le=500)
    polygon_json: dict | None = None
    status: ServiceAreaStatus | None = None
    notes: str | None = None


class ServiceAreaResponse(ServiceAreaCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

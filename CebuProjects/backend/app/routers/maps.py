import math
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.company import Branch, BranchStatus, Company, CompanyStatus
from app.models.maps import Region, RegionStatus, ServiceArea, ServiceAreaStatus
from app.models.user import User, UserRole
from app.services.maps_config_service import get_maps_config
from app.schemas.maps import (
    CoverageEstimateResponse,
    GeocodeResponse,
    MapPlaceResponse,
    RegionCreate,
    RegionResponse,
    RegionUpdate,
    ServiceAreaCreate,
    ServiceAreaResponse,
    ServiceAreaUpdate,
)

router = APIRouter(tags=["Maps"])

LOCAL_PLACES = [
    {"label": "Cebu City, Cebu, Philippines", "country": "Philippines", "city": "Cebu City", "lat": 10.3157, "lng": 123.8854},
    {"label": "Mandaue City, Cebu, Philippines", "country": "Philippines", "city": "Mandaue City", "lat": 10.3333, "lng": 123.9333},
    {"label": "Lapu-Lapu City, Cebu, Philippines", "country": "Philippines", "city": "Lapu-Lapu City", "lat": 10.3103, "lng": 123.9494},
    {"label": "Talisay City, Cebu, Philippines", "country": "Philippines", "city": "Talisay City", "lat": 10.2447, "lng": 123.8494},
    {"label": "Consolacion, Cebu, Philippines", "country": "Philippines", "city": "Consolacion", "lat": 10.3766, "lng": 123.9573},
]


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/maps/autocomplete", response_model=list[MapPlaceResponse])
async def autocomplete(q: str = Query(min_length=1), db: AsyncSession = Depends(get_db)):
    cfg = await get_maps_config(db)
    provider = (cfg.get("provider") or "LOCAL").upper()

    if provider == "GOOGLE" and cfg.get("maps_enabled") and cfg.get("google_maps_api_key"):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                    params={
                        "input": q,
                        "key": cfg.get("google_maps_api_key"),
                        "components": f"country:{(cfg.get('google_maps_region') or 'PH').lower()}",
                        "language": cfg.get("google_maps_language") or "en",
                    },
                )
            data = response.json()
            if data.get("status") in ("OK", "ZERO_RESULTS"):
                return [
                    MapPlaceResponse(
                        label=p.get("description") or "",
                        place_id=p.get("place_id") or "",
                        country=(cfg.get("google_maps_region") or "PH"),
                        city=None,
                        lat=None,
                        lng=None,
                    )
                    for p in data.get("predictions", [])[:10]
                ]
        except Exception:
            pass

    needle = q.lower()
    local = [
        MapPlaceResponse(
            label=place["label"],
            place_id=f"local:{place['city']}",
            country=place["country"],
            city=place["city"],
            lat=place["lat"],
            lng=place["lng"],
        )
        for place in LOCAL_PLACES
        if needle in place["label"].lower()
    ]
    regions = (await db.execute(
        select(Region).where(Region.status == RegionStatus.ACTIVE, Region.name.ilike(f"%{q}%")).limit(10)
    )).scalars().all()
    return local + [
        MapPlaceResponse(
            label=f"{r.name}, {r.country}",
            place_id=str(r.id),
            country=r.country,
            city=r.city,
            lat=r.center_lat,
            lng=r.center_lng,
        )
        for r in regions
    ]


@router.get("/maps/geocode", response_model=GeocodeResponse)
async def geocode(address: str = Query(min_length=2), db: AsyncSession = Depends(get_db)):
    cfg = await get_maps_config(db)
    provider = (cfg.get("provider") or "LOCAL").upper()

    if provider == "GOOGLE" and cfg.get("maps_enabled") and cfg.get("google_maps_api_key"):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "address": address,
                        "key": cfg.get("google_maps_api_key"),
                        "region": cfg.get("google_maps_region") or "PH",
                        "language": cfg.get("google_maps_language") or "en",
                    },
                )
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                first = data["results"][0]
                loc = (first.get("geometry") or {}).get("location") or {}
                return GeocodeResponse(
                    address=first.get("formatted_address") or address,
                    country=cfg.get("google_maps_region") or "PH",
                    city=None,
                    lat=float(loc.get("lat") or 10.3157),
                    lng=float(loc.get("lng") or 123.8854),
                )
        except Exception:
            pass

    needle = address.lower()
    for place in LOCAL_PLACES:
        if needle in place["label"].lower() or needle in place["city"].lower():
            return GeocodeResponse(address=place["label"], country=place["country"], city=place["city"], lat=place["lat"], lng=place["lng"])
    region = (await db.execute(select(Region).where(Region.name.ilike(f"%{address}%")))).scalar_one_or_none()
    if region and region.center_lat is not None and region.center_lng is not None:
        return GeocodeResponse(address=f"{region.name}, {region.country}", country=region.country, city=region.city, lat=region.center_lat, lng=region.center_lng)
    return GeocodeResponse(address=address, country="Philippines", city=None, lat=10.3157, lng=123.8854)


@router.get("/maps/reverse-geocode", response_model=GeocodeResponse)
async def reverse_geocode(lat: float, lng: float, db: AsyncSession = Depends(get_db)):
    cfg = await get_maps_config(db)
    provider = (cfg.get("provider") or "LOCAL").upper()

    if provider == "GOOGLE" and cfg.get("maps_enabled") and cfg.get("google_maps_api_key"):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "latlng": f"{lat},{lng}",
                        "key": cfg.get("google_maps_api_key"),
                        "language": cfg.get("google_maps_language") or "en",
                    },
                )
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                first = data["results"][0]
                return GeocodeResponse(
                    address=first.get("formatted_address") or "",
                    country=cfg.get("google_maps_region") or "PH",
                    city=None,
                    lat=lat,
                    lng=lng,
                )
        except Exception:
            pass

    nearest = min(LOCAL_PLACES, key=lambda p: distance_km(lat, lng, p["lat"], p["lng"]))
    return GeocodeResponse(address=nearest["label"], country=nearest["country"], city=nearest["city"], lat=lat, lng=lng)


@router.get("/maps/coverage/estimate", response_model=CoverageEstimateResponse)
async def coverage_estimate(
    lat: float,
    lng: float,
    radius_km: int = Query(default=15, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Branch, Company)
        .join(Company, Branch.company_id == Company.id)
        .where(Branch.status == BranchStatus.ACTIVE, Company.status == CompanyStatus.ACTIVE)
    )).all()
    company_ids = set()
    branch_count = 0
    for branch, company in rows:
        if branch.lat is None or branch.lng is None:
            continue
        if distance_km(lat, lng, branch.lat, branch.lng) <= radius_km + (branch.radius_km or 0):
            branch_count += 1
            company_ids.add(company.id)

    regions = (await db.execute(select(Region).where(Region.status == RegionStatus.ACTIVE))).scalars().all()
    active_regions = [
        r.name
        for r in regions
        if r.center_lat is not None and r.center_lng is not None and distance_km(lat, lng, r.center_lat, r.center_lng) <= (r.default_radius_km or radius_km)
    ]
    return CoverageEstimateResponse(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        matching_branches=branch_count,
        matching_companies=len(company_ids),
        active_regions=active_regions,
    )


@router.get("/admin/regions", response_model=list[RegionResponse])
async def list_regions(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Region).order_by(Region.country.asc(), Region.city.asc(), Region.name.asc()))
    return result.scalars().all()


@router.post("/admin/regions", response_model=RegionResponse, status_code=201)
async def create_region(
    req: RegionCreate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    region = Region(**req.model_dump())
    db.add(region)
    await db.commit()
    await db.refresh(region)
    return region


@router.patch("/admin/regions/{region_id}", response_model=RegionResponse)
async def update_region(
    region_id: UUID,
    req: RegionUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    region = (await db.execute(select(Region).where(Region.id == region_id))).scalar_one_or_none()
    if not region:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Region not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(region, field, value)
    await db.commit()
    await db.refresh(region)
    return region


@router.get("/admin/service-areas", response_model=list[ServiceAreaResponse])
async def list_service_areas(
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER, UserRole.SUPPORT_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServiceArea).order_by(ServiceArea.created_at.desc()))
    return result.scalars().all()


@router.post("/admin/service-areas", response_model=ServiceAreaResponse, status_code=201)
async def create_service_area(
    req: ServiceAreaCreate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    area = ServiceArea(**req.model_dump())
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return area


@router.patch("/admin/service-areas/{area_id}", response_model=ServiceAreaResponse)
async def update_service_area(
    area_id: UUID,
    req: ServiceAreaUpdate,
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPS_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    area = (await db.execute(select(ServiceArea).where(ServiceArea.id == area_id))).scalar_one_or_none()
    if not area:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service area not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    await db.commit()
    await db.refresh(area)
    return area

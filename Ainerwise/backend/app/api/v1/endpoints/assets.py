import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.models.asset import Asset, Site

router = APIRouter(prefix="/admin", tags=["assets"])


class SiteUpsert(BaseModel):
    name: str
    region_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    contact_user_id: uuid.UUID | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    building_meta_json: dict | None = None


class AssetUpsert(BaseModel):
    site_id: uuid.UUID
    name: str
    project_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    parent_asset_id: uuid.UUID | None = None
    floor: str | None = None
    room: str | None = None
    serial_no: str | None = None
    installed_at: date | None = None
    customer_warranty_id: uuid.UUID | None = None
    amc_contract_id: uuid.UUID | None = None
    status: str = "active"
    notes: str | None = None
    meta_json: dict | None = None


def _site_dict(s: Site) -> dict:
    return {
        "id": str(s.id), "name": s.name, "address": s.address, "city": s.city,
        "country": s.country, "company_id": str(s.company_id) if s.company_id else None,
        "building_meta_json": s.building_meta_json, "created_at": s.created_at.isoformat(),
    }


def _asset_dict(a: Asset) -> dict:
    return {
        "id": str(a.id), "site_id": str(a.site_id), "name": a.name,
        "project_id": str(a.project_id) if a.project_id else None,
        "product_id": str(a.product_id) if a.product_id else None,
        "parent_asset_id": str(a.parent_asset_id) if a.parent_asset_id else None,
        "floor": a.floor, "room": a.room, "serial_no": a.serial_no,
        "installed_at": a.installed_at.isoformat() if a.installed_at else None,
        "customer_warranty_id": str(a.customer_warranty_id) if a.customer_warranty_id else None,
        "amc_contract_id": str(a.amc_contract_id) if a.amc_contract_id else None,
        "status": a.status, "notes": a.notes, "created_at": a.created_at.isoformat(),
    }


@router.post("/sites")
async def create_site(data: SiteUpsert, db: DB, admin: AdminUser):
    site = Site(**data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return _site_dict(site)


@router.get("/sites")
async def list_sites(
    db: DB, admin: AdminUser,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    total = (await db.execute(select(func.count()).select_from(Site))).scalar() or 0
    rows = (
        await db.execute(select(Site).order_by(Site.created_at.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return {"items": [_site_dict(s) for s in rows], "total": total}


@router.get("/sites/{id}/assets")
async def list_site_assets(id: uuid.UUID, db: DB, admin: AdminUser):
    site = await db.get(Site, id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    rows = (
        await db.execute(select(Asset).where(Asset.site_id == id).order_by(Asset.floor, Asset.room, Asset.name))
    ).scalars().all()
    return {"site": _site_dict(site), "assets": [_asset_dict(a) for a in rows]}


@router.post("/assets")
async def create_asset(data: AssetUpsert, db: DB, admin: AdminUser):
    if await db.get(Site, data.site_id) is None:
        raise HTTPException(status_code=404, detail="Site not found")
    asset = Asset(**data.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _asset_dict(asset)


@router.patch("/assets/{id}")
async def update_asset(id: uuid.UUID, data: AssetUpsert, db: DB, admin: AdminUser):
    asset = await db.get(Asset, id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _asset_dict(asset)


class DesignRevisionCreate(BaseModel):
    title: str
    file_minio_key: str  # from the existing /files/upload-url flow
    site_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    file_kind: str | None = None
    notes: str | None = None


@router.post("/design-revisions")
async def create_design_revision(data: DesignRevisionCreate, db: DB, admin: AdminUser):
    from app.models.content import DesignRevision

    if not data.site_id and not data.project_id:
        raise HTTPException(status_code=400, detail="site_id or project_id required")
    latest = (
        await db.execute(
            select(func.max(DesignRevision.version)).where(
                DesignRevision.site_id == data.site_id,
                DesignRevision.project_id == data.project_id,
                DesignRevision.title == data.title,
            )
        )
    ).scalar()
    revision = DesignRevision(**data.model_dump(), version=(latest or 0) + 1, uploaded_by=admin.id)
    db.add(revision)
    await db.commit()
    await db.refresh(revision)
    return {
        "id": str(revision.id), "title": revision.title, "version": revision.version,
        "file_minio_key": revision.file_minio_key, "file_kind": revision.file_kind,
    }


@router.get("/design-revisions")
async def list_design_revisions(
    db: DB, admin: AdminUser,
    site_id: uuid.UUID | None = None, project_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    from app.models.content import DesignRevision

    query = select(DesignRevision).order_by(DesignRevision.created_at.desc())
    if site_id:
        query = query.where(DesignRevision.site_id == site_id)
    if project_id:
        query = query.where(DesignRevision.project_id == project_id)
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {
        "items": [
            {"id": str(r.id), "title": r.title, "version": r.version,
             "site_id": str(r.site_id) if r.site_id else None,
             "project_id": str(r.project_id) if r.project_id else None,
             "file_minio_key": r.file_minio_key, "file_kind": r.file_kind,
             "notes": r.notes, "created_at": r.created_at.isoformat()}
            for r in rows
        ]
    }


@router.get("/assets")
async def list_assets(
    db: DB, admin: AdminUser,
    site_id: uuid.UUID | None = None, project_id: uuid.UUID | None = None, status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    query = select(Asset).order_by(Asset.created_at.desc())
    count_query = select(func.count()).select_from(Asset)
    for column, value in ((Asset.site_id, site_id), (Asset.project_id, project_id), (Asset.status, status)):
        if value is not None:
            query = query.where(column == value)
            count_query = count_query.where(column == value)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_asset_dict(a) for a in rows], "total": total}

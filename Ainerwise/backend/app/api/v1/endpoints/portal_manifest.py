"""Read-only Portal Manifest API (PF01).

Manifests describe layout, menus, and route allowlists only. They never grant
permissions — backend APIs enforce Membership + Grant separately.
"""
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.core.portal_registry import (
    PhysicalFrontend,
    get_manifest,
    is_valid_portal_key,
    list_manifests,
    resolve_portal_key,
)
from app.schemas.portal_manifest import PortalManifestListResponse, PortalManifestRead

router = APIRouter(prefix="/portal-manifests", tags=["portal-manifests"])


@router.get("", response_model=PortalManifestListResponse)
async def list_portal_manifests(
    physical_frontend: Literal["pc", "h5", "admin"] | None = Query(None),
):
    items = [PortalManifestRead.model_validate(m) for m in list_manifests(physical_frontend=physical_frontend)]
    return PortalManifestListResponse(items=items, total=len(items))


@router.get("/resolve/{portal_key}", response_model=PortalManifestRead)
async def resolve_portal_manifest(portal_key: str):
    """Map legacy NUXT_PUBLIC_PORTAL_MODE aliases to canonical manifests."""
    if not is_valid_portal_key(portal_key):
        raise HTTPException(status_code=400, detail="Invalid portal_key format")
    resolved = resolve_portal_key(portal_key)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Unknown portal")
    manifest = get_manifest(resolved)
    assert manifest is not None
    return PortalManifestRead.model_validate(manifest)


@router.get("/{portal_key}", response_model=PortalManifestRead)
async def get_portal_manifest(portal_key: str):
    if not is_valid_portal_key(portal_key):
        raise HTTPException(status_code=400, detail="Invalid portal_key format")
    manifest = get_manifest(portal_key)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Unknown portal")
    return PortalManifestRead.model_validate(manifest)

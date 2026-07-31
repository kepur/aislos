"""Portal Manifest API schemas (PF01)."""
from typing import Literal

from app.schemas.base import BaseSchema

PhysicalFrontend = Literal["pc", "h5", "admin"]


class PortalManifestRead(BaseSchema):
    portal_key: str
    version: int
    physical_frontend: PhysicalFrontend
    layout: str
    home_route: str
    theme_key: str
    menu_keys: list[str]
    route_allowlist: list[str]
    required_grants: list[str]
    pwa_manifest_key: str | None = None
    offline_policy_key: str | None = None
    legacy_portal_mode: str | None = None
    migration_note: str | None = None
    display_name: str


class PortalManifestListResponse(BaseSchema):
    items: list[PortalManifestRead]
    total: int

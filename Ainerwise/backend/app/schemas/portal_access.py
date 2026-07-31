import uuid
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.portal_manifest import PortalManifestRead


class PortalSummary(BaseSchema):
    portal_key: str
    display_name: str
    physical_frontend: str
    home_route: str
    legacy_portal_mode: str | None = None


class UserPortalsResponse(BaseSchema):
    items: list[PortalSummary]
    memberships: list["MembershipRead"]


class MembershipRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    membership_type: str
    status: str
    company_id: uuid.UUID | None = None


class PortalSwitchRequest(BaseSchema):
    portal_key: str
    workspace_id: uuid.UUID | None = None


class PortalSwitchResponse(BaseSchema):
    portal_key: str
    workspace_id: uuid.UUID | None = None
    manifest: PortalManifestRead

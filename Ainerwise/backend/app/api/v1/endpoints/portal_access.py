"""PF02: Portal membership and switch API."""
from fastapi import APIRouter, HTTPException, Request

from app.api.deps import CurrentUser, DB
from app.core.portal_registry import get_manifest
from app.schemas.portal_access import (
    MembershipRead,
    PortalSwitchRequest,
    PortalSwitchResponse,
    PortalSummary,
    UserPortalsResponse,
)
from app.schemas.portal_manifest import PortalManifestRead
from app.services.portal_access import (
    list_memberships,
    list_user_portals,
    resolve_workspace_scope,
    switch_portal_audit,
)

router = APIRouter(prefix="/auth", tags=["portal-access"])


@router.get("/me/portals", response_model=UserPortalsResponse)
async def get_my_portals(db: DB, user: CurrentUser):
    portals = await list_user_portals(db, user.id)
    memberships = await list_memberships(db, user.id)
    return UserPortalsResponse(
        items=[PortalSummary.model_validate(p) for p in portals],
        memberships=[MembershipRead.model_validate(m) for m in memberships],
    )


@router.post("/portal-switch", response_model=PortalSwitchResponse)
async def portal_switch(data: PortalSwitchRequest, request: Request, db: DB, user: CurrentUser):
    manifest = get_manifest(data.portal_key)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Unknown portal")
    try:
        workspace_id = await resolve_workspace_scope(
            db,
            user_id=user.id,
            requested_workspace_id=data.workspace_id,
        )
        await switch_portal_audit(
            db,
            user_id=user.id,
            portal_key=data.portal_key,
            workspace_id=workspace_id,
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
    except PermissionError as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return PortalSwitchResponse(
        portal_key=manifest["portal_key"],
        workspace_id=workspace_id,
        manifest=PortalManifestRead.model_validate(manifest),
    )

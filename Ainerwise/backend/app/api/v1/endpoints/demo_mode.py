from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import AdminUser, DB
from app.core.config import settings
from app.services.demo_bootstrap import bootstrap_demo_environment
from app.services.demo_mode import SERVICE_TEST_ACCOUNTS, is_demo_mode_enabled, set_demo_mode_enabled

router = APIRouter(prefix="/demo-mode", tags=["demo-mode"])


class DemoModeUpdate(BaseModel):
    enabled: bool


async def _account_matrix(db) -> list[dict]:
    from app.models.portal_access import PortalGrant
    from app.models.showroom import KioskDevice
    from app.models.user import User
    from app.services.portal_access import list_memberships, list_user_portals

    rows: list[dict] = []
    for account in SERVICE_TEST_ACCOUNTS:
        row = {
            **account,
            "demo_only": bool(account.get("demo_only")),
            "exists": False,
            "is_active": None,
            "portal_keys": [],
            "membership_count": 0,
            "grant_count": 0,
            "login_blocked_when_demo_off": bool(account.get("demo_only")),
        }
        email = account.get("email")
        if email:
            user = (
                await db.execute(select(User).where(User.email == str(email)))
            ).scalar_one_or_none()
            if user:
                memberships = await list_memberships(db, user.id)
                grants = (
                    (
                        await db.execute(
                            select(PortalGrant).where(
                                PortalGrant.user_id == user.id,
                                PortalGrant.granted.is_(True),
                                PortalGrant.revoked_at.is_(None),
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                portals = await list_user_portals(db, user.id)
                row.update(
                    {
                        "id": str(user.id),
                        "exists": True,
                        "is_active": bool(user.is_active),
                        "actual_role": user.role,
                        "full_name": user.full_name,
                        "portal_keys": [item["portal_key"] for item in portals],
                        "membership_count": len(memberships),
                        "grant_count": len(grants),
                    }
                )
        elif account.get("auth_type") == "device_token":
            active_devices = (
                (
                    await db.execute(
                        select(KioskDevice.id).where(KioskDevice.status == "active")
                    )
                )
                .scalars()
                .all()
            )
            row.update(
                {
                    "exists": bool(active_devices),
                    "is_active": bool(active_devices),
                    "device_count": len(active_devices),
                }
            )
        rows.append(row)
    return rows


async def _payload(db, *, include_admin: bool = False) -> dict:
    enabled = await is_demo_mode_enabled(db)
    data = {
        "enabled": enabled,
        "urls": {
            "pc": "http://localhost:4099",
            "h5": "http://localhost:4098",
            "admin": "http://localhost:4097",
            "cebu_pc": "http://cebu.localhost/cebu",
            "api_docs": "http://localhost:8000/docs",
        },
    }
    if enabled or include_admin:
        data["buyer"] = {
            "label": "Demo Customer",
            "email": settings.DEMO_BUYER_EMAIL,
            "password": settings.DEMO_BUYER_PASSWORD,
            "description": "Explore customer portal, AI assessment, leads, quotes, tickets, and project previews.",
        }
    if include_admin:
        data["admin"] = {
            "label": "Demo Admin",
            "email": settings.DEMO_ADMIN_EMAIL,
            "password": settings.DEMO_ADMIN_PASSWORD,
            "description": "Explore admin CRM, leads, products, solutions, proposals, and operations views.",
        }
        accounts = await _account_matrix(db)
        data["service_accounts"] = accounts
        data["account_matrix"] = accounts
    return data


@router.get("")
async def get_demo_mode(db: DB):
    return await _payload(db, include_admin=False)


@router.get("/admin")
async def get_admin_demo_mode(db: DB, _: AdminUser):
    return await _payload(db, include_admin=True)


@router.patch("")
async def update_demo_mode(data: DemoModeUpdate, db: DB, _: AdminUser):
    await set_demo_mode_enabled(db, data.enabled)
    return await _payload(db, include_admin=True)


@router.post("/bootstrap")
async def bootstrap_demo_data(db: DB, _: AdminUser):
    """Seed demo buyer, portal test users, commerce sample, and enable demo mode."""
    results = await bootstrap_demo_environment(db)
    payload = await _payload(db, include_admin=True)
    payload["bootstrap"] = results
    return payload

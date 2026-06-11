from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import AdminUser
from app.core.config import settings

router = APIRouter(prefix="/demo-mode", tags=["demo-mode"])

_demo_mode_enabled = settings.DEMO_MODE_ENABLED


class DemoModeUpdate(BaseModel):
    enabled: bool


def _payload(include_admin: bool = False) -> dict:
    data = {
        "enabled": _demo_mode_enabled,
        "buyer": {
            "label": "Demo Customer",
            "email": settings.DEMO_BUYER_EMAIL,
            "password": settings.DEMO_BUYER_PASSWORD,
            "description": "Explore customer portal, AI assessment, leads, quotes, tickets, and project previews.",
        },
    }
    if include_admin:
        data["admin"] = {
            "label": "Demo Admin",
            "email": settings.DEMO_ADMIN_EMAIL,
            "password": settings.DEMO_ADMIN_PASSWORD,
            "description": "Explore admin CRM, leads, products, solutions, proposals, and operations views.",
        }
    return data


@router.get("")
async def get_demo_mode():
    return _payload(include_admin=True)


@router.get("/admin")
async def get_admin_demo_mode(_: AdminUser):
    return _payload(include_admin=True)


@router.patch("")
async def update_demo_mode(data: DemoModeUpdate, _: AdminUser):
    global _demo_mode_enabled
    _demo_mode_enabled = data.enabled
    return _payload(include_admin=True)

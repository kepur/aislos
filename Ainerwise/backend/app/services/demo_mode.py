"""Demo mode toggle (DB-persisted) and demo account registry."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.integrations import get_setting, upsert_config

PLATFORM_CATEGORY = "platform"

SERVICE_TEST_ACCOUNTS: list[dict] = [
    {
        "key": "super_admin",
        "auth_type": "password",
        "role": "super_admin",
        "label": "Super Admin",
        "email": settings.DEMO_ADMIN_EMAIL,
        "password": settings.DEMO_ADMIN_PASSWORD,
        "portals": ["Admin :4097", "Store Admin :4095", "Marketing :4094", "Agent :4093"],
        "notes": "Full back-office; always allowed to log in.",
    },
    {
        "key": "demo_customer",
        "auth_type": "password",
        "role": "buyer",
        "label": "Demo Customer",
        "email": settings.DEMO_BUYER_EMAIL,
        "password": settings.DEMO_BUYER_PASSWORD,
        "portals": ["PC :4099", "H5 Customer :4098", "Cebu Buyer"],
        "notes": "Leads, projects, procurement, Cebu buyer; blocked when demo mode off.",
        "demo_only": True,
    },
    {
        "key": "store_admin",
        "auth_type": "password",
        "role": "admin",
        "label": "Store Admin Operator",
        "email": "store_admin@example.com",
        "password": "storeadmin123",
        "portals": ["Store Admin :4095/store-orders", "Admin :4097"],
        "notes": "Operational test account for Store Admin and commerce workbenches.",
    },
    {
        "key": "customer_owner",
        "auth_type": "password",
        "role": "customer_owner",
        "label": "Customer Owner",
        "email": "customer_owner@example.com",
        "password": "customer123",
        "portals": ["H5 Customer"],
    },
    {
        "key": "partner_owner",
        "auth_type": "password",
        "role": "partner_company_owner",
        "label": "Partner Company",
        "email": "partner_owner@example.com",
        "password": "partner123",
        "portals": ["H5 Partner /partner"],
    },
    {
        "key": "field_installer",
        "auth_type": "password",
        "role": "field_worker",
        "label": "Field Installer",
        "email": "installer@example.com",
        "password": "worker123",
        "portals": ["H5 Field /field/today"],
    },
    {
        "key": "supplier",
        "auth_type": "password",
        "role": "supplier",
        "label": "Supplier / Vendor",
        "email": "supplier@example.com",
        "password": "supplier123",
        "portals": ["H5 Supplier", "Commerce orders"],
    },
    {
        "key": "demo_supplier",
        "auth_type": "password",
        "role": "demo_supplier",
        "label": "Demo Supplier (Cebu)",
        "email": "demo-supplier@ainerwise.com",
        "password": "supplier123",
        "portals": ["Commerce / Cebu intents"],
        "demo_only": True,
    },
    {
        "key": "marketing_operator",
        "auth_type": "password",
        "role": "marketing_operator",
        "label": "Marketing Operator",
        "email": "marketing_operator@example.com",
        "password": "marketing123",
        "portals": ["Marketing :4094", "Marketing H5"],
        "notes": "Scoped marketing operator test account.",
    },
    {
        "key": "agent_operator",
        "auth_type": "password",
        "role": "admin",
        "label": "Agent Console Operator",
        "email": "agent_operator@example.com",
        "password": "agent123456",
        "portals": ["Agent Console :4093/agents"],
        "notes": "Admin-role test account for AI Supervisor / Agent Console.",
    },
    {
        "key": "project_manager",
        "auth_type": "password",
        "role": "project_manager",
        "label": "Project Manager",
        "email": "pm@example.com",
        "password": "pm123456",
        "portals": ["Admin Field Ops"],
    },
    {
        "key": "kiosk_device",
        "auth_type": "device_token",
        "role": "kiosk_device",
        "label": "Kiosk Device",
        "email": None,
        "password": None,
        "portals": ["Kiosk :4090/kiosk"],
        "notes": "Uses a revocable device token issued in Admin -> Showroom -> Devices; no human password login.",
    },
]

# Logins blocked when demo mode is off (Cebu parity: demo personas only).
DEMO_RESTRICTED_EMAILS = frozenset(
    str(account["email"]).lower()
    for account in SERVICE_TEST_ACCOUNTS
    if account.get("demo_only") and account.get("email")
)


async def is_demo_mode_enabled(db: AsyncSession) -> bool:
    row = await get_setting(db, PLATFORM_CATEGORY)
    if row and row.config_json and "demo_mode_enabled" in row.config_json:
        return bool(row.config_json["demo_mode_enabled"])
    return settings.DEMO_MODE_ENABLED


async def set_demo_mode_enabled(db: AsyncSession, enabled: bool) -> bool:
    await upsert_config(
        db,
        PLATFORM_CATEGORY,
        config={"demo_mode_enabled": enabled},
        is_enabled=enabled,
    )
    return enabled


def is_demo_restricted_email(email: str) -> bool:
    return email.strip().lower() in DEMO_RESTRICTED_EMAILS

"""Idempotent demo / test account and sample data bootstrap."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import Company, User
from app.services.demo_mode import set_demo_mode_enabled
from app.services.portal_access import (
    ensure_grant,
    ensure_membership,
    get_default_workspace,
    sync_role_portal_access,
)

PORTAL_IDENTITIES = [
    {
        "email": "store_admin@example.com",
        "password": "storeadmin123",
        "role": "admin",
        "membership_type": "admin_operator",
        "company_type": "official",
        "grants": [],
    },
    {
        "email": "customer_owner@example.com",
        "password": "customer123",
        "role": "buyer",
        "membership_type": "customer_owner",
        "company_type": "buyer",
        "grants": ["portal.h5.customer"],
    },
    {
        "email": "partner_owner@example.com",
        "password": "partner123",
        "role": "service_partner",
        "membership_type": "partner_company_owner",
        "company_type": "service_partner",
        "grants": ["partner.rfq.read", "partner.work_package.read"],
    },
    {
        "email": "installer@example.com",
        "password": "worker123",
        "role": "partner_worker",
        "membership_type": "field_worker",
        "company_type": "service_partner",
        "grants": ["field_task.read_assigned"],
    },
    {
        "email": "supplier@example.com",
        "password": "supplier123",
        "role": "vendor",
        "membership_type": "supplier_operator",
        "company_type": "supplier",
        "grants": ["supplier.rfq.read", "supplier.catalog.read"],
    },
    {
        "email": "marketing_operator@example.com",
        "password": "marketing123",
        "role": "marketing_operator",
        "membership_type": "marketing_operator",
        "company_type": "official",
        "grants": [],
    },
    {
        "email": "agent_operator@example.com",
        "password": "agent123456",
        "role": "admin",
        "membership_type": "admin_operator",
        "company_type": "official",
        "grants": [],
    },
    {
        "email": "pm@example.com",
        "password": "pm123456",
        "role": "project_manager",
        "membership_type": "project_manager",
        "company_type": "service_partner",
        "grants": ["admin.field_ops.read", "admin.project.read"],
    },
]

DEMO_SUPPLIER_EMAIL = "demo-supplier@ainerwise.com"
DEMO_SUPPLIER_PASSWORD = "supplier123"


async def ensure_superadmin(db: AsyncSession) -> bool:
    existing = await db.execute(select(User).where(User.email == "admin@ainerwise.com"))
    user = existing.scalar_one_or_none()
    if user:
        user.is_active = True
        user.role = "super_admin"
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
        )
        return False
    company = Company(name="AinerWise Official", type="official", country="Serbia", city="Belgrade")
    db.add(company)
    await db.flush()
    user = User(
        email="admin@ainerwise.com",
        password_hash=hash_password("admin123456"),
        full_name="AinerWise Admin",
        role="super_admin",
        language="en",
        country="Serbia",
        company_id=company.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await sync_role_portal_access(
        db,
        user_id=user.id,
        role=user.role,
        company_id=user.company_id,
    )
    return True


async def ensure_portal_identities(db: AsyncSession) -> int:
    ws = await get_default_workspace(db)
    if ws is None:
        return 0
    created = 0
    for spec in PORTAL_IDENTITIES:
        email = str(spec["email"])
        role = str(spec["role"])
        membership_type = str(spec["membership_type"])
        grants = list(spec.get("grants") or [])
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            company = Company(
                name=str(spec.get("label") or email.split("@")[0].replace("_", " ").title()),
                type=str(spec.get("company_type") or "buyer"),
                verification_status="verified",
            )
            db.add(company)
            await db.flush()
            user = User(
                email=email,
                password_hash=hash_password(str(spec["password"])),
                full_name=email.split("@")[0].replace("_", " ").title(),
                role=role,
                company_id=company.id,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            created += 1
        else:
            user.role = role
            user.is_active = True
        await ensure_membership(
            db,
            user_id=user.id,
            membership_type=membership_type,
            workspace_id=ws.id,
            company_id=user.company_id,
        )
        for grant_key in grants:
            await ensure_grant(db, user_id=user.id, grant_key=grant_key, workspace_id=ws.id)
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
            workspace_id=ws.id,
        )
    return created


async def ensure_demo_supplier(db: AsyncSession) -> bool:
    user = (await db.execute(select(User).where(User.email == DEMO_SUPPLIER_EMAIL))).scalar_one_or_none()
    if user:
        user.role = "vendor"
        user.is_active = True
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
        )
        return False
    company = Company(name="Cebu Demo Supplier", type="supplier", country="Philippines", verification_status="verified")
    db.add(company)
    await db.flush()
    user = User(
        email=DEMO_SUPPLIER_EMAIL,
        password_hash=hash_password(DEMO_SUPPLIER_PASSWORD),
        full_name="Cebu Demo Supplier",
        role="vendor",
        company_id=company.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    ws = await get_default_workspace(db)
    if ws:
        await ensure_membership(
            db,
            user_id=user.id,
            membership_type="supplier_operator",
            workspace_id=ws.id,
            company_id=company.id,
        )
        await ensure_grant(db, user_id=user.id, grant_key="supplier.catalog.read", workspace_id=ws.id)
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=user.company_id,
            workspace_id=ws.id,
        )
    return True


async def ensure_commerce_demo_listing(db: AsyncSession) -> bool:
    from app.models.commerce import SupplierListing, TradeCategorySchema

    supplier = (
        await db.execute(select(User).where(User.email == DEMO_SUPPLIER_EMAIL))
    ).scalar_one_or_none()
    if not supplier or not supplier.company_id:
        return False
    slug = "cebu-demo-lighting"
    cat = (
        await db.execute(select(TradeCategorySchema).where(TradeCategorySchema.slug == slug))
    ).scalar_one_or_none()
    if cat is None:
        cat = TradeCategorySchema(slug=slug, name="Cebu Demo Lighting", schema_json={"fields": []})
        db.add(cat)
        await db.flush()
    existing = (
        await db.execute(
            select(SupplierListing).where(
                SupplierListing.company_id == supplier.company_id,
                SupplierListing.title == "Cebu LED Starter Kit",
            )
        )
    ).scalar_one_or_none()
    if existing:
        return False
    db.add(
        SupplierListing(
            company_id=supplier.company_id,
            category_schema_id=cat.id,
            title="Cebu LED Starter Kit",
            price_minor=89000,
            currency="USD",
            status="active",
        )
    )
    await db.flush()
    return True


async def bootstrap_demo_environment(db: AsyncSession) -> dict:
    """Run all idempotent demo seeds; enable demo mode in DB."""
    results: dict[str, bool | int] = {}
    results["superadmin_created"] = await ensure_superadmin(db)
    results["portal_identities_created"] = await ensure_portal_identities(db)
    results["demo_supplier_created"] = await ensure_demo_supplier(db)
    results["commerce_listing_created"] = await ensure_commerce_demo_listing(db)
    await db.commit()

    # Demo buyer + sample projects (separate session)
    from scripts.create_demo_buyer import main as seed_demo_buyer  # noqa: PLC0415

    await seed_demo_buyer()

    await set_demo_mode_enabled(db, True)
    return results

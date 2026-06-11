"""Ainerwise Store, Agent Marketplace and Developer Portal API."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from slugify import slugify
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.models.agent import AGENT_GRANT_SCOPES
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem
from app.models.product import Product
from app.schemas.ecosystem import (
    AgentInstallationCreate,
    MarketplaceListingCreate,
    MarketplaceReview,
    StoreOrderCreate,
    StoreOrderStatusUpdate,
)
from app.schemas.product import ProductRead
from app.services.audit import log_action
from app.services.ecosystem import (
    PUBLIC_PRODUCT_STATUSES,
    approve_marketplace_listing,
    create_marketplace_listing,
    create_store_order,
    install_marketplace_agent,
    installation_dict,
    listing_dict,
    resubmit_marketplace_listing,
    store_order_dict,
    update_store_order_status,
)

router = APIRouter(tags=["ecosystem portals"])


async def _order_with_items(db: DB, order: StoreOrder) -> dict:
    items = (
        await db.execute(
            select(StoreOrderItem).where(StoreOrderItem.order_id == order.id).order_by(StoreOrderItem.created_at)
        )
    ).scalars().all()
    return store_order_dict(order, list(items))


@router.get("/store/catalog")
async def store_catalog(db: DB, search: str | None = None):
    query = select(Product).where(
        Product.status.in_(PUBLIC_PRODUCT_STATUSES),
        Product.list_price.is_not(None),
    )
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    products = (await db.execute(query.order_by(Product.name))).scalars().all()
    return {
        "items": [ProductRead.model_validate(product) for product in products],
        "total": len(products),
        "checkout_mode": "request_for_quote",
        "payment_boundary": "The Store never charges a card. Submitted requests are reviewed before a formal quote.",
    }


@router.post("/store/orders", status_code=status.HTTP_201_CREATED)
async def submit_store_order(data: StoreOrderCreate, db: DB, current_user: CurrentUser):
    order, items = await create_store_order(db, user=current_user, data=data)
    await log_action(
        db,
        actor_user_id=current_user.id,
        action="store_order_requested",
        entity_type="store_order",
        entity_id=order.id,
        after={"status": order.status, "subtotal": float(order.subtotal), "currency": order.currency},
    )
    return store_order_dict(order, items)


@router.get("/store/orders/my")
async def my_store_orders(db: DB, current_user: CurrentUser):
    orders = (
        await db.execute(
            select(StoreOrder).where(StoreOrder.user_id == current_user.id).order_by(StoreOrder.created_at.desc())
        )
    ).scalars().all()
    return {"items": [await _order_with_items(db, order) for order in orders]}


@router.get("/admin/store/orders")
async def admin_store_orders(db: DB, admin: AdminUser, order_status: str | None = Query(default=None, alias="status")):
    query = select(StoreOrder)
    if order_status:
        query = query.where(StoreOrder.status == order_status)
    orders = (await db.execute(query.order_by(StoreOrder.created_at.desc()))).scalars().all()
    return {"items": [await _order_with_items(db, order) for order in orders]}


@router.patch("/admin/store/orders/{order_id}/status")
async def admin_update_store_order(
    order_id: uuid.UUID, data: StoreOrderStatusUpdate, db: DB, admin: AdminUser
):
    order = await db.get(StoreOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Store request not found")
    before = order.status
    order = await update_store_order_status(db, order=order, new_status=data.status, reviewer_id=admin.id)
    await log_action(
        db,
        actor_user_id=admin.id,
        action="store_order_status_change",
        entity_type="store_order",
        entity_id=order.id,
        before={"status": before},
        after={"status": order.status},
    )
    return await _order_with_items(db, order)


@router.get("/marketplace/listings")
async def public_marketplace_listings(db: DB):
    listings = (
        await db.execute(
            select(MarketplaceListing)
            .where(MarketplaceListing.status == "approved")
            .order_by(MarketplaceListing.name)
        )
    ).scalars().all()
    return {"items": [listing_dict(listing) for listing in listings], "total": len(listings)}


@router.get("/marketplace/listings/{listing_slug}")
async def public_marketplace_listing(listing_slug: str, db: DB):
    listing = (
        await db.execute(
            select(MarketplaceListing).where(
                MarketplaceListing.slug == listing_slug,
                MarketplaceListing.status == "approved",
            )
        )
    ).scalar_one_or_none()
    if listing is None:
        raise HTTPException(status_code=404, detail="Marketplace Agent not found")
    return listing_dict(listing)


@router.post("/marketplace/listings/{listing_id}/install", status_code=status.HTTP_201_CREATED)
async def install_listing(
    listing_id: uuid.UUID, data: AgentInstallationCreate, db: DB, current_user: CurrentUser
):
    listing = await db.get(MarketplaceListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Marketplace Agent not found")
    installation = await install_marketplace_agent(
        db, listing=listing, user=current_user, config_json=data.config_json
    )
    await log_action(
        db,
        actor_user_id=current_user.id,
        action="marketplace_agent_installed",
        entity_type="agent_installation",
        entity_id=installation.id,
        after={"listing_id": str(listing.id), "agent_id": str(installation.agent_id)},
    )
    return installation_dict(installation, listing)


@router.get("/marketplace/installations/my")
async def my_installations(db: DB, current_user: CurrentUser):
    rows = (
        await db.execute(
            select(AgentInstallation, MarketplaceListing)
            .join(MarketplaceListing, MarketplaceListing.id == AgentInstallation.listing_id)
            .where(AgentInstallation.installed_by == current_user.id)
            .order_by(AgentInstallation.installed_at.desc())
        )
    ).all()
    return {"items": [installation_dict(installation, listing) for installation, listing in rows]}


@router.post("/marketplace/installations/{installation_id}/uninstall")
async def uninstall_agent(installation_id: uuid.UUID, db: DB, current_user: CurrentUser):
    installation = await db.get(AgentInstallation, installation_id)
    if installation is None or installation.installed_by != current_user.id:
        raise HTTPException(status_code=404, detail="Installation not found")
    installation.status = "uninstalled"
    installation.uninstalled_at = datetime.now(timezone.utc)
    db.add(installation)
    await db.commit()
    await db.refresh(installation)
    return installation_dict(installation)


@router.get("/developer/sdk/manifest")
async def developer_sdk_manifest():
    return {
        "manifest_version": "1.0",
        "required": ["name", "version", "workflows"],
        "valid_scopes": list(AGENT_GRANT_SCOPES),
        "review_flow": ["submitted", "approved_or_rejected", "installable"],
        "guardrails": {
            "human_review_required": True,
            "third_party_default_status": "paused",
            "third_party_default_grants": "all_denied",
            "payment_access_never_automatic": True,
        },
        "example": {
            "name": "KNX Design Agent",
            "slug": "knx-design-agent",
            "version": "1.0.0",
            "workflows": ["knx_design_review"],
            "requested_scopes": ["project_data"],
            "price_monthly": 299,
            "currency": "EUR",
        },
    }


@router.post("/developer/listings", status_code=status.HTTP_201_CREATED)
async def submit_marketplace_listing(
    data: MarketplaceListingCreate, db: DB, current_user: CurrentUser
):
    listing_slug = slugify(data.slug or data.name)
    if not listing_slug:
        raise HTTPException(status_code=400, detail="A valid Marketplace slug is required")
    listing = await create_marketplace_listing(db, user=current_user, data=data, slug=listing_slug)
    await log_action(
        db,
        actor_user_id=current_user.id,
        action="marketplace_listing_submitted",
        entity_type="marketplace_listing",
        entity_id=listing.id,
        after={"slug": listing.slug, "requested_scopes": listing.requested_scopes_json},
    )
    return listing_dict(listing, include_review=True)


@router.put("/developer/listings/{listing_id}")
async def edit_marketplace_listing(
    listing_id: uuid.UUID, data: MarketplaceListingCreate, db: DB, current_user: CurrentUser
):
    listing = await db.get(MarketplaceListing, listing_id)
    if listing is None or listing.developer_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Developer listing not found")
    listing = await resubmit_marketplace_listing(db, listing=listing, data=data)
    return listing_dict(listing, include_review=True)


@router.get("/developer/listings/my")
async def my_developer_listings(db: DB, current_user: CurrentUser):
    listings = (
        await db.execute(
            select(MarketplaceListing)
            .where(MarketplaceListing.developer_user_id == current_user.id)
            .order_by(MarketplaceListing.created_at.desc())
        )
    ).scalars().all()
    return {"items": [listing_dict(listing, include_review=True) for listing in listings]}


@router.get("/admin/marketplace/listings")
async def admin_marketplace_listings(db: DB, admin: AdminUser):
    listings = (
        await db.execute(select(MarketplaceListing).order_by(MarketplaceListing.created_at.desc()))
    ).scalars().all()
    return {"items": [listing_dict(listing, include_review=True) for listing in listings]}


@router.post("/admin/marketplace/listings/{listing_id}/approve")
async def admin_approve_listing(
    listing_id: uuid.UUID, data: MarketplaceReview, db: DB, admin: AdminUser
):
    listing = await db.get(MarketplaceListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Marketplace listing not found")
    agent = await approve_marketplace_listing(db, listing=listing, reviewer_id=admin.id, notes=data.notes)
    await log_action(
        db,
        actor_user_id=admin.id,
        action="marketplace_listing_approved",
        entity_type="marketplace_listing",
        entity_id=listing.id,
        after={"agent_id": str(agent.id), "agent_status": agent.status, "grants": "all_denied_for_third_party"},
    )
    return listing_dict(listing, include_review=True)


@router.post("/admin/marketplace/listings/{listing_id}/reject")
async def admin_reject_listing(
    listing_id: uuid.UUID, data: MarketplaceReview, db: DB, admin: AdminUser
):
    listing = await db.get(MarketplaceListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Marketplace listing not found")
    if listing.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted listings can be rejected")
    listing.status = "rejected"
    listing.review_notes = data.notes
    listing.reviewed_by = admin.id
    listing.reviewed_at = datetime.now(timezone.utc)
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    await log_action(
        db,
        actor_user_id=admin.id,
        action="marketplace_listing_rejected",
        entity_type="marketplace_listing",
        entity_id=listing.id,
        after={"notes": data.notes},
    )
    return listing_dict(listing, include_review=True)

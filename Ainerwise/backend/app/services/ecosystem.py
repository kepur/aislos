"""Business rules for Store requests and the governed Agent Marketplace."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AGENT_GRANT_SCOPES, Agent, AgentGrant
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.ecosystem import MarketplaceListingCreate, StoreOrderCreate

PUBLIC_PRODUCT_STATUSES = ("approved", "active", "published")
STORE_ORDER_TRANSITIONS = {
    "requested": {"reviewing", "cancelled"},
    "reviewing": {"quoted", "cancelled"},
    "quoted": {"confirmed", "cancelled"},
    "confirmed": set(),
    "cancelled": set(),
}


def store_order_dict(order: StoreOrder, items: list[StoreOrderItem]) -> dict:
    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "company_id": str(order.company_id) if order.company_id else None,
        "status": order.status,
        "currency": order.currency,
        "subtotal": float(order.subtotal),
        "notes": order.notes,
        "delivery_json": order.delivery_json,
        "reviewed_by": str(order.reviewed_by) if order.reviewed_by else None,
        "reviewed_at": order.reviewed_at.isoformat() if order.reviewed_at else None,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "line_total": float(item.line_total),
            }
            for item in items
        ],
        "payment_boundary": "No payment was taken. AinerWise will review and issue a formal quote.",
    }


async def create_store_order(
    db: AsyncSession, *, user: User, data: StoreOrderCreate
) -> tuple[StoreOrder, list[StoreOrderItem]]:
    product_ids = {item.product_id for item in data.items}
    products = (
        await db.execute(
            select(Product).where(
                Product.id.in_(product_ids),
                Product.status.in_(PUBLIC_PRODUCT_STATUSES),
                Product.list_price.is_not(None),
            )
        )
    ).scalars().all()
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(product_ids):
        raise HTTPException(status_code=400, detail="One or more products are not available for Store requests")

    currencies = {product.currency for product in products}
    if len(currencies) != 1:
        raise HTTPException(status_code=400, detail="All Store request items must use the same currency")
    currency = currencies.pop()
    subtotal = sum(
        Decimal(str(products_by_id[item.product_id].list_price)) * item.quantity
        for item in data.items
    )
    order = StoreOrder(
        user_id=user.id,
        company_id=user.company_id,
        status="requested",
        currency=currency,
        subtotal=subtotal,
        notes=data.notes,
        delivery_json=data.delivery_json,
    )
    db.add(order)
    await db.flush()
    order_items = []
    for requested in data.items:
        product = products_by_id[requested.product_id]
        unit_price = Decimal(str(product.list_price))
        item = StoreOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.public_name or product.name,
            quantity=requested.quantity,
            unit_price=unit_price,
            line_total=unit_price * requested.quantity,
        )
        db.add(item)
        order_items.append(item)
    await db.commit()
    await db.refresh(order)
    for item in order_items:
        await db.refresh(item)
    return order, order_items


async def update_store_order_status(
    db: AsyncSession, *, order: StoreOrder, new_status: str, reviewer_id: uuid.UUID
) -> StoreOrder:
    allowed = STORE_ORDER_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move Store request from {order.status} to {new_status}",
        )
    order.status = new_status
    order.reviewed_by = reviewer_id
    order.reviewed_at = datetime.now(timezone.utc)
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


def listing_dict(listing: MarketplaceListing, *, include_review: bool = False) -> dict:
    data = {
        "id": str(listing.id),
        "agent_id": str(listing.agent_id) if listing.agent_id else None,
        "slug": listing.slug,
        "name": listing.name,
        "role_title": listing.role_title,
        "description": listing.description,
        "version": listing.version,
        "workflows": listing.workflows_json or [],
        "requested_scopes": listing.requested_scopes_json or [],
        "price_monthly": float(listing.price_monthly) if listing.price_monthly is not None else None,
        "currency": listing.currency,
        "status": listing.status,
        "created_at": listing.created_at.isoformat(),
    }
    if include_review:
        data.update(
            {
                "developer_user_id": str(listing.developer_user_id) if listing.developer_user_id else None,
                "developer_company_id": str(listing.developer_company_id) if listing.developer_company_id else None,
                "review_notes": listing.review_notes,
                "reviewed_by": str(listing.reviewed_by) if listing.reviewed_by else None,
                "reviewed_at": listing.reviewed_at.isoformat() if listing.reviewed_at else None,
            }
        )
    return data


def installation_dict(installation: AgentInstallation, listing: MarketplaceListing | None = None) -> dict:
    return {
        "id": str(installation.id),
        "listing_id": str(installation.listing_id),
        "agent_id": str(installation.agent_id),
        "name": listing.name if listing else None,
        "slug": listing.slug if listing else None,
        "status": installation.status,
        "config_json": installation.config_json,
        "installed_at": installation.installed_at.isoformat(),
        "uninstalled_at": installation.uninstalled_at.isoformat() if installation.uninstalled_at else None,
        "permission_boundary": "Installation does not grant product, customer, project, quote, email, ads, payment or partner access.",
    }


def _validate_requested_scopes(scopes: list[str]) -> None:
    unknown = set(scopes) - set(AGENT_GRANT_SCOPES)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown requested scopes: {sorted(unknown)}")


async def create_marketplace_listing(
    db: AsyncSession, *, user: User, data: MarketplaceListingCreate, slug: str
) -> MarketplaceListing:
    _validate_requested_scopes(data.requested_scopes)
    existing = (
        await db.execute(select(MarketplaceListing).where(MarketplaceListing.slug == slug))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Marketplace slug already exists")
    listing = MarketplaceListing(
        developer_user_id=user.id,
        developer_company_id=user.company_id,
        slug=slug,
        name=data.name,
        role_title=data.role_title,
        description=data.description,
        version=data.version,
        workflows_json=data.workflows,
        requested_scopes_json=data.requested_scopes,
        price_monthly=data.price_monthly,
        currency=data.currency.upper(),
        status="submitted",
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


async def resubmit_marketplace_listing(
    db: AsyncSession, *, listing: MarketplaceListing, data: MarketplaceListingCreate
) -> MarketplaceListing:
    if listing.status not in {"submitted", "rejected"}:
        raise HTTPException(status_code=400, detail="Only submitted or rejected listings can be edited")
    _validate_requested_scopes(data.requested_scopes)
    for attr, value in {
        "name": data.name,
        "role_title": data.role_title,
        "description": data.description,
        "version": data.version,
        "workflows_json": data.workflows,
        "requested_scopes_json": data.requested_scopes,
        "price_monthly": data.price_monthly,
        "currency": data.currency.upper(),
    }.items():
        setattr(listing, attr, value)
    listing.status = "submitted"
    listing.review_notes = None
    listing.reviewed_by = None
    listing.reviewed_at = None
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


async def approve_marketplace_listing(
    db: AsyncSession, *, listing: MarketplaceListing, reviewer_id: uuid.UUID, notes: str | None
) -> Agent:
    if listing.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted listings can be approved")
    agent = await db.get(Agent, listing.agent_id) if listing.agent_id else None
    if agent is None:
        conflict = (await db.execute(select(Agent).where(Agent.slug == listing.slug))).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=409, detail="Agent slug already exists")
        agent = Agent(
            slug=listing.slug,
            name=listing.name,
            role_title=listing.role_title,
            description=listing.description,
            vendor="third_party",
            workflows_json=listing.workflows_json or [],
            config_json={"marketplace_listing_id": str(listing.id)},
            price_monthly=listing.price_monthly,
            currency=listing.currency,
            status="paused",
        )
        db.add(agent)
        await db.flush()
        for scope in AGENT_GRANT_SCOPES:
            db.add(AgentGrant(agent_id=agent.id, scope=scope, granted=False))
    listing.agent_id = agent.id
    listing.status = "approved"
    listing.review_notes = notes
    listing.reviewed_by = reviewer_id
    listing.reviewed_at = datetime.now(timezone.utc)
    db.add(listing)
    await db.commit()
    await db.refresh(agent)
    return agent


async def install_marketplace_agent(
    db: AsyncSession, *, listing: MarketplaceListing, user: User, config_json: dict | None
) -> AgentInstallation:
    if listing.status != "approved" or not listing.agent_id:
        raise HTTPException(status_code=400, detail="Only approved Marketplace Agents can be installed")
    installation = (
        await db.execute(
            select(AgentInstallation).where(
                AgentInstallation.listing_id == listing.id,
                AgentInstallation.installed_by == user.id,
            )
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if installation is None:
        installation = AgentInstallation(
            listing_id=listing.id,
            agent_id=listing.agent_id,
            installed_by=user.id,
            company_id=user.company_id,
            status="installed",
            config_json=config_json,
            installed_at=now,
        )
    else:
        installation.status = "installed"
        installation.config_json = config_json
        installation.installed_at = now
        installation.uninstalled_at = None
    db.add(installation)
    await db.commit()
    await db.refresh(installation)
    return installation

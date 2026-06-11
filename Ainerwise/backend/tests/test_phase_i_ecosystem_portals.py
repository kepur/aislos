"""Phase I minimum loops: Store requests, Developer Portal and Agent Marketplace."""
import asyncio
import uuid
from decimal import Decimal

from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import AGENT_GRANT_SCOPES, Agent, AgentGrant
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.ecosystem import MarketplaceListingCreate, StoreOrderCreate, StoreOrderItemCreate


def test_eight_portal_closure_routes_registered():
    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/store/catalog",
        "/api/v1/store/orders",
        "/api/v1/store/orders/my",
        "/api/v1/admin/store/orders",
        "/api/v1/admin/store/orders/{order_id}/status",
        "/api/v1/marketplace/listings",
        "/api/v1/marketplace/listings/{listing_id}/install",
        "/api/v1/marketplace/installations/my",
        "/api/v1/developer/sdk/manifest",
        "/api/v1/developer/listings",
        "/api/v1/developer/listings/my",
        "/api/v1/admin/marketplace/listings",
        "/api/v1/admin/marketplace/listings/{listing_id}/approve",
        "/api/v1/admin/marketplace/listings/{listing_id}/reject",
    ):
        assert path in paths, path


def test_official_agents_are_seeded_as_marketplace_listings():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            official_agents = (
                await db.execute(select(Agent).where(Agent.vendor == "official"))
            ).scalars().all()
            listings = (
                await db.execute(
                    select(MarketplaceListing).where(MarketplaceListing.status == "approved")
                )
            ).scalars().all()
            listing_agent_ids = {listing.agent_id for listing in listings}
            assert official_agents
            assert {agent.id for agent in official_agents} <= listing_agent_ids

    asyncio.run(_run())


def test_store_request_uses_server_price_and_takes_no_payment():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.ecosystem import create_store_order, store_order_dict

            suffix = uuid.uuid4().hex[:10]
            user = User(email=f"store-{suffix}@test.local", password_hash="unused", role="buyer")
            product = Product(
                name=f"Store Product {suffix}",
                slug=f"store-product-{suffix}",
                list_price=123.45,
                currency="EUR",
                status="active",
            )
            db.add_all([user, product])
            await db.flush()
            order, items = await create_store_order(
                db,
                user=user,
                data=StoreOrderCreate(
                    items=[StoreOrderItemCreate(product_id=product.id, quantity=2)],
                    notes="Need installation advice",
                ),
            )
            payload = store_order_dict(order, items)
            assert payload["subtotal"] == 246.9
            assert payload["status"] == "requested"
            assert "No payment was taken" in payload["payment_boundary"]
            assert items[0].unit_price == Decimal("123.45")
            await db.delete(order)
            await db.delete(product)
            await db.delete(user)
            await db.commit()

    asyncio.run(_run())


def test_third_party_agent_approval_defaults_to_paused_and_all_denied():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.ecosystem import (
                approve_marketplace_listing,
                create_marketplace_listing,
                install_marketplace_agent,
            )

            suffix = uuid.uuid4().hex[:10]
            developer = User(
                email=f"developer-{suffix}@test.local",
                password_hash="unused",
                role="developer",
            )
            admin = User(email=f"admin-i-{suffix}@test.local", password_hash="unused", role="admin")
            db.add_all([developer, admin])
            await db.flush()
            listing = await create_marketplace_listing(
                db,
                user=developer,
                slug=f"knx-design-{suffix}",
                data=MarketplaceListingCreate(
                    name="KNX Design Agent",
                    workflows=["knx_design_review"],
                    requested_scopes=["project_data", "payment"],
                    price_monthly=299,
                ),
            )
            agent = await approve_marketplace_listing(
                db, listing=listing, reviewer_id=admin.id, notes="Sandbox review passed"
            )
            assert agent.vendor == "third_party"
            assert agent.status == "paused"
            grants = (
                await db.execute(select(AgentGrant).where(AgentGrant.agent_id == agent.id))
            ).scalars().all()
            assert {grant.scope for grant in grants} == set(AGENT_GRANT_SCOPES)
            assert all(grant.granted is False for grant in grants)

            installation = await install_marketplace_agent(
                db, listing=listing, user=developer, config_json={"project_mode": "review_only"}
            )
            assert installation.status == "installed"
            grants_after_install = (
                await db.execute(select(AgentGrant).where(AgentGrant.agent_id == agent.id))
            ).scalars().all()
            assert all(grant.granted is False for grant in grants_after_install)

            await db.delete(installation)
            for grant in grants_after_install:
                await db.delete(grant)
            await db.delete(listing)
            await db.flush()
            await db.delete(agent)
            await db.delete(admin)
            await db.delete(developer)
            await db.commit()

    asyncio.run(_run())


def test_ecosystem_models_are_registered():
    assert StoreOrder.__tablename__ == "store_orders"
    assert StoreOrderItem.__tablename__ == "store_order_items"
    assert MarketplaceListing.__tablename__ == "marketplace_listings"
    assert AgentInstallation.__tablename__ == "agent_installations"

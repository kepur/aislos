"""Phase I minimum loops: Store requests, Developer Portal and Agent Marketplace."""
import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from tests.route_utils import registered_route_paths
from app.models.agent import AGENT_GRANT_SCOPES, Agent, AgentGrant
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem
from app.models.product import Product
from app.models.portal_access import Workspace, WorkspaceMembership
from app.models.user import User
from app.schemas.ecosystem import MarketplaceListingCreate, StoreOrderCreate, StoreOrderItemCreate


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_eight_portal_closure_routes_registered():
    paths = registered_route_paths(app)
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
            assert "reviewed_by" not in payload
            assert "user_id" not in payload
            internal_payload = store_order_dict(order, items, include_internal=True)
            assert internal_payload["user_id"] == str(user.id)
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
                require_agent_install_manager,
            )

            suffix = uuid.uuid4().hex[:10]
            developer = User(
                email=f"developer-{suffix}@test.local",
                password_hash="unused",
                role="developer",
            )
            admin = User(email=f"admin-i-{suffix}@test.local", password_hash="unused", role="admin")
            member = User(email=f"member-i-{suffix}@test.local", password_hash="unused", role="customer_user")
            workspace_a = Workspace(name=f"Agent Workspace A {suffix}", slug=f"agent-a-{suffix}")
            workspace_b = Workspace(name=f"Agent Workspace B {suffix}", slug=f"agent-b-{suffix}")
            db.add_all([developer, admin, member, workspace_a, workspace_b])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=developer.id,
                        membership_type="developer",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_b.id,
                        user_id=developer.id,
                        membership_type="developer",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=member.id,
                        membership_type="customer_member",
                        status="active",
                    ),
                ]
            )
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
                db,
                listing=listing,
                user=developer,
                workspace_id=workspace_a.id,
                config_json={"project_mode": "review_only"},
            )
            assert installation.status == "installed"
            assert installation.workspace_id == workspace_a.id
            second_installation = await install_marketplace_agent(
                db,
                listing=listing,
                user=developer,
                workspace_id=workspace_b.id,
                config_json={"project_mode": "review_only"},
            )
            assert second_installation.id != installation.id
            assert second_installation.workspace_id == workspace_b.id
            with pytest.raises(PermissionError, match="Owner or Admin"):
                await require_agent_install_manager(
                    db,
                    user_id=member.id,
                    workspace_id=workspace_a.id,
                )
            grants_after_install = (
                await db.execute(select(AgentGrant).where(AgentGrant.agent_id == agent.id))
            ).scalars().all()
            assert all(grant.granted is False for grant in grants_after_install)

            await db.delete(installation)
            await db.delete(second_installation)
            for grant in grants_after_install:
                await db.delete(grant)
            await db.delete(listing)
            await db.flush()
            await db.delete(agent)
            await db.delete(workspace_a)
            await db.delete(workspace_b)
            await db.delete(admin)
            await db.delete(developer)
            await db.delete(member)
            await db.commit()

    asyncio.run(_run())


def test_ecosystem_models_are_registered():
    assert StoreOrder.__tablename__ == "store_orders"
    assert StoreOrderItem.__tablename__ == "store_order_items"
    assert MarketplaceListing.__tablename__ == "marketplace_listings"
    assert AgentInstallation.__tablename__ == "agent_installations"


def test_agent_installation_api_is_workspace_scoped_and_owner_managed():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        password = "agent-scope-123"
        async with async_session_factory() as db:
            owner = User(
                email=f"agent-owner-{suffix}@example.com",
                password_hash=hash_password(password),
                role="buyer",
                is_active=True,
            )
            member = User(
                email=f"agent-member-{suffix}@example.com",
                password_hash=hash_password(password),
                role="customer_user",
                is_active=True,
            )
            workspace_a = Workspace(name=f"Scoped A {suffix}", slug=f"scoped-a-{suffix}")
            workspace_b = Workspace(name=f"Scoped B {suffix}", slug=f"scoped-b-{suffix}")
            db.add_all([owner, member, workspace_a, workspace_b])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=owner.id,
                        membership_type="customer_owner",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_b.id,
                        user_id=owner.id,
                        membership_type="customer_owner",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=member.id,
                        membership_type="customer_member",
                        status="active",
                    ),
                ]
            )
            listing = (
                await db.execute(
                    select(MarketplaceListing)
                    .where(MarketplaceListing.status == "approved")
                    .order_by(MarketplaceListing.created_at)
                )
            ).scalars().first()
            assert listing is not None
            listing_id = listing.id
            owner_id = owner.id
            workspace_a_id = workspace_a.id
            workspace_b_id = workspace_b.id
            member_email = member.email
            owner_email = owner.email
            await db.commit()

        owner_headers = await _login(owner_email, password)
        member_headers = await _login(member_email, password)
        async with _client() as client:
            no_scope = await client.get("/api/v1/marketplace/installations/my", headers=owner_headers)
            assert no_scope.status_code == 400

            install_a = await client.post(
                f"/api/v1/marketplace/listings/{listing_id}/install",
                headers=owner_headers,
                json={"workspace_id": str(workspace_a_id)},
            )
            assert install_a.status_code == 201, install_a.text
            assert install_a.json()["workspace_id"] == str(workspace_a_id)

            install_b = await client.post(
                f"/api/v1/marketplace/listings/{listing_id}/install",
                headers=owner_headers,
                json={"workspace_id": str(workspace_b_id)},
            )
            assert install_b.status_code == 201, install_b.text
            assert install_b.json()["workspace_id"] == str(workspace_b_id)

            list_a = await client.get(
                f"/api/v1/marketplace/installations/my?workspace_id={workspace_a_id}",
                headers=owner_headers,
            )
            assert list_a.status_code == 200, list_a.text
            assert {item["workspace_id"] for item in list_a.json()["items"]} == {str(workspace_a_id)}

            member_denied = await client.post(
                f"/api/v1/marketplace/listings/{listing_id}/install",
                headers=member_headers,
                json={"workspace_id": str(workspace_a_id)},
            )
            assert member_denied.status_code == 403

        async with async_session_factory() as db:
            memberships = (
                await db.execute(
                    select(WorkspaceMembership).where(
                        WorkspaceMembership.user_id == owner_id,
                        WorkspaceMembership.workspace_id == workspace_a_id,
                    )
                )
            ).scalars().all()
            for membership in memberships:
                membership.status = "suspended"
            await db.commit()

        async with _client() as client:
            revoked = await client.post(
                f"/api/v1/marketplace/installations/{install_a.json()['id']}/uninstall",
                headers=owner_headers,
            )
            assert revoked.status_code == 403

    asyncio.run(_run())

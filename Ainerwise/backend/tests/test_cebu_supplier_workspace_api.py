"""Core-backed Supplier PC/H5 workspace contracts and ownership boundaries."""

import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_access import PortalGrant, WorkspaceMembership
from app.models.region import Region
from app.models.user import User
from app.core.security import hash_password
from app.services.portal_access import sync_role_portal_access


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_supplier_workspace_endpoints_and_cross_company_denial():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        attacker_email, password, _ = await _create_identity(role="vendor")
        attacker = await _login(attacker_email, password)

        async with _client() as client:
            listings = await client.get("/api/v1/commerce/supplier-listings", headers=supplier)
            assert listings.status_code == 200, listings.text
            assert listings.json()["total"] == 1
            listing = listings.json()["items"][0]
            listing_id = listing["id"]
            category_id = listing["category_schema_id"]

            buyer_cannot_list_private_catalog = await client.get(
                "/api/v1/commerce/supplier-listings", headers=buyer
            )
            assert buyer_cannot_list_private_catalog.status_code == 403
            attacker_cannot_edit = await client.patch(
                f"/api/v1/commerce/supplier-listings/{listing_id}",
                headers=attacker,
                json={"title": "Stolen listing"},
            )
            assert attacker_cannot_edit.status_code == 403
            updated = await client.patch(
                f"/api/v1/commerce/supplier-listings/{listing_id}",
                headers=supplier,
                json={"title": "Supplier-owned listing"},
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["title"] == "Supplier-owned listing"

            request = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer,
                json={
                    "title": "Open supplier ping",
                    "category_schema_id": category_id,
                    "portal_key": "cebu",
                },
            )
            assert request.status_code == 201, request.text
            request_id = request.json()["id"]
            published = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/publish", headers=buyer
            )
            assert published.status_code == 200, published.text

            pings = await client.get("/api/v1/commerce/supplier-pings", headers=supplier)
            assert pings.status_code == 200, pings.text
            ping = next(item for item in pings.json()["items"] if item["id"] == request_id)
            assert ping["already_offered"] is False
            assert listing_id in ping["matching_listing_ids"]

            offer = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers",
                headers=supplier,
                json={"supplier_listing_id": listing_id, "price_minor": 99000, "currency": "EUR"},
            )
            assert offer.status_code == 201, offer.text
            offer_id = offer.json()["id"]
            attacker_withdraw = await client.post(
                f"/api/v1/commerce/offers/{offer_id}/withdraw", headers=attacker
            )
            assert attacker_withdraw.status_code == 403
            withdrawn = await client.post(
                f"/api/v1/commerce/offers/{offer_id}/withdraw", headers=supplier
            )
            assert withdrawn.status_code == 200, withdrawn.text
            assert withdrawn.json()["status"] == "withdrawn"

            offers = await client.get("/api/v1/commerce/supplier-offers", headers=supplier)
            assert offers.status_code == 200, offers.text
            assert any(item["id"] == offer_id for item in offers.json()["items"])
            attacker_offers = await client.get("/api/v1/commerce/supplier-offers", headers=attacker)
            assert all(item["id"] != offer_id for item in attacker_offers.json()["items"])

            completed = await client.post(f"/api/v1/commerce/orders/{order_id}/complete", headers=buyer)
            assert completed.status_code == 200, completed.text
            review = await client.post(
                f"/api/v1/commerce/orders/{order_id}/reviews",
                headers=buyer,
                json={"rating": 5, "comment": "Delivered as promised"},
            )
            assert review.status_code == 201, review.text
            reviews = await client.get("/api/v1/commerce/supplier-reviews", headers=supplier)
            assert reviews.status_code == 200, reviews.text
            assert any(item["id"] == review.json()["id"] for item in reviews.json()["items"])
            attacker_reviews = await client.get("/api/v1/commerce/supplier-reviews", headers=attacker)
            assert attacker_reviews.json()["total"] == 0

            account = await client.get("/api/v1/commerce/supplier-account", headers=supplier)
            assert account.status_code == 200, account.text
            team = await client.get("/api/v1/commerce/supplier-team", headers=supplier)
            assert team.status_code == 200, team.text
            assert team.json()["total"] == 1
            invited = await client.post(
                "/api/v1/commerce/supplier-team",
                headers=supplier,
                json={
                    "email": f"supplier-team-{uuid.uuid4().hex[:8]}@example.com",
                    "full_name": "Supplier Operator",
                },
            )
            assert invited.status_code == 201, invited.text
            assert invited.json()["password_reset_required"] is True
            member_id = invited.json()["user"]["id"]
            assert invited.json()["user"]["role"] == "vendor"

            cross_company_update = await client.patch(
                f"/api/v1/commerce/supplier-team/{member_id}",
                headers=attacker,
                json={"is_active": False},
            )
            assert cross_company_update.status_code == 404
            cannot_deactivate_self = await client.patch(
                f"/api/v1/commerce/supplier-team/{team.json()['items'][0]['id']}",
                headers=supplier,
                json={"is_active": False},
            )
            assert cannot_deactivate_self.status_code == 409
            deactivated = await client.patch(
                f"/api/v1/commerce/supplier-team/{member_id}",
                headers=supplier,
                json={"is_active": False},
            )
            assert deactivated.status_code == 200, deactivated.text
            assert deactivated.json()["is_active"] is False
            async with async_session_factory() as db:
                grants = list(
                    (
                        await db.execute(
                            select(PortalGrant).where(PortalGrant.user_id == uuid.UUID(member_id))
                        )
                    ).scalars()
                )
                memberships = list(
                    (
                        await db.execute(
                            select(WorkspaceMembership).where(
                                WorkspaceMembership.user_id == uuid.UUID(member_id)
                            )
                        )
                    ).scalars()
                )
                assert grants and all(not grant.granted and grant.revoked_at for grant in grants)
                assert memberships and all(row.status == "suspended" for row in memberships)
            team_with_inactive = await client.get("/api/v1/commerce/supplier-team", headers=supplier)
            assert team_with_inactive.json()["total"] == 2
            assert next(row for row in team_with_inactive.json()["items"] if row["id"] == member_id)["is_active"] is False
            reactivated = await client.patch(
                f"/api/v1/commerce/supplier-team/{member_id}",
                headers=supplier,
                json={"is_active": True, "full_name": "Restored Supplier Operator"},
            )
            assert reactivated.status_code == 200, reactivated.text
            assert reactivated.json()["is_active"] is True
            assert reactivated.json()["full_name"] == "Restored Supplier Operator"
            dashboard = await client.get("/api/v1/commerce/supplier-dashboard", headers=supplier)
            assert dashboard.status_code == 200, dashboard.text
            assert dashboard.json()["listings"] == 1
            assert dashboard.json()["orders"] >= 1

    asyncio.run(_run())


def test_supplier_operator_cannot_manage_company_or_team():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        owner_email, password, company_id = await _create_identity(role="vendor")
        owner = await _login(owner_email, password)
        operator_email = f"supplier-operator-{uuid.uuid4().hex[:8]}@example.com"
        operator_password = "operator-password-123"

        async with async_session_factory() as db:
            operator = User(
                email=operator_email,
                password_hash=hash_password(operator_password),
                full_name="Supplier Operator",
                role="vendor",
                company_id=company_id,
                is_active=True,
            )
            db.add(operator)
            await db.flush()
            await sync_role_portal_access(
                db,
                user_id=operator.id,
                role=operator.role,
                company_id=company_id,
            )
            await db.commit()
            operator_id = operator.id

        operator = await _login(operator_email, operator_password)
        async with _client() as client:
            owner_account = await client.get("/api/v1/commerce/supplier-account", headers=owner)
            assert owner_account.status_code == 200, owner_account.text
            assert owner_account.json()["permissions"]["manage_company"] is True
            assert owner_account.json()["permissions"]["manage_team"] is True

            operator_account = await client.get(
                "/api/v1/commerce/supplier-account", headers=operator
            )
            assert operator_account.status_code == 200, operator_account.text
            assert operator_account.json()["permissions"]["manage_company"] is False
            assert operator_account.json()["permissions"]["manage_team"] is False

            personal_update = await client.patch(
                "/api/v1/commerce/supplier-account",
                headers=operator,
                json={"full_name": "Updated Operator"},
            )
            assert personal_update.status_code == 200, personal_update.text

            company_update = await client.patch(
                "/api/v1/commerce/supplier-account",
                headers=operator,
                json={"company_name": "Operator Cannot Rename"},
            )
            assert company_update.status_code == 403

            invite = await client.post(
                "/api/v1/commerce/supplier-team",
                headers=operator,
                json={"email": f"forbidden-{uuid.uuid4().hex[:8]}@example.com"},
            )
            assert invite.status_code == 403

            member_update = await client.patch(
                f"/api/v1/commerce/supplier-team/{operator_id}",
                headers=operator,
                json={"phone": "+63 900 111 2222"},
            )
            assert member_update.status_code == 403

        async with async_session_factory() as db:
            owner_types = {
                row.membership_type
                for row in (
                    await db.execute(
                        select(WorkspaceMembership)
                        .join(User, User.id == WorkspaceMembership.user_id)
                        .where(User.email == owner_email)
                    )
                ).scalars()
            }
            operator_types = {
                row.membership_type
                for row in (
                    await db.execute(
                        select(WorkspaceMembership).where(
                            WorkspaceMembership.user_id == operator_id
                        )
                    )
                ).scalars()
            }
            assert "supplier_owner" in owner_types
            assert "supplier_owner" not in operator_types
            assert "supplier_operator" in operator_types

    asyncio.run(_run())


def test_supplier_category_and_region_rules_filter_real_pings_and_candidates():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        _, buyer, supplier, _ = await _setup_awarded_order()
        suffix = uuid.uuid4().hex[:6].upper()
        async with async_session_factory() as db:
            matching_region = Region(
                code=f"M{suffix}",
                name=f"Matching Region {suffix}",
                currency_code="EUR",
                is_active=True,
            )
            other_region = Region(
                code=f"O{suffix}",
                name=f"Other Region {suffix}",
                currency_code="EUR",
                is_active=True,
            )
            db.add_all([matching_region, other_region])
            await db.commit()
            await db.refresh(matching_region)
            await db.refresh(other_region)
            matching_region_id = matching_region.id
            other_region_id = other_region.id

        async with _client() as client:
            listings = await client.get("/api/v1/commerce/supplier-listings", headers=supplier)
            listing = listings.json()["items"][0]
            listing_id = listing["id"]
            category_id = listing["category_schema_id"]
            scoped_listing = await client.patch(
                f"/api/v1/commerce/supplier-listings/{listing_id}",
                headers=supplier,
                json={"region_id": str(matching_region_id)},
            )
            assert scoped_listing.status_code == 200, scoped_listing.text

            preferences = await client.put(
                "/api/v1/portal/notification-preferences",
                headers=supplier,
                json={
                    "supplier_category_ids_json": [category_id],
                    "supplier_region_ids_json": [str(matching_region_id)],
                },
            )
            assert preferences.status_code == 200, preferences.text

            request_ids: list[str] = []
            for title, region_id in (
                ("Matching supplier rule", matching_region_id),
                ("Outside supplier rule", other_region_id),
            ):
                created = await client.post(
                    "/api/v1/commerce/procurement-requests",
                    headers=buyer,
                    json={
                        "title": title,
                        "category_schema_id": category_id,
                        "region_id": str(region_id),
                        "portal_key": "cebu",
                    },
                )
                assert created.status_code == 201, created.text
                request_ids.append(created.json()["id"])
                published = await client.post(
                    f"/api/v1/commerce/procurement-requests/{created.json()['id']}/publish",
                    headers=buyer,
                )
                assert published.status_code == 200, published.text

            pings = await client.get("/api/v1/commerce/supplier-pings", headers=supplier)
            ping_ids = {item["id"] for item in pings.json()["items"]}
            assert request_ids[0] in ping_ids
            assert request_ids[1] not in ping_ids

            matching_candidates = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_ids[0]}/supplier-candidates",
                headers=buyer,
            )
            assert listing_id in {item["id"] for item in matching_candidates.json()["items"]}
            other_candidates = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_ids[1]}/supplier-candidates",
                headers=buyer,
            )
            assert listing_id not in {item["id"] for item in other_candidates.json()["items"]}

            invalid = await client.put(
                "/api/v1/portal/notification-preferences",
                headers=supplier,
                json={"supplier_region_ids_json": [str(uuid.uuid4())]},
            )
            assert invalid.status_code == 422

    asyncio.run(_run())

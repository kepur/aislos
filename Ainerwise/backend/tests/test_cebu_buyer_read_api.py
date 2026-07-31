"""Buyer/Public read contracts used by the zero-loss Cebu PC and H5 portals."""

import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_access import WorkspaceMembership
from app.models.user import Company, User


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _unrelated_headers() -> dict:
    suffix = uuid.uuid4().hex[:8]
    email = f"unrelated-buyer-{suffix}@example.com"
    password = "buyer123"
    async with async_session_factory() as db:
        company = Company(
            name=f"Unrelated Buyer {suffix}",
            type="customer",
            country="Philippines",
            verification_status="verified",
        )
        db.add(company)
        await db.flush()
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name="Unrelated Buyer",
                role="buyer",
                company_id=company.id,
                is_active=True,
            )
        )
        await db.commit()
    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_public_marketplace_and_buyer_read_models():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        unrelated = await _unrelated_headers()

        async with _client() as client:
            categories = await client.get("/api/v1/commerce/public/category-schemas")
            assert categories.status_code == 200, categories.text
            assert categories.json()["total"] >= 1

            listings = await client.get("/api/v1/commerce/public/listings")
            assert listings.status_code == 200, listings.text
            assert listings.json()["total"] >= 1
            listing_id = listings.json()["items"][0]["id"]
            listing = await client.get(f"/api/v1/commerce/public/listings/{listing_id}")
            assert listing.status_code == 200, listing.text

            order = await client.get(f"/api/v1/commerce/orders/{order_id}", headers=buyer)
            assert order.status_code == 200, order.text
            request_id = order.json()["procurement_request_id"]
            offer_id = order.json()["winning_offer_id"]

            offers = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers", headers=buyer
            )
            assert offers.status_code == 200, offers.text
            assert offers.json()["total"] == 1

            supplier_offer = await client.get(f"/api/v1/commerce/offers/{offer_id}", headers=supplier)
            assert supplier_offer.status_code == 200, supplier_offer.text

            forbidden_offers = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers", headers=unrelated
            )
            assert forbidden_offers.status_code == 403
            forbidden_offer = await client.get(f"/api/v1/commerce/offers/{offer_id}", headers=unrelated)
            assert forbidden_offer.status_code == 403

            threads = await client.get("/api/v1/commerce/threads", headers=buyer)
            assert threads.status_code == 200, threads.text
            assert threads.json()["total"] >= 1
            unrelated_threads = await client.get("/api/v1/commerce/threads", headers=unrelated)
            assert unrelated_threads.json()["total"] == 0

    asyncio.run(_run())


def test_buyer_dispute_and_payment_ledger_are_party_scoped():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, _, _ = await _setup_awarded_order()
        unrelated = await _unrelated_headers()

        async with _client() as client:
            payment = await client.post(
                f"/api/v1/commerce/orders/{order_id}/payment-intent",
                headers=buyer,
                json={"psp_provider": "stripe"},
            )
            assert payment.status_code == 201, payment.text

            dispute = await client.post(
                f"/api/v1/commerce/orders/{order_id}/disputes",
                headers=buyer,
                json={"reason_code": "delivery_terms", "description": "Need clarification"},
            )
            assert dispute.status_code == 201, dispute.text

            disputes = await client.get("/api/v1/commerce/disputes", headers=buyer)
            assert disputes.status_code == 200, disputes.text
            assert any(item["id"] == dispute.json()["id"] for item in disputes.json()["items"])
            unrelated_disputes = await client.get("/api/v1/commerce/disputes", headers=unrelated)
            assert unrelated_disputes.json()["total"] == 0

            ledger = await client.get("/api/v1/commerce/payment-ledger", headers=buyer)
            assert ledger.status_code == 200, ledger.text
            assert any(item["order_id"] == order_id for item in ledger.json()["items"])
            unrelated_ledger = await client.get("/api/v1/commerce/payment-ledger", headers=unrelated)
            assert unrelated_ledger.json()["total"] == 0

    asyncio.run(_run())


def test_buyer_account_team_and_watchlist_are_self_scoped():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        await _setup_awarded_order()
        buyer = await _unrelated_headers()
        attacker = await _unrelated_headers()

        async with _client() as client:
            account = await client.get("/api/v1/commerce/buyer-account", headers=buyer)
            assert account.status_code == 200, account.text
            company_id = account.json()["company"]["id"]

            updated = await client.patch(
                "/api/v1/commerce/buyer-account",
                headers=buyer,
                json={
                    "full_name": "Cebu Buyer Owner",
                    "company_city": "Cebu City",
                    "company_description": "Buyer-managed procurement workspace",
                },
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["user"]["full_name"] == "Cebu Buyer Owner"
            assert updated.json()["company"]["id"] == company_id
            assert updated.json()["company"]["city"] == "Cebu City"

            team = await client.get("/api/v1/commerce/buyer-team", headers=buyer)
            assert team.status_code == 200, team.text
            assert team.json()["total"] == 1
            attacker_team = await client.get("/api/v1/commerce/buyer-team", headers=attacker)
            assert attacker_team.status_code == 200
            assert all(member["id"] != team.json()["items"][0]["id"] for member in attacker_team.json()["items"])

            listings = await client.get("/api/v1/commerce/public/listings")
            listing_id = listings.json()["items"][0]["id"]
            watch = await client.post(
                "/api/v1/commerce/watchlist",
                headers=buyer,
                json={"supplier_listing_id": listing_id, "target_price_minor": 100000, "currency": "EUR"},
            )
            assert watch.status_code == 201, watch.text
            watch_id = watch.json()["id"]

            buyer_watchlist = await client.get("/api/v1/commerce/watchlist", headers=buyer)
            assert buyer_watchlist.json()["total"] == 1
            attacker_watchlist = await client.get("/api/v1/commerce/watchlist", headers=attacker)
            assert attacker_watchlist.json()["total"] == 0
            forbidden = await client.delete(f"/api/v1/commerce/watchlist/{watch_id}", headers=attacker)
            assert forbidden.status_code == 403
            removed = await client.delete(f"/api/v1/commerce/watchlist/{watch_id}", headers=buyer)
            assert removed.status_code == 204

    asyncio.run(_run())


def test_individual_buyer_can_create_company_profile_and_update_self():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:8]
        email = f"individual-buyer-{suffix}@example.com"
        password = "buyer-password-123"
        async with _client() as client:
            registered = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password, "role": "buyer", "full_name": "Individual Buyer"},
            )
            assert registered.status_code == 201, registered.text
            headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}

            self_update = await client.patch(
                "/api/v1/users/me",
                headers=headers,
                json={"phone": "+63 900 000 0000", "language": "tl"},
            )
            assert self_update.status_code == 200, self_update.text
            assert self_update.json()["phone"] == "+63 900 000 0000"
            assert self_update.json()["language"] == "tl"

            account = await client.get("/api/v1/commerce/buyer-account", headers=headers)
            assert account.status_code == 200, account.text
            assert account.json()["company"] is None

            created = await client.patch(
                "/api/v1/commerce/buyer-account",
                headers=headers,
                json={
                    "company_name": f"Buyer Company {suffix}",
                    "company_country": "Philippines",
                    "company_city": "Cebu City",
                },
            )
            assert created.status_code == 200, created.text
            assert created.json()["company"]["name"] == f"Buyer Company {suffix}"
            assert created.json()["company"]["city"] == "Cebu City"
            assert created.json()["user"]["company_id"] == created.json()["company"]["id"]
            async with async_session_factory() as db:
                membership = (
                    await db.execute(
                        select(WorkspaceMembership).where(
                            WorkspaceMembership.user_id == uuid.UUID(created.json()["user"]["id"]),
                            WorkspaceMembership.membership_type == "customer_owner",
                            WorkspaceMembership.status == "active",
                        )
                    )
                ).scalar_one()
                assert str(membership.company_id) == created.json()["company"]["id"]

    asyncio.run(_run())


def test_customer_member_cannot_manage_buyer_company():
    async def _run():
        await engine.dispose()
        owner = await _unrelated_headers()
        async with _client() as client:
            owner_account = await client.get("/api/v1/commerce/buyer-account", headers=owner)
            assert owner_account.status_code == 200, owner_account.text
            assert owner_account.json()["permissions"]["manage_company"] is True
            company_id = uuid.UUID(owner_account.json()["company"]["id"])

        suffix = uuid.uuid4().hex[:8]
        member_email = f"customer-member-{suffix}@example.com"
        member_password = "customer-member-password"
        async with async_session_factory() as db:
            member = User(
                email=member_email,
                password_hash=hash_password(member_password),
                full_name="Customer Member",
                role="customer_user",
                company_id=company_id,
                is_active=True,
            )
            db.add(member)
            await db.commit()

        async with _client() as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": member_email, "password": member_password},
            )
            assert login.status_code == 200, login.text
            member = {"Authorization": f"Bearer {login.json()['access_token']}"}

            account = await client.get("/api/v1/commerce/buyer-account", headers=member)
            assert account.status_code == 200, account.text
            assert account.json()["permissions"]["manage_company"] is False

            personal = await client.patch(
                "/api/v1/commerce/buyer-account",
                headers=member,
                json={"full_name": "Updated Customer Member"},
            )
            assert personal.status_code == 200, personal.text

            forbidden = await client.patch(
                "/api/v1/commerce/buyer-account",
                headers=member,
                json={"company_name": "Member Cannot Rename"},
            )
            assert forbidden.status_code == 403

    asyncio.run(_run())

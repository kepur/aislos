"""2Hands P0: seller listing, address-disclosure gate and records-first pickup.

The privacy assertions here are the point: a seller's pickup address must never
leak through public/browse/detail responses, and must only reach a buyer the
seller explicitly granted.
"""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from tests.route_utils import registered_route_paths

RESTRICTED = ("pickup_address", "pickup_note", "contact_phone")


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(email: str, password: str) -> dict:
    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_secondhand_routes_registered():
    paths = registered_route_paths(app)
    for p in (
        "/api/v1/secondhand/listings",
        "/api/v1/secondhand/listings/{listing_id}/pickup-details",
        "/api/v1/secondhand/disclosures/{disclosure_id}/grant",
        "/api/v1/secondhand/deals/{deal_id}/confirm-pickup",
    ):
        assert p in paths, p


def test_pickup_address_stays_private_until_granted():
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        buyer = await _headers("demo@ainerwise.com", "demo123")
        marker = f"2Hands Test {uuid.uuid4().hex[:6]}"
        secret_address = "Secret Street 42, Beograd"

        async with _client() as client:
            created = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={
                    "title": marker,
                    "price_minor": 12345,
                    "currency": "EUR",
                    "condition_grade": "B",
                    "fulfillment_mode": "SELLER_PICKUP",
                    "pickup_country": "RS",
                    "pickup_city": "Beograd",
                    "pickup_address": secret_address,
                    "pickup_note": "evenings only",
                    "contact_phone": "+381 60 000000",
                },
            )
            assert created.status_code == 201, created.text
            listing_id = created.json()["id"]

            # 1. Create response carries no restricted field.
            assert not [k for k in RESTRICTED if k in created.json()]

            # 2. Anonymous browse + detail expose the city but never the address.
            browse = await client.get("/api/v1/secondhand/listings", params={"keyword": marker})
            assert browse.status_code == 200
            found = [i for i in browse.json()["items"] if i["title"] == marker]
            assert found, "listing should be publicly browsable"
            assert found[0]["pickup_city"] == "Beograd"
            assert not [k for k in RESTRICTED if k in found[0]]
            assert secret_address not in browse.text

            detail = await client.get(f"/api/v1/secondhand/listings/{listing_id}")
            assert secret_address not in detail.text

            # 3. A buyer without a grant is refused.
            denied = await client.get(
                f"/api/v1/secondhand/listings/{listing_id}/pickup-details", headers=buyer
            )
            assert denied.status_code == 403

            # 4. Buyer requests, seller grants only the address.
            req = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/disclosure-request",
                headers=buyer,
                json={"message": "can I collect tonight?"},
            )
            assert req.status_code == 201, req.text
            disclosure_id = req.json()["id"]
            assert req.json()["status"] == "requested"

            seller_view = await client.get(
                f"/api/v1/secondhand/listings/{listing_id}/disclosures", headers=seller
            )
            assert seller_view.status_code == 200
            assert any(d["id"] == disclosure_id for d in seller_view.json()["items"])

            granted = await client.post(
                f"/api/v1/secondhand/disclosures/{disclosure_id}/grant",
                headers=seller,
                json={"fields": ["address"]},
            )
            assert granted.status_code == 200, granted.text

            # 5. Now the buyer sees the address — but not the ungranted fields.
            allowed = await client.get(
                f"/api/v1/secondhand/listings/{listing_id}/pickup-details", headers=buyer
            )
            assert allowed.status_code == 200
            assert allowed.json()["pickup_address"] == secret_address
            assert "contact_phone" not in allowed.json()
            assert "pickup_note" not in allowed.json()

            # 6. Revoking closes access again.
            revoked = await client.post(
                f"/api/v1/secondhand/disclosures/{disclosure_id}/revoke", headers=seller
            )
            assert revoked.status_code == 200
            after = await client.get(
                f"/api/v1/secondhand/listings/{listing_id}/pickup-details", headers=buyer
            )
            assert after.status_code == 403

    asyncio.run(_run())


def test_unique_stock_reserve_and_records_first_pickup():
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        buyer = await _headers("demo@ainerwise.com", "demo123")
        marker = f"2Hands Test {uuid.uuid4().hex[:6]}"

        async with _client() as client:
            created = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={"title": marker, "price_minor": 50000, "condition_grade": "A"},
            )
            assert created.status_code == 201, created.text
            listing_id = created.json()["id"]

            reserved = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/reserve",
                headers=buyer,
                json={"agreed_price_minor": 45000},
            )
            assert reserved.status_code == 201, reserved.text
            deal_id = reserved.json()["id"]
            assert reserved.json()["status"] == "reserved"

            # Unique stock: a second reservation is refused.
            again = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/reserve", headers=buyer, json={}
            )
            assert again.status_code == 409

            # Records-first: the platform records how the parties settled directly.
            done = await client.post(
                f"/api/v1/secondhand/deals/{deal_id}/confirm-pickup",
                headers=buyer,
                json={"payment_method": "CASH", "payment_reference": "cash on collection"},
            )
            assert done.status_code == 200, done.text
            assert done.json()["status"] == "picked_up"
            assert done.json()["agreed_price_minor"] == 45000

            # Selling the unique item delists it.
            after = await client.get(f"/api/v1/secondhand/listings/{listing_id}")
            assert after.json()["status"] == "sold"
            assert after.json()["sold_at"] is not None

            browse = await client.get("/api/v1/secondhand/listings", params={"keyword": marker})
            assert not [i for i in browse.json()["items"] if i["title"] == marker]

    asyncio.run(_run())


def test_duplicate_active_serial_is_rejected():
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        serial = f"2HANDS-TEST-{uuid.uuid4().hex[:8].upper()}"
        marker = f"2Hands Test {uuid.uuid4().hex[:6]}"

        async with _client() as client:
            first = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={
                    "title": marker,
                    "price_minor": 10000,
                    "serial_type": "IMEI",
                    "serial_no": serial,
                },
            )
            assert first.status_code == 201, first.text

            clash = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={
                    "title": f"{marker} dup",
                    "price_minor": 10000,
                    "serial_type": "IMEI",
                    "serial_no": serial,
                },
            )
            assert clash.status_code == 409

    asyncio.run(_run())

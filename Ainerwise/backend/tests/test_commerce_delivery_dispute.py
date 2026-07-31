"""Commerce order delivery lifecycle and dispute resolution."""
import asyncio
import json
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import Company, User
from sqlalchemy import select


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _demo_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@ainerwise.com", "password": "demo123"},
        )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _setup_awarded_order():
    """Return order_id, buyer headers, supplier headers, admin headers."""
    suffix = uuid.uuid4().hex[:8]
    supplier_email = f"supplier-{suffix}@example.com"
    supplier_password = "supplier123"

    async with async_session_factory() as db:
        supplier_co = Company(
            name=f"Commerce Supplier {suffix}",
            type="supplier",
            country="Serbia",
            verification_status="verified",
        )
        db.add(supplier_co)
        await db.flush()
        db.add(
            User(
                email=supplier_email,
                password_hash=hash_password(supplier_password),
                full_name="Commerce Supplier",
                role="vendor",
                company_id=supplier_co.id,
                is_active=True,
            )
        )
        await db.commit()
        supplier_company_id = supplier_co.id

    admin = await _admin_headers()
    buyer = await _demo_headers()
    async with _client() as client:
        supplier_login = await client.post(
            "/api/v1/auth/login",
            json={"email": supplier_email, "password": supplier_password},
        )
        assert supplier_login.status_code == 200, supplier_login.text
        supplier = {"Authorization": f"Bearer {supplier_login.json()['access_token']}"}

        cat = await client.post(
            "/api/v1/commerce/category-schemas",
            headers=admin,
            json={
                "slug": f"delivery-cat-{suffix}",
                "name": "Delivery Test Category",
                "definition": {"fields": []},
            },
        )
        assert cat.status_code == 201, cat.text
        cat_id = cat.json()["id"]

        listing = await client.post(
            "/api/v1/commerce/supplier-listings",
            headers=supplier,
            json={
                "company_id": str(supplier_company_id),
                "category_schema_id": cat_id,
                "title": "LED Panel Bundle",
                "price_minor": 125000,
            },
        )
        assert listing.status_code == 201, listing.text

        req = await client.post(
            "/api/v1/commerce/procurement-requests",
            headers=buyer,
            json={"title": f"Delivery flow {suffix}", "category_schema_id": cat_id, "portal_key": "cebu"},
        )
        assert req.status_code == 201, req.text
        request_id = req.json()["id"]

        pub = await client.post(f"/api/v1/commerce/procurement-requests/{request_id}/publish", headers=buyer)
        assert pub.status_code == 200, pub.text

        offer = await client.post(
            f"/api/v1/commerce/procurement-requests/{request_id}/offers",
            headers=supplier,
            json={
                "supplier_company_id": str(supplier_company_id),
                "supplier_listing_id": listing.json()["id"],
                "price_minor": 125000,
                "currency": "EUR",
            },
        )
        assert offer.status_code == 201, offer.text

        award = await client.post(f"/api/v1/commerce/offers/{offer.json()['id']}/award", headers=admin)
        assert award.status_code == 200, award.text
        order_id = award.json()["id"]

    return order_id, buyer, supplier, admin


def test_delivery_flow_then_complete_order():
    async def _run():
        await engine.dispose()
        order_id, buyer, supplier, admin = await _setup_awarded_order()

        async with _client() as client:
            delivery = await client.post(
                f"/api/v1/commerce/orders/{order_id}/deliveries",
                headers=supplier,
                json={"carrier": "DHL", "tracking_number": "TRK-001"},
            )
            assert delivery.status_code == 201, delivery.text
            delivery_id = delivery.json()["id"]
            assert delivery.json()["status"] == "scheduled"

            for status in ("shipped", "in_transit", "delivered"):
                step = await client.patch(
                    f"/api/v1/commerce/deliveries/{delivery_id}/status",
                    headers=supplier,
                    json={"status": status},
                )
                assert step.status_code == 200, step.text
                assert step.json()["status"] == status

            done = await client.post(f"/api/v1/commerce/orders/{order_id}/complete", headers=buyer)
            assert done.status_code == 200, done.text
            assert done.json()["status"] == "completed"

            listings = await client.get(f"/api/v1/commerce/orders/{order_id}/deliveries", headers=buyer)
            assert listings.status_code == 200
            assert listings.json()["total"] == 1

    asyncio.run(_run())


def test_dispute_blocks_complete_until_resolved():
    async def _run():
        await engine.dispose()
        order_id, buyer, supplier, admin = await _setup_awarded_order()

        async with _client() as client:
            delivery = await client.post(
                f"/api/v1/commerce/orders/{order_id}/deliveries",
                headers=supplier,
                json={"tracking_number": "TRK-002"},
            )
            assert delivery.status_code == 201, delivery.text
            delivery_id = delivery.json()["id"]

            for status in ("shipped", "in_transit", "delivered"):
                step = await client.patch(
                    f"/api/v1/commerce/deliveries/{delivery_id}/status",
                    headers=supplier,
                    json={"status": status},
                )
                assert step.status_code == 200, step.text

            dispute = await client.post(
                f"/api/v1/commerce/orders/{order_id}/disputes",
                headers=buyer,
                json={"reason_code": "damaged_goods", "description": "Cartons crushed"},
            )
            assert dispute.status_code == 201, dispute.text
            dispute_id = dispute.json()["id"]
            assert dispute.json()["status"] == "open"

            blocked = await client.post(f"/api/v1/commerce/orders/{order_id}/complete", headers=buyer)
            assert blocked.status_code == 409

            resolved = await client.post(
                f"/api/v1/commerce/disputes/{dispute_id}/resolve",
                headers=admin,
                json={"resolution": "resolved_buyer", "resolution_json": {"refund_minor": 5000}},
            )
            assert resolved.status_code == 200, resolved.text
            assert resolved.json()["status"] == "resolved_buyer"

            done = await client.post(f"/api/v1/commerce/orders/{order_id}/complete", headers=buyer)
            assert done.status_code == 200, done.text
            assert done.json()["status"] == "completed"

    asyncio.run(_run())


def test_legacy_bridge_opens_dispute():
    async def _run():
        await engine.dispose()
        from tests.test_legacy_bridge import BASE, _sign

        order_id, _, _, _ = await _setup_awarded_order()
        body = {
            "event_type": "commerce.dispute.opened",
            "portal_key": "cebu",
            "payload": {
                "order_id": order_id,
                "reason_code": "legacy_import",
                "description": "Imported from Cebu",
                "legacy_dispute_id": f"legacy-disp-{uuid.uuid4().hex[:8]}",
            },
        }
        raw = json.dumps(body).encode()
        headers = _sign(raw)
        async with _client() as client:
            resp = await client.post(BASE, headers=headers, content=raw)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("dispute_id")
        assert data.get("commerce_order_id") == order_id

        async with async_session_factory() as db:
            from app.models.commerce import OrderDispute

            row = await db.get(OrderDispute, uuid.UUID(data["dispute_id"]))
            assert row is not None
            assert row.status == "open"

    asyncio.run(_run())

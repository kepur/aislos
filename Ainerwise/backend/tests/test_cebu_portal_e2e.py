"""
P3-07: Cebu PC portal E2E — same API paths frontend-pc uses after Core base URL switch.

Simulates:
  login → portal manifest → list/create/publish procurement-requests → award → list orders
"""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import Company, User


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


def test_cebu_portal_core_api_e2e():
    """Buyer flow on /api/v1/commerce/* with portal_key=cebu (frontend-pc useCommerce)."""

    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:8]
        supplier_email = f"cebu-supplier-{suffix}@example.com"
        supplier_password = "supplier123"

        async with async_session_factory() as db:
            supplier_co = Company(
                name=f"Cebu Supplier {suffix}",
                type="supplier",
                country="Philippines",
                verification_status="verified",
            )
            db.add(supplier_co)
            await db.flush()
            db.add(
                User(
                    email=supplier_email,
                    password_hash=hash_password(supplier_password),
                    full_name="Cebu Supplier",
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
            manifest = await client.get("/api/v1/portal-manifests/cebu")
            assert manifest.status_code == 200, manifest.text
            assert manifest.json()["portal_key"] == "cebu"

            cat = await client.post(
                "/api/v1/commerce/category-schemas",
                headers=admin,
                json={
                    "slug": f"cebu-e2e-{suffix}",
                    "name": "Cebu E2E Category",
                    "definition": {"fields": []},
                },
            )
            assert cat.status_code == 201, cat.text
            cat_id = cat.json()["id"]

            listing_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": supplier_email, "password": supplier_password},
            )
            assert listing_resp.status_code == 200
            supplier = {"Authorization": f"Bearer {listing_resp.json()['access_token']}"}

            listing = await client.post(
                "/api/v1/commerce/supplier-listings",
                headers=supplier,
                json={
                    "company_id": str(supplier_company_id),
                    "category_schema_id": cat_id,
                    "title": "Cebu LED Kit",
                    "price_minor": 99000,
                },
            )
            assert listing.status_code == 201, listing.text

            create = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer,
                json={
                    "title": f"Cebu portal E2E {suffix}",
                    "description": "P3-07 frontend-pc flow",
                    "category_schema_id": cat_id,
                    "portal_key": "cebu",
                },
            )
            assert create.status_code == 201, create.text
            request_id = create.json()["id"]
            assert create.json()["portal_key"] == "cebu"

            detail = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_id}",
                headers=buyer,
            )
            assert detail.status_code == 200
            assert detail.json()["status"] == "draft"

            pub = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/publish",
                headers=buyer,
            )
            assert pub.status_code == 200, pub.text
            assert pub.json()["status"] == "published"

            candidates = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_id}/supplier-candidates",
                headers=buyer,
            )
            assert candidates.status_code == 200
            assert candidates.json()["total"] >= 1

            offer = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers",
                headers=supplier,
                json={
                    "supplier_company_id": str(supplier_company_id),
                    "supplier_listing_id": listing.json()["id"],
                    "price_minor": 99000,
                    "currency": "USD",
                },
            )
            assert offer.status_code == 201, offer.text

            award = await client.post(
                f"/api/v1/commerce/offers/{offer.json()['id']}/award",
                headers=admin,
            )
            assert award.status_code == 200, award.text
            order_id = award.json()["id"]

            orders = await client.get("/api/v1/commerce/orders", headers=buyer)
            assert orders.status_code == 200
            order_ids = {o["id"] for o in orders.json()["items"]}
            assert order_id in order_ids

            list_after = await client.get("/api/v1/commerce/procurement-requests", headers=buyer)
            assert list_after.status_code == 200
            listed_ids = {i["id"] for i in list_after.json()["items"]}
            assert request_id in listed_ids

    asyncio.run(_run())

"""IP2-09: commerce settlement and reconciliation."""
import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.costing import ExchangeRate
from decimal import Decimal


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_funding_settlement_and_reconciliation():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        async with async_session_factory() as db:
            today = date.today()
            existing = (
                await db.execute(
                    __import__("sqlalchemy").select(ExchangeRate).where(
                        ExchangeRate.base == "EUR",
                        ExchangeRate.quote == "USD",
                        ExchangeRate.as_of == today,
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(
                    ExchangeRate(
                        base="EUR", quote="USD", rate=Decimal("1.1"), as_of=today
                    )
                )
                await db.commit()

        order_id, buyer, _, _ = await _setup_awarded_order()
        admin = await _admin_headers()
        async with _client() as client:
            intent = await client.post(
                f"/api/v1/commerce/orders/{order_id}/payment-intent",
                headers=buyer,
                json={"psp_provider": "stripe"},
            )
            assert intent.status_code == 201, intent.text

            funded = await client.post(
                f"/api/v1/commerce/orders/{order_id}/confirm-funding",
                headers=admin,
                json={"external_ref": f"WIRE-{uuid.uuid4().hex[:8]}"},
            )
            assert funded.status_code == 200, funded.text
            assert funded.json()["status"] == "funded"
            settlement_id = funded.json()["id"]

            settled = await client.post(
                f"/api/v1/commerce/settlements/{settlement_id}/settle",
                headers=admin,
                json={"psp_settlement_ref": "STRIPE-SETTLE-001", "platform_fee_minor": 250},
            )
            assert settled.status_code == 200, settled.text
            assert settled.json()["status"] == "settled"

            now = datetime.now(timezone.utc)
            recon = await client.post(
                "/api/v1/commerce/reconciliation-runs",
                headers=admin,
                json={
                    "period_start": (now - timedelta(days=1)).isoformat(),
                    "period_end": (now + timedelta(days=1)).isoformat(),
                },
            )
            assert recon.status_code == 201, recon.text
            assert recon.json()["status"] == "completed"
            assert recon.json()["matched_count"] >= 1

            listings = await client.get("/api/v1/commerce/settlements", headers=admin)
            assert listings.status_code == 200
            assert any(s["id"] == settlement_id for s in listings.json()["items"])

    asyncio.run(_run())


def test_list_orders_for_supplier():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, _, supplier, _ = await _setup_awarded_order()
        async with _client() as client:
            orders = await client.get("/api/v1/commerce/orders", headers=supplier)
            assert orders.status_code == 200, orders.text
            assert any(o["id"] == order_id for o in orders.json()["items"])

    asyncio.run(_run())

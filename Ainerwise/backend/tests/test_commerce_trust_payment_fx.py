"""IP2-07: Trust profiles, reviews, risk flags, payment intents, FX."""
import asyncio
import uuid
from datetime import date
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.commerce import TrustProfile, TrustScoreEvent
from app.models.costing import ExchangeRate


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _complete_order(client: AsyncClient, order_id: str, buyer: dict, supplier: dict) -> None:
    delivery = await client.post(
        f"/api/v1/commerce/orders/{order_id}/deliveries",
        headers=supplier,
        json={"tracking_number": f"TRK-{uuid.uuid4().hex[:6]}"},
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
    done = await client.post(f"/api/v1/commerce/orders/{order_id}/complete", headers=buyer)
    assert done.status_code == 200, done.text


def test_trust_profile_updates_on_complete_and_review():
    async def _run():
        from tests.test_commerce_delivery_dispute import _admin_headers, _demo_headers, _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, admin = await _setup_awarded_order()
        async with _client() as client:
            order = await client.get(f"/api/v1/commerce/orders/{order_id}", headers=buyer)
            supplier_company_id = order.json()["supplier_company_id"]

            await _complete_order(client, order_id, buyer, supplier)

            trust = await client.get(
                f"/api/v1/commerce/trust-profiles/{supplier_company_id}",
                headers=buyer,
            )
            assert trust.status_code == 200, trust.text
            assert trust.json()["completed_orders"] >= 1
            assert trust.json()["trust_score"] >= 50

            review = await client.post(
                f"/api/v1/commerce/orders/{order_id}/reviews",
                headers=buyer,
                json={"rating": 5, "comment": "On time delivery"},
            )
            assert review.status_code == 201, review.text

            trust2 = await client.get(
                f"/api/v1/commerce/trust-profiles/{supplier_company_id}",
                headers=buyer,
            )
            assert trust2.json()["review_count"] >= 1
            assert float(trust2.json()["avg_rating"]) == 5.0

        async with async_session_factory() as db:
            profile = (
                await db.execute(
                    select(TrustProfile).where(TrustProfile.company_id == uuid.UUID(supplier_company_id))
                )
            ).scalar_one()
            events = list(
                (
                    await db.execute(
                        select(TrustScoreEvent)
                        .where(TrustScoreEvent.trust_profile_id == profile.id)
                        .order_by(TrustScoreEvent.created_at)
                    )
                ).scalars()
            )
            assert [event.event_type for event in events[-2:]] == [
                "ORDER_COMPLETED",
                "REVIEW_SUBMITTED",
            ]
            assert all(event.related_entity_id == uuid.UUID(order_id) for event in events[-2:])
            assert events[-1].created_by is not None

    asyncio.run(_run())


def test_dispute_creates_risk_flag():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order, _admin_headers

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        admin = await _admin_headers()
        async with _client() as client:
            delivery = await client.post(
                f"/api/v1/commerce/orders/{order_id}/deliveries",
                headers=supplier,
                json={"tracking_number": "TRK-RISK"},
            )
            assert delivery.status_code == 201
            delivery_id = delivery.json()["id"]
            for status in ("shipped", "in_transit", "delivered"):
                await client.patch(
                    f"/api/v1/commerce/deliveries/{delivery_id}/status",
                    headers=supplier,
                    json={"status": status},
                )

            dispute = await client.post(
                f"/api/v1/commerce/orders/{order_id}/disputes",
                headers=buyer,
                json={"reason_code": "damaged_goods", "description": "Box crushed"},
            )
            assert dispute.status_code == 201, dispute.text

            flags = await client.get("/api/v1/commerce/risk-flags?status=open", headers=admin)
            assert flags.status_code == 200, flags.text
            items = flags.json()["items"]
            assert any(f["subject_id"] == order_id for f in items)

            flag_id = next(f["id"] for f in items if f["subject_id"] == order_id)
            resolved = await client.post(
                f"/api/v1/commerce/risk-flags/{flag_id}/resolve",
                headers=admin,
                json={"resolution": "resolved"},
            )
            assert resolved.status_code == 200, resolved.text
            assert resolved.json()["status"] == "resolved"

        async with async_session_factory() as db:
            event = (
                await db.execute(
                    select(TrustScoreEvent)
                    .where(
                        TrustScoreEvent.related_entity_id == uuid.UUID(order_id),
                        TrustScoreEvent.event_type == "DISPUTE_OPENED",
                    )
                )
            ).scalar_one()
            assert event.reason == "Commerce dispute opened: damaged_goods"
            assert event.created_by is not None

    asyncio.run(_run())


def test_payment_intent_and_fx_quote():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        async with async_session_factory() as db:
            today = date.today()
            existing = (
                await db.execute(
                    select(ExchangeRate).where(
                        ExchangeRate.base == "EUR",
                        ExchangeRate.quote == "USD",
                        ExchangeRate.as_of == today,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                existing.rate = Decimal("1.10000000")
            else:
                db.add(
                    ExchangeRate(
                        base="EUR",
                        quote="USD",
                        rate=Decimal("1.10000000"),
                        as_of=today,
                    )
                )
            await db.commit()

        order_id, buyer, supplier, _ = await _setup_awarded_order()
        async with _client() as client:
            fx = await client.get(
                f"/api/v1/commerce/orders/{order_id}/fx-quote",
                headers=buyer,
                params={"quote_currency": "USD"},
            )
            assert fx.status_code == 200, fx.text
            assert fx.json()["quote_currency"] == "USD"
            assert fx.json()["quote_amount_minor"] > fx.json()["base_amount_minor"]

            intent = await client.post(
                f"/api/v1/commerce/orders/{order_id}/payment-intent",
                headers=buyer,
                json={"quote_currency": "USD", "psp_provider": "stripe"},
            )
            assert intent.status_code == 201, intent.text
            assert intent.json()["payment_plan_id"]
            assert intent.json()["quote_amount_minor"] is not None

            again = await client.get(f"/api/v1/commerce/orders/{order_id}/payment-intent", headers=buyer)
            assert again.status_code == 200
            assert again.json()["id"] == intent.json()["id"]

    asyncio.run(_run())

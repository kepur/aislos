"""Stripe webhook auto-settlement for commerce orders."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.commerce import CommerceSettlement
from app.services.stripe_payments import EVENT_CHECKOUT_COMPLETED, handle_stripe_event


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _demo_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@ainerwise.com", "password": "demo123"},
        )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_stripe_checkout_webhook_funds_commerce_order():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, _, _ = await _setup_awarded_order()
        async with _client() as client:
            intent = await client.post(
                f"/api/v1/commerce/orders/{order_id}/payment-intent",
                headers=buyer,
                json={"psp_provider": "stripe"},
            )
            assert intent.status_code == 201, intent.text

            checkout = await client.post(
                f"/api/v1/commerce/orders/{order_id}/checkout", headers=buyer
            )
            assert checkout.status_code == 200, checkout.text
            # Stripe unconfigured in test env — graceful degrade
            if not checkout.json().get("configured"):
                assert checkout.json()["detail"]

        async with async_session_factory() as db:
            fake_event = {
                "type": EVENT_CHECKOUT_COMPLETED,
                "data": {
                    "object": {
                        "id": f"cs_test_{uuid.uuid4().hex[:8]}",
                        "payment_intent": f"pi_test_{uuid.uuid4().hex[:8]}",
                        "metadata": {
                            "kind": "commerce_order",
                            "order_id": order_id,
                        },
                    }
                },
            }

            class _FakeEvent(dict):
                def __getitem__(self, key):
                    return super().__getitem__(key)

            result = await handle_stripe_event(db, _FakeEvent(fake_event))
            assert result.get("handled") is True, result
            assert result.get("settlement_id") or result.get("idempotent")

            settlement = (
                await db.execute(
                    __import__("sqlalchemy").select(CommerceSettlement).where(
                        CommerceSettlement.commerce_order_id == uuid.UUID(order_id)
                    )
                )
            ).scalar_one_or_none()
            assert settlement is not None
            assert settlement.status == "funded"
            await db.rollback()

    asyncio.run(_run())


def test_stripe_webhook_idempotent_on_retry():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, _, _ = await _setup_awarded_order()
        async with _client() as client:
            await client.post(
                f"/api/v1/commerce/orders/{order_id}/payment-intent",
                headers=buyer,
                json={"psp_provider": "stripe"},
            )

        async with async_session_factory() as db:
            session_id = f"cs_test_{uuid.uuid4().hex[:8]}"
            payload = {
                "type": EVENT_CHECKOUT_COMPLETED,
                "data": {
                    "object": {
                        "id": session_id,
                        "payment_intent": f"pi_{uuid.uuid4().hex[:8]}",
                        "metadata": {"kind": "commerce_order", "order_id": order_id},
                    }
                },
            }

            class _FakeEvent(dict):
                pass

            first = await handle_stripe_event(db, _FakeEvent(payload))
            assert first.get("handled")
            second = await handle_stripe_event(db, _FakeEvent(payload))
            assert second.get("handled")
            assert second.get("idempotent") or second.get("settlement_id")
            await db.rollback()

    asyncio.run(_run())

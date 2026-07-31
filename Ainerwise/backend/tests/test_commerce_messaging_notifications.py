"""IP2-08: commerce threads, in-app notifications."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.integration import IntegrationEvent
from sqlalchemy import select


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_award_creates_notifications_and_thread():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        async with _client() as client:
            notifs = await client.get("/api/v1/commerce/notifications", headers=buyer)
            assert notifs.status_code == 200, notifs.text
            assert notifs.json()["total"] >= 1
            assert any(n["event_type"] == "commerce.order.awarded" for n in notifs.json()["items"])

            supplier_notifs = await client.get("/api/v1/commerce/notifications", headers=supplier)
            assert supplier_notifs.json()["total"] >= 1
            assert any(
                n["event_type"] == "procurement.offer.awarded" for n in supplier_notifs.json()["items"]
            )

            thread = await client.get(f"/api/v1/commerce/orders/{order_id}/thread", headers=buyer)
            assert thread.status_code == 200, thread.text
            thread_id = thread.json()["id"]

            unread = await client.get("/api/v1/commerce/notifications/unread-count", headers=buyer)
            assert unread.json()["count"] >= 1

    asyncio.run(_run())


def test_thread_message_notifies_counterparty():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        async with _client() as client:
            thread = await client.get(f"/api/v1/commerce/orders/{order_id}/thread", headers=buyer)
            thread_id = thread.json()["id"]

            msg = await client.post(
                f"/api/v1/commerce/threads/{thread_id}/messages",
                headers=buyer,
                json={"body": "When will you ship?"},
            )
            assert msg.status_code == 201, msg.text

            supplier_notifs = await client.get(
                "/api/v1/commerce/notifications?status=unread",
                headers=supplier,
            )
            assert any(n["event_type"] == "commerce.message.received" for n in supplier_notifs.json()["items"])

            listing = await client.get(f"/api/v1/commerce/threads/{thread_id}/messages", headers=supplier)
            assert listing.status_code == 200
            assert listing.json()["total"] >= 1

    asyncio.run(_run())


def test_mark_notification_read():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        _, buyer, _, _ = await _setup_awarded_order()
        async with _client() as client:
            notifs = await client.get("/api/v1/commerce/notifications?status=unread", headers=buyer)
            nid = notifs.json()["items"][0]["id"]
            read = await client.post(f"/api/v1/commerce/notifications/{nid}/read", headers=buyer)
            assert read.status_code == 200
            assert read.json()["status"] == "read"

            all_read = await client.post("/api/v1/commerce/notifications/read-all", headers=buyer)
            assert all_read.status_code == 200
            count = await client.get("/api/v1/commerce/notifications/unread-count", headers=buyer)
            assert count.json()["count"] == 0

    asyncio.run(_run())


def test_dispute_queues_admin_telegram_and_notifies_party():
    async def _run():
        from tests.test_commerce_delivery_dispute import _setup_awarded_order

        await engine.dispose()
        order_id, buyer, supplier, _ = await _setup_awarded_order()
        async with _client() as client:
            delivery = await client.post(
                f"/api/v1/commerce/orders/{order_id}/deliveries",
                headers=supplier,
                json={"tracking_number": "MSG-01"},
            )
            delivery_id = delivery.json()["id"]
            for status in ("shipped", "in_transit", "delivered"):
                await client.patch(
                    f"/api/v1/commerce/deliveries/{delivery_id}/status",
                    headers=supplier,
                    json={"status": status},
                )

            before = await client.get("/api/v1/commerce/notifications/unread-count", headers=supplier)
            dispute = await client.post(
                f"/api/v1/commerce/orders/{order_id}/disputes",
                headers=buyer,
                json={"reason_code": "damaged_goods", "description": "Damaged"},
            )
            assert dispute.status_code == 201, dispute.text

            after = await client.get("/api/v1/commerce/notifications", headers=supplier)
            assert after.json()["total"] > before.json()["count"]
            assert any(n["event_type"] == "commerce.dispute.opened" for n in after.json()["items"])

        async with async_session_factory() as db:
            row = (
                await db.execute(
                    select(IntegrationEvent)
                    .where(IntegrationEvent.event_type == "commerce.dispute.opened")
                    .order_by(IntegrationEvent.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            assert row is not None
            assert row.target_channel == "telegram_admin"
            assert row.status == "pending"

    asyncio.run(_run())

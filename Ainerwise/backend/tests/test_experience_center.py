"""Experience Center (Portal 10): kiosk device auth, showroom tool surface,
the POS transition flow, and the constitution red lines."""
import asyncio
import hashlib
import secrets
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.agent import Agent, AgentGrant
from app.models.lifecycle import InventoryItem
from app.models.payment import LedgerEntry
from app.models.product import Product
from app.models.showroom import KioskDevice, ShowroomOrder, ShowroomSession, Store
from app.models.user import User

SHOWROOM_SLUGS = [
    "smart-home-expert", "solar-expert", "security-expert",
    "shopping-assistant", "design-consultant",
]


def test_portal_10_routes_registered():
    paths = {route.path for route in app.routes}
    for path in (
        "/api/v1/showroom/kiosk/bootstrap",
        "/api/v1/showroom/kiosk/sessions",
        "/api/v1/showroom/kiosk/sessions/{session_id}",
        "/api/v1/showroom/kiosk/sessions/{session_id}/messages",
        "/api/v1/showroom/kiosk/products",
        "/api/v1/showroom/kiosk/products/compare",
        "/api/v1/showroom/kiosk/products/{product_id}/stock",
        "/api/v1/showroom/kiosk/orders",
        "/api/v1/showroom/kiosk/leads",
        "/api/v1/showroom/kiosk/chat",
        "/api/v1/showroom/kiosk/voice-config",
        "/api/v1/showroom/kiosk/realtime-tool-call",
        "/api/v1/admin/showroom/stores",
        "/api/v1/admin/showroom/devices",
        "/api/v1/admin/showroom/devices/{device_id}/rotate-token",
        "/api/v1/admin/showroom/sessions",
        "/api/v1/admin/showroom/orders",
        "/api/v1/admin/showroom/orders/{order_id}/confirm",
    ):
        assert path in paths, path


def test_showroom_personas_seeded_and_payment_never_granted():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            for slug in SHOWROOM_SLUGS:
                agent = (
                    await db.execute(select(Agent).where(Agent.slug == slug))
                ).scalar_one()
                assert agent.vendor == "official"
                assert "showroom" in (agent.workflows_json or [])
                payment = (
                    await db.execute(
                        select(AgentGrant).where(
                            AgentGrant.agent_id == agent.id,
                            AgentGrant.scope == "payment",
                        )
                    )
                ).scalar_one()
                # Constitution Art.9 red line: kiosks may never move money.
                assert payment.granted is False

    asyncio.run(_run())


async def _make_device(db, *, agent_slug: str = "shopping-assistant") -> tuple[KioskDevice, str]:
    suffix = uuid.uuid4().hex[:8]
    store = Store(name=f"EC Test Store {suffix}", city="Belgrade", country="RS")
    db.add(store)
    await db.flush()
    token = secrets.token_urlsafe(32)
    device = KioskDevice(
        store_id=store.id, name=f"kiosk-{suffix}",
        device_token_hash=hashlib.sha256(token.encode()).hexdigest(),
        agent_slug=agent_slug, default_lang="sr", voice_mode="text",
    )
    db.add(device)
    await db.commit()
    return device, token


def test_kiosk_walkthrough_to_pos_confirmation():
    """Bootstrap -> session -> tools -> order draft -> counter confirmation."""

    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:8]
        async with async_session_factory() as db:
            device, token = await _make_device(db)
            product = Product(
                name=f"EC Motor Valve {suffix}", slug=f"ec-valve-{suffix}",
                list_price=80.0, currency="EUR", status="active",
                specs_json={"voltage": "230V", "torque": "10Nm"},
            )
            product_b = Product(
                name=f"EC Motor Valve Pro {suffix}", slug=f"ec-valve-pro-{suffix}",
                list_price=120.0, currency="EUR", status="active",
                specs_json={"voltage": "24V", "torque": "20Nm"},
            )
            db.add_all([product, product_b])
            await db.flush()
            inventory = InventoryItem(
                product_id=product.id, name=product.name,
                location="store", quantity=5, reserved_quantity=0,
            )
            db.add(inventory)
            await db.commit()
            product_id, product_b_id = product.id, product_b.id
            inventory_id = inventory.id

        headers = {"X-Kiosk-Token": token}
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # No/invalid token is rejected — the tablet is a dumb terminal.
            r = await client.get("/api/v1/showroom/kiosk/bootstrap")
            assert r.status_code == 401
            r = await client.get(
                "/api/v1/showroom/kiosk/bootstrap", headers={"X-Kiosk-Token": "wrong"}
            )
            assert r.status_code == 401

            r = await client.get("/api/v1/showroom/kiosk/bootstrap", headers=headers)
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["agent"]["slug"] == "shopping-assistant"
            # AI Act Art.50 — self-disclosure is part of the API contract.
            assert "AI" in body["ai_disclosure"]

            r = await client.post(
                "/api/v1/showroom/kiosk/sessions", json={"lang": "sr"}, headers=headers
            )
            assert r.status_code == 201, r.text
            session_id = r.json()["id"]

            r = await client.get(
                f"/api/v1/showroom/kiosk/products?q={suffix}",
                headers=headers,
            )
            assert r.status_code == 200
            assert len(r.json()["items"]) == 2

            r = await client.post(
                "/api/v1/showroom/kiosk/products/compare",
                json={"session_id": session_id,
                      "product_ids": [str(product_id), str(product_b_id)]},
                headers=headers,
            )
            assert r.status_code == 200, r.text
            spec_keys = {row["key"] for row in r.json()["spec_rows"]}
            assert {"voltage", "torque"} <= spec_keys

            r = await client.get(
                f"/api/v1/showroom/kiosk/products/{product_id}/stock", headers=headers
            )
            assert r.status_code == 200
            assert r.json()["available"] == 5

            r = await client.post(
                "/api/v1/showroom/kiosk/orders",
                json={"session_id": session_id,
                      "items": [{"product_id": str(product_id), "qty": 2}]},
                headers=headers,
            )
            assert r.status_code == 201, r.text
            order = r.json()
            assert order["total"] == 160.0
            assert order["status"] == "draft"
            assert len(order["pickup_code"]) == 6
            order_id = order["id"]

            r = await client.post(
                f"/api/v1/showroom/kiosk/sessions/{session_id}/messages",
                json={"role": "user", "content": "Uzecu jedan, hvala"},
                headers=headers,
            )
            assert r.status_code == 201

        # Counter confirmation (admin): POS card paid -> stock + ledger + outcome.
        async with async_session_factory() as db:
            admin = User(
                email=f"ec-admin-{suffix}@test.local", password_hash="unused", role="admin"
            )
            db.add(admin)
            await db.commit()

            from app.api.v1.endpoints.showroom import confirm_order

            result = await confirm_order(uuid.UUID(order_id), db, admin)
            assert result["status"] == "paid_in_store"

        async with async_session_factory() as db:
            refreshed_order = await db.get(ShowroomOrder, uuid.UUID(order_id))
            assert refreshed_order.status == "paid_in_store"

            refreshed_inventory = await db.get(InventoryItem, inventory_id)
            assert refreshed_inventory.quantity == 3

            entries = (
                await db.execute(
                    select(LedgerEntry).where(
                        LedgerEntry.memo == f"Showroom order {refreshed_order.pickup_code}"
                    )
                )
            ).scalars().all()
            assert {e.account for e in entries} == {"bank:pos_store", "platform:revenue"}
            assert sum(e.amount for e in entries if e.direction == "debit") == sum(
                e.amount for e in entries if e.direction == "credit"
            )

            session = await db.get(ShowroomSession, uuid.UUID(session_id))
            assert session.outcome == "purchase"
            assert str(product_id) in (session.products_viewed_json or [])

    asyncio.run(_run())


def test_paused_persona_blocks_kiosk_tools():
    """Pausing the agent in the Console pauses the tablet (one employee)."""

    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            device, token = await _make_device(db, agent_slug="solar-expert")
            agent = (
                await db.execute(select(Agent).where(Agent.slug == "solar-expert"))
            ).scalar_one()
            agent.status = "paused"
            db.add(agent)
            await db.commit()
            agent_id = agent.id

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get(
                    "/api/v1/showroom/kiosk/products?q=valve",
                    headers={"X-Kiosk-Token": token},
                )
                assert r.status_code == 403
                assert "paused" in r.json()["detail"]
        finally:
            async with async_session_factory() as db:
                agent = await db.get(Agent, agent_id)
                agent.status = "active"
                db.add(agent)
                await db.commit()

    asyncio.run(_run())


def test_revoked_device_token_is_rejected():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            device, token = await _make_device(db)
            device.status = "revoked"
            db.add(device)
            await db.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get(
                "/api/v1/showroom/kiosk/bootstrap", headers={"X-Kiosk-Token": token}
            )
            assert r.status_code == 403

    asyncio.run(_run())

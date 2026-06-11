"""EC-0 Experience Center tests: device auth, persona governance, and the
full walk-up loop (bootstrap -> session -> chat with persona attribution ->
order -> POS confirm with ledger). Runs live against the in-container stack."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text as sql_text

from app.db.session import async_session_factory, engine
from app.main import app


def test_showroom_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/showroom/kiosk/bootstrap",
        "/api/v1/showroom/kiosk/sessions",
        "/api/v1/showroom/kiosk/chat",
        "/api/v1/showroom/kiosk/voice-config",
        "/api/v1/showroom/kiosk/realtime-tool-call",
        "/api/v1/showroom/kiosk/orders",
        "/api/v1/showroom/kiosk/leads",
        "/api/v1/admin/showroom/stores",
        "/api/v1/admin/showroom/devices",
        "/api/v1/admin/showroom/orders/{order_id}/confirm",
    ):
        assert p in paths, p


def test_showroom_personas_governed():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.models.agent import Agent, AgentGrant

            personas = (
                await db.execute(
                    select(Agent).where(Agent.slug.in_([
                        "smart-home-expert", "solar-expert", "security-expert",
                        "shopping-assistant", "design-consultant",
                    ]))
                )
            ).scalars().all()
            assert len(personas) == 5
            for persona in personas:
                assert "showroom" in (persona.workflows_json or []), persona.slug
                payment = (
                    await db.execute(
                        select(AgentGrant).where(
                            AgentGrant.agent_id == persona.id,
                            AgentGrant.scope == "payment",
                            AgentGrant.granted.is_(True),
                        )
                    )
                ).scalars().first()
                assert payment is None, f"{persona.slug} must never hold payment"

    asyncio.run(_run())


def test_kiosk_full_walkup_loop():
    async def _run():
        await engine.dispose()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=120) as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@ainerwise.com", "password": "admin123456"},
            )
            assert login.status_code == 200, login.text
            admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            # 1. store + device (token returned exactly once)
            store = (
                await client.post("/api/v1/admin/showroom/stores", headers=admin_headers,
                                  json={"name": "EC-0 test store", "city": "Belgrade",
                                        "country": "Serbia"})
            ).json()
            device_resp = await client.post(
                "/api/v1/admin/showroom/devices", headers=admin_headers,
                json={"store_id": store["id"], "name": "test tablet 1",
                      "agent_slug": "shopping-assistant", "default_lang": "en"},
            )
            assert device_resp.status_code == 201, device_resp.text
            device = device_resp.json()
            kiosk_headers = {"X-Kiosk-Token": device["device_token"]}

            # 2. bootstrap: persona claim + non-overridable AI disclosure
            bad = await client.get("/api/v1/showroom/kiosk/bootstrap",
                                   headers={"X-Kiosk-Token": "wrong"})
            assert bad.status_code == 401
            boot = (
                await client.get("/api/v1/showroom/kiosk/bootstrap", headers=kiosk_headers)
            ).json()
            assert boot["agent"]["slug"] == "shopping-assistant"
            assert "AI" in boot["ai_disclosure"]

            # 3. voice-config degrades to text mode when unconfigured
            voice = (
                await client.get("/api/v1/showroom/kiosk/voice-config", headers=kiosk_headers)
            ).json()
            assert voice["enabled"] is False and voice["mode"] == "text"

            # 4. session + chat (live orchestrator; persona attribution)
            session = (
                await client.post("/api/v1/showroom/kiosk/sessions", headers=kiosk_headers,
                                  json={"lang": "en"})
            ).json()
            chat = (
                await client.post("/api/v1/showroom/kiosk/chat", headers=kiosk_headers,
                                  json={"session_id": session["id"],
                                        "message": "Do you have smart relays or valves?"})
            ).json()
            assert chat["ai_disclosure"]
            assert chat["answer"] or chat["fallback_products"] is not None

            # 5. order draft with a real product -> pickup code
            async with async_session_factory() as db:
                from app.models.product import Product

                product = (await db.execute(select(Product).limit(1))).scalars().first()
                assert product is not None, "seeded products required"
                product_id = str(product.id)
            order_resp = await client.post(
                "/api/v1/showroom/kiosk/orders", headers=kiosk_headers,
                json={"session_id": session["id"],
                      "items": [{"product_id": product_id, "qty": 1}]},
            )
            assert order_resp.status_code == 201, order_resp.text
            order = order_resp.json()
            assert len(order["pickup_code"]) == 6

            # 6. POS confirmation: ledger balanced, session closed as purchase
            confirm = await client.post(
                f"/api/v1/admin/showroom/orders/{order['id']}/confirm", headers=admin_headers
            )
            assert confirm.status_code == 200, confirm.text
            assert confirm.json()["status"] == "paid_in_store"

        async with async_session_factory() as db:
            from app.models.ai import Conversation
            from app.models.lifecycle import StockMovement
            from app.models.payment import LedgerEntry
            from app.models.showroom import KioskDevice, ShowroomOrder, ShowroomSession, Store

            ledger = (
                await db.execute(
                    select(LedgerEntry).where(
                        LedgerEntry.memo == f"Showroom order {order['pickup_code']}"
                    )
                )
            ).scalars().all()
            assert len(ledger) == 2
            assert {e.direction for e in ledger} == {"debit", "credit"}
            assert ledger[0].amount == ledger[1].amount

            refreshed_session = await db.get(ShowroomSession, uuid.UUID(session["id"]))
            assert refreshed_session.outcome == "purchase"

            # persona attribution on the live run
            runs = (
                await db.execute(
                    sql_text(
                        "SELECT agent_slug FROM ai.agent_runs WHERE conversation_id = :cid"
                    ),
                    {"cid": session["conversation_id"]},
                )
            ).scalars().all()
            if runs:  # orchestrator reachable in-container
                assert set(runs) == {"shopping-assistant"}

            # cleanup (FK order, explicit flushes)
            for entry in ledger:
                await db.delete(entry)
            movements = (
                await db.execute(
                    select(StockMovement).where(
                        StockMovement.reference == f"showroom:{order['pickup_code']}"
                    )
                )
            ).scalars().all()
            for movement in movements:
                await db.delete(movement)
            await db.flush()
            await db.execute(
                sql_text("DELETE FROM ai.agent_runs WHERE conversation_id = :cid"),
                {"cid": session["conversation_id"]},
            )
            order_row = await db.get(ShowroomOrder, uuid.UUID(order["id"]))
            await db.delete(order_row)
            await db.flush()
            await db.delete(refreshed_session)
            await db.flush()
            conversation = await db.get(Conversation, uuid.UUID(session["conversation_id"]))
            if conversation:
                await db.delete(conversation)
            device_row = await db.get(KioskDevice, uuid.UUID(device["id"]))
            await db.delete(device_row)
            await db.flush()
            store_row = await db.get(Store, uuid.UUID(store["id"]))
            await db.delete(store_row)
            await db.commit()

    asyncio.run(_run())

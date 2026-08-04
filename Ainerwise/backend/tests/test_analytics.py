"""P2 analytics spine.

The point of these tests is that the numbers can be trusted: a retry must not
double-count revenue, visitor identifiers must not be reversible, and the
funnel must not silently present a >100% conversion as if it were normal.
"""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from app.services.analytics import hash_actor
from tests.route_utils import registered_route_paths


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(email: str, password: str) -> dict:
    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_analytics_routes_registered():
    paths = registered_route_paths(app)
    for p in (
        "/api/v1/analytics/events",
        "/api/v1/analytics/funnel",
        "/api/v1/analytics/sku",
        "/api/v1/analytics/channel",
        "/api/v1/analytics/creative",
    ):
        assert p in paths, p


def test_actor_hash_is_one_way_and_stable():
    raw = "buyer@example.com"
    hashed = hash_actor(raw)
    assert hashed and hashed != raw
    assert raw not in hashed
    assert len(hashed) == 64
    assert hash_actor(raw) == hashed          # stable, so a person can be counted once
    assert hash_actor("someone-else") != hashed
    assert hash_actor(None) is None


def test_ingest_requires_source_app_and_known_event_types():
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")

        async with _client() as client:
            # Without source_app cross-project attribution is impossible.
            missing = await client.post(
                "/api/v1/analytics/events",
                headers=seller,
                json={"events": [{"event_type": "listing.view"}]},
            )
            assert missing.status_code == 422

            # An unknown type would silently pollute the funnel.
            unknown = await client.post(
                "/api/v1/analytics/events",
                headers=seller,
                json={"source_app": "test", "events": [{"event_type": "made.up"}]},
            )
            assert unknown.status_code == 422

    asyncio.run(_run())


def test_replayed_events_do_not_double_count():
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        key = f"test-idem-{uuid.uuid4().hex[:10]}"
        body = {
            "source_app": "test-suite",
            "events": [{"event_type": "deal.completed", "value_minor": 1000, "idempotency_key": key}],
        }

        async with _client() as client:
            first = await client.post("/api/v1/analytics/events", headers=seller, json=body)
            assert first.status_code == 202, first.text
            assert first.json()["accepted"] == 1

            replay = await client.post("/api/v1/analytics/events", headers=seller, json=body)
            assert replay.status_code == 202
            assert replay.json()["accepted"] == 0
            assert replay.json()["duplicates"] == 1

    asyncio.run(_run())


def test_creative_ctr_is_measured_per_variant():
    """The question aggregate campaign counters cannot answer."""
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        admin = await _headers("admin@ainerwise.com", "admin123456")
        run = uuid.uuid4().hex[:8]

        async with _client() as client:
            good = await client.post(
                "/api/v1/analytics/creatives",
                headers=seller,
                json={"variant_label": f"good-{run}", "image_url": "https://x/good.jpg"},
            )
            poor = await client.post(
                "/api/v1/analytics/creatives",
                headers=seller,
                json={"variant_label": f"poor-{run}", "image_url": "https://x/poor.jpg"},
            )
            assert good.status_code == 201 and poor.status_code == 201
            good_id, poor_id = good.json()["id"], poor.json()["id"]

            events = (
                [{"event_type": "creative.impression", "creative_id": good_id} for _ in range(50)]
                + [{"event_type": "creative.click", "creative_id": good_id} for _ in range(10)]
                + [{"event_type": "creative.impression", "creative_id": poor_id} for _ in range(50)]
                + [{"event_type": "creative.click", "creative_id": poor_id} for _ in range(1)]
            )
            posted = await client.post(
                "/api/v1/analytics/events",
                headers=seller,
                json={"source_app": "test-suite", "events": events},
            )
            assert posted.status_code == 202, posted.text

            report = await client.get("/api/v1/analytics/creative?days=1", headers=admin)
            assert report.status_code == 200
            by_id = {r["creative_id"]: r for r in report.json()["items"]}
            assert by_id[good_id]["ctr_pct"] == 20.0
            assert by_id[poor_id]["ctr_pct"] == 2.0
            # Best performer must sort first — that is how a human uses this.
            ordered = [r["creative_id"] for r in report.json()["items"]]
            assert ordered.index(good_id) < ordered.index(poor_id)

    asyncio.run(_run())


def test_funnel_flags_conversion_above_one_hundred_percent():
    """Sales arriving without our upstream steps are real, and must be labelled
    rather than shown as if the arithmetic were broken."""
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        admin = await _headers("admin@ainerwise.com", "admin123456")
        portal = f"test-portal-{uuid.uuid4().hex[:8]}"

        async with _client() as client:
            await client.post(
                "/api/v1/analytics/events",
                headers=seller,
                json={
                    "source_app": "test-suite",
                    "events": [
                        {"event_type": "listing.view", "portal_key": portal},
                        {"event_type": "deal.completed", "portal_key": portal, "value_minor": 100},
                        {"event_type": "deal.completed", "portal_key": portal, "value_minor": 100},
                    ],
                },
            )

            report = await client.get(
                f"/api/v1/analytics/funnel?days=1&portal_key={portal}", headers=admin
            )
            steps = {s["step"]: s for s in report.json()["steps"]}
            assert steps["listing.view"]["count"] == 1
            assert steps["deal.completed"]["count"] == 2
            assert steps["deal.completed"]["exceeds_previous_step"] is True
            assert steps["listing.view"]["exceeds_previous_step"] is False

    asyncio.run(_run())


def test_secondhand_flow_feeds_the_spine():
    """Browsing, asking for an address and completing a pickup must all land
    in the funnel without the caller doing anything special."""
    async def _run():
        await engine.dispose()
        seller = await _headers("supplier@example.com", "supplier123")
        buyer = await _headers("demo@ainerwise.com", "demo123")
        admin = await _headers("admin@ainerwise.com", "admin123456")
        marker = f"2Hands Test AN {uuid.uuid4().hex[:6]}"

        async with _client() as client:
            listing = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={"title": marker, "price_minor": 20000, "condition_grade": "B"},
            )
            assert listing.status_code == 201, listing.text
            listing_id = listing.json()["id"]

            await client.get(f"/api/v1/secondhand/listings/{listing_id}?session_id=t1")
            request = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/disclosure-request", headers=buyer, json={}
            )
            await client.post(
                f"/api/v1/secondhand/disclosures/{request.json()['id']}/grant",
                headers=seller,
                json={"fields": ["address"]},
            )
            deal = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/reserve",
                headers=buyer,
                json={"agreed_price_minor": 18000},
            )
            await client.post(
                f"/api/v1/secondhand/deals/{deal.json()['id']}/confirm-pickup",
                headers=buyer,
                json={"payment_method": "CASH"},
            )

            report = await client.get("/api/v1/analytics/sku?days=1&limit=200", headers=admin)
            row = next((r for r in report.json()["items"] if r["listing_id"] == listing_id), None)
            assert row is not None, "the sale never reached the analytics spine"
            assert row["views"] >= 1
            assert row["leads"] >= 1
            assert row["sold"] == 1
            assert row["revenue_minor"] == 18000

    asyncio.run(_run())

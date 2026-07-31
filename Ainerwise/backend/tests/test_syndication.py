"""P1 channel syndication.

Two things matter here beyond the happy path:
  * a seller's pickup address must never reach an external channel, and
  * selling unique stock must take the item down everywhere it was published.
"""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from app.services.syndication import (
    ChannelPayload,
    get_driver,
    render_assisted_pack,
    render_feed_item,
)
from tests.route_utils import registered_route_paths

SECRET_ADDRESS = "Tajna Adresa 99, stan 5"
SECRET_PHONE = "+381 60 5550001"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(email: str, password: str) -> dict:
    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_syndication_routes_registered():
    paths = registered_route_paths(app)
    for p in (
        "/api/v1/syndication/channels",
        "/api/v1/syndication/listings/{listing_id}/publish",
        "/api/v1/syndication/listings/{listing_id}/delist",
        "/api/v1/syndication/queue",
        "/api/v1/syndication/feed/{feed_slug}.xml",
    ):
        assert p in paths, p


def test_driver_registry_never_silently_automates():
    """`api`/`agent` need a per-channel integration; until then, stay assisted."""
    assert get_driver("feed", "olx").kind == "feed"
    assert get_driver("assisted", "kp").kind == "assisted"
    # No API agreement registered yet -> must not pretend it can post.
    assert get_driver("api", "kp").kind == "assisted"
    assert get_driver("agent", "kp").kind == "assisted"
    assert get_driver("nonsense", "kp").kind == "assisted"


def test_payload_hash_is_stable_and_change_sensitive():
    base = dict(title="X", description="d", price_minor=100, currency="EUR")
    a = ChannelPayload(**base)
    b = ChannelPayload(**base)
    assert a.content_hash() == b.content_hash()
    c = ChannelPayload(**{**base, "price_minor": 200})
    assert a.content_hash() != c.content_hash()


def test_renderers_only_emit_coarse_location():
    payload = ChannelPayload(
        title="Laptop",
        description="Good",
        price_minor=50000,
        currency="EUR",
        location={"country": "RS", "city": "Beograd", "area": "Vračar"},
    )
    for rendered in (render_feed_item(payload), render_assisted_pack(payload, channel="olx")):
        assert "Beograd" in rendered
        assert SECRET_ADDRESS not in rendered
        assert SECRET_PHONE not in rendered


def test_publish_hides_address_and_delists_on_sale():
    async def _run():
        await engine.dispose()
        admin = await _headers("admin@ainerwise.com", "admin123456")
        seller = await _headers("supplier@example.com", "supplier123")
        buyer = await _headers("demo@ainerwise.com", "demo123")
        marker = f"2Hands Test SYN {uuid.uuid4().hex[:6]}"
        slug = f"test-feed-{uuid.uuid4().hex[:8]}"

        async with _client() as client:
            # Channel names deliberately differ from the listing marker so the
            # feed assertions below cannot be satisfied by the feed's own title.
            feed_channel = await client.post(
                "/api/v1/syndication/channels",
                headers=admin,
                json={"channel": "testfeed", "name": "Feed channel", "driver_kind": "feed", "feed_slug": slug},
            )
            assert feed_channel.status_code == 201, feed_channel.text
            assert "credentials_json" not in feed_channel.json()

            assisted_channel = await client.post(
                "/api/v1/syndication/channels",
                headers=admin,
                json={"channel": "testassisted", "name": "Assisted channel", "driver_kind": "assisted"},
            )
            assert assisted_channel.status_code == 201
            account_ids = [feed_channel.json()["id"], assisted_channel.json()["id"]]

            listing = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={
                    "title": marker,
                    "price_minor": 30000,
                    "condition_grade": "B",
                    "pickup_country": "RS",
                    "pickup_city": "Beograd",
                    "pickup_address": SECRET_ADDRESS,
                    "contact_phone": SECRET_PHONE,
                },
            )
            assert listing.status_code == 201, listing.text
            listing_id = listing.json()["id"]

            published = await client.post(
                f"/api/v1/syndication/listings/{listing_id}/publish",
                headers=seller,
                json={"account_ids": account_ids},
            )
            assert published.status_code == 200, published.text
            # The whole syndicated payload must be free of restricted data.
            assert SECRET_ADDRESS not in published.text
            assert SECRET_PHONE not in published.text

            by_channel = {i["channel"]: i for i in published.json()["items"]}
            assert by_channel["testfeed"]["status"] == "published"
            assert by_channel["testassisted"]["status"] == "pending_review"

            # Unchanged content is not pushed again.
            again = await client.post(
                f"/api/v1/syndication/listings/{listing_id}/publish",
                headers=seller,
                json={"account_ids": account_ids},
            )
            assert any(i.get("skipped") for i in again.json()["items"])

            feed = await client.get(f"/api/v1/syndication/feed/{slug}.xml")
            assert feed.status_code == 200
            assert marker in feed.text
            assert SECRET_ADDRESS not in feed.text

            # Selling unique stock takes it down everywhere.
            request = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/disclosure-request", headers=buyer, json={}
            )
            await client.post(
                f"/api/v1/secondhand/disclosures/{request.json()['id']}/grant",
                headers=seller,
                json={"fields": ["address"]},
            )
            deal = await client.post(
                f"/api/v1/secondhand/listings/{listing_id}/reserve", headers=buyer, json={}
            )
            done = await client.post(
                f"/api/v1/secondhand/deals/{deal.json()['id']}/confirm-pickup",
                headers=buyer,
                json={"payment_method": "CASH"},
            )
            assert done.status_code == 200, done.text

            status = await client.get(
                f"/api/v1/syndication/listings/{listing_id}/status", headers=seller
            )
            states = {i["channel"]: i["status"] for i in status.json()["items"]}
            # Automatable channel is gone; the manual one is queued for takedown
            # and must not still read as published.
            assert states["testfeed"] == "delisted"
            assert states["testassisted"] == "pending_takedown"

            queue = await client.get("/api/v1/syndication/queue", headers=seller)
            takedowns = [i for i in queue.json()["items"] if i["action"] == "take_down"]
            assert any(i["listing_title"] == marker for i in takedowns)

            # Operator confirms the manual removal.
            target = next(i for i in takedowns if i["listing_title"] == marker)
            confirmed = await client.post(
                f"/api/v1/syndication/channel-listings/{target['id']}/confirm-takedown", headers=seller
            )
            assert confirmed.json()["status"] == "delisted"

            gone = await client.get(f"/api/v1/syndication/feed/{slug}.xml")
            assert marker not in gone.text

    asyncio.run(_run())

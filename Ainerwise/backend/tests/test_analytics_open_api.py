"""Open ingestion keys and channel stats pull-back.

Two integrity properties matter most here:
  * a key cannot attribute events to another project, and
  * repeated stat readings must not re-count the same impressions.
"""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app
from app.services.syndication import StatsResult, get_driver


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(email: str, password: str) -> dict:
    async with _client() as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_drivers_report_missing_stats_instead_of_zeros():
    """Zeros would silently become a denominator and break every rate."""
    for kind in ("feed", "assisted"):
        stats = get_driver(kind, "somechannel").fetch_stats(account=None, external_id="x")
        assert isinstance(stats, StatsResult)
        assert stats.available is False
        assert stats.impressions is None
        assert stats.message


def test_api_key_binds_source_app_and_rejects_user_tokens():
    async def _run():
        await engine.dispose()
        admin = await _headers("admin@ainerwise.com", "admin123456")
        app_key = f"test-app-{uuid.uuid4().hex[:8]}"

        async with _client() as client:
            issued = await client.post(
                "/api/v1/analytics/clients",
                headers=admin,
                json={"name": "Test client", "source_app": app_key, "scopes": ["events:write"]},
            )
            assert issued.status_code == 201, issued.text
            secret = issued.json()["secret"]
            client_id = issued.json()["id"]
            key_headers = {"Authorization": f"Bearer {secret}"}

            # A client cannot claim to be another project.
            posted = await client.post(
                "/api/v1/analytics/ingest",
                headers=key_headers,
                json={"source_app": "somebody-else", "events": [{"event_type": "listing.view"}]},
            )
            assert posted.status_code == 202, posted.text
            assert posted.json()["source_app"] == app_key

            # A signed-in user token must not work as a machine key.
            as_user = await client.post(
                "/api/v1/analytics/ingest",
                headers=admin,
                json={"source_app": app_key, "events": [{"event_type": "listing.view"}]},
            )
            assert as_user.status_code == 401

            anonymous = await client.post(
                "/api/v1/analytics/ingest",
                json={"source_app": app_key, "events": [{"event_type": "listing.view"}]},
            )
            assert anonymous.status_code == 401

            # Revocation takes effect immediately.
            revoked = await client.post(f"/api/v1/analytics/clients/{client_id}/revoke", headers=admin)
            assert revoked.json()["status"] == "revoked"
            after = await client.post(
                "/api/v1/analytics/ingest",
                headers=key_headers,
                json={"source_app": app_key, "events": [{"event_type": "listing.view"}]},
            )
            assert after.status_code == 403

    asyncio.run(_run())


def test_scope_is_enforced():
    async def _run():
        await engine.dispose()
        admin = await _headers("admin@ainerwise.com", "admin123456")

        async with _client() as client:
            issued = await client.post(
                "/api/v1/analytics/clients",
                headers=admin,
                json={
                    "name": "Read only",
                    "source_app": f"test-ro-{uuid.uuid4().hex[:6]}",
                    "scopes": ["reports:read"],
                },
            )
            secret = issued.json()["secret"]
            blocked = await client.post(
                "/api/v1/analytics/ingest",
                headers={"Authorization": f"Bearer {secret}"},
                json={"source_app": "x", "events": [{"event_type": "listing.view"}]},
            )
            assert blocked.status_code == 403

    asyncio.run(_run())


def test_repeated_stat_readings_only_count_the_increase():
    """Channel counters are cumulative; re-reading must not re-count."""
    async def _run():
        await engine.dispose()
        admin = await _headers("admin@ainerwise.com", "admin123456")
        seller = await _headers("supplier@example.com", "supplier123")
        marker = f"2Hands Test STATS {uuid.uuid4().hex[:6]}"

        async with _client() as client:
            channel = await client.post(
                "/api/v1/syndication/channels",
                headers=admin,
                json={"channel": "testassisted", "name": "Assisted", "driver_kind": "assisted"},
            )
            account_id = channel.json()["id"]

            listing = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={"title": marker, "price_minor": 1000, "condition_grade": "B"},
            )
            listing_id = listing.json()["id"]

            published = await client.post(
                f"/api/v1/syndication/listings/{listing_id}/publish",
                headers=seller,
                json={"account_ids": [account_id]},
            )
            channel_listing_id = published.json()["items"][0]["id"]
            await client.post(
                f"/api/v1/syndication/channel-listings/{channel_listing_id}/external-ref",
                headers=seller,
                json={"external_id": "X-1", "mark_published": True},
            )

            first = await client.post(
                f"/api/v1/syndication/channel-listings/{channel_listing_id}/stats",
                headers=seller,
                json={"impressions": 100, "views": 40},
            )
            assert first.status_code == 200, first.text
            assert first.json()["events_emitted"] == 140

            # Same totals again -> nothing new.
            same = await client.post(
                f"/api/v1/syndication/channel-listings/{channel_listing_id}/stats",
                headers=seller,
                json={"impressions": 100, "views": 40},
            )
            assert same.json()["events_emitted"] == 0

            # Grown totals -> only the delta.
            grown = await client.post(
                f"/api/v1/syndication/channel-listings/{channel_listing_id}/stats",
                headers=seller,
                json={"impressions": 130, "views": 55},
            )
            assert grown.json()["events_emitted"] == 45

            # And the channel now has a denominator to convert against.
            report = await client.get("/api/v1/analytics/channel?days=1", headers=admin)
            row = next(
                (r for r in report.json()["items"] if r["channel_account_id"] == account_id), None
            )
            assert row is not None
            assert row["impressions"] == 130
            assert row["views"] == 55

    asyncio.run(_run())


def test_pull_stats_marks_channels_needing_manual_entry():
    async def _run():
        await engine.dispose()
        admin = await _headers("admin@ainerwise.com", "admin123456")
        seller = await _headers("supplier@example.com", "supplier123")
        marker = f"2Hands Test PULL {uuid.uuid4().hex[:6]}"

        async with _client() as client:
            channel = await client.post(
                "/api/v1/syndication/channels",
                headers=admin,
                json={"channel": "testassisted", "name": "Assisted", "driver_kind": "assisted"},
            )
            account_id = channel.json()["id"]
            listing = await client.post(
                "/api/v1/secondhand/listings",
                headers=seller,
                json={"title": marker, "price_minor": 1000, "condition_grade": "B"},
            )
            listing_id = listing.json()["id"]
            published = await client.post(
                f"/api/v1/syndication/listings/{listing_id}/publish",
                headers=seller,
                json={"account_ids": [account_id]},
            )
            await client.post(
                f"/api/v1/syndication/channel-listings/{published.json()['items'][0]['id']}/external-ref",
                headers=seller,
                json={"external_id": "X-2", "mark_published": True},
            )

            pulled = await client.post(
                f"/api/v1/syndication/listings/{listing_id}/pull-stats", headers=seller
            )
            assert pulled.status_code == 200, pulled.text
            row = pulled.json()["items"][0]
            assert row["available"] is False
            assert row["needs_manual_entry"] is True
            assert row["events_emitted"] == 0

    asyncio.run(_run())

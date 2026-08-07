import asyncio

from httpx import ASGITransport, AsyncClient

from app.db.session import engine
from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_marketplace_feed_country_market_mode_does_not_shadow_listing_origin():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            response = await client.get(
                "/api/v1/cebu-compat/marketplace/feed",
                params={
                    "page": 1,
                    "page_size": 20,
                    "sort": "rank",
                    "market_mode": "B2B",
                    "country": "RS",
                },
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert {"items", "total", "page", "page_size", "has_next"}.issubset(payload)

    asyncio.run(_run())


def test_marketplace_feed_supports_unified_product_surfaces():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            for surface in ("all", "official", "market", "enterprise_recycled", "personal_secondhand"):
                response = await client.get(
                    "/api/v1/cebu-compat/marketplace/feed",
                    params={"page": 1, "page_size": 5, "surface": surface, "country": "RS"},
                )
                assert response.status_code == 200, f"{surface}: {response.text}"
                assert isinstance(response.json()["items"], list)

    asyncio.run(_run())

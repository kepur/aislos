"""Tests for buyer portal lifecycle workspace endpoints (FI.5)."""
import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.route_utils import registered_route_paths


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_portal_routes_registered():
    paths = registered_route_paths(app)
    for sub in ("amc-contracts", "warranties", "monitoring-points", "reports", "tickets", "workspace"):
        assert f"/api/v1/portal/projects/{{project_id}}/{sub}" in paths, sub


def test_portal_requires_auth():
    async def _run():
        async with _client() as client:
            r = await client.get(
                "/api/v1/portal/projects/00000000-0000-0000-0000-000000000000/amc-contracts"
            )
        assert r.status_code == 401

    asyncio.run(_run())

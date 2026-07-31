import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.route_utils import registered_route_paths


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_health_check():
    async def _run():
        async with _client() as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    asyncio.run(_run())


def test_phase_5_routes_are_registered():
    paths = registered_route_paths(app)

    assert "/api/v1/ai-runs" in paths
    assert "/api/v1/integration-events" in paths
    assert "/api/v1/leads/{lead_id}/analyze" in paths

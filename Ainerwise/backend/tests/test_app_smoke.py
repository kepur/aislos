from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_phase_5_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/api/v1/ai-runs" in paths
    assert "/api/v1/integration-events" in paths
    assert "/api/v1/leads/{lead_id}/analyze" in paths

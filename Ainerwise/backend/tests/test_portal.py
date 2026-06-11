"""Tests for buyer portal lifecycle workspace endpoints (FI.5)."""
from fastapi.testclient import TestClient

from app.main import app


def test_portal_routes_registered():
    paths = {r.path for r in app.routes}
    for sub in ("amc-contracts", "warranties", "monitoring-points", "reports", "tickets", "workspace"):
        assert f"/api/v1/portal/projects/{{project_id}}/{sub}" in paths, sub


def test_portal_requires_auth():
    client = TestClient(app)
    r = client.get("/api/v1/portal/projects/00000000-0000-0000-0000-000000000000/amc-contracts")
    assert r.status_code in (401, 403)

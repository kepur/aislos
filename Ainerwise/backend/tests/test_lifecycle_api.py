"""Route registration tests for the lifecycle CRUD API (FI.2.12)."""
from app.main import app


def _paths() -> set[str]:
    return {route.path for route in app.routes}


def test_lifecycle_collection_routes_registered():
    paths = _paths()
    for resource in (
        "supplier-warranties",
        "customer-warranties",
        "amc-contracts",
        "monitoring-points",
        "inventory-items",
        "stock-movements",
        "maintenance-schedules",
        "calibration-records",
    ):
        assert f"/api/v1/{resource}" in paths, resource
        assert f"/api/v1/{resource}/{{id}}" in paths, resource


def test_stock_movements_have_no_update_route():
    methods = set()
    for route in app.routes:
        if route.path == "/api/v1/stock-movements/{id}":
            methods |= route.methods
    # append-only: GET + DELETE, but never PUT
    assert "PUT" not in methods
    assert "DELETE" in methods


def test_monitoring_points_full_crud():
    get_methods, item_methods = set(), set()
    for route in app.routes:
        if route.path == "/api/v1/monitoring-points":
            get_methods |= route.methods
        if route.path == "/api/v1/monitoring-points/{id}":
            item_methods |= route.methods
    assert {"GET", "POST"}.issubset(get_methods)
    assert {"GET", "PUT", "DELETE"}.issubset(item_methods)

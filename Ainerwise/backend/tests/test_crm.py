"""Tests for CRM batch: scorecard, renewal queue, dashboard, lead filters (FI.6.3-6.6)."""
import asyncio

from app.api.v1.endpoints.crm import _with_overall
from app.db.session import async_session_factory, engine
from app.main import app
from app.services import renewal_queue


def test_scorecard_overall_is_average_of_dimensions():
    payload = _with_overall({"quality": 5, "delivery": 4, "response": 3})
    assert payload["overall_score"] == 4.0


def test_scorecard_overall_skips_missing_dimensions():
    payload = _with_overall({"quality": 4, "delivery": None})
    assert payload["overall_score"] == 4.0
    empty = _with_overall({"notes": "x"})
    assert "overall_score" not in empty


def test_crm_and_dashboard_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/renewal-queue",
        "/api/v1/supplier-scorecards",
        "/api/v1/supplier-scorecards/{id}",
        "/api/v1/admin/lifecycle-dashboard",
    ):
        assert p in paths, p


def test_leads_list_accepts_crm_filter_params():
    # The admin leads list endpoint must declare the FI.6.3 filter/sort params.
    route = next(r for r in app.routes if r.path == "/api/v1/leads" and "GET" in getattr(r, "methods", set()))
    params = set(route.dependant.query_params and [p.name for p in route.dependant.query_params] or [])
    for expected in ("solution_line", "min_recurring_score", "compliance_risk", "amc_potential", "multi_site", "sort", "order"):
        assert expected in params, expected


def test_renewal_queue_returns_structure():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            res = await renewal_queue.build_renewal_queue(db, within_days=90)
        assert "total" in res and "counts" in res and "opportunities" in res
        assert isinstance(res["opportunities"], list)

    asyncio.run(_run())

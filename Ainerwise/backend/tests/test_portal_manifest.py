"""PF01: Portal Registry, Manifest API and fail-closed behaviour."""
from httpx import ASGITransport, AsyncClient

from app.core.portal_registry import PORTAL_REGISTRY, get_manifest, resolve_portal_key
from app.main import app

TARGET_PORTAL_MATRIX = {
    "consumer_pc": "pc",
    "consumer_h5": "h5",
    "customer_pc": "pc",
    "customer_h5": "h5",
    "cebu_buyer_pc": "pc",
    "cebu_buyer_h5": "h5",
    "supplier_pc": "pc",
    "supplier_h5": "h5",
    "partner_company_pc": "pc",
    "partner_company_h5": "h5",
    "marketing_pc": "admin",
    "marketing_h5": "h5",
    "field_worker_h5": "h5",
    "crew_lead_h5": "h5",
    "kiosk_h5": "h5",
}


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_registry_exposes_final_zero_loss_portal_matrix():
    assert {
        key: PORTAL_REGISTRY[key]["physical_frontend"] for key in TARGET_PORTAL_MATRIX
    } == TARGET_PORTAL_MATRIX
    for key in TARGET_PORTAL_MATRIX:
        manifest = get_manifest(key)
        assert manifest is not None
        assert manifest["portal_key"] == key
        assert manifest["home_route"] in manifest["route_allowlist"]


def test_pc_h5_experiences_have_distinct_manifests():
    for stem in (
        "consumer",
        "customer",
        "cebu_buyer",
        "supplier",
        "partner_company",
        "marketing",
    ):
        pc = get_manifest(f"{stem}_pc")
        h5 = get_manifest(f"{stem}_h5")
        assert pc is not None and h5 is not None
        assert pc["portal_key"] != h5["portal_key"]
        assert pc["physical_frontend"] != h5["physical_frontend"]
        assert pc["layout"] != h5["layout"]


def test_registry_covers_pc_h5_admin():
    fronts = {m["physical_frontend"] for m in PORTAL_REGISTRY.values()}
    assert fronts == {"pc", "h5", "admin"}
    h5_keys = {k for k, m in PORTAL_REGISTRY.items() if m["physical_frontend"] == "h5"}
    assert {"customer", "partner_company", "field_worker", "supplier", "kiosk", "cebu_buyer"} <= h5_keys
    assert "cebu" in PORTAL_REGISTRY
    admin_keys = {k for k, m in PORTAL_REGISTRY.items() if m["physical_frontend"] == "admin"}
    assert len(admin_keys) >= 15
    assert {
        "consumer_h5",
        "customer_pc",
        "partner_company_pc",
        "marketing_h5",
        "crew_lead_h5",
        "admin_cebu",
    } <= set(PORTAL_REGISTRY)


def test_h5_manifests_are_distinct():
    h5 = [
        PORTAL_REGISTRY[key]
        for key, frontend in TARGET_PORTAL_MATRIX.items()
        if frontend == "h5"
    ]
    home_routes = {m["home_route"] for m in h5}
    assert len(home_routes) == len(h5)


def test_field_worker_excludes_commercial_routes():
    fw = get_manifest("field_worker")
    assert fw is not None
    allow = " ".join(fw["route_allowlist"])
    assert "/partner" not in allow and "/supplier" not in allow
    assert "field_task.read_assigned" in fw["required_grants"]
    menus = fw["menu_keys"]
    assert "rfq" not in menus and "quotes" not in menus


def test_supplier_excludes_field_tasks():
    sup = get_manifest("supplier")
    assert sup is not None
    allow = " ".join(sup["route_allowlist"])
    assert "/field" not in allow
    assert "/commerce" in allow
    assert "field_task" not in " ".join(sup["required_grants"])
    assert "notifications" in sup["menu_keys"]


def test_partner_company_not_field_worker():
    pc = get_manifest("partner_company")
    fw = get_manifest("field_worker")
    assert pc["home_route"] != fw["home_route"]
    assert pc["layout"] != fw["layout"]


def test_legacy_partner_alias_resolves():
    assert resolve_portal_key("partner") == "partner_company"


def test_unknown_portal_fail_closed():
    assert get_manifest("forged_portal") is None
    assert resolve_portal_key("not_a_real_portal") is None


def test_marketing_portals_exclude_internal_delivery_documents_and_cases():
    for portal_key in ("marketing_pc", "admin_marketing"):
        routes = PORTAL_REGISTRY[portal_key]["route_allowlist"]
        assert not any(route.startswith("/documents") for route in routes)
        assert not any(route.startswith("/case-library") for route in routes)

    assert "/case-library/**" in PORTAL_REGISTRY["admin_knowledge"]["route_allowlist"]
    assert "/documents/**" in PORTAL_REGISTRY["admin_audit"]["route_allowlist"]


def test_manifest_api_list_and_get():
    import asyncio

    async def _run():
        async with _client() as client:
            h5 = await client.get("/api/v1/portal-manifests", params={"physical_frontend": "h5"})
            assert h5.status_code == 200
            assert h5.json()["total"] >= 5

            one = await client.get("/api/v1/portal-manifests/field_worker")
            assert one.status_code == 200
            assert one.json()["portal_key"] == "field_worker"

            legacy = await client.get("/api/v1/portal-manifests/resolve/partner")
            assert legacy.status_code == 200
            assert legacy.json()["portal_key"] == "partner_company"

            bad = await client.get("/api/v1/portal-manifests/unknown_portal_xyz")
            assert bad.status_code == 404

            forged = await client.get("/api/v1/portal-manifests/../../etc")
            assert forged.status_code == 404

    asyncio.run(_run())

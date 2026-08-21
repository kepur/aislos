"""Static Logical Portal registry and versioned manifests (PF01).

Manifests describe UX only — they do not grant permissions. Unknown portals
fail closed. Legacy ``NUXT_PUBLIC_PORTAL_MODE`` values remain mapped for migration.
"""
from __future__ import annotations

from typing import Any, Literal

PhysicalFrontend = Literal["pc", "h5", "admin"]

# version bumped when manifest shape or route allowlists change materially
MANIFEST_VERSION = 3


def _m(
    *,
    portal_key: str,
    physical_frontend: PhysicalFrontend,
    layout: str,
    home_route: str,
    theme_key: str,
    menu_keys: list[str],
    route_allowlist: list[str],
    required_grants: list[str],
    display_name: str,
    pwa_manifest_key: str | None = None,
    offline_policy_key: str | None = None,
    legacy_portal_mode: str | None = None,
    migration_note: str | None = None,
) -> dict[str, Any]:
    return {
        "portal_key": portal_key,
        "version": MANIFEST_VERSION,
        "physical_frontend": physical_frontend,
        "layout": layout,
        "home_route": home_route,
        "theme_key": theme_key,
        "menu_keys": menu_keys,
        "route_allowlist": route_allowlist,
        "required_grants": required_grants,
        "pwa_manifest_key": pwa_manifest_key,
        "offline_policy_key": offline_policy_key,
        "legacy_portal_mode": legacy_portal_mode,
        "migration_note": migration_note,
        "display_name": display_name,
    }


# --- PC logical portals -------------------------------------------------------

_PC_AISLOS = _m(
    portal_key="aislos",
    physical_frontend="pc",
    layout="marketing",
    home_route="/",
    theme_key="ainerwise-aislos",
    menu_keys=["solutions", "store", "developers", "procurement", "about"],
    route_allowlist=[
        "/", "/solutions/**", "/insights/**", "/procurement/**",
        # Unified catalogue: official products, supplier listings and
        # second-hand stock behind one route with a source filter.
        "/catalog", "/catalog/**",
        "/login", "/register", "/demo-login",
    ],
    required_grants=["portal.pc.aislos"],
    display_name="AISLOS Website",
    legacy_portal_mode="aislos",
)

_PC_STORE = _m(
    portal_key="store",
    physical_frontend="pc",
    layout="commerce",
    home_route="/products",
    theme_key="ainerwise-store",
    menu_keys=["catalog", "cart", "orders"],
    route_allowlist=["/store/**", "/products/**", "/catalog", "/catalog/**", "/login", "/register", "/demo-login"],
    required_grants=["portal.pc.store"],
    display_name="AISLOS Product Catalog",
    legacy_portal_mode="store",
)

_PC_DEVELOPER = _m(
    portal_key="developer",
    physical_frontend="pc",
    layout="developer",
    home_route="/developers",
    theme_key="ainerwise-developer",
    menu_keys=["docs", "marketplace", "agents"],
    route_allowlist=["/developers/**", "/marketplace/**", "/login", "/register", "/demo-login"],
    required_grants=["portal.pc.developer"],
    display_name="AISLOS Developer Portal",
    legacy_portal_mode="developer",
)

_PC_PROCUREMENT = _m(
    portal_key="procurement",
    physical_frontend="pc",
    layout="procurement",
    home_route="/procurement",
    theme_key="ainerwise-procurement",
    menu_keys=["projects", "workspace", "rfq"],
    route_allowlist=["/procurement/**", "/login", "/demo-login"],
    required_grants=["portal.pc.procurement"],
    display_name="Shared Procurement Workspace",
    migration_note="Served via Portal Policy (aislos / cebu) on frontend-pc",
)

_PC_CEBU = _m(
    portal_key="cebu",
    physical_frontend="pc",
    layout="procurement",
    home_route="/market",
    theme_key="cebu-procurement",
    menu_keys=["intents", "offers", "orders", "messages", "notifications"],
    route_allowlist=["/market/**", "/cebu/**", "/buyer/**", "/commerce/**", "/portal/**", "/catalog", "/catalog/**", "/login", "/demo-login"],
    required_grants=["portal.pc.cebu"],
    display_name="Cebu Procurement Portal",
    legacy_portal_mode="cebu",
    migration_note="Phase 3: Cebu brand experience on Core commerce API",
)

# 2Hands second-hand storefront. Public browsing needs no grant; selling and
# buyer/seller workspaces are guarded by the portal grant below.
_PC_SECONDHAND = _m(
    portal_key="secondhand",
    physical_frontend="pc",
    layout="secondhand",
    home_route="/",
    theme_key="2hands",
    menu_keys=["listings", "orders", "messages", "notifications"],
    route_allowlist=[
        "/",
        "/browse/**",
        "/item/**",
        "/sell/**",
        "/me/**",
        "/login",
        "/register",
        "/demo-login",
    ],
    required_grants=["portal.pc.secondhand"],
    display_name="2Hands Marketplace",
    migration_note="P0: second-hand storefront on Core commerce API (records-first, pickup-first)",
)

# --- H5 logical portals -------------------------------------------------------

_H5_CUSTOMER = _m(
    portal_key="customer",
    physical_frontend="h5",
    layout="customer",
    home_route="/",
    theme_key="ainerwise-customer",
    menu_keys=["products", "projects", "approvals", "assets", "tickets", "profile"],
    route_allowlist=["/", "/products/**", "/projects/**", "/portal/**", "/market/**", "/catalog", "/catalog/**", "/profile", "/access-denied", "/login"],
    required_grants=["portal.h5.customer"],
    pwa_manifest_key="customer",
    display_name="Customer Portal",
    legacy_portal_mode="customer",
)

_H5_PARTNER_COMPANY = _m(
    portal_key="partner_company",
    physical_frontend="h5",
    layout="partner",
    home_route="/partner",
    theme_key="ainerwise-partner",
    menu_keys=["rfq", "bids", "work_packages", "crews", "schedule", "performance"],
    route_allowlist=["/partner/**", "/profile", "/access-denied", "/login"],
    required_grants=["partner.rfq.read", "partner.work_package.read"],
    pwa_manifest_key="partner-company",
    display_name="Partner Company PWA",
    legacy_portal_mode="partner",
    migration_note="Legacy partner mode mixed company + worker — migrate to partner_company + field_worker",
)

_H5_FIELD_WORKER = _m(
    portal_key="field_worker",
    physical_frontend="h5",
    layout="field",
    home_route="/field/today",
    theme_key="ainerwise-field",
    menu_keys=["today", "tasks", "scan", "offline_queue", "profile"],
    route_allowlist=["/field/**", "/profile", "/access-denied", "/login"],
    required_grants=["field_task.read_assigned"],
    pwa_manifest_key="field-worker",
    offline_policy_key="field-v1",
    display_name="Field Worker PWA",
    migration_note="Split from legacy partner mode — no RFQ, profit, or company settings",
)

_H5_SUPPLIER = _m(
    portal_key="supplier",
    physical_frontend="h5",
    layout="supplier",
    home_route="/supplier",
    theme_key="ainerwise-supplier",
    menu_keys=["rfq", "quotes", "catalog", "orders", "notifications", "shipping", "warranty"],
    route_allowlist=["/supplier/**", "/messages/**", "/commerce/**", "/profile", "/profile/**", "/settings/**", "/access-denied", "/login"],
    required_grants=["supplier.rfq.read", "supplier.catalog.read"],
    pwa_manifest_key="supplier",
    display_name="Supplier PWA",
    migration_note="Phase 3: commerce orders + notifications via Core API",
)

_H5_CEBU_BUYER = _m(
    portal_key="cebu_buyer",
    physical_frontend="h5",
    layout="buyer",
    home_route="/buyer",
    theme_key="cebu-buyer",
    menu_keys=["marketplace", "secondhand", "requests", "orders", "messages", "notifications"],
    route_allowlist=["/buyer/**", "/marketplace/**", "/secondhand/**", "/messages/**", "/commerce/**", "/profile", "/access-denied", "/login"],
    required_grants=["portal.h5.cebu_buyer"],
    display_name="AinerWise Market Buyer H5",
    migration_note="Phase 3 buyer commerce on Core",
)

_H5_KIOSK = _m(
    portal_key="kiosk",
    physical_frontend="h5",
    layout="kiosk",
    home_route="/kiosk",
    theme_key="ainerwise-kiosk",
    menu_keys=["welcome", "products", "lead_capture"],
    route_allowlist=["/kiosk/**", "/access-denied"],
    required_grants=["portal.h5.kiosk"],
    pwa_manifest_key="kiosk",
    display_name="AISLOS Experience Center Kiosk",
    legacy_portal_mode="kiosk",
)

# --- Final zero-loss experience keys -----------------------------------------
#
# Keep the earlier keys above as compatibility entries while callers migrate.
# These explicit PC/H5 keys are the stable contract used by new grants,
# navigation, and route enforcement.

_TARGET_EXPERIENCE_PORTALS: list[dict[str, Any]] = [
    _m(
        portal_key="consumer_pc",
        physical_frontend="pc",
        layout="consumer",
        home_route="/",
        theme_key="ainerwise-consumer",
        menu_keys=["solutions", "products", "shopping", "procurement", "contact"],
        route_allowlist=["/", "/solutions/**", "/products/**", "/store/**", "/procurement/**", "/services/**", "/insights/**", "/market", "/market/categories", "/market/marketplace/**", "/market/how-it-works", "/market/pricing", "/market/trust-safety", "/market/post-request", "/cebu", "/cebu/categories", "/cebu/marketplace/**", "/cebu/how-it-works", "/cebu/pricing", "/cebu/trust-safety", "/cebu/post-request",
            # Unified catalogue replaces the split product/market entries.
            "/catalog", "/catalog/**", "/agents", "/agents/**",
            # Buyer journey: sourcing under /market, delivery onward under /portal.
            "/market/**", "/portal", "/portal/**",
            "/submit-requirement", "/supplier-application", "/recurring-solutions", "/ai-building-brain-demo", "/ai-building-brain", "/ai-building-brain/**", "/about", "/contact", "/sign/**", "/login", "/register", "/register-buyer", "/register-role", "/register-supplier", "/forgot-password", "/demo-login"],
        required_grants=[],
        display_name="AinerWise Consumer Platform",
        migration_note="Final public PC experience; legacy aislos/store entries remain compatible",
    ),
    _m(
        portal_key="consumer_h5",
        physical_frontend="h5",
        layout="consumer-mobile",
        home_route="/",
        theme_key="ainerwise-consumer",
        menu_keys=["home", "solutions", "products", "requirement", "profile"],
        route_allowlist=["/", "/solutions/**", "/products/**", "/marketplace/**", "/services", "/submit-requirement", "/ai-brain", "/about", "/contact", "/login", "/register", "/auth/**"],
        required_grants=[],
        pwa_manifest_key="consumer",
        display_name="AinerWise",
    ),
    _m(
        portal_key="customer_pc",
        physical_frontend="pc",
        layout="customer-workspace",
        home_route="/portal",
        theme_key="ainerwise-customer",
        menu_keys=["requirements", "procurement", "projects", "approvals", "installations", "assets", "tickets"],
        route_allowlist=["/portal", "/portal/**", "/market/**", "/procurement/**", "/catalog", "/catalog/**", "/login", "/demo-login"],
        required_grants=["portal.pc.customer"],
        display_name="Customer Workspace PC",
    ),
    _m(
        portal_key="customer_h5",
        physical_frontend="h5",
        layout="customer-mobile",
        home_route="/projects",
        theme_key="ainerwise-customer",
        menu_keys=["products", "projects", "approvals", "installations", "assets", "tickets", "profile"],
        route_allowlist=["/dashboard", "/products", "/products/**", "/projects", "/projects/**", "/customer/**", "/profile", "/access-denied", "/login"],
        required_grants=["portal.h5.customer"],
        pwa_manifest_key="customer",
        display_name="Workspace",
    ),
    _m(
        portal_key="cebu_buyer_pc",
        physical_frontend="pc",
        layout="cebu-buyer",
        home_route="/market/buyer/dashboard",
        theme_key="cebu-procurement",
        menu_keys=["marketplace", "requests", "offers", "orders", "messages", "wallet", "disputes"],
        route_allowlist=["/market/buyer/dashboard", "/market", "/market/**", "/cebu/buyer/dashboard", "/cebu", "/cebu/**", "/buyer/**", "/commerce/**", "/login", "/register", "/demo-login"],
        required_grants=["portal.pc.cebu_buyer"],
        display_name="AinerWise Market Buyer PC",
    ),
    _m(
        portal_key="cebu_buyer_h5",
        physical_frontend="h5",
        layout="cebu-buyer-mobile",
        home_route="/buyer",
        theme_key="cebu-buyer",
        menu_keys=["marketplace", "secondhand", "requests", "orders", "messages", "wallet", "notifications"],
        route_allowlist=["/buyer", "/buyer/**", "/marketplace", "/marketplace/**", "/secondhand", "/secondhand/**", "/messages/**", "/commerce/**", "/profile", "/profile/**", "/settings/**", "/access-denied", "/login", "/auth/**"],
        required_grants=["portal.h5.cebu_buyer"],
        pwa_manifest_key="cebu-buyer",
        display_name="AinerWise Market H5",
        migration_note="Former Cebu Procurement Buyer H5; now the standalone AinerWise Market mobile product",
    ),
    _m(
        portal_key="supplier_pc",
        physical_frontend="pc",
        layout="supplier-workspace",
        home_route="/supplier",
        theme_key="ainerwise-supplier",
        menu_keys=["rfq", "quotes", "catalog", "orders", "ads", "wallet", "shipping", "warranty"],
        route_allowlist=["/supplier", "/supplier/**", "/supplier-onboarding", "/commerce/**", "/login", "/demo-login"],
        required_grants=["supplier.rfq.read", "supplier.catalog.read"],
        display_name="Supplier Workspace PC",
    ),
    _m(
        portal_key="supplier_h5",
        physical_frontend="h5",
        layout="supplier-mobile",
        home_route="/supplier",
        theme_key="ainerwise-supplier",
        menu_keys=["rfq", "quotes", "catalog", "orders", "notifications", "shipping", "warranty"],
        route_allowlist=["/supplier", "/supplier/**", "/messages/**", "/commerce/**", "/profile", "/profile/**", "/settings/**", "/access-denied", "/login"],
        required_grants=["supplier.rfq.read", "supplier.catalog.read"],
        pwa_manifest_key="supplier",
        display_name="Supplier Workspace H5",
    ),
    _m(
        portal_key="partner_company_pc",
        physical_frontend="pc",
        layout="partner-workspace",
        home_route="/partner",
        theme_key="ainerwise-partner",
        menu_keys=["rfq", "bids", "work_packages", "crews", "workers", "schedule", "performance"],
        route_allowlist=["/partner", "/partner/**", "/login", "/demo-login"],
        required_grants=["partner.rfq.read", "partner.work_package.read"],
        display_name="Partner Company PC",
    ),
    _m(
        portal_key="partner_company_h5",
        physical_frontend="h5",
        layout="partner-mobile",
        home_route="/partner",
        theme_key="ainerwise-partner",
        menu_keys=["rfq", "bids", "work_packages", "crews", "schedule", "performance"],
        route_allowlist=["/partner", "/partner/**", "/profile", "/access-denied", "/login"],
        required_grants=["partner.rfq.read", "partner.work_package.read"],
        pwa_manifest_key="partner-company",
        display_name="Partner Company H5",
    ),
    _m(
        portal_key="marketing_pc",
        physical_frontend="admin",
        layout="marketing-workbench",
        home_route="/marketing",
        theme_key="ainerwise-admin",
        menu_keys=["campaigns", "briefs", "review", "assets", "schedule", "performance", "integration", "seo"],
        route_allowlist=["/marketing", "/marketing/**", "/marketing-studio/**", "/seo", "/seo/**"],
        required_grants=["admin.marketing.read"],
        display_name="Marketing Operations PC",
    ),
    _m(
        portal_key="marketing_h5",
        physical_frontend="h5",
        layout="marketing-mobile",
        home_route="/marketing-mobile",
        theme_key="ainerwise-marketing",
        menu_keys=["capture", "review", "assets", "schedule", "performance"],
        route_allowlist=["/marketing-mobile", "/marketing-mobile/**", "/profile", "/access-denied", "/login"],
        required_grants=["admin.marketing.read"],
        pwa_manifest_key="marketing",
        display_name="Marketing Operations H5",
        migration_note="Brief capture/review only; AinerN2D remains an external media engine",
    ),
    _m(
        portal_key="field_worker_h5",
        physical_frontend="h5",
        layout="field-worker",
        home_route="/field/today",
        theme_key="ainerwise-field",
        menu_keys=["today", "tasks", "scan", "offline_queue", "profile"],
        route_allowlist=["/field/today", "/field/**", "/profile", "/access-denied", "/login"],
        required_grants=["field_task.read_assigned"],
        pwa_manifest_key="field-worker",
        offline_policy_key="field-v1",
        display_name="Field Worker H5",
    ),
    _m(
        portal_key="crew_lead_h5",
        physical_frontend="h5",
        layout="crew-lead",
        home_route="/crew",
        theme_key="ainerwise-field",
        menu_keys=["crew_tasks", "members", "handover", "exceptions", "evidence", "completion"],
        route_allowlist=["/crew", "/crew/**", "/field/**", "/profile", "/access-denied", "/login"],
        required_grants=["crew.task.manage"],
        pwa_manifest_key="crew-lead",
        offline_policy_key="field-v1",
        display_name="Crew Lead H5",
    ),
    _m(
        portal_key="kiosk_h5",
        physical_frontend="h5",
        layout="experience-kiosk",
        home_route="/kiosk",
        theme_key="ainerwise-kiosk",
        menu_keys=["welcome", "ai_reception", "products", "requirement", "staff_confirm"],
        route_allowlist=["/kiosk", "/kiosk/**", "/access-denied"],
        required_grants=["portal.h5.kiosk"],
        pwa_manifest_key="kiosk",
        display_name="AinerWise Experience Store Kiosk",
    ),
]

# --- Admin logical workbenches (section 2.4) ----------------------------------

def _admin_wb(
    portal_key: str,
    *,
    home_route: str,
    menu_keys: list[str],
    route_allowlist: list[str],
    required_grants: list[str],
    display_name: str,
    legacy_portal_mode: str | None = None,
) -> dict[str, Any]:
    return _m(
        portal_key=portal_key,
        physical_frontend="admin",
        layout="workbench",
        home_route=home_route,
        theme_key="ainerwise-admin",
        menu_keys=menu_keys,
        route_allowlist=route_allowlist,
        required_grants=required_grants,
        display_name=display_name,
        legacy_portal_mode=legacy_portal_mode,
    )


_ADMIN_WORKBENCHES: list[dict[str, Any]] = [
    _admin_wb("admin_executive", home_route="/", menu_keys=["dashboard", "kpis"], route_allowlist=["/", "/dashboard/**"], required_grants=["admin.executive.read"], display_name="Executive / Operations Dashboard", legacy_portal_mode="aislos"),
    _admin_wb("admin_crm", home_route="/leads", menu_keys=["leads", "inquiries", "contacts"], route_allowlist=["/leads/**", "/inquiries/**", "/crm/**", "/tickets/**"], required_grants=["admin.crm.read"], display_name="CRM / Lead"),
    _admin_wb("admin_ai_solution", home_route="/solutions", menu_keys=["solutions", "boq", "proposals"], route_allowlist=["/solutions/**", "/proposals/**", "/quotes/**"], required_grants=["admin.ai_solution.read"], display_name="AI Solution / BOQ"),
    _admin_wb("admin_procurement", home_route="/rfqs", menu_keys=["rfq", "bids", "awards"], route_allowlist=["/rfqs/**", "/procurement/**"], required_grants=["admin.procurement.read"], display_name="Procurement / RFQ / Bid / Award"),
    _admin_wb("admin_supplier_ops", home_route="/vendors", menu_keys=["vendors", "catalog", "scorecards"], route_allowlist=["/vendors/**", "/products/**", "/inventory/**", "/categories/**", "/service-packages/**", "/compatibility/**", "/warranty-policies/**", "/supplier-warranties/**", "/supplier-scorecards/**"], required_grants=["admin.supplier_ops.read"], display_name="Supplier Operations", legacy_portal_mode="store"),
    _admin_wb("admin_partner", home_route="/service-partners", menu_keys=["partners", "capabilities"], route_allowlist=["/service-partners/**", "/certifications/**"], required_grants=["admin.partner.read"], display_name="Partner Company / Capability"),
    _admin_wb("admin_field_ops", home_route="/field-ops", menu_keys=["dispatch", "crews", "workers", "map"], route_allowlist=["/field-ops/**"], required_grants=["admin.field_ops.read"], display_name="Field Operations / Dispatch"),
    _admin_wb("admin_project", home_route="/projects", menu_keys=["projects", "acceptance"], route_allowlist=["/projects/**"], required_grants=["admin.project.read"], display_name="Project / Acceptance"),
    _admin_wb("admin_asset", home_route="/lifecycle-dashboard", menu_keys=["assets", "warranty", "amc", "maintenance"], route_allowlist=["/lifecycle-dashboard/**", "/assets/**", "/sites/**", "/amc-contracts/**", "/monitoring-points/**", "/maintenance/**", "/calibration/**", "/customer-warranties/**", "/renewal-queue/**"], required_grants=["admin.asset.read"], display_name="Asset / Warranty / AMC / Maintenance"),
    _admin_wb("admin_commerce", home_route="/store-orders", menu_keys=["orders", "payments", "risk", "reconciliation"], route_allowlist=["/payments/**", "/payment-plans/**", "/store-orders/**", "/commerce/**", "/platform-fee-rules/**"], required_grants=["admin.commerce.read"], display_name="Commerce / Order / Payment / Risk"),
    _admin_wb("admin_cebu", home_route="/cebu-admin", menu_keys=["dashboard", "migrations", "users", "companies", "intents", "offers", "orders", "disputes", "risk", "trade", "backups", "notifications", "settings", "integrations", "audit"], route_allowlist=["/cebu-admin/**", "/settings/**", "/regions/**", "/integration-events/**"], required_grants=["admin.cebu.read"], display_name="Cebu Administration"),
    _admin_wb("admin_growth", home_route="/growth", menu_keys=["sources", "providers", "pricing", "publishing", "queue", "arbitrage"], route_allowlist=["/growth/**"], required_grants=["admin.growth.read"], display_name="Growth / Sourcing & Syndication"),
    _admin_wb("admin_marketing", home_route="/marketing", menu_keys=["campaigns", "briefs", "integration", "seo"], route_allowlist=["/marketing/**", "/marketing-studio/**", "/seo", "/seo/**"], required_grants=["admin.marketing.read"], display_name="Marketing", legacy_portal_mode="marketing"),
    _admin_wb("admin_ai_supervisor", home_route="/agents", menu_keys=["agents", "missions", "brain"], route_allowlist=["/agents/**", "/agent-missions/**", "/business-brain/**", "/ai-runs/**", "/ai-reviews/**"], required_grants=["admin.ai_supervisor.read"], display_name="AI Supervisor / Agent Console", legacy_portal_mode="agent"),
    _admin_wb("admin_knowledge", home_route="/knowledge", menu_keys=["knowledge", "cases"], route_allowlist=["/knowledge/**", "/case-library/**"], required_grants=["admin.knowledge.read"], display_name="Knowledge / Living Case"),
    _admin_wb("admin_finance", home_route="/project-finance", menu_keys=["finance", "margin", "settlement"], route_allowlist=["/project-finance/**", "/platform-fee-rules/**", "/finance/**", "/commerce/reconciliation/**"], required_grants=["admin.finance.read"], display_name="Finance / Margin / Settlement"),
    _admin_wb("admin_audit", home_route="/audit-logs", menu_keys=["audit", "privacy", "integrations", "settings", "documents", "access"], route_allowlist=["/access-center/**", "/audit-logs/**", "/privacy/**", "/integration-events/**", "/settings/**", "/regions/**", "/users/**", "/companies/**", "/documents/**"], required_grants=["admin.audit.read"], display_name="Audit / Integration / Settings"),
]

PORTAL_REGISTRY: dict[str, dict[str, Any]] = {
    _PC_AISLOS["portal_key"]: _PC_AISLOS,
    _PC_STORE["portal_key"]: _PC_STORE,
    _PC_DEVELOPER["portal_key"]: _PC_DEVELOPER,
    _PC_PROCUREMENT["portal_key"]: _PC_PROCUREMENT,
    _PC_CEBU["portal_key"]: _PC_CEBU,
    _PC_SECONDHAND["portal_key"]: _PC_SECONDHAND,
    _H5_CUSTOMER["portal_key"]: _H5_CUSTOMER,
    _H5_CEBU_BUYER["portal_key"]: _H5_CEBU_BUYER,
    _H5_PARTNER_COMPANY["portal_key"]: _H5_PARTNER_COMPANY,
    _H5_FIELD_WORKER["portal_key"]: _H5_FIELD_WORKER,
    _H5_SUPPLIER["portal_key"]: _H5_SUPPLIER,
    _H5_KIOSK["portal_key"]: _H5_KIOSK,
    **{portal["portal_key"]: portal for portal in _TARGET_EXPERIENCE_PORTALS},
    **{wb["portal_key"]: wb for wb in _ADMIN_WORKBENCHES},
}

# Compatibility manifests remain directly resolvable for old clients, but are
# hidden from the normal portal picker once their final successor is available.
COMPATIBILITY_PORTAL_SUCCESSORS: dict[str, str] = {
    "aislos": "consumer_pc",
    "cebu": "cebu_buyer_pc",
    "customer": "customer_h5",
    "cebu_buyer": "cebu_buyer_h5",
    "partner_company": "partner_company_h5",
    "field_worker": "field_worker_h5",
    "supplier": "supplier_h5",
    "kiosk": "kiosk_h5",
    "admin_marketing": "marketing_pc",
}

# Legacy NUXT_PUBLIC_PORTAL_MODE -> canonical logical portal_key
LEGACY_PORTAL_MODE_MAP: dict[str, str] = {
    "aislos": "aislos",
    "store": "store",
    "developer": "developer",
    "customer": "customer",
    "partner": "partner_company",
    "kiosk": "kiosk",
    "marketing": "marketing_pc",
    "agent": "admin_ai_supervisor",
    "cebu": "cebu",
}

_PORTAL_KEY_RE = __import__("re").compile(r"^[a-z][a-z0-9_]{1,63}$")


def is_valid_portal_key(portal_key: str) -> bool:
    key = (portal_key or "").strip().lower()
    return bool(key and _PORTAL_KEY_RE.match(key))


def resolve_portal_key(portal_key: str) -> str | None:
    """Normalize and map legacy mode aliases; returns None if unknown."""
    key = (portal_key or "").strip().lower()
    if not key:
        return None
    key = LEGACY_PORTAL_MODE_MAP.get(key, key)
    if key not in PORTAL_REGISTRY:
        return None
    return key


def get_manifest(portal_key: str) -> dict[str, Any] | None:
    resolved = resolve_portal_key(portal_key)
    if not resolved:
        return None
    return dict(PORTAL_REGISTRY[resolved])


def list_manifests(*, physical_frontend: PhysicalFrontend | None = None) -> list[dict[str, Any]]:
    items = list(PORTAL_REGISTRY.values())
    if physical_frontend:
        items = [m for m in items if m["physical_frontend"] == physical_frontend]
    return sorted(items, key=lambda m: (m["physical_frontend"], m["portal_key"]))

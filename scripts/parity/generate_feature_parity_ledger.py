#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import hashlib
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs" / "parity"
RUNTIME_API_MANIFEST_PATH = DOCS_DIR / "runtime-api-manifest.json"
VERIFICATION_ATTESTATIONS_PATH = DOCS_DIR / "verification-attestations.json"

EXPECTED_CEBU_BASELINES = {
    ("CebuProjects", "PC", "page"): 59,
    ("CebuProjects", "H5", "page"): 41,
    ("CebuProjects", "Admin", "admin_view"): 24,
}

STATUS_TODO = "TODO"
STATUS_READY_FOR_VERIFY = "READY_FOR_VERIFY"
ALLOWED_STATUSES = {
    STATUS_TODO,
    "IN_PROGRESS",
    STATUS_READY_FOR_VERIFY,
    "VERIFIED",
    "FAILED_VERIFY",
    "BLOCKED",
}


@dataclass(frozen=True)
class InventorySpec:
    name: str
    source_project: str
    source_surface: str
    capability_type: str
    base_dir: Path
    file_glob: str


FRONTEND_SPECS = (
    InventorySpec(
        name="cebu_pc_pages",
        source_project="CebuProjects",
        source_surface="PC",
        capability_type="page",
        base_dir=ROOT / "CebuProjects" / "pc-frontend" / "pages",
        file_glob="**/*.vue",
    ),
    InventorySpec(
        name="cebu_h5_pages",
        source_project="CebuProjects",
        source_surface="H5",
        capability_type="page",
        base_dir=ROOT / "CebuProjects" / "h5-frontend" / "pages",
        file_glob="**/*.vue",
    ),
    InventorySpec(
        name="cebu_admin_views",
        source_project="CebuProjects",
        source_surface="Admin",
        capability_type="admin_view",
        base_dir=ROOT / "CebuProjects" / "admin-frontend" / "src",
        file_glob="**/*.vue",
    ),
    InventorySpec(
        name="ainerwise_pc_pages",
        source_project="Ainerwise",
        source_surface="PC",
        capability_type="page",
        base_dir=ROOT / "Ainerwise" / "frontend-pc" / "pages",
        file_glob="**/*.vue",
    ),
    InventorySpec(
        name="ainerwise_h5_pages",
        source_project="Ainerwise",
        source_surface="H5",
        capability_type="page",
        base_dir=ROOT / "Ainerwise" / "frontend-h5" / "pages",
        file_glob="**/*.vue",
    ),
    InventorySpec(
        name="ainerwise_admin_pages",
        source_project="Ainerwise",
        source_surface="Admin",
        capability_type="page",
        base_dir=ROOT / "Ainerwise" / "frontend-admin" / "pages",
        file_glob="**/*.vue",
    ),
)

BACKEND_SPECS = (
    InventorySpec(
        name="cebu_backend_api",
        source_project="CebuProjects",
        source_surface="API",
        capability_type="api",
        base_dir=ROOT / "CebuProjects" / "backend" / "app" / "routers",
        file_glob="**/*.py",
    ),
    InventorySpec(
        name="cebu_admin_backend_api",
        source_project="CebuProjects",
        source_surface="Admin API",
        capability_type="api",
        base_dir=ROOT / "CebuProjects" / "admin-backend",
        file_glob="*.py",
    ),
)

RUNTIME_API_SOURCE_SPECS = (
    InventorySpec("ainerwise_backend_api_sources", "Ainerwise", "Runtime API", "api", ROOT / "Ainerwise" / "backend" / "app" / "api", "**/*.py"),
    InventorySpec("ainerwise_backend_module_api_sources", "Ainerwise", "Runtime API", "api", ROOT / "Ainerwise" / "backend" / "app" / "modules", "**/api.py"),
    InventorySpec("ainerwise_backend_main_source", "Ainerwise", "Runtime API", "api", ROOT / "Ainerwise" / "backend" / "app", "main.py"),
    InventorySpec("ainerwise_ai_orchestrator_sources", "Ainerwise", "Runtime API", "api", ROOT / "Ainerwise" / "ai_orchestrator" / "app", "**/*.py"),
    InventorySpec("ainerwise_channel_gateway_sources", "Ainerwise", "Runtime API", "api", ROOT / "Ainerwise" / "channel_gateway" / "app", "**/*.py"),
)

AUTOMATION_SPECS = (
    InventorySpec(
        name="ainerwise_tasks",
        source_project="Ainerwise",
        source_surface="Task",
        capability_type="task",
        base_dir=ROOT / "Ainerwise" / "backend" / "app" / "tasks",
        file_glob="*.py",
    ),
    InventorySpec(
        name="ainerwise_seed_scripts",
        source_project="Ainerwise",
        source_surface="Script",
        capability_type="script",
        base_dir=ROOT / "Ainerwise" / "backend" / "scripts",
        file_glob="*.py",
    ),
    InventorySpec(
        name="ainerwise_shared_platform_scripts",
        source_project="Ainerwise",
        source_surface="Script",
        capability_type="script",
        base_dir=ROOT / "Ainerwise" / "scripts" / "shared-platform",
        file_glob="*.sh",
    ),
    InventorySpec(
        name="cebu_seed_script",
        source_project="CebuProjects",
        source_surface="Script",
        capability_type="script",
        base_dir=ROOT / "CebuProjects" / "backend",
        file_glob="seed.py",
    ),
)

DOMAIN_FILE_SPECS = (
    InventorySpec("ainerwise_services", "Ainerwise", "Service", "service", ROOT / "Ainerwise" / "backend" / "app" / "services", "*.py"),
    InventorySpec("ainerwise_modules", "Ainerwise", "Module", "module", ROOT / "Ainerwise" / "backend" / "app" / "modules", "**/*.py"),
    InventorySpec("cebu_services", "CebuProjects", "Service", "service", ROOT / "CebuProjects" / "backend" / "app" / "services", "*.py"),
    InventorySpec("ainerwise_migrations", "Ainerwise", "Migration", "migration", ROOT / "Ainerwise" / "backend" / "alembic" / "versions", "*.py"),
    InventorySpec("cebu_migrations", "CebuProjects", "Migration", "migration", ROOT / "CebuProjects" / "backend" / "app" / "migrations" / "versions", "*.py"),
    InventorySpec("ainerwise_pc_workflows", "Ainerwise", "Workflow", "frontend_workflow", ROOT / "Ainerwise" / "frontend-pc" / "composables", "*.ts"),
    InventorySpec("ainerwise_h5_workflows", "Ainerwise", "Workflow", "frontend_workflow", ROOT / "Ainerwise" / "frontend-h5" / "composables", "*.ts"),
    InventorySpec("ainerwise_admin_workflows", "Ainerwise", "Workflow", "frontend_workflow", ROOT / "Ainerwise" / "frontend-admin" / "composables", "*.ts"),
    InventorySpec("cebu_pc_stores", "CebuProjects", "Workflow", "frontend_workflow", ROOT / "CebuProjects" / "pc-frontend" / "stores", "*.ts"),
    InventorySpec("cebu_h5_stores", "CebuProjects", "Workflow", "frontend_workflow", ROOT / "CebuProjects" / "h5-frontend" / "stores", "*.ts"),
    InventorySpec("ainerwise_ai_orchestrator_workflows", "Ainerwise", "Workflow", "workflow", ROOT / "Ainerwise" / "ai_orchestrator" / "app" / "workflows", "*.py"),
    InventorySpec("ainerwise_channel_gateway_adapters", "Ainerwise", "Integration", "integration", ROOT / "Ainerwise" / "channel_gateway" / "app" / "adapters", "*.py"),
    InventorySpec("ainerwise_compose_manifests", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise", "docker-compose*.yml"),
    InventorySpec("ainerwise_backend_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "backend", "Dockerfile"),
    InventorySpec("ainerwise_ai_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "ai_orchestrator", "Dockerfile"),
    InventorySpec("ainerwise_channel_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "channel_gateway", "Dockerfile"),
    InventorySpec("ainerwise_pc_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "frontend-pc", "Dockerfile"),
    InventorySpec("ainerwise_h5_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "frontend-h5", "Dockerfile"),
    InventorySpec("ainerwise_admin_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "frontend-admin", "Dockerfile"),
    InventorySpec("ainerwise_legacy_frontend_dockerfile", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "frontend", "Dockerfile"),
    InventorySpec("ainerwise_nginx", "Ainerwise", "Infrastructure", "infrastructure", ROOT / "Ainerwise" / "nginx", "*.conf"),
    InventorySpec("cebu_root_compose", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects", "docker-compose*.yml"),
    InventorySpec("cebu_deploy_compose", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "deploy" / "compose", "docker-compose*.yml"),
    InventorySpec("cebu_backend_dockerfile", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "backend", "Dockerfile"),
    InventorySpec("cebu_admin_backend_dockerfile", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "admin-backend", "Dockerfile"),
    InventorySpec("cebu_pc_dockerfile", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "pc-frontend", "Dockerfile"),
    InventorySpec("cebu_h5_dockerfile", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "h5-frontend", "Dockerfile"),
    InventorySpec("cebu_nginx", "CebuProjects", "Infrastructure", "infrastructure", ROOT / "CebuProjects" / "deploy" / "nginx", "**/*.conf"),
)

MODEL_SPECS = (
    InventorySpec("ainerwise_models", "Ainerwise", "Data", "model", ROOT / "Ainerwise" / "backend" / "app" / "models", "*.py"),
    InventorySpec("cebu_models", "CebuProjects", "Data", "model", ROOT / "CebuProjects" / "backend" / "app" / "models", "*.py"),
)

PLANNED_PORTAL_GAPS = (
    ("consumer_h5", "frontend-h5", "AinerWise consumer H5", "customer_owner, customer_member, anonymous_guest"),
    ("customer_pc", "frontend-pc", "Customer workspace PC", "customer_owner, customer_member"),
    ("partner_company_pc", "frontend-pc", "Partner Company PC", "partner_company_owner, partner_dispatcher"),
    ("marketing_h5", "frontend-h5", "Marketing Operations H5", "marketing_operator"),
    ("crew_lead_h5", "frontend-h5", "Crew Lead task workspace", "crew_lead"),
    ("admin_cebu", "frontend-admin", "Cebu Admin workbench parity", "admin, finance_auditor, risk_operator"),
)

ROLE_SPECS = (
    {
        "source_project": "Ainerwise",
        "source_surface": "Role",
        "capability_type": "role",
        "file_path": ROOT / "Ainerwise" / "backend" / "app" / "core" / "permissions.py",
        "enum_class": "UserRole",
    },
    {
        "source_project": "CebuProjects",
        "source_surface": "Role",
        "capability_type": "role",
        "file_path": ROOT / "CebuProjects" / "backend" / "app" / "models" / "user.py",
        "enum_class": "UserRole",
    },
)

PERMISSION_MODEL_SPECS = (
    {
        "source_project": "Ainerwise",
        "source_surface": "Permission",
        "capability_type": "permission_model",
        "file_path": ROOT / "Ainerwise" / "backend" / "app" / "models" / "portal_access.py",
        "classes": ("Workspace", "WorkspaceMembership", "PortalGrant"),
    },
)

ROUTE_DECORATOR_RE = re.compile(
    r"@(?P<router>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method>get|post|put|patch|delete|options|head)\(\s*[\"'](?P<path>[^\"']+)[\"']"
)
ROUTER_RE = re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*APIRouter\((?P<body>.*?)\)", re.DOTALL)
PREFIX_RE = re.compile(r"prefix\s*=\s*[\"'](?P<prefix>[^\"']+)[\"']")
ENUM_CLASS_RE = re.compile(r"class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\([^)]*Enum\):(?P<body>.*?)(?:\nclass\s+[A-Za-z_][A-Za-z0-9_]*\(|\Z)", re.DOTALL)
ENUM_VALUE_RE = re.compile(r"^\s+(?P<member>[A-Z0-9_]+)\s*=\s*[\"'](?P<value>[^\"']+)[\"']", re.MULTILINE)
CLASS_DECL_RE = re.compile(r"^class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\(", re.MULTILINE)
VUE_EVENT_RE = re.compile(r"@(?P<event>click|submit|change|confirm|input|blur|focus|keydown|keyup|update:[A-Za-z0-9_-]+)\b")
STATE_LINE_RE = re.compile(
    r"\bstatus\b.*(?:===|!==|==|!=|=|:)|(?:set|update|change)[A-Za-z0-9_]*status|status(?:options|es|filter)",
    re.IGNORECASE,
)
EXCEPTION_LINE_RE = re.compile(
    r"\b(?:catch|error|failed|failure|reject|denied|forbidden|unauthorized)\b",
    re.IGNORECASE,
)
REQUIRED_CONTEXT_PATHS = (
    ROOT / "Ainerwise" / "docs" / "AISLOS_MARKETING_INTEGRATION_V4_TASKS.md",
    ROOT / "Ainerwise" / "docs" / "PORTAL_FIELD_SERVICE_V1_TASKS.md",
    ROOT / "Ainerwise" / "docs" / "ARCHITECTURE_CONSTITUTION.md",
    ROOT / "SHARED_PLATFORM_MIDDLEWARE_PLAN.md",
)


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    entries = []
    entries.extend(generate_frontend_entries())
    entries.extend(generate_frontend_interaction_entries())
    entries.extend(generate_runtime_api_entries())
    entries.extend(generate_backend_entries())
    entries.extend(generate_automation_entries())
    entries.extend(generate_domain_file_entries())
    entries.extend(generate_model_entries())
    entries.extend(generate_role_entries())
    entries.extend(generate_permission_model_entries())
    entries.extend(generate_planned_gap_entries())
    entries.sort(key=lambda item: (item["source_project"], item["source_surface"], item["source_path"], item["source_route_or_capability"]))
    apply_status_overrides(entries)
    source_fingerprint = calculate_source_fingerprint()
    verification_risks = scan_verification_risks()

    payload = {
        "generated_at": generated_at,
        "source_fingerprint": source_fingerprint,
        "verification_risks": verification_risks,
        "repo_root": str(ROOT),
        "baseline_expectations": [
            {
                "source_project": project,
                "source_surface": surface,
                "capability_type": capability_type,
                "expected_count": expected_count,
            }
            for (project, surface, capability_type), expected_count in EXPECTED_CEBU_BASELINES.items()
        ],
        "source_inventory_expectations": build_source_inventory_expectations(),
        "entries": entries,
    }

    (DOCS_DIR / "feature-parity-ledger.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DOCS_DIR / "FEATURE_PARITY_LEDGER.md").write_text(build_feature_parity_markdown(payload), encoding="utf-8")
    (DOCS_DIR / "PORTAL_ROUTE_MATRIX.md").write_text(build_portal_route_matrix(payload), encoding="utf-8")
    (DOCS_DIR / "API_DATA_MIGRATION_MATRIX.md").write_text(build_api_migration_matrix(payload), encoding="utf-8")
    (DOCS_DIR / "PARALLEL_AGENT_WORK_PACKAGES.md").write_text(build_work_packages(payload), encoding="utf-8")
    (DOCS_DIR / "VERIFICATION_RISK_REGISTER.md").write_text(build_verification_risk_register(payload), encoding="utf-8")
    print(f"Generated {len(entries)} ledger entries under {DOCS_DIR}")
    return 0


def generate_frontend_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in FRONTEND_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file():
                continue
            source_capability = page_capability_name(spec, file_path)
            source_route = to_route(spec.base_dir, file_path)
            target_portal = infer_target_portal(spec, source_route, file_path)
            risk_flags = detect_source_risks(file_path)
            entry = {
                "entry_id": build_entry_id(spec.source_project, spec.source_surface, file_path.relative_to(ROOT).as_posix()),
                "source_project": spec.source_project,
                "source_surface": spec.source_surface,
                "source_route_or_capability": source_capability,
                "source_path": file_path.relative_to(ROOT).as_posix(),
                "capability_type": spec.capability_type,
                "user_role": infer_user_role(spec, source_route, file_path),
                "target_portal": target_portal,
                "target_route_or_api": infer_target_route(spec, source_route, file_path, target_portal),
                "data_owner": infer_data_owner(spec, file_path, source_route),
                "permission": infer_permission(spec, target_portal),
                "migration": infer_migration_strategy(spec),
                "verification": infer_verification_strategy(spec),
                "verification_evidence": [],
                "risk_flags": risk_flags,
                "status": STATUS_TODO if risk_flags else infer_status(spec),
            }
            entries.append(entry)
    return entries


def generate_frontend_interaction_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in FRONTEND_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file():
                continue
            source_route = to_route(spec.base_dir, file_path)
            target_portal = infer_target_portal(spec, source_route, file_path)
            target_route = infer_target_route(spec, source_route, file_path, target_portal)
            risk_flags = detect_source_risks(file_path)
            for interaction in parse_page_interactions(file_path):
                capability_type = interaction["capability_type"]
                raw = (
                    f"{file_path.relative_to(ROOT).as_posix()}::{capability_type}::"
                    f"{interaction['line']}::{interaction['ordinal']}"
                )
                entries.append(
                    {
                        "entry_id": build_entry_id(spec.source_project, spec.source_surface, raw),
                        "source_project": spec.source_project,
                        "source_surface": spec.source_surface,
                        "source_route_or_capability": (
                            f"{capability_type}:{source_route}:L{interaction['line']}:"
                            f"{interaction['label']}"
                        ),
                        "source_path": file_path.relative_to(ROOT).as_posix(),
                        "capability_type": capability_type,
                        "user_role": infer_user_role(spec, source_route, file_path),
                        "target_portal": target_portal,
                        "target_route_or_api": f"{target_route}#{capability_type}-L{interaction['line']}",
                        "data_owner": infer_data_owner(spec, file_path, source_route),
                        "permission": infer_permission(spec, target_portal),
                        "migration": infer_migration_strategy(spec),
                        "verification": (
                            "Browser interaction parity + linked API contract + exact success/failure and permission assertions."
                        ),
                        "verification_evidence": [],
                        "risk_flags": risk_flags,
                        "status": STATUS_TODO if risk_flags else infer_status(spec),
                    }
                )
    return entries


def generate_backend_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in BACKEND_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file() or file_path.name == "__init__.py":
                continue
            for api_route in parse_fastapi_routes(file_path):
                target_portal = infer_api_target_portal(spec, api_route)
                entries.append(
                    {
                        "entry_id": build_entry_id(spec.source_project, spec.source_surface, f"{file_path.relative_to(ROOT).as_posix()}::{api_route['method']}::{api_route['path']}"),
                        "source_project": spec.source_project,
                        "source_surface": spec.source_surface,
                        "source_route_or_capability": f"{api_route['method']} {api_route['path']}",
                        "source_path": file_path.relative_to(ROOT).as_posix(),
                        "capability_type": spec.capability_type,
                        "user_role": infer_api_user_role(spec, api_route),
                        "target_portal": target_portal,
                        "target_route_or_api": infer_api_target_route(spec, api_route),
                        "data_owner": infer_api_data_owner(spec, file_path, api_route),
                        "permission": infer_api_permission(spec, api_route, target_portal),
                        "migration": infer_api_migration_strategy(spec),
                        "verification": infer_api_verification_strategy(spec),
                        "verification_evidence": [],
                        "status": infer_status(spec),
                    }
                )
    return entries


def generate_runtime_api_entries() -> list[dict[str, str]]:
    if not RUNTIME_API_MANIFEST_PATH.exists():
        raise SystemExit(
            "Runtime API manifest is missing. Run: python3 scripts/parity/export_runtime_api_manifest.py"
        )
    manifest = json.loads(RUNTIME_API_MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_fingerprint = calculate_runtime_api_source_fingerprint()
    if manifest.get("source_fingerprint") != expected_fingerprint:
        raise SystemExit(
            "Runtime API manifest is stale. Run: python3 scripts/parity/export_runtime_api_manifest.py"
        )

    entries: list[dict[str, str]] = []
    for api_route in manifest.get("routes", []):
        source_path = api_route["source_path"]
        service = api_route["service"]
        target_portal = infer_runtime_api_target_portal(service, api_route)
        entries.append(
            {
                "entry_id": build_entry_id(
                    "Ainerwise",
                    "Runtime API",
                    f"{service}::{api_route['method']}::{api_route['path']}",
                ),
                "source_project": "Ainerwise",
                "source_surface": "Runtime API",
                "source_route_or_capability": f"{api_route['method']} {api_route['path']}",
                "source_path": source_path,
                "capability_type": "api",
                "user_role": infer_runtime_api_user_role(service, api_route),
                "target_portal": target_portal,
                "target_route_or_api": api_route["path"],
                "data_owner": infer_runtime_api_data_owner(service, api_route),
                "permission": infer_runtime_api_permission(service, api_route, target_portal),
                "migration": "Retain as an Ainerwise runtime API contract; route changes require a regenerated manifest and parity review.",
                "verification": "Runtime route coverage + contract test + authorization negative test + audit/outbox validation when state changes.",
                "verification_evidence": [],
                "runtime_service": service,
                "runtime_endpoint": api_route["endpoint"],
                "status": STATUS_READY_FOR_VERIFY,
            }
        )
    return entries


def generate_automation_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in AUTOMATION_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file() or file_path.name == "__init__.py":
                continue
            relative = file_path.relative_to(ROOT).as_posix()
            capabilities = (
                parse_task_functions(file_path)
                if spec.capability_type == "task"
                else [{"name": infer_file_capability_name(spec, file_path), "line": 1}]
            )
            for capability in capabilities:
                raw = relative if spec.capability_type != "task" else f"{relative}::{capability['name']}"
                entries.append({
                    "entry_id": build_entry_id(spec.source_project, spec.source_surface, raw),
                    "source_project": spec.source_project,
                    "source_surface": spec.source_surface,
                    "source_route_or_capability": capability["name"],
                    "source_path": relative,
                    "capability_type": spec.capability_type,
                    "user_role": infer_file_user_role(spec, file_path),
                    "target_portal": infer_file_target_portal(spec, file_path),
                    "target_route_or_api": infer_file_target(spec, file_path),
                    "data_owner": infer_file_data_owner(spec, file_path),
                    "permission": infer_file_permission(spec, file_path),
                    "migration": infer_file_migration_strategy(spec),
                    "verification": infer_file_verification_strategy(spec),
                    "verification_evidence": [],
                    "status": infer_status(spec),
                    "source_line": capability["line"],
                })
    return entries


def generate_domain_file_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in DOMAIN_FILE_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file() or file_path.name == "__init__.py":
                continue
            relative = file_path.relative_to(ROOT).as_posix()
            stem = file_path.stem
            is_integration = any(
                token in stem
                for token in (
                    "bridge",
                    "integration",
                    "stripe",
                    "telegram",
                    "email",
                    "channel_gateway",
                    "media",
                )
            )
            surface = "Integration" if is_integration else spec.source_surface
            capability_type = "integration" if is_integration else spec.capability_type
            target = infer_domain_target(spec, file_path, capability_type)
            entries.append(
                {
                    "entry_id": build_entry_id(spec.source_project, surface, relative),
                    "source_project": spec.source_project,
                    "source_surface": surface,
                    "source_route_or_capability": f"{capability_type}:{file_path.stem}",
                    "source_path": relative,
                    "capability_type": capability_type,
                    "user_role": infer_domain_user_role(capability_type),
                    "target_portal": target,
                    "target_route_or_api": f"{capability_type}:{file_path.stem}",
                    "data_owner": infer_domain_data_owner(spec, file_path, capability_type),
                    "permission": infer_domain_permission(capability_type),
                    "migration": infer_domain_migration(spec, capability_type),
                    "verification": infer_domain_verification(capability_type),
                    "verification_evidence": [],
                    "status": infer_status(spec),
                }
            )
    return entries


def generate_model_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in MODEL_SPECS:
        for file_path in sorted(spec.base_dir.glob(spec.file_glob)):
            if not file_path.is_file() or file_path.name in {"__init__.py", "base_model.py"}:
                continue
            relative = file_path.relative_to(ROOT).as_posix()
            for class_name in sorted(parse_class_names(file_path)):
                entries.append(
                    {
                        "entry_id": build_entry_id(spec.source_project, spec.source_surface, f"{relative}:{class_name}"),
                        "source_project": spec.source_project,
                        "source_surface": spec.source_surface,
                        "source_route_or_capability": f"model:{class_name}",
                        "source_path": relative,
                        "capability_type": spec.capability_type,
                        "user_role": "system_data_owner",
                        "target_portal": "ainerwise_core_data",
                        "target_route_or_api": f"model:{class_name}",
                        "data_owner": infer_model_owner(file_path),
                        "permission": "owning_module object authorization + workspace/company/region scope",
                        "migration": (
                            "Map legacy rows, foreign keys, status values, files, and audit history into Ainerwise Core."
                            if spec.source_project == "CebuProjects"
                            else "Retain as Ainerwise Core data contract and require migration/backfill evidence for schema changes."
                        ),
                        "verification": "Schema parity + row-count/reconciliation + ownership and rollback verification.",
                        "verification_evidence": [],
                        "status": infer_status(spec),
                    }
                )
    return entries


def generate_planned_gap_entries() -> list[dict[str, str]]:
    source_path = "FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md"
    return [
        {
            "entry_id": build_entry_id("Ainerwise", "Gap", portal_key),
            "source_project": "Ainerwise",
            "source_surface": "Gap",
            "source_route_or_capability": description,
            "source_path": source_path,
            "capability_type": "planned_portal_gap",
            "user_role": roles,
            "target_portal": portal_key,
            "target_route_or_api": f"portal:{portal_key}",
            "data_owner": "identity_and_portal_core",
            "permission": "membership + portal_grant + route allowlist + object authorization",
            "migration": f"Implement {description} in {physical_frontend} without creating a fourth physical frontend.",
            "verification": "Independent browser E2E + distinct layout/menu + unauthorized route rejection + production build.",
            "verification_evidence": [],
            "status": STATUS_READY_FOR_VERIFY,
        }
        for portal_key, physical_frontend, description, roles in PLANNED_PORTAL_GAPS
    ]


def generate_role_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in ROLE_SPECS:
        file_path = spec["file_path"]
        relative = file_path.relative_to(ROOT).as_posix()
        for role_value in parse_enum_values(file_path, spec["enum_class"]):
            entries.append(
                {
                    "entry_id": build_entry_id(spec["source_project"], spec["source_surface"], f"{relative}:{role_value}"),
                    "source_project": spec["source_project"],
                    "source_surface": spec["source_surface"],
                    "source_route_or_capability": role_value,
                    "source_path": relative,
                    "capability_type": spec["capability_type"],
                    "user_role": role_value,
                    "target_portal": "identity_and_portal_core",
                    "target_route_or_api": f"role:{role_value}",
                    "data_owner": "identity_and_portal_core",
                    "permission": "role_definition + membership mapping + portal_grant policy",
                    "migration": infer_role_migration_strategy(spec["source_project"]),
                    "verification": "Role parity review + membership/grant mapping check + permission negative tests.",
                    "verification_evidence": [],
                    "status": STATUS_TODO if spec["source_project"] == "CebuProjects" else STATUS_READY_FOR_VERIFY,
                }
            )
    return entries


def generate_permission_model_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for spec in PERMISSION_MODEL_SPECS:
        file_path = spec["file_path"]
        relative = file_path.relative_to(ROOT).as_posix()
        present_classes = parse_class_names(file_path)
        for class_name in spec["classes"]:
            if class_name not in present_classes:
                continue
            entries.append(
                {
                    "entry_id": build_entry_id(spec["source_project"], spec["source_surface"], f"{relative}:{class_name}"),
                    "source_project": spec["source_project"],
                    "source_surface": spec["source_surface"],
                    "source_route_or_capability": class_name,
                    "source_path": relative,
                    "capability_type": spec["capability_type"],
                    "user_role": "admin, authenticated_user, workspace_member",
                    "target_portal": "identity_and_portal_core",
                    "target_route_or_api": f"model:{class_name}",
                    "data_owner": "identity_and_portal_core",
                    "permission": "workspace_id + portal_key + grant_key + region scope",
                    "migration": "Retain as the core authorization model and verify object scope boundaries against every consuming portal.",
                    "verification": "Model-level contract review + ownership tests + cross-workspace and cross-portal negative tests.",
                    "verification_evidence": [],
                    "status": STATUS_READY_FOR_VERIFY,
                }
            )
    return entries


def parse_fastapi_routes(file_path: Path) -> list[dict[str, str]]:
    text = file_path.read_text(encoding="utf-8")
    router_prefixes = {"app": ""}
    for match in ROUTER_RE.finditer(text):
        prefix_match = PREFIX_RE.search(match.group("body"))
        router_prefixes[match.group("name")] = prefix_match.group("prefix") if prefix_match else ""

    routes: list[dict[str, str]] = []
    for match in ROUTE_DECORATOR_RE.finditer(text):
        router_name = match.group("router")
        prefix = router_prefixes.get(router_name, "")
        routes.append(
            {
                "router": router_name,
                "method": match.group("method").upper(),
                "path": join_paths(prefix, match.group("path")),
            }
        )
    return routes


def parse_enum_values(file_path: Path, enum_class: str) -> list[str]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    in_target_enum = False
    values: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_target_enum:
            if stripped.startswith(f"class {enum_class}("):
                in_target_enum = True
            continue

        if stripped.startswith("class ") and not line.startswith(" "):
            break
        if stripped and not line.startswith(" "):
            break

        value_match = ENUM_VALUE_RE.match(line)
        if value_match:
            values.append(value_match.group("value"))
    return values


def parse_class_names(file_path: Path) -> set[str]:
    text = file_path.read_text(encoding="utf-8")
    return {match.group("name") for match in CLASS_DECL_RE.finditer(text)}


def parse_page_interactions(file_path: Path) -> list[dict[str, str | int]]:
    interactions: list[dict[str, str | int]] = []
    ordinal = 0
    for line_number, line in enumerate(file_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        stripped = " ".join(line.strip().split())
        for match in VUE_EVENT_RE.finditer(line):
            ordinal += 1
            interactions.append(
                {
                    "capability_type": "operation",
                    "line": line_number,
                    "ordinal": ordinal,
                    "label": f"@{match.group('event')}",
                }
            )
        if "status" in line.lower() and STATE_LINE_RE.search(line):
            ordinal += 1
            interactions.append(
                {
                    "capability_type": "state_machine",
                    "line": line_number,
                    "ordinal": ordinal,
                    "label": stripped[:100] or "status transition",
                }
            )
        if EXCEPTION_LINE_RE.search(line):
            ordinal += 1
            interactions.append(
                {
                    "capability_type": "exception_flow",
                    "line": line_number,
                    "ordinal": ordinal,
                    "label": stripped[:100] or "exception flow",
                }
            )
    return interactions


def parse_task_functions(file_path: Path) -> list[dict[str, str | int]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    tasks: list[dict[str, str | int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            is_task = (
                isinstance(target, ast.Attribute)
                and target.attr == "task"
                or isinstance(target, ast.Name)
                and target.id in {"task", "shared_task"}
            )
            if not is_task:
                continue
            task_name = node.name
            if isinstance(decorator, ast.Call):
                for keyword in decorator.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                        task_name = str(keyword.value.value)
            tasks.append({"name": f"task:{task_name}", "line": node.lineno})
            break
    return sorted(tasks, key=lambda item: (item["line"], item["name"]))


def build_source_inventory_expectations() -> list[dict[str, str | int]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for spec in FRONTEND_SPECS:
        for file_path in spec.base_dir.glob(spec.file_glob):
            if not file_path.is_file():
                continue
            counts[(spec.source_project, spec.source_surface, spec.capability_type)] += 1
            for interaction in parse_page_interactions(file_path):
                counts[(spec.source_project, spec.source_surface, interaction["capability_type"])] += 1
    for spec in AUTOMATION_SPECS:
        for file_path in spec.base_dir.glob(spec.file_glob):
            if not file_path.is_file() or file_path.name == "__init__.py":
                continue
            amount = len(parse_task_functions(file_path)) if spec.capability_type == "task" else 1
            counts[(spec.source_project, spec.source_surface, spec.capability_type)] += amount
    runtime_manifest = json.loads(RUNTIME_API_MANIFEST_PATH.read_text(encoding="utf-8"))
    counts[("Ainerwise", "Runtime API", "api")] += len(runtime_manifest.get("routes", []))
    for spec in BACKEND_SPECS:
        for file_path in spec.base_dir.glob(spec.file_glob):
            if file_path.is_file() and file_path.name != "__init__.py":
                counts[(spec.source_project, spec.source_surface, spec.capability_type)] += len(
                    parse_fastapi_routes(file_path)
                )
    for spec in DOMAIN_FILE_SPECS:
        for file_path in spec.base_dir.glob(spec.file_glob):
            if not file_path.is_file() or file_path.name == "__init__.py":
                continue
            is_integration = any(
                token in file_path.stem
                for token in (
                    "bridge",
                    "integration",
                    "stripe",
                    "telegram",
                    "email",
                    "channel_gateway",
                    "media",
                )
            )
            surface = "Integration" if is_integration else spec.source_surface
            capability_type = "integration" if is_integration else spec.capability_type
            counts[(spec.source_project, surface, capability_type)] += 1
    for spec in MODEL_SPECS:
        for file_path in spec.base_dir.glob(spec.file_glob):
            if file_path.is_file() and file_path.name not in {"__init__.py", "base_model.py"}:
                counts[(spec.source_project, spec.source_surface, spec.capability_type)] += len(
                    parse_class_names(file_path)
                )
    for spec in ROLE_SPECS:
        counts[(spec["source_project"], spec["source_surface"], spec["capability_type"])] += len(
            parse_enum_values(spec["file_path"], spec["enum_class"])
        )
    for spec in PERMISSION_MODEL_SPECS:
        present_classes = parse_class_names(spec["file_path"])
        counts[(spec["source_project"], spec["source_surface"], spec["capability_type"])] += sum(
            class_name in present_classes for class_name in spec["classes"]
        )
    counts[("Ainerwise", "Gap", "planned_portal_gap")] += len(PLANNED_PORTAL_GAPS)
    return [
        {
            "source_project": project,
            "source_surface": surface,
            "capability_type": capability_type,
            "expected_count": count,
        }
        for (project, surface, capability_type), count in sorted(counts.items())
    ]


def calculate_source_fingerprint() -> str:
    paths: set[Path] = {
        Path(__file__),
        ROOT / "FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md",
        DOCS_DIR / "status-overrides.json",
        RUNTIME_API_MANIFEST_PATH,
    }
    paths.update(REQUIRED_CONTEXT_PATHS)
    for spec in (*FRONTEND_SPECS, *BACKEND_SPECS, *AUTOMATION_SPECS, *DOMAIN_FILE_SPECS, *MODEL_SPECS):
        if spec.base_dir.exists():
            paths.update(path for path in spec.base_dir.glob(spec.file_glob) if path.is_file())
    for spec in (*ROLE_SPECS, *PERMISSION_MODEL_SPECS):
        paths.add(spec["file_path"])
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def calculate_verification_subject_fingerprint() -> str:
    paths: set[Path] = set(REQUIRED_CONTEXT_PATHS)
    for spec in (*FRONTEND_SPECS, *BACKEND_SPECS, *RUNTIME_API_SOURCE_SPECS, *AUTOMATION_SPECS, *DOMAIN_FILE_SPECS, *MODEL_SPECS):
        if spec.base_dir.exists():
            paths.update(path for path in spec.base_dir.glob(spec.file_glob) if path.is_file())
    for spec in (*ROLE_SPECS, *PERMISSION_MODEL_SPECS):
        paths.add(spec["file_path"])
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def calculate_runtime_api_source_fingerprint() -> str:
    paths: set[Path] = set()
    for spec in RUNTIME_API_SOURCE_SPECS:
        if spec.base_dir.exists():
            paths.update(path for path in spec.base_dir.glob(spec.file_glob) if path.is_file())
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def detect_source_risks(file_path: Path) -> list[str]:
    if file_path.suffix not in {".vue", ".ts", ".py"}:
        return []
    text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
    markers = {
        "under development": "placeholder_or_under_development",
        "coming soon": "placeholder_or_under_development",
        "demodata": "static_demo_data_dependency",
        "mockdata": "static_mock_data_dependency",
        "notimplementederror": "not_implemented_code_path",
    }
    return sorted({risk for marker, risk in markers.items() if marker in text})


def scan_verification_risks() -> list[dict[str, str | int]]:
    risks: list[dict[str, str | int]] = []
    tests_dir = ROOT / "Ainerwise" / "backend" / "tests"
    early_return_re = re.compile(r"^\s+if\s+.+:\s*\n\s+return\s*$", re.MULTILINE)
    accepted_failure_re = re.compile(
        r"status_code\s+in\s+\([^)]*(?:401|403|404|409|422|500|503)[^)]*\)"
    )
    for file_path in sorted(tests_dir.glob("test_*.py")):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in early_return_re.finditer(text):
            line = text[: match.start()].count("\n") + 1
            risks.append(
                {
                    "source_path": file_path.relative_to(ROOT).as_posix(),
                    "line": line,
                    "risk": "conditional_early_return_in_test",
                    "detail": match.group(0).strip().replace("\n", " "),
                    "required_action": "Replace early return with an explicit setup assertion or pytest.skip with a documented external prerequisite.",
                }
            )
        for match in accepted_failure_re.finditer(text):
            line = text[: match.start()].count("\n") + 1
            risks.append(
                {
                    "source_path": file_path.relative_to(ROOT).as_posix(),
                    "line": line,
                    "risk": "test_accepts_failure_status",
                    "detail": match.group(0),
                    "required_action": "Assert the exact expected success or denial status for the tested identity.",
                }
            )
    return risks


def apply_status_overrides(entries: list[dict]) -> None:
    overrides_path = DOCS_DIR / "status-overrides.json"
    if not overrides_path.exists():
        return
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    attestations = load_valid_verification_attestations()
    by_id = {entry["entry_id"]: entry for entry in entries}
    for entry_id, override in overrides.items():
        if entry_id not in by_id:
            raise ValueError(f"Status override references unknown entry: {entry_id}")
        status = override.get("status")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Status override for {entry_id} has invalid status: {status}")
        if status == "VERIFIED":
            attestation_id = override.get("attestation_id")
            if attestation_id not in attestations:
                raise ValueError(
                    f"VERIFIED override for {entry_id} requires a valid independent attestation_id"
                )
        by_id[entry_id]["status"] = status
        by_id[entry_id]["verification_evidence"] = (
            [{"attestation_id": override["attestation_id"]}]
            if status == "VERIFIED"
            else override.get("verification_evidence", [])
        )
        if override.get("notes"):
            by_id[entry_id]["status_notes"] = override["notes"]


def load_valid_verification_attestations() -> dict[str, dict]:
    if not VERIFICATION_ATTESTATIONS_PATH.exists():
        return {}
    payload = json.loads(VERIFICATION_ATTESTATIONS_PATH.read_text(encoding="utf-8"))
    valid: dict[str, dict] = {}
    expected_fingerprint = calculate_verification_subject_fingerprint()
    required = {
        "attestation_id",
        "decision",
        "scope",
        "verifier_role",
        "verifier_agent_id",
        "implementation_agent_id",
        "verified_at",
        "source_fingerprint",
        "commands",
        "results",
        "evidence_files",
        "attestation_sha256",
    }
    for attestation in payload.get("attestations", []):
        missing = required - set(attestation)
        if missing:
            raise ValueError(
                f"Verification attestation missing fields: {', '.join(sorted(missing))}"
            )
        if attestation["decision"] != "VERIFIED" or attestation["verifier_role"] != "independent_verifier":
            raise ValueError(f"Invalid verification decision/role: {attestation['attestation_id']}")
        if attestation["scope"] != "ZL01":
            raise ValueError(f"Invalid verification scope: {attestation['attestation_id']}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}", attestation["attestation_id"]):
            raise ValueError(f"Invalid verification attestation_id: {attestation['attestation_id']}")
        if (
            not attestation["verifier_agent_id"]
            or not attestation["implementation_agent_id"]
            or attestation["verifier_agent_id"] == attestation["implementation_agent_id"]
        ):
            raise ValueError(f"Verifier must be independent: {attestation['attestation_id']}")
        try:
            verified_at = datetime.fromisoformat(attestation["verified_at"])
        except ValueError as exc:
            raise ValueError(f"Invalid verification timestamp: {attestation['attestation_id']}") from exc
        if verified_at.tzinfo is None:
            raise ValueError(f"Verification timestamp must include timezone: {attestation['attestation_id']}")
        if attestation["source_fingerprint"] != expected_fingerprint:
            raise ValueError(f"Verification attestation is stale: {attestation['attestation_id']}")
        if not attestation["commands"] or not attestation["results"] or not attestation["evidence_files"]:
            raise ValueError(f"Verification attestation lacks repeatable evidence: {attestation['attestation_id']}")
        result_commands = [result.get("command") for result in attestation["results"]]
        if result_commands != attestation["commands"]:
            raise ValueError(f"Verification commands/results mismatch: {attestation['attestation_id']}")
        if any(result.get("exit_code") != 0 or not re.fullmatch(r"[0-9a-f]{64}", result.get("output_sha256", "")) for result in attestation["results"]):
            raise ValueError(f"Verification attestation has invalid command results: {attestation['attestation_id']}")
        for evidence in attestation["evidence_files"]:
            evidence_relative = evidence.get("path", "")
            if not evidence_relative.startswith("docs/parity/verification/"):
                raise ValueError(
                    f"Verification evidence must be stored under docs/parity/verification: {evidence_relative}"
                )
            evidence_path = ROOT / evidence_relative
            expected_sha = evidence.get("sha256", "")
            if not evidence_path.is_file() or hashlib.sha256(evidence_path.read_bytes()).hexdigest() != expected_sha:
                raise ValueError(f"Verification evidence file mismatch: {evidence_path}")
        canonical = dict(attestation)
        claimed_sha = canonical.pop("attestation_sha256")
        actual_sha = hashlib.sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if claimed_sha != actual_sha:
            raise ValueError(f"Verification attestation integrity check failed: {attestation['attestation_id']}")
        valid[attestation["attestation_id"]] = attestation
    return valid


def join_paths(prefix: str, path: str) -> str:
    if path == "/":
        return prefix or "/"
    prefix_part = prefix.rstrip("/")
    path_part = path if path.startswith("/") else f"/{path}"
    joined = f"{prefix_part}{path_part}"
    return joined or "/"


def to_route(base_dir: Path, file_path: Path) -> str:
    relative = file_path.relative_to(base_dir).as_posix()
    if relative.endswith(".vue"):
        relative = relative[:-4]
    elif relative.endswith(".tsx"):
        relative = relative[:-4]
    elif relative.endswith(".ts"):
        relative = relative[:-3]
    parts = []
    for part in relative.split("/"):
        if part == "index":
            continue
        if part.startswith("[[...") and part.endswith("]]"):
            parts.append(f":{part[5:-2]}*")
            continue
        if part.startswith("[...") and part.endswith("]"):
            parts.append(f":{part[4:-1]}*")
            continue
        if part.startswith("[") and part.endswith("]"):
            parts.append(f":{part[1:-1]}")
            continue
        parts.append(part)
    route = "/" + "/".join(parts)
    return route if route != "" else "/"


def page_capability_name(spec: InventorySpec, file_path: Path) -> str:
    relative = file_path.relative_to(spec.base_dir).as_posix()
    if spec.capability_type == "admin_view":
        return f"admin_view:{relative}"
    return to_route(spec.base_dir, file_path)


def infer_target_portal(spec: InventorySpec, route: str, file_path: Path) -> str:
    if spec.source_project == "CebuProjects":
        if spec.source_surface == "PC":
            if route.startswith("/admin"):
                return "cebu_admin"
            if route.startswith("/buyer"):
                return "cebu_buyer_pc"
            if route.startswith("/supplier"):
                return "supplier_pc"
            return "cebu_public_pc"
        if spec.source_surface == "H5":
            if route.startswith("/supplier"):
                return "supplier_h5"
            return "cebu_buyer_h5"
        return "cebu_admin"

    if spec.source_surface == "PC":
        if route.startswith("/developers"):
            return "developer_pc"
        if route.startswith("/portal"):
            return "customer_pc"
        if route.startswith("/store"):
            return "consumer_pc"
        return "consumer_pc"
    if spec.source_surface == "H5":
        if route.startswith("/supplier"):
            return "supplier_h5"
        if route.startswith("/kiosk"):
            return "kiosk_h5"
        if route.startswith("/partner"):
            return "partner_company_h5"
        if route.startswith("/field"):
            return "field_worker_h5"
        return "customer_h5"
    if spec.source_surface == "Admin":
        if route.startswith("/marketing"):
            return "marketing_admin"
        if route.startswith("/agent") or route.startswith("/calibration"):
            return "ai_supervisor_admin"
        return "frontend_admin"
    return "unclassified_portal"


def infer_target_route(spec: InventorySpec, route: str, file_path: Path, target_portal: str) -> str:
    if spec.source_project == "CebuProjects" and spec.source_surface == "Admin":
        slug = file_path.stem
        slug = re.sub(r"(?<!^)(?=[A-Z])", "-", slug).lower()
        return f"/cebu-admin/{slug}"
    if spec.source_project == "CebuProjects" and spec.source_surface == "PC" and target_portal == "cebu_public_pc":
        return f"/cebu{route}" if route != "/" else "/cebu"
    if spec.source_project == "CebuProjects" and spec.source_surface == "PC" and target_portal == "cebu_admin":
        return f"/cebu-admin{route.removeprefix('/admin') or '/'}"
    if spec.source_project == "CebuProjects" and spec.source_surface == "PC" and target_portal == "cebu_buyer_pc":
        return f"/cebu{route}"
    return route


def infer_data_owner(spec: InventorySpec, file_path: Path, route: str) -> str:
    relative = file_path.relative_to(ROOT).as_posix()
    if spec.source_surface in {"PC", "H5", "Admin"}:
        if route.startswith("/supplier"):
            return "commerce_supplier_portal"
        if route.startswith("/buyer") or route.startswith("/cebu"):
            return "commerce_buyer_portal"
        if route.startswith("/kiosk"):
            return "experience_kiosk_portal"
        if route.startswith("/partner"):
            return "partner_operations_portal"
        if route.startswith("/field"):
            return "field_operations_portal"
        if route.startswith("/developers"):
            return "developer_portal"
        return "consumer_platform_portal"
    return relative


def infer_permission(spec: InventorySpec, target_portal: str) -> str:
    if spec.source_surface == "Admin":
        return "membership:admin + portal_grant:admin.* + object_scope"
    if target_portal == "supplier_pc" or target_portal == "supplier_h5":
        return "membership:supplier + portal_grant:supplier.* + object_scope"
    if target_portal == "partner_company_h5":
        return "membership:partner_company + portal_grant:partner.* + object_scope"
    if target_portal == "field_worker_h5":
        return "membership:worker + portal_grant:field.* + assignment_scope"
    if target_portal == "kiosk_h5":
        return "device_token + kiosk_manifest"
    if target_portal.startswith("cebu_"):
        return "membership:cebu + portal_grant:cebu.* + object_scope"
    return "membership:customer + portal_grant:portal.* + object_scope"


def infer_migration_strategy(spec: InventorySpec) -> str:
    if spec.source_project == "CebuProjects":
        return "Legacy surface parity mapping into Ainerwise Core portal/API with data retained via identity, object, and audit migration."
    return "Retain in Ainerwise Core and verify portal wiring, route allowlist, menu, layout, and object permission parity."


def infer_verification_strategy(spec: InventorySpec) -> str:
    if spec.source_surface in {"PC", "H5", "Admin"}:
        return "Browser parity review + role-based access verification + build validation + linked API contract coverage."
    return "API contract test + negative permission test + audit/outbox verification when applicable."


def infer_status(spec: InventorySpec) -> str:
    return STATUS_TODO if spec.source_project == "CebuProjects" else STATUS_READY_FOR_VERIFY


def infer_user_role(spec: InventorySpec, route: str, file_path: Path) -> str:
    if spec.source_surface == "Admin":
        return "admin, finance_auditor, ai_supervisor, marketing_operator, project_manager"
    if route.startswith("/supplier"):
        return "supplier_operator"
    if route.startswith("/buyer"):
        return "buyer, customer_owner, customer_member"
    if route.startswith("/partner"):
        return "partner_company_owner, partner_dispatcher"
    if route.startswith("/field"):
        return "crew_lead, installer_worker, electrician_worker, maintenance_worker"
    if route.startswith("/kiosk"):
        return "kiosk_staff, anonymous_guest"
    if route.startswith("/developers"):
        return "developer"
    return "customer_owner, customer_member, anonymous_guest"


def infer_file_capability_name(spec: InventorySpec, file_path: Path) -> str:
    relative = file_path.relative_to(spec.base_dir).as_posix()
    if spec.capability_type == "task":
        return f"task:{file_path.stem}"
    if spec.capability_type == "integration":
        return f"integration:{file_path.stem}"
    return f"script:{relative}"


def infer_file_user_role(spec: InventorySpec, file_path: Path) -> str:
    if spec.capability_type == "task":
        return "admin, ai_supervisor, system_worker"
    if spec.capability_type == "integration":
        return "admin, system_integration"
    return "admin, devops_operator"


def infer_file_target_portal(spec: InventorySpec, file_path: Path) -> str:
    if spec.capability_type == "task":
        return "automation_core"
    if spec.capability_type == "integration":
        return "integration_boundary"
    return "migration_control"


def infer_file_target(spec: InventorySpec, file_path: Path) -> str:
    if spec.capability_type == "task":
        return f"worker:{file_path.stem}"
    if spec.capability_type == "integration":
        return f"integration:{file_path.stem}"
    return file_path.relative_to(ROOT).as_posix()


def infer_file_data_owner(spec: InventorySpec, file_path: Path) -> str:
    if spec.capability_type == "task":
        return "automation_core"
    if spec.capability_type == "integration":
        return "integration_boundary"
    return "migration_control"


def infer_file_permission(spec: InventorySpec, file_path: Path) -> str:
    if spec.capability_type == "task":
        return "system_worker + least_privilege queue access + audit"
    if spec.capability_type == "integration":
        return "integration_secret + allowlisted endpoint + audit"
    return "admin + controlled execution + rollback procedure"


def infer_file_migration_strategy(spec: InventorySpec) -> str:
    if spec.source_project == "CebuProjects":
        return "Preserve the legacy bridge surface until the equivalent Ainerwise Core capability and data migration are verified."
    if spec.capability_type == "task":
        return "Retain as scheduled or queue-driven Core automation with queue, audit, and outbox parity checks."
    if spec.capability_type == "integration":
        return "Retain the external integration boundary and verify contract-only access without internal dependency leakage."
    return "Retain as controlled bootstrap or migration script with explicit operator runbook coverage."


def infer_file_verification_strategy(spec: InventorySpec) -> str:
    if spec.capability_type == "task":
        return "Worker import validation + schedule review + queue isolation + integration or E2E task tests."
    if spec.capability_type == "integration":
        return "Contract test + secret handling review + webhook or SDK boundary validation."
    return "Operator runbook review + dry-run or seed validation in isolated environment."


def infer_domain_target(spec: InventorySpec, file_path: Path, capability_type: str) -> str:
    stem = file_path.stem
    if capability_type == "integration":
        return "integration_boundary"
    if capability_type == "migration":
        return "ainerwise_core_data"
    if capability_type == "frontend_workflow":
        if "admin" in spec.name:
            return "frontend_admin"
        if "h5" in spec.name:
            return "shared_h5_portals"
        return "shared_pc_portals"
    if capability_type == "infrastructure":
        return "shared_platform_infrastructure"
    if spec.source_project == "CebuProjects":
        return f"cebu_domain::{stem}"
    return f"core_domain::{stem}"


def infer_domain_user_role(capability_type: str) -> str:
    if capability_type == "migration":
        return "migration_operator, database_owner"
    if capability_type == "integration":
        return "system_integration, admin"
    if capability_type == "frontend_workflow":
        return "portal_member"
    if capability_type == "infrastructure":
        return "devops_operator, platform_owner"
    return "owning_module_operator, system_worker"


def infer_domain_data_owner(spec: InventorySpec, file_path: Path, capability_type: str) -> str:
    if capability_type == "migration":
        return "ainerwise_core_data" if spec.source_project == "Ainerwise" else "legacy_cebu_data"
    if capability_type == "integration":
        return "integration_boundary"
    if capability_type == "frontend_workflow":
        return "owning_portal_and_core_api"
    if capability_type == "infrastructure":
        return "shared_platform_middleware"
    return f"{'legacy_cebu' if spec.source_project == 'CebuProjects' else 'core'}::{file_path.stem}"


def infer_domain_permission(capability_type: str) -> str:
    if capability_type == "migration":
        return "single migration lock + database owner + rollback approval"
    if capability_type == "integration":
        return "integration credential + allowlist + idempotency + audit"
    if capability_type == "frontend_workflow":
        return "portal route guard + Core API object authorization"
    if capability_type == "infrastructure":
        return "change approval + secret review + environment isolation + rollback"
    return "owning module authorization + workspace/company/region/object scope"


def infer_domain_migration(spec: InventorySpec, capability_type: str) -> str:
    if spec.source_project == "CebuProjects":
        return "Preserve behavior and data semantics while moving implementation into the owning Ainerwise module; keep CebuProjects read-only."
    if capability_type == "migration":
        return "Retain serialized Ainerwise migration chain; prove upgrade, downgrade, and reconciliation."
    return "Retain in Ainerwise and verify the capability belongs to the declared module boundary."


def infer_domain_verification(capability_type: str) -> str:
    if capability_type == "migration":
        return "Single-head check + upgrade/downgrade/upgrade + row reconciliation + rollback evidence."
    if capability_type == "integration":
        return "Contract test + secret review + idempotency/retry + external dependency boundary evidence."
    if capability_type == "frontend_workflow":
        return "Browser workflow E2E + API contract + unauthorized route/object negative tests."
    if capability_type == "infrastructure":
        return "Compose config validation + clean rebuild + service health + routing smoke + rollback evidence."
    return "Domain unit tests + API integration tests + object authorization negative tests."


def infer_model_owner(file_path: Path) -> str:
    return f"core_domain::{file_path.stem}"


def infer_role_migration_strategy(source_project: str) -> str:
    if source_project == "CebuProjects":
        return "Map the legacy role into Membership, Portal Grant, and object-scope rules before any legacy portal can be retired."
    return "Retain as current core role taxonomy and verify grant-based portal segregation instead of broad UI exposure."


def infer_api_target_portal(spec: InventorySpec, api_route: dict[str, str]) -> str:
    path = api_route["path"]
    if spec.source_project == "CebuProjects":
        if spec.source_surface == "Admin API":
            return "cebu_admin"
        if path.startswith("/admin"):
            return "cebu_admin"
        if path.startswith("/auth"):
            return "shared_auth"
        if "/supplier" in path or any(token in path for token in ("/catalog", "/ranking")):
            return "supplier_pc"
        if "/buyer" in path or any(token in path for token in ("/intents", "/addresses")):
            return "cebu_buyer_pc"
        return "cebu_trade_shared"
    if path.startswith("/api/v1/auth") or path.startswith("/auth"):
        return "shared_auth"
    if any(token in path for token in ("/field", "/crew", "/workers", "/dispatch")):
        return "field_worker_h5"
    if any(token in path for token in ("/marketing", "/brief", "/campaign")):
        return "marketing_admin"
    return "ainerwise_core_api"


def infer_api_user_role(spec: InventorySpec, api_route: dict[str, str]) -> str:
    path = api_route["path"]
    if spec.source_surface == "Admin API":
        return "admin, finance_auditor, ai_supervisor, marketing_operator, project_manager"
    if path.startswith("/auth") or path.startswith("/api/v1/auth"):
        return "anonymous_guest, authenticated_user"
    if any(token in path for token in ("/offers", "/companies", "/catalog", "/shipping", "/wallets", "/payments")):
        return "supplier_operator"
    if any(token in path for token in ("/intents", "/buyer", "/orders", "/messages", "/notifications", "/addresses")):
        return "buyer, customer_owner, customer_member"
    if any(token in path for token in ("/field", "/crew", "/workers", "/dispatch")):
        return "crew_lead, installer_worker, electrician_worker, maintenance_worker, project_manager"
    if any(token in path for token in ("/marketing", "/brief", "/campaign")):
        return "marketing_operator, admin"
    return "authenticated_user"


def infer_api_target_route(spec: InventorySpec, api_route: dict[str, str]) -> str:
    if spec.source_project == "CebuProjects" and not api_route["path"].startswith("/api"):
        return f"/api/v1/cebu-compat{api_route['path']}"
    return api_route["path"]


def infer_api_data_owner(spec: InventorySpec, file_path: Path, api_route: dict[str, str]) -> str:
    stem = file_path.stem
    if spec.source_project == "CebuProjects":
        return f"legacy_compat::{stem}"
    if "procurement" in stem or "procurement" in api_route["path"]:
        return "procurement_core"
    if any(token in stem for token in ("marketing", "brief")):
        return "marketing_core"
    if any(token in stem for token in ("portal", "auth")):
        return "identity_and_portal_core"
    return f"core::{stem}"


def infer_api_permission(spec: InventorySpec, api_route: dict[str, str], target_portal: str) -> str:
    method = api_route["method"]
    base = "object_scope + workspace_id + portal_key + region"
    if target_portal == "shared_auth":
        return "anonymous_or_authenticated + token_scope"
    if method == "GET":
        return f"read_scope + {base}"
    return f"write_scope + {base}"


def infer_api_migration_strategy(spec: InventorySpec) -> str:
    if spec.source_project == "CebuProjects":
        return "Preserve legacy API semantics through compatibility layer while moving ownership and object checks into Ainerwise Core."
    return "Retain as Core API and link each route to portal grants, audit, and parity verification evidence."


def infer_api_verification_strategy(spec: InventorySpec) -> str:
    if spec.source_project == "CebuProjects":
        return "Compatibility contract tests + ownership negative tests + portal/workspace/region isolation tests."
    return "Unit/integration tests + portal grant checks + audit/outbox validation for state-changing commands."


def infer_runtime_api_target_portal(service: str, api_route: dict[str, str]) -> str:
    path = api_route["path"]
    if service == "ai-orchestrator":
        return "ai_solution_core"
    if service == "channel-gateway":
        return "integration_boundary"
    if path.startswith("/api/v1/auth"):
        return "shared_auth"
    if any(token in path for token in ("/field", "/crew", "/workers", "/dispatch")):
        return "field_worker_h5"
    if any(token in path for token in ("/marketing", "/brief", "/campaign")):
        return "marketing_admin"
    return "ainerwise_core_api"


def infer_runtime_api_user_role(service: str, api_route: dict[str, str]) -> str:
    path = api_route["path"]
    if service in {"ai-orchestrator", "channel-gateway"}:
        return "system_integration, service_operator"
    if path.startswith("/api/v1/auth"):
        return "anonymous_guest, authenticated_user"
    if any(token in path for token in ("/field", "/crew", "/workers", "/dispatch")):
        return "crew_lead, field_worker, project_manager"
    if any(token in path for token in ("/marketing", "/brief", "/campaign")):
        return "marketing_operator, admin"
    return "authenticated_user, owning_module_operator"


def infer_runtime_api_data_owner(service: str, api_route: dict[str, str]) -> str:
    if service == "ai-orchestrator":
        return "ai_solution_core"
    if service == "channel-gateway":
        return "integration_boundary"
    path = api_route["path"]
    if "/procurement" in path:
        return "procurement_core"
    if any(token in path for token in ("/marketing", "/brief", "/campaign")):
        return "marketing_core"
    if any(token in path for token in ("/auth", "/portal")):
        return "identity_and_portal_core"
    return "ainerwise_core_api"


def infer_runtime_api_permission(service: str, api_route: dict[str, str], target_portal: str) -> str:
    path = api_route["path"]
    if service == "ai-orchestrator":
        return "service_token + internal_network + audit"
    if service == "channel-gateway" and path.startswith("/webhooks/"):
        return "provider_webhook_signature + idempotency + audit"
    if service == "channel-gateway":
        return "service_token + internal_network + idempotency + audit"
    if target_portal == "shared_auth":
        return "anonymous_or_authenticated + token_scope"
    method = api_route["method"]
    scope = "read_scope" if method == "GET" else "write_scope"
    return f"{scope} + object_scope + workspace_id + portal_key + region"


def build_entry_id(source_project: str, source_surface: str, raw: str) -> str:
    token = f"{source_project}-{source_surface}-{raw}".lower()
    token = token.replace("/", "-").replace(" ", "-").replace(":", "-")
    token = re.sub(r"[^a-z0-9_-]+", "-", token)
    token = re.sub(r"-+", "-", token)
    return token.strip("-")


def build_feature_parity_markdown(payload: dict) -> str:
    entries = payload["entries"]
    lines = [
        "# Feature Parity Ledger\n",
        f"Generated at: {payload['generated_at']}\n",
        "\n",
        "This file is generated from the repository source tree. Edit the generator, then regenerate the ledger.\n",
        "\n",
        "## Summary\n",
        "\n",
        "| Source Project | Surface | Capability Type | Count | Status Mix |\n",
        "|---|---|---:|---:|---|\n",
    ]
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[(entry["source_project"], entry["source_surface"], entry["capability_type"])].append(entry)
    for key in sorted(grouped):
        bucket = grouped[key]
        statuses = Counter(item["status"] for item in bucket)
        status_mix = ", ".join(f"{name}:{count}" for name, count in sorted(statuses.items()))
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {len(bucket)} | {status_mix} |\n")

    lines.extend(
        [
            "\n",
            "## Cebu Baseline Guards\n",
            "\n",
            "| Source Project | Surface | Capability Type | Expected | Actual | Result |\n",
            "|---|---|---:|---:|---:|---|\n",
        ]
    )
    actuals = Counter((entry["source_project"], entry["source_surface"], entry["capability_type"]) for entry in entries)
    for key, expected in EXPECTED_CEBU_BASELINES.items():
        actual = actuals.get(key, 0)
        result = "PASS" if actual == expected else "FAIL"
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {expected} | {actual} | {result} |\n")

    lines.extend(
        [
            "\n",
            "## Portal Coverage Snapshot\n",
            "\n",
            "| Target Portal | Source Entries | Source Projects |\n",
            "|---|---:|---|\n",
        ]
    )
    portal_counts: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        portal_counts[entry["target_portal"]].append(entry)
    for portal in sorted(portal_counts):
        projects = sorted({item["source_project"] for item in portal_counts[portal]})
        lines.append(f"| {portal} | {len(portal_counts[portal])} | {', '.join(projects)} |\n")

    lines.extend(
        [
            "\n",
            "## Immediate Gaps\n",
            "\n",
            "- Cebu legacy entries remain TODO until route, API, object permission, and parity evidence are mapped and independently verified.\n",
            "- Existing Ainerwise entries are conservatively seeded as READY_FOR_VERIFY; this is not VERIFIED evidence.\n",
            "- VERIFIED is rejected unless status-overrides.json contains repeatable independent verification evidence.\n",
            "- Portal route ownership, shared auth, compatibility APIs, worker/offline capabilities, automation tasks, and external integrations remain dependent on follow-up implementation packages.\n",
        ]
    )
    return "".join(lines)


def build_portal_route_matrix(payload: dict) -> str:
    entries = payload["entries"]
    lines = [
        "# Portal Route Matrix\n",
        f"Generated at: {payload['generated_at']}\n",
        "\n",
        "| Target Portal | Physical Frontend | Roles | Source Entries | Representative Routes |\n",
        "|---|---|---|---:|---|\n",
    ]
    portal_info = {
        "consumer_pc": ("frontend-pc", "customer_owner, customer_member, anonymous_guest"),
        "consumer_h5": ("frontend-h5", "customer_owner, customer_member, anonymous_guest"),
        "customer_pc": ("frontend-pc", "customer_owner, customer_member"),
        "customer_h5": ("frontend-h5", "customer_owner, customer_member"),
        "cebu_public_pc": ("frontend-pc", "anonymous_guest, buyer, supplier_operator"),
        "cebu_buyer_pc": ("frontend-pc", "buyer, customer_owner, customer_member"),
        "cebu_buyer_h5": ("frontend-h5", "buyer, customer_owner, customer_member"),
        "supplier_pc": ("frontend-pc", "supplier_operator"),
        "supplier_h5": ("frontend-h5", "supplier_operator"),
        "partner_company_pc": ("frontend-pc", "partner_company_owner, partner_dispatcher"),
        "partner_company_h5": ("frontend-h5", "partner_company_owner, partner_dispatcher"),
        "field_worker_h5": ("frontend-h5", "crew_lead, installer_worker, electrician_worker, maintenance_worker"),
        "crew_lead_h5": ("frontend-h5", "crew_lead"),
        "marketing_h5": ("frontend-h5", "marketing_operator"),
        "kiosk_h5": ("frontend-h5", "kiosk_staff, anonymous_guest"),
        "developer_pc": ("frontend-pc", "developer"),
        "frontend_admin": ("frontend-admin", "admin, finance_auditor, project_manager"),
        "cebu_admin": ("frontend-admin", "admin, finance_auditor, risk_operator"),
        "cebu_trade_shared": ("backend", "buyer, supplier_operator, finance_auditor"),
        "marketing_admin": ("frontend-admin", "marketing_operator, admin"),
        "ai_supervisor_admin": ("frontend-admin", "ai_supervisor, admin"),
        "shared_auth": ("backend", "anonymous_or_authenticated"),
        "ainerwise_core_api": ("backend", "authenticated_via_grants"),
        "identity_and_portal_core": ("backend", "authenticated_via_membership_and_grants"),
        "automation_core": ("worker", "system_worker, admin"),
        "integration_boundary": ("backend", "admin, system_integration"),
        "migration_control": ("operator", "admin, devops_operator"),
        "ainerwise_core_data": ("backend", "database_owner, owning_module_operator"),
        "shared_pc_portals": ("frontend-pc", "portal_member"),
        "shared_h5_portals": ("frontend-h5", "portal_member"),
    }
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if entry["target_portal"] in portal_info:
            grouped[entry["target_portal"]].append(entry)
    for portal in sorted(grouped):
        samples = sorted({item["target_route_or_api"] for item in grouped[portal] if item["capability_type"] != "api"})[:5]
        physical, roles = portal_info.get(portal, ("unassigned", "pending"))
        lines.append(f"| {portal} | {physical} | {roles} | {len(grouped[portal])} | {', '.join(samples) if samples else 'API only'} |\n")

    lines.extend(
        [
            "\n",
            "## Route Guard Notes\n",
            "\n",
            "- Customer, Partner Company, Supplier, Field Worker, and Cebu Buyer must render distinct layouts, menus, and route allowlists even when they share a physical frontend.\n",
            "- Any route listed here still needs membership, portal grant, workspace, region, and object-level verification before it can move to VERIFIED.\n",
            "- Cebu public PC routes are intentionally isolated under the cebu portal family to avoid collapsing buyer and supplier flows into a generic consumer shell.\n",
        ]
    )
    return "".join(lines)


def build_api_migration_matrix(payload: dict) -> str:
    entries = [entry for entry in payload["entries"] if entry["capability_type"] == "api"]
    lines = [
        "# API Data Migration Matrix\n",
        f"Generated at: {payload['generated_at']}\n",
        "\n",
        "| Source Project | Source Surface | Source File | API Count | Target API Base | Data Owner | Migration Strategy |\n",
        "|---|---|---|---:|---|---|---|\n",
    ]
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[(entry["source_project"], entry["source_surface"], entry["source_path"])].append(entry)
    for key in sorted(grouped):
        bucket = grouped[key]
        targets = sorted({item["target_route_or_api"].split("/")[1] if item["target_route_or_api"].startswith("/") and len(item["target_route_or_api"].split("/")) > 1 else item["target_route_or_api"] for item in bucket})
        owners = sorted({item["data_owner"] for item in bucket})
        strategies = sorted({item["migration"] for item in bucket})
        lines.append(
            f"| {key[0]} | {key[1]} | {key[2]} | {len(bucket)} | {', '.join(targets)} | {', '.join(owners[:2])}{' ...' if len(owners) > 2 else ''} | {strategies[0]} |\n"
        )

    lines.extend(
        [
            "\n",
            "## Ownership Priorities\n",
            "\n",
            "- Compatibility APIs from CebuProjects must move ownership checks into Ainerwise Core before they can be treated as migrated.\n",
            "- Admin API rows must remove wildcard admin permissions and be remapped to explicit grants before verification.\n",
            "- Field, procurement, supplier, and order routes require workspace, portal, region, and object ownership evidence in their negative tests.\n",
        ]
    )
    return "".join(lines)


def build_work_packages(payload: dict) -> str:
    counts = Counter((entry["source_project"], entry["source_surface"]) for entry in payload["entries"])
    lines = [
        "# Parallel Agent Work Packages\n",
        f"Generated at: {payload['generated_at']}\n",
        "\n",
        "The work packages below are derived from the current zero-loss inventory and preserve the single-migration-lock rule.\n",
        "\n",
        "## Shared Preconditions\n",
        "\n",
        "- Root of truth: /Users/mac/Code_Start/Aislos\n",
        "- Status flow: TODO -> IN_PROGRESS -> READY_FOR_VERIFY -> VERIFIED or FAILED_VERIFY\n",
        "- No agent may self-mark VERIFIED\n",
        "- Backend schema migrations remain serialized behind a global lock\n",
        "\n",
        "## Agent 1: Security and Permissions\n",
        "\n",
        "- Scope: Ainerwise/backend and Cebu compatibility ownership paths only\n",
        "- Primary inputs: compatibility APIs, portal grants, procurement ownership, field permissions\n",
        "- File ownership: Ainerwise/backend/app, Ainerwise/backend/tests\n",
        "- Cannot overlap with any other backend migration package\n",
        "\n",
        "## Agent 2: Frontend Build and CI\n",
        "\n",
        "- Scope: frontend-pc, frontend-h5, frontend-admin, lockfiles, CI definitions\n",
        "- Guardrail: no business behavior changes\n",
        "- Parallel-safe with Agent 1 because it must not touch backend business logic\n",
        "\n",
        "## Agent 3: Portal Foundation\n",
        "\n",
        "- Scope: shared portal manifest state, portal switch, route/menu/layout grant enforcement\n",
        "- Depends on: ZL01 inventory and the security contract that defines valid grants\n",
        "- File ownership: frontend-pc, frontend-h5, frontend-admin portal infrastructure files plus supporting auth endpoints\n",
        "\n",
        "## Agent 4: Field Operations and Worker PWA\n",
        "\n",
        "- Scope: field operations admin models and worker H5 real-device flows\n",
        "- Depends on: Agent 3 portal foundation\n",
        "- Validation must include photo, scan, signature, location, offline queue, and conflict recovery evidence\n",
        "\n",
        "## Agent 5: Cebu Zero-Loss Migration\n",
        "\n",
        f"- Inventory baseline: Cebu PC {counts.get(('CebuProjects', 'PC'), 0)} entries, H5 {counts.get(('CebuProjects', 'H5'), 0)} entries, Admin {counts.get(('CebuProjects', 'Admin'), 0)} entries\n",
        "- Migration batches: Marketplace, RFQ, Offer, Order, Message, Wallet, Dispute, KYC, Buyer, Supplier, Admin, Notifications\n",
        "- Each batch must link old route, new route, new API, permission rule, tests, and screenshots before READY_FOR_VERIFY\n",
        "\n",
        "## Agent 6: Independent Verification\n",
        "\n",
        "- Scope: read-only verification and reproducible failure evidence only\n",
        "- Must reject placeholder data, fake completion, early-return tests, and privilege-escalation paths\n",
        "- Can move tasks from READY_FOR_VERIFY to VERIFIED or FAILED_VERIFY only\n",
    ]
    return "".join(lines)


def build_verification_risk_register(payload: dict) -> str:
    risks = payload["verification_risks"]
    flagged_entries = [entry for entry in payload["entries"] if entry.get("risk_flags")]
    lines = [
        "# Verification Risk Register\n",
        f"Generated at: {payload['generated_at']}\n",
        "\n",
        "These findings block the affected capability from VERIFIED until an independent verifier confirms the risk is removed or explicitly accepted.\n",
        "\n",
        "## Source Capability Risks\n",
        "\n",
        "| Source | Capability | Risk Flags | Status |\n",
        "|---|---|---|---|\n",
    ]
    for entry in flagged_entries:
        lines.append(
            f"| {entry['source_path']} | {entry['source_route_or_capability']} | {', '.join(entry['risk_flags'])} | {entry['status']} |\n"
        )
    if not flagged_entries:
        lines.append("| — | — | none detected | — |\n")
    lines.extend(
        [
            "\n",
            "## Test Quality Risks\n",
            "\n",
            "| Source | Line | Risk | Detail | Required Action |\n",
            "|---|---:|---|---|---|\n",
        ]
    )
    for risk in risks:
        detail = str(risk["detail"]).replace("|", "\\|")
        action = str(risk["required_action"]).replace("|", "\\|")
        lines.append(
            f"| {risk['source_path']} | {risk['line']} | {risk['risk']} | {detail} | {action} |\n"
        )
    if not risks:
        lines.append("| — | — | none detected | — | — |\n")
    return "".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

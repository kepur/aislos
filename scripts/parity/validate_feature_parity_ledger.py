#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "docs" / "parity" / "feature-parity-ledger.json"
RUNTIME_API_MANIFEST_PATH = ROOT / "docs" / "parity" / "runtime-api-manifest.json"
REQUIRED_FIELDS = {
    "entry_id",
    "source_project",
    "source_surface",
    "source_route_or_capability",
    "source_path",
    "capability_type",
    "user_role",
    "target_portal",
    "target_route_or_api",
    "data_owner",
    "permission",
    "migration",
    "verification",
    "verification_evidence",
    "status",
}
ALLOWED_STATUSES = {
    "TODO",
    "IN_PROGRESS",
    "READY_FOR_VERIFY",
    "VERIFIED",
    "FAILED_VERIFY",
    "BLOCKED",
}
EXPECTED_CEBU_BASELINES = {
    ("CebuProjects", "PC", "page"): 59,
    ("CebuProjects", "H5", "page"): 41,
    ("CebuProjects", "Admin", "admin_view"): 24,
}
MINIMUM_REQUIRED_SURFACES = {
    ("Ainerwise", "Task", "task"): 1,
    ("Ainerwise", "Integration", "integration"): 1,
    ("Ainerwise", "Role", "role"): 1,
    ("Ainerwise", "Permission", "permission_model"): 1,
    ("CebuProjects", "Role", "role"): 1,
    ("CebuProjects", "Data", "model"): 1,
    ("CebuProjects", "Service", "service"): 1,
    ("CebuProjects", "Migration", "migration"): 1,
    ("CebuProjects", "Workflow", "frontend_workflow"): 1,
    ("Ainerwise", "Data", "model"): 1,
    ("Ainerwise", "Service", "service"): 1,
    ("Ainerwise", "Migration", "migration"): 1,
    ("Ainerwise", "Gap", "planned_portal_gap"): 6,
    ("Ainerwise", "Runtime API", "api"): 1,
}


def main() -> int:
    if not LEDGER_PATH.exists():
        raise SystemExit(f"Ledger file not found: {LEDGER_PATH}")
    payload = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    if not entries:
        raise SystemExit("Ledger has no entries")
    verification_risks = payload.get("verification_risks")
    if not isinstance(verification_risks, list):
        raise SystemExit("Ledger verification_risks must be a list")
    source_inventory_expectations = payload.get("source_inventory_expectations")
    if not isinstance(source_inventory_expectations, list):
        raise SystemExit("Ledger source_inventory_expectations must be a list")

    generator_path = ROOT / "scripts" / "parity" / "generate_feature_parity_ledger.py"
    spec = importlib.util.spec_from_file_location("parity_generator", generator_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Cannot load parity generator for source fingerprint validation")
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    try:
        valid_attestations = generator.load_valid_verification_attestations()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    seen_ids: set[str] = set()
    seen_capabilities: set[tuple[str, str, str, str]] = set()
    counts = Counter()
    for index, entry in enumerate(entries, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in entry]
        if missing:
            raise SystemExit(f"Entry {index} missing required fields: {', '.join(sorted(missing))}")
        empty = [
            field
            for field in REQUIRED_FIELDS - {"verification_evidence"}
            if not entry.get(field)
        ]
        if empty:
            raise SystemExit(f"Entry {index} has empty required fields: {', '.join(sorted(empty))}")
        if not isinstance(entry["verification_evidence"], list):
            raise SystemExit(f"Entry {index} verification_evidence must be a list")
        status = entry["status"]
        if status not in ALLOWED_STATUSES:
            raise SystemExit(f"Entry {entry['entry_id']} has invalid status: {status}")
        entry_id = entry["entry_id"]
        if entry_id in seen_ids:
            raise SystemExit(f"Duplicate entry_id detected: {entry_id}")
        seen_ids.add(entry_id)
        capability_key = (
            entry["source_project"],
            entry["source_surface"],
            entry["source_path"],
            entry["source_route_or_capability"],
        )
        if capability_key in seen_capabilities:
            raise SystemExit(f"Duplicate source capability detected: {capability_key}")
        seen_capabilities.add(capability_key)
        if status == "VERIFIED":
            evidence_ids = {
                evidence.get("attestation_id")
                for evidence in entry["verification_evidence"]
                if isinstance(evidence, dict)
            }
            if not evidence_ids or not evidence_ids.issubset(valid_attestations):
                raise SystemExit(f"VERIFIED entry lacks a valid independent attestation: {entry_id}")
        if entry.get("risk_flags") and status in {"READY_FOR_VERIFY", "VERIFIED"}:
            raise SystemExit(f"Risk-flagged entry cannot be {status}: {entry_id}")
        counts[(entry["source_project"], entry["source_surface"], entry["capability_type"])] += 1

    for index, risk in enumerate(verification_risks, start=1):
        required = {"source_path", "line", "risk", "detail", "required_action"}
        missing = required - set(risk)
        if missing:
            raise SystemExit(f"Verification risk {index} missing fields: {', '.join(sorted(missing))}")

    for key, expected in EXPECTED_CEBU_BASELINES.items():
        actual = counts.get(key, 0)
        if actual != expected:
            raise SystemExit(
                f"Baseline mismatch for {key[0]} {key[1]} {key[2]}: expected {expected}, found {actual}"
            )

    for key, minimum in MINIMUM_REQUIRED_SURFACES.items():
        actual = counts.get(key, 0)
        if actual < minimum:
            raise SystemExit(
                f"Required parity surface missing for {key[0]} {key[1]} {key[2]}: expected at least {minimum}, found {actual}"
            )

    expected_inventory = {
        (
            item["source_project"],
            item["source_surface"],
            item["capability_type"],
        ): item["expected_count"]
        for item in source_inventory_expectations
    }
    current_inventory = {
        (
            item["source_project"],
            item["source_surface"],
            item["capability_type"],
        ): item["expected_count"]
        for item in generator.build_source_inventory_expectations()
    }
    if expected_inventory != current_inventory:
        raise SystemExit(
            "Ledger source inventory expectations are stale. Run: "
            "python3 scripts/parity/generate_feature_parity_ledger.py"
        )
    for key, expected in expected_inventory.items():
        actual = counts.get(key, 0)
        if actual != expected:
            raise SystemExit(
                f"Exact source inventory mismatch for {key[0]} {key[1]} {key[2]}: "
                f"expected {expected}, found {actual}"
            )

    validate_runtime_api_coverage(generator, entries)
    expected_fingerprint = generator.calculate_source_fingerprint()
    if payload.get("source_fingerprint") != expected_fingerprint:
        raise SystemExit(
            "Ledger source fingerprint is stale. Run: python3 scripts/parity/generate_feature_parity_ledger.py"
        )

    print(f"Validated {len(entries)} ledger entries")
    print(f"Source fingerprint: {expected_fingerprint}")
    for key, expected in EXPECTED_CEBU_BASELINES.items():
        print(f"Baseline {key[0]} {key[1]} {key[2]}: {expected}")
    for key, minimum in MINIMUM_REQUIRED_SURFACES.items():
        print(f"Surface {key[0]} {key[1]} {key[2]} >= {minimum}")
    return 0


def validate_runtime_api_coverage(generator, entries: list[dict]) -> None:
    if not RUNTIME_API_MANIFEST_PATH.exists():
        raise SystemExit(f"Runtime API manifest not found: {RUNTIME_API_MANIFEST_PATH}")
    manifest = json.loads(RUNTIME_API_MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_source_fingerprint = generator.calculate_runtime_api_source_fingerprint()
    if manifest.get("source_fingerprint") != expected_source_fingerprint:
        raise SystemExit(
            "Runtime API manifest source fingerprint is stale. Run: "
            "python3 scripts/parity/export_runtime_api_manifest.py"
        )

    manifest_keys = {
        (route["service"], route["method"], route["path"])
        for route in manifest.get("routes", [])
    }
    if len(manifest_keys) != len(manifest.get("routes", [])):
        raise SystemExit("Runtime API manifest contains duplicate service/method/path routes")
    ledger_keys = {
        (
            entry.get("runtime_service"),
            entry["source_route_or_capability"].split(" ", 1)[0],
            entry["target_route_or_api"],
        )
        for entry in entries
        if entry["source_project"] == "Ainerwise" and entry["source_surface"] == "Runtime API"
    }
    missing = sorted(manifest_keys - ledger_keys)
    unexpected = sorted(ledger_keys - manifest_keys)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing={missing[:10]}")
        if unexpected:
            details.append(f"unexpected={unexpected[:10]}")
        raise SystemExit(f"Runtime API ledger coverage mismatch: {'; '.join(details)}")
    print(f"Runtime API coverage: {len(manifest_keys)} / {len(manifest_keys)}")


if __name__ == "__main__":
    raise SystemExit(main())

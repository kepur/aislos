#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from generate_feature_parity_ledger import calculate_runtime_api_source_fingerprint


ROOT = Path(__file__).resolve().parents[2]
AINERWISE_ROOT = ROOT / "Ainerwise"
OUTPUT_PATH = ROOT / "docs" / "parity" / "runtime-api-manifest.json"

SERVICES = (
    ("backend", "Ainerwise/backend"),
    ("ai-orchestrator", "Ainerwise/ai_orchestrator"),
    ("channel-gateway", "Ainerwise/channel_gateway"),
)

CONTAINER_EXPORT_CODE = r"""
import inspect
import json

from app.main import app

rows = []
for route in app.routes:
    methods = sorted((getattr(route, "methods", None) or set()) - {"HEAD", "OPTIONS"})
    endpoint = getattr(route, "endpoint", None)
    module = getattr(endpoint, "__module__", "")
    if module.startswith(("fastapi.", "starlette.")):
        continue
    source = inspect.getsourcefile(endpoint) if endpoint else None
    if source and source.startswith("/app/"):
        source = source.removeprefix("/app/")
    for method in methods:
        rows.append(
            {
                "method": method,
                "path": route.path,
                "endpoint": getattr(endpoint, "__qualname__", getattr(endpoint, "__name__", "unknown")),
                "source": source or "runtime-generated",
                "tags": list(getattr(route, "tags", None) or []),
            }
        )
print(json.dumps(rows, sort_keys=True))
"""


def main() -> int:
    all_routes: list[dict] = []
    for service, source_prefix in SERVICES:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", service, "python", "-c", CONTAINER_EXPORT_CODE],
            cwd=AINERWISE_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        routes = json.loads(result.stdout.strip())
        for route in routes:
            source = route.pop("source")
            route["service"] = service
            route["source_path"] = f"{source_prefix}/{source}"
            all_routes.append(route)

    all_routes.sort(key=lambda item: (item["service"], item["path"], item["method"], item["source_path"]))
    route_keys = [(row["service"], row["method"], row["path"]) for row in all_routes]
    duplicates = sorted({key for key in route_keys if route_keys.count(key) > 1})
    if duplicates:
        formatted = "\n".join(f"- {service} {method} {path}" for service, method, path in duplicates)
        raise SystemExit(f"Duplicate runtime API routes detected:\n{formatted}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_fingerprint": calculate_runtime_api_source_fingerprint(),
        "services": [service for service, _ in SERVICES],
        "routes": all_routes,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(all_routes)} runtime API routes to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

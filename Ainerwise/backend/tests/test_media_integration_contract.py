"""MI05: OpenAPI contract alignment and SDK idempotency semantics."""
from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

import httpx

from app.main import app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
FIXTURE_OPENAPI = Path(__file__).resolve().parent / "fixtures" / "media-integration-v1.yaml"
CANONICAL_OPENAPI = REPO_ROOT / "docs" / "openapi" / "media-integration-v1.yaml"
OPENAPI_PATH = CANONICAL_OPENAPI if CANONICAL_OPENAPI.is_file() else FIXTURE_OPENAPI
PYTHON_SDK = REPO_ROOT / "sdk" / "media-integration-python"
TS_SDK = REPO_ROOT / "sdk" / "media-integration-typescript" / "src" / "client.ts"
FIXTURE_PY_CLIENT = Path(__file__).resolve().parent / "fixtures" / "sdk" / "python_client.py"
FIXTURE_TS_CLIENT = Path(__file__).resolve().parent / "fixtures" / "sdk" / "typescript_client.ts"

EXTERNAL_ROUTE_PREFIX = "/api/v1/media-integration/v1"

OPENAPI_PATHS = {
    "/requests",
    "/requests/{request_id}",
    "/requests/{request_id}/claim",
    "/requests/{request_id}/heartbeat",
    "/requests/{request_id}/fail",
    "/requests/{request_id}/uploads",
    "/requests/{request_id}/assets",
    "/requests/{request_id}/complete",
}

MUTATING_OPS = {
    "claim",
    "heartbeat",
    "fail",
    "uploads",
    "assets",
    "complete",
}


def _openapi_declared_paths() -> set[str]:
    text = OPENAPI_PATH.read_text(encoding="utf-8")
    paths: set[str] = set()
    in_paths = False
    for line in text.splitlines():
        if line.strip() == "paths:":
            in_paths = True
            continue
        if in_paths:
            m = re.match(r"^  (/[^:]+):", line)
            if m:
                paths.add(m.group(1))
            elif line and not line.startswith(" "):
                break
    return paths


def _fastapi_external_paths() -> set[str]:
    paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith(EXTERNAL_ROUTE_PREFIX):
            continue
        suffix = path[len("/api/v1/media-integration/v1") :]
        paths.add(suffix or "/")
    return paths


def test_openapi_file_exists_and_declares_v1():
    assert OPENAPI_PATH.is_file()
    text = OPENAPI_PATH.read_text(encoding="utf-8")
    assert 'version: "1.0.0"' in text or "version: '1.0.0'" in text
    assert "/media-integration/v1" in text


def test_openapi_paths_match_fastapi_external_routes():
    declared = _openapi_declared_paths()
    assert declared == OPENAPI_PATHS
    runtime = _fastapi_external_paths()
    assert runtime == OPENAPI_PATHS


def test_openapi_mutations_require_idempotency_key():
    text = OPENAPI_PATH.read_text(encoding="utf-8")
    for op in MUTATING_OPS:
        section = f"/{op}" if op != "uploads" and op != "assets" else f"/requests/{{request_id}}/{op}"
        assert section in text
    assert "Idempotency-Key" in text
    assert "required: true" in text


def test_canonical_openapi_matches_fixture_when_present():
    if not CANONICAL_OPENAPI.is_file():
        return
    assert CANONICAL_OPENAPI.read_text(encoding="utf-8") == FIXTURE_OPENAPI.read_text(encoding="utf-8")


def test_python_sdk_sends_idempotency_key():
    if (PYTHON_SDK / "media_integration" / "client.py").is_file():
        sys.path.insert(0, str(PYTHON_SDK))
        from media_integration.client import MediaIntegrationClient
    else:
        import importlib.util

        spec = importlib.util.spec_from_file_location("fixture_media_client", FIXTURE_PY_CLIENT)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        MediaIntegrationClient = mod.MediaIntegrationClient

    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idempotency"] = request.headers.get("Idempotency-Key", "")
        return httpx.Response(200, json={"id": str(uuid.uuid4()), "status": "claimed"})

    transport = httpx.MockTransport(handler)
    with MediaIntegrationClient(
        "http://example.test/api/v1",
        "mic_test_secret",
        transport=transport,
    ) as client:
        client.claim(uuid.uuid4(), idempotency_key="contract-claim-key")

    assert captured["idempotency"] == "contract-claim-key"


def test_python_and_typescript_sdk_surface_parity():
    py_path = PYTHON_SDK / "media_integration" / "client.py"
    ts_path = TS_SDK
    py_client = (py_path if py_path.is_file() else FIXTURE_PY_CLIENT).read_text(encoding="utf-8")
    ts_client = (ts_path if ts_path.is_file() else FIXTURE_TS_CLIENT).read_text(encoding="utf-8")
    for method in (
        "list_requests",
        "listRequests",
        "claim",
        "heartbeat",
        "fail",
        "create_upload",
        "createUpload",
        "submit_asset",
        "submitAsset",
        "complete",
    ):
        assert method in py_client or method in ts_client
    assert "retryable" in py_client and "retryable" in ts_client
    assert "Idempotency-Key" in py_client and "Idempotency-Key" in ts_client


def test_openapi_excludes_admin_routes():
    text = OPENAPI_PATH.read_text(encoding="utf-8")
    assert "integration-clients" not in text
    assert "/admin/" not in text

#!/usr/bin/env bash
# SP05: Phase 1 Core procurement parity gate (legacy is read-only migration source).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"

echo "=== Alembic head ==="
docker compose exec -T backend sh -c "cd /app && alembic heads"

echo "=== Procurement tests ==="
docker compose exec -T backend sh -c "cd /app && python -m pytest -q tests/test_procurement_*.py"

echo "=== Legacy bridge tests ==="
docker compose exec -T backend sh -c "cd /app && python -m pytest -q tests/test_legacy_bridge.py"

echo "SP05 parity gate: Core procurement is the write path; Cebu legacy optional on :8100."

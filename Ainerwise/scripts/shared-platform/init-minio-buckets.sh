#!/usr/bin/env bash
# SP04: create isolated MinIO buckets for Core + Cebu import.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"

docker compose -f docker-compose.infrastructure.yml exec -T minio sh -c '
  mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" 2>/dev/null || true
  for b in product-assets knowledge-source project-evidence marketing-assets documents cebu-import quarantine; do
    mc mb -p "local/$b" 2>/dev/null || true
  done
  echo "Buckets ready"
'

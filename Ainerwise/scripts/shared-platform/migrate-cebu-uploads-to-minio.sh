#!/usr/bin/env bash
# SP04: stage Cebu local uploads into MinIO cebu-import (host-side mc required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CEBU_UPLOADS="${CEBU_UPLOADS:-$ROOT/../CebuProjects/backend/uploads}"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"

./scripts/shared-platform/init-minio-buckets.sh

if [ ! -d "$CEBU_UPLOADS" ]; then
  echo "No Cebu uploads at $CEBU_UPLOADS — nothing to migrate"
  exit 0
fi

if ! command -v mc >/dev/null 2>&1; then
  echo "Install MinIO client (mc) and configure alias 'local' -> http://localhost:9000"
  echo "Then: mc mirror $CEBU_UPLOADS local/cebu-import/legacy-uploads/"
  exit 1
fi

mc mirror "$CEBU_UPLOADS" local/cebu-import/legacy-uploads/
echo "Staged uploads under cebu-import/legacy-uploads/"

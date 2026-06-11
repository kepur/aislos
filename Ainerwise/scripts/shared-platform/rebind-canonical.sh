#!/usr/bin/env bash
# SP02: recreate app containers so bind mounts use canonical Aislos/Ainerwise paths.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"

SERVICES=(
  frontend-pc frontend-h5 frontend-admin store-frontend store-admin
  developer-portal partner-portal kiosk-portal marketing-portal agent-console
  celery-worker celery-beat ai-orchestrator channel-gateway nginx backend
)

echo "Recreating from ${ROOT} (compose project: ${COMPOSE_PROJECT_NAME})..."
docker compose up -d --force-recreate "${SERVICES[@]}"
echo "Done. Verify: curl -s -o /dev/null -w '%{http_code}' http://localhost:4099/procurement"

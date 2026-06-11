#!/usr/bin/env bash
# SP02: shared middleware + optional Cebu legacy backend (port 8100).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.legacy-cebu.yml \
  --profile legacy-cebu \
  up -d "$@"

#!/usr/bin/env bash
# SP02: start shared PostgreSQL, Redis, MinIO only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"
docker compose -f docker-compose.infrastructure.yml up -d "$@"

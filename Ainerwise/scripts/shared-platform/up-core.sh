#!/usr/bin/env bash
# SP02: full Ainerwise Core + portals from canonical workspace.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"
docker compose up -d "$@"

#!/usr/bin/env bash
# SP06: restore drill — verify dump integrity without overwriting live DB.
set -euo pipefail
DUMP="${1:?Usage: restore-drill.sh /path/to/ainerwise.dump}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"

docker compose -f docker-compose.infrastructure.yml exec -T postgres \
  pg_restore --list < "$DUMP" | head -20
echo "Restore drill: archive listing OK for $DUMP"
echo "Full restore requires maintenance window and separate database name."

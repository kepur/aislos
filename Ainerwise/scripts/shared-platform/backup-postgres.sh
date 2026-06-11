#!/usr/bin/env bash
# SP06: backup Core + Cebu legacy databases from shared postgres.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"
STAMP="${1:-$(date +%Y%m%d-%H%M%S)}"
OUT_DIR="${BACKUP_DIR:-$ROOT/backups}/$STAMP"
mkdir -p "$OUT_DIR"

for DB in ainerwise cebu; do
  docker compose -f docker-compose.infrastructure.yml exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-ainerwise}" -Fc "$DB" > "$OUT_DIR/${DB}.dump"
  echo "Wrote $OUT_DIR/${DB}.dump"
done

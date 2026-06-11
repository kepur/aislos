#!/usr/bin/env bash
# SP02: create cebu_app role + cebu database on an existing postgres volume.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ainerwise}"
CEBU_PW="${CEBU_LEGACY_DB_PASSWORD:-cebu_legacy_dev}"
PG_USER="${POSTGRES_USER:-ainerwise}"
PG_DB="${POSTGRES_DB:-ainerwise}"

docker compose -f docker-compose.infrastructure.yml exec -T postgres \
  psql -U "$PG_USER" -d "$PG_DB" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cebu_app') THEN CREATE ROLE cebu_app LOGIN PASSWORD '${CEBU_PW}'; END IF; END \$\$;"

if ! docker compose -f docker-compose.infrastructure.yml exec -T postgres \
  psql -U "$PG_USER" -tAc "SELECT 1 FROM pg_database WHERE datname = 'cebu'" | grep -q 1; then
  docker compose -f docker-compose.infrastructure.yml exec -T postgres \
    psql -U "$PG_USER" -c "CREATE DATABASE cebu OWNER cebu_app"
fi

docker compose -f docker-compose.infrastructure.yml exec -T postgres \
  psql -U "$PG_USER" -d "$PG_DB" -c "REVOKE ALL ON DATABASE cebu FROM PUBLIC" || true
docker compose -f docker-compose.infrastructure.yml exec -T postgres \
  psql -U "$PG_USER" -d "$PG_DB" -c "GRANT CONNECT ON DATABASE cebu TO cebu_app"

echo "Cebu legacy database ready (database=cebu, role=cebu_app)."

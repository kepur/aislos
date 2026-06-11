#!/bin/bash
# SP02: Cebu legacy database on shared PostgreSQL (first init only).
set -euo pipefail

CEBU_PW="${CEBU_LEGACY_DB_PASSWORD:-cebu_legacy_dev}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cebu_app') THEN
    CREATE ROLE cebu_app LOGIN PASSWORD '${CEBU_PW}';
  END IF;
END
\$\$;
EOSQL

if ! psql -tAc "SELECT 1 FROM pg_database WHERE datname = 'cebu'" | grep -q 1; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -c "CREATE DATABASE cebu OWNER cebu_app"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "REVOKE ALL ON DATABASE cebu FROM PUBLIC"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "GRANT CONNECT ON DATABASE cebu TO cebu_app"

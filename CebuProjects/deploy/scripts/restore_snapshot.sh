#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
ENV_FILE="${ROOT_DIR}/.env.prod"
COMPOSE_FILE="${ROOT_DIR}/deploy/compose/docker-compose.prod.yml"
SNAPSHOT_DIR="${1:-${ROOT_DIR}/deploy/export/current}"

export PROJECT_ROOT="${PROJECT_ROOT:-${ROOT_DIR}}"

if [[ ! -f "${ENV_FILE}" ]]; then
  if [[ -f "${SNAPSHOT_DIR}/config/.env.prod.current" ]]; then
    cp "${SNAPSHOT_DIR}/config/.env.prod.current" "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
  else
    echo "Missing ${ENV_FILE}. Copy deploy/env/.env.prod.example to .env.prod and edit it first."
    exit 1
  fi
fi

if [[ ! -f "${SNAPSHOT_DIR}/db/procureping_full.sql" ]]; then
  echo "Missing SQL dump: ${SNAPSHOT_DIR}/db/procureping_full.sql"
  exit 1
fi

bash "${ROOT_DIR}/deploy/scripts/prepare.sh"

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d postgres

echo "Waiting for PostgreSQL..."
for _ in $(seq 1 60); do
  if docker exec procureping-postgres pg_isready -U "$(grep '^POSTGRES_USER=' "${ENV_FILE}" | cut -d= -f2-)" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Restoring database from ${SNAPSHOT_DIR}/db/procureping_full.sql ..."
cat "${SNAPSHOT_DIR}/db/procureping_full.sql" \
  | docker exec -i procureping-postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'

if [[ -f "${SNAPSHOT_DIR}/uploads/uploads.tar.gz" ]]; then
  echo "Restoring uploads..."
  mkdir -p "${ROOT_DIR}/data"
  tar -C "${ROOT_DIR}/data" -xzf "${SNAPSHOT_DIR}/uploads/uploads.tar.gz"
  chmod -R 775 "${ROOT_DIR}/data/uploads" || true
fi

echo "Starting full stack..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build

echo "Restore complete."

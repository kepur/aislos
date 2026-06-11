#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.prod"
COMPOSE_FILE="${ROOT_DIR}/deploy/compose/docker-compose.prod.yml"
export PROJECT_ROOT="${PROJECT_ROOT:-${ROOT_DIR}}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}"
  echo "Run: cp deploy/env/.env.prod.example .env.prod"
  exit 1
fi

bash "${ROOT_DIR}/deploy/scripts/prepare.sh"

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build

echo "Deployment complete."
echo "Check status:"
echo "docker compose --env-file ${ENV_FILE} -f ${COMPOSE_FILE} ps"

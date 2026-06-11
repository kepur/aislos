#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${PROJECT_ROOT:-/opt/cebuproject}"
DATA_DIR="${BASE_DIR}/data"

mkdir -p "${DATA_DIR}/postgres"
mkdir -p "${DATA_DIR}/uploads/avatars"
mkdir -p "${DATA_DIR}/uploads/kyc"
mkdir -p "${DATA_DIR}/uploads/catalog"
mkdir -p "${DATA_DIR}/uploads/messages"
mkdir -p "${DATA_DIR}/uploads/misc"

chmod -R 775 "${DATA_DIR}/uploads" || true

echo "Prepared persistent directories under ${DATA_DIR}"

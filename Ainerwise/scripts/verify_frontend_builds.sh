#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-build}"

node -e '
const [major, minor] = process.versions.node.split(".").map(Number);
const supported = (major === 20 && minor >= 19) || (major === 22 && minor >= 12);
if (!supported) {
  console.error(`Node ${process.versions.node} is unsupported. Use the repository .nvmrc (Node 22.14.0).`);
  process.exit(1);
}
'

for frontend in frontend-pc frontend-h5 frontend-admin; do
  echo "==> ${frontend}"
  cd "${ROOT_DIR}/${frontend}"
  if [[ "${MODE}" == "install-build" ]]; then
    npm ci
  fi
  npm run build
done

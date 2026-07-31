#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

python3 scripts/parity/export_runtime_api_manifest.py
python3 scripts/parity/generate_feature_parity_ledger.py
python3 scripts/parity/validate_feature_parity_ledger.py
python3 -m py_compile \
  scripts/parity/export_runtime_api_manifest.py \
  scripts/parity/generate_feature_parity_ledger.py \
  scripts/parity/validate_feature_parity_ledger.py
(cd Ainerwise && docker compose config --quiet)
git diff --check -- scripts/parity docs/parity FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md

echo "Feature parity ledger implementation checks passed; independent verification is still required."

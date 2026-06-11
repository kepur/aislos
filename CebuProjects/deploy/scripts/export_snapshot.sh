#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
EXPORT_DIR="${ROOT_DIR}/deploy/export/current"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${ROOT_DIR}/deploy/export/procureping-deploy-snapshot-${STAMP}.tar.gz"

mkdir -p "${EXPORT_DIR}/db" "${EXPORT_DIR}/uploads" "${EXPORT_DIR}/config" "${EXPORT_DIR}/manifests"

echo "Exporting PostgreSQL dump..."
docker exec procureping-postgres sh -c 'pg_dump --clean --if-exists --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "${EXPORT_DIR}/db/procureping_full.sql"

echo "Exporting uploads..."
tar -C "${ROOT_DIR}/data" -czf "${EXPORT_DIR}/uploads/uploads.tar.gz" uploads

echo "Copying deployment config..."
cp "${ROOT_DIR}/deploy/compose/docker-compose.prod.yml" "${EXPORT_DIR}/config/docker-compose.prod.yml"
cp "${ROOT_DIR}/deploy/nginx/nginx.conf" "${EXPORT_DIR}/config/nginx.conf"
cp -R "${ROOT_DIR}/deploy/nginx/conf.d" "${EXPORT_DIR}/config/nginx-conf.d"
cp "${ROOT_DIR}/deploy/env/.env.prod.example" "${EXPORT_DIR}/config/.env.prod.example"
if [[ -f "${ROOT_DIR}/.env.prod" ]]; then
  cp "${ROOT_DIR}/.env.prod" "${EXPORT_DIR}/config/.env.prod.current"
  chmod 600 "${EXPORT_DIR}/config/.env.prod.current"
fi

echo "Writing manifests..."
docker compose --env-file "${ROOT_DIR}/.env.prod" -f "${ROOT_DIR}/deploy/compose/docker-compose.prod.yml" ps \
  > "${EXPORT_DIR}/manifests/compose-ps.txt" || true
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}' \
  > "${EXPORT_DIR}/manifests/docker-images.txt" || true
find "${ROOT_DIR}/data/uploads" -type f -printf '%P\t%s bytes\n' \
  > "${EXPORT_DIR}/manifests/uploads-files.txt" || true

cat > "${EXPORT_DIR}/RESTORE_QUICKSTART.md" <<'EOF'
# ProcurePing Migration Snapshot

This snapshot contains:

- `db/procureping_full.sql`: full PostgreSQL dump, including schema and seeded/demo data.
- `uploads/uploads.tar.gz`: uploaded/static user files.
- `config/`: production compose, nginx config, env example, and `.env.prod.current` when present.
- `manifests/`: source container and file inventory.

## Restore On New Server

1. Put the project at `/opt/cebuproject` or set `PROJECT_ROOT=/your/path`.
2. Copy `config/.env.prod.current` to project root as `.env.prod`, or create one from `.env.prod.example`.
3. Run the restore helper:

```bash
bash deploy/scripts/restore_snapshot.sh
```

The helper starts PostgreSQL, restores SQL, restores uploads, and starts the full stack.

Manual restore steps are below if you prefer to run each step yourself.

## Manual Restore

Start database only:

```bash
docker compose --env-file .env.prod -f deploy/compose/docker-compose.prod.yml up -d postgres
```

Restore database:

```bash
cat deploy/export/current/db/procureping_full.sql | docker exec -i procureping-postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```

Restore uploads:

```bash
mkdir -p data
tar -C data -xzf deploy/export/current/uploads/uploads.tar.gz
```

Start everything:

```bash
bash deploy/scripts/deploy.sh
```
EOF

echo "Creating archive ${ARCHIVE}..."
tar -C "${ROOT_DIR}" \
  --exclude='admin-frontend/node_modules' \
  --exclude='admin-frontend/dist' \
  --exclude='pc-frontend/node_modules' \
  --exclude='pc-frontend/.nuxt' \
  --exclude='pc-frontend/.output' \
  --exclude='h5-frontend/node_modules' \
  --exclude='h5-frontend/.nuxt' \
  --exclude='h5-frontend/.output' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/postgres' \
  --exclude='deploy/export/procureping-deploy-snapshot-*.tar.gz' \
  -czf "${ARCHIVE}" \
  backend admin-backend admin-frontend pc-frontend h5-frontend deploy docker-compose.yml PROJECT_ARCHITECTURE.md DEPLOY_SKILL.md .env.prod

echo "Snapshot ready:"
echo "  ${EXPORT_DIR}"
echo "  ${ARCHIVE}"

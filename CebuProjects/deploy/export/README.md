# Deploy Export

Run this from the project root to refresh the migration snapshot:

```bash
bash deploy/scripts/export_snapshot.sh
```

The latest unpacked snapshot is written to `deploy/export/current`.

The script also creates a portable archive named:

```text
deploy/export/procureping-deploy-snapshot-YYYYMMDD-HHMMSS.tar.gz
```

The archive excludes live PostgreSQL data files and frontend build caches, but includes:

- source code needed to rebuild containers
- deploy compose/nginx/scripts/env files
- full SQL dump with current demo data
- uploads archive
- current `.env.prod` for direct migration

Restore the latest unpacked snapshot on a target server with:

```bash
bash deploy/scripts/restore_snapshot.sh
```

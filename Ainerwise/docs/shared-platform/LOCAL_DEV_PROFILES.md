# Local Dev Profiles (SP02)

Canonical workspace: `/Users/mac/Code_Start/Aislos/Ainerwise`  
Compose project: `ainerwise`

## Profiles

| 命令 | 用途 |
|------|------|
| `./scripts/shared-platform/up-infrastructure.sh` | 仅 PostgreSQL + Redis + MinIO |
| `./scripts/shared-platform/up-core.sh` | 完整 Ainerwise Core + 全部 Portal |
| `./scripts/shared-platform/up-legacy-cebu.sh` | 共享中间件 + Cebu legacy API（`:8100`） |
| `./scripts/shared-platform/rebind-canonical.sh` | 修复旧 checkout bind mount 漂移 |
| `./scripts/shared-platform/init-cebu-legacy-db.sh` | 在已有 postgres volume 上创建 `cebu` 库 |

等价 compose：

```bash
# 仅中间件
docker compose -f docker-compose.infrastructure.yml up -d

# 全栈（推荐）
docker compose up -d

# Legacy Cebu（迁移参考，非新业务写入目标）
docker compose -f docker-compose.infrastructure.yml -f docker-compose.legacy-cebu.yml --profile legacy-cebu up -d
```

## 隔离边界

| 资源 | Ainerwise Core | Cebu Legacy |
|------|----------------|-------------|
| PostgreSQL | database `ainerwise` | database `cebu` / role `cebu_app` |
| Redis Celery | prefix `ainerwise:celery:` | 独立进程时使用 `cebu-legacy:` |
| Legacy Bridge | `POST /api/v1/legacy-bridge/events` | HMAC 签名 + 幂等键 |
| Event streams | `ainerwise:stream:events` / `cebu-legacy:stream:bridge` | Core / Legacy 隔离 |
| MinIO | 业务 buckets | `cebu-import`（SP04 规划） |
| API 端口 | `8000` | `8100` |

## 禁止事项

- 禁止两个后端写同一 `public` schema。
- 禁止将 Cebu Alembic 链合并进 `Ainerwise/backend/alembic`。
- 禁止在未批准维护窗口外批量删除 compose 卷。

## 验证

```bash
curl -s http://localhost:8000/api/v1/procurement/portal-policy -H "X-Portal-Key: aislos" | head
docker compose exec postgres psql -U ainerwise -tAc "SELECT datname FROM pg_database"
```

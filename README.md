# AISLOS Monorepo

统一仓库：`git@github.com:kepur/aislos.git`

## 目录结构

```text
Aislos/
├── Ainerwise/          # 唯一实现目录 — Ainerwise Core + AISLOS Portals
├── CebuProjects/       # Legacy 采购交易域（迁移来源，逐步退役）
├── PROCUREMENT_PHASE1_EXECUTION_TASKS.md
├── SHARED_PLATFORM_MIDDLEWARE_PLAN.md
└── INTEGRATION_ASSESSMENT.md
```

## 快速开始

```bash
cd Ainerwise
cp .env.example .env
./scripts/shared-platform/up-core.sh
```

| 服务 | 地址 |
|------|------|
| AISLOS Website | http://localhost:4099 |
| Core API | http://localhost:8000/docs |
| Cebu Legacy（可选） | http://localhost:8100 |

## 架构原则

- **Ainerwise Core** = 唯一业务数据写入者
- **CebuProjects** = 迁移参考，新功能只在 Core 实现
- **共享中间件** = 同一 PostgreSQL / Redis / MinIO 物理集群，逻辑隔离 database / prefix / bucket

详见 [SHARED_PLATFORM_MIDDLEWARE_PLAN.md](SHARED_PLATFORM_MIDDLEWARE_PLAN.md) 与 [Ainerwise/docs/shared-platform/LOCAL_DEV_PROFILES.md](Ainerwise/docs/shared-platform/LOCAL_DEV_PROFILES.md)。

## Phase 1 采购

C01–C09 已全部 `VERIFIED`。运行手册：`Ainerwise/docs/procurement_phase1_runbook.md`。

## Shared Platform

SP00–SP06 已全部 `VERIFIED`。Legacy → Core 通过签名 Bridge：

```bash
# Cebu 发布采购需求到 Core（示例）
AINERWISE_CORE_URL=http://localhost:8000 LEGACY_BRIDGE_SECRET=... python -c "
import asyncio
from app.services.ainerwise_bridge import post_legacy_event
asyncio.run(post_legacy_event(event_type='procurement.request.created', payload={'legacy_request_id':'x','contact_email':'a@b.c'}))
"
```

详见 `SHARED_PLATFORM_MIDDLEWARE_PLAN.md`。

## 禁止

- 在 `/Users/mac/Code_Start/Ainerwise` 等旧 checkout 继续开发
- 两个后端共写同一 `public` schema
- 合并 Cebu 与 Ainerwise 的 Alembic migration 链

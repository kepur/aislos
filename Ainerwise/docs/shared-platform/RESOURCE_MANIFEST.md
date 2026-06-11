# Shared Platform Resource Manifest

日期：2026-06-11  
Owner：Platform Engineering / Ainerwise Core  
状态：SP01 草案（文档 only，不修改运行环境）

## 1. Canonical Workspace

| 项 | 值 |
|---|---|
| **Canonical workspace** | `/Users/mac/Code_Start/Aislos/Ainerwise` |
| **Compose project name** | `ainerwise` |
| **Compose file** | `/Users/mac/Code_Start/Aislos/Ainerwise/docker-compose.yml` |
| **Working directory** | `/Users/mac/Code_Start/Aislos/Ainerwise` |
| **正式实现目录** | 仅 `Aislos/Ainerwise`；禁止在 `/Users/mac/Code_Start/Ainerwise` 开发 |

### 1.1 混用 checkout 风险（当前观测）

截至 2026-06-11，运行中容器存在**同一 compose project 绑定两个源码 checkout** 的情况：

| 服务 | bind mount 来源 | 风险 |
|---|---|---|
| `backend`, `marketing-portal` | `/Users/mac/Code_Start/Aislos/Ainerwise/...` | ✅ canonical |
| `frontend-pc`, `frontend-h5`, `frontend-admin`, `celery-*`, `ai-orchestrator`, `channel-gateway`, `nginx` 等 | `/Users/mac/Code_Start/Ainerwise/...` | ⚠️ 旧 checkout，与 canonical 代码漂移 |

**切换方案（SP02 前不得擅自重建容器）：**

1. 在维护窗口内，对每个仍绑定旧路径的服务执行 `docker compose up -d <service>`（从 canonical working directory），使 bind mount 指向 `Aislos/Ainerwise`。
2. 切换后验证：各 Portal 页面、API smoke、Celery worker 队列消费正常。
3. 旧目录 `/Users/mac/Code_Start/Ainerwise` 保留为只读参考，直至 SP02 profile 验证通过。
4. **禁止**在未获用户批准前停止、删除或重建全部容器。

## 2. 服务 Owner 与环境

| 服务 | Owner | 环境 | 用途 |
|---|---|---|---|
| `postgres` | Ainerwise Core | local dev | 主业务库 + pgvector |
| `redis` | Ainerwise Core | local dev | Celery broker/backend、事件 Stream |
| `minio` | Ainerwise Core | local dev | 对象存储 |
| `backend` | Ainerwise Core | local dev | FastAPI 模块化单体 API |
| `celery-worker` / `celery-beat` | Ainerwise Core | local dev | 异步任务 |
| `ai-orchestrator` | AI Platform | local dev（内网） | LLM/embedding 编排，不对外暴露端口 |
| `channel-gateway` | Messaging | local dev（内网） | Telegram 等渠道 webhook |
| `nginx` | Platform Gateway | local dev | 反向代理、Portal Context 注入 |
| `frontend-*` / `*-portal` | Portal Teams | local dev | 多品牌 Nuxt 前端 |
| Cebu Legacy Backend | CebuProjects（过渡） | 待迁入 | 采购交易域迁移来源，**非写入目标** |
| AinerN2D / 外部媒体引擎 | 外部系统 | 生产/测试 | 仅通过 Marketing REST/OpenAPI/SDK |

## 3. PostgreSQL 隔离

| 逻辑域 | Database | Schema | Role | Migration owner |
|---|---|---|---|---|
| Ainerwise Core | `ainerwise` | `public` | `ainerwise`（应用） | `Ainerwise/backend/alembic` |
| AI Orchestrator | `ainerwise` | `public`（受限视图/role） | `ainerwise_orchestrator` | Orchestrator 独立初始化脚本 |
| Cebu Legacy（过渡） | `cebu` 或独立 schema（SP02） | `cebu` | `cebu_app`（规划） | **Cebu 独立 migration 链，禁止合并进 Ainerwise** |

- 金额字段：NUMERIC/Decimal，禁止 Float。
- 新状态：小写字符串。
- 关键引用：真实 Foreign Key。
- 当前 Alembic head：`028`（单一 head 要求见 MIGRATION_COORDINATION.md）。

## 4. Redis 隔离

| 用途 | Key / Queue | Owner | 说明 |
|---|---|---|---|
| Celery default | queue `default` | Core | 用户可见延迟任务、outbox relay |
| Celery AI | queue `ai_ingestion` | Core | 知识库 embedding |
| Celery automation | queue `automation` | Core | 生命周期/营销批处理 |
| Domain events | stream `stream:events` | Core | transactional outbox → Redis Stream |
| Cebu Legacy（规划） | prefix `cebu:` | Cebu 过渡 | SP02 启用独立 prefix，禁止与 Core 键冲突 |

- 认证：Redis `requirepass`（dev 占位符见 `.env.example`，**非真实生产 secret**）。
- 外部媒体系统：**不得**持有 Redis 访问权。

## 5. MinIO 隔离

| Bucket | Prefix / 用途 | Service account（规划） | Retention |
|---|---|---|---|
| `marketing-assets` | 营销素材导入/审核 | `svc-marketing-upload` | 业务策略 + 审核通过后长期保留 |
| `knowledge`（知识库） | 文档分块 | `svc-knowledge` | 与文档生命周期绑定 |
| `cebu-import`（规划 SP04） | Legacy uploads 迁移 | `svc-cebu-import` | 只读观察期后归档 |

- Root 凭据：仅基础设施管理员；应用使用 scoped service account。
- 外部媒体系统：仅 presigned PUT URL（短时），**无**长期 MinIO root 或 bucket admin。

## 6. Hostname 与 Portal Mapping

| 对外 Host（dev） | Portal key | 上游 |
|---|---|---|
| `localhost` | `aislos` | frontend-pc + backend |
| `cebu.localhost` | `cebu` | frontend-pc + backend（C08 前临时复用） |
| `localhost:4097` | admin | frontend-admin |
| `localhost:4094` | marketing | marketing-portal |
| `localhost:8000` | — | backend 直连（无网关 Portal 注入） |

内部 endpoint（Docker 网络）：

- `http://backend:8000/api/v1`
- `http://ai-orchestrator:8001`
- `http://channel-gateway:8200`
- `http://minio:9000`

## 7. 凭据与 Integration Client

| 凭据类型 | Scope / 用途 | 轮换责任 | 记录方式 |
|---|---|---|---|
| User JWT | 用户/管理员 API | Auth 团队 | 仅 `SECRET_KEY` 占位符在 `.env.example` |
| Service Token | 内部服务间调用 | Platform | `.env.example` 占位符 |
| Integration Client Secret | `media-integration/v1` 外部媒体 | Marketing Admin | DB `marketing_integration_clients`，**本文档不记录 secret** |
| Orchestrator DB role | 受限 SQL | AI Platform | 独立密码 env |

外部媒体系统 scopes（示例）：`briefs:read`, `briefs:claim`, `briefs:progress`, `briefs:upload`, `briefs:submit`。

## 8. 备份、RPO/RTO 与退役

| 资源 | 备份范围 | RPO（目标） | RTO（目标） | Restore owner | 退役条件 |
|---|---|---|---|---|---|
| PostgreSQL `ainerwise` | 全库 + WAL | 24h（dev N/A） | 4h | DBA / Platform | Cebu 数据核对完成 + 只读观察期结束 |
| Redis | RDB/AOF（生产） | 24h | 2h | Platform | 无独立业务状态要求持久化时 |
| MinIO | bucket 级复制 | 24h | 4h | Platform | Legacy bucket 迁移并核对后删除 import 副本 |
| Cebu Legacy Backend | DB + uploads | 迁移前全量 | — | Cebu 迁移负责人 | Parity + 核对报告 + 用户批准 |

**Legacy 退役门禁：** 未完成备份演练、数据核对和只读观察期前，**不得**删除 Legacy 数据或切换生产 DNS。

## 9. 外部系统边界

- AinerN2D 及其他媒体引擎：**仅**通过 `GET/POST /api/v1/media-integration/v1/*` 与 OpenAPI/SDK 对接。
- 禁止：外部系统访问 PostgreSQL、Redis、Celery、内部 API、长期 MinIO 凭据。
- 禁止：修改外部媒体引擎内部代码。

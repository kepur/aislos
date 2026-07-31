# Full Portal Zero-Loss Integration Tasks

更新日期：2026-06-12

## 0. 创始人冻结原则

> 原有 Ainerwise、AISLOS 与 CebuProjects 的功能只能增加，不能减少。两个项目结合后必须形成能力超集；任何原页面、按钮、API、工作流、数据、权限、后台任务和外部集成都必须有新归属。

三套物理前端代码基座不等于三个界面：

```text
frontend-pc
  -> 多个互相独立的 PC Logical Portal

frontend-h5
  -> 多个互相独立的 H5/PWA Logical Portal

frontend-admin
  -> 多个互相独立的内部 PC Workbench
```

迁移期间保留所有现有前端工程和兼容端口。只有通过本文件最终零损失发布闸门后，才允许逐个退役旧工程；退役必须获得创始人明确批准。

---

## 1. 零损失定义

每个旧能力都必须进入 `Feature Parity Ledger`，至少记录：

| 字段 | 要求 |
|---|---|
| source_project | `Ainerwise` / `AISLOS` / `CebuProjects` |
| source_surface | PC / H5 / Admin / API / Worker / Integration |
| source_route_or_capability | 原路由或能力标识 |
| user_role | 谁在使用 |
| target_portal | 目标 Logical Portal |
| target_route_or_api | 新路由或 Core API |
| data_owner | Core 模块与数据表 |
| permission | Membership / Grant / 对象级权限 |
| migration | 数据与账号迁移方法 |
| verification | 单测、契约测试、浏览器 E2E、视觉对照 |
| status | `NOT_STARTED / IMPLEMENTED / VERIFIED / APPROVED_RETIREMENT` |

以下情况均不算迁移完成：

- 只有新页面，但原按钮、筛选、状态或异常流程消失。
- 只有 UI，没有等价 Core API、数据迁移或权限控制。
- 用一个通用 Dashboard 代替原 Buyer、Supplier、Partner 或 Marketing 工作流。
- 旧能力被认为“不重要”而静默删除。
- 只验证正常路径，不验证越权、失败、撤权、离线与重试。
- 只统计页面数，不盘点后台任务、通知、支付、审计与外部集成。

功能确需取消时，必须记录取消原因、数据处置、替代方案和创始人批准；状态才可标记为 `APPROVED_RETIREMENT`。

---

## 2. 目标 Portal 矩阵

### 2.1 必须同时具备 PC 与 H5

| 业务体验 | PC Logical Portal | H5 Logical Portal | 说明 |
|---|---|---|---|
| AinerWise 官网 / Consumer Platform | `consumer_pc` | `consumer_h5` | 官网、AI Shopping、需求提交、产品、方案、采购入口 |
| Customer Workspace | `customer_pc` | `customer_h5` | 需求、采购、项目、审批、安装、验收、资产、售后 |
| Cebu Procurement Buyer | `cebu_buyer_pc` | `cebu_buyer_h5` | 保留并增强原 Cebu Buyer 全部界面与能力 |
| Cebu / Core Supplier | `supplier_pc` | `supplier_h5` | 保留并增强原 Cebu Supplier 全部界面与能力 |
| Partner Company | `partner_company_pc` | `partner_company_h5` | RFQ、报价、Crew、Worker、排期、交付、绩效 |
| Marketing Operations | `marketing_pc` | `marketing_h5` | 文案/Brief、审核、素材回收、发布计划、效果查看 |

Marketing 仍遵守 AISLOS Marketing Integration V4：

> AISLOS exports approved Creative Briefs and imports generated Media Assets. It never controls or depends on the media engine internals.

`marketing_h5` 用于移动采集、审核、退回、查看素材、确认排期和效果；它不实现 AinerN2D 的图片或视频生成内部能力。

### 2.2 主要使用 H5/PWA

| 体验 | Logical Portal | 必须能力 |
|---|---|---|
| Field Worker / 施工人员 | `field_worker_h5` | 今日任务、导航、客户联系、清单、拍照、定位、扫码、签字、完工、离线缓存 |
| Crew Lead / 施工队长 | `crew_lead_h5` | 班组任务、人员、交接、异常、证据、完工提交 |
| Kiosk / Experience Store | `kiosk_h5` | AI 接待、产品展示、需求与线索采集、店员确认 |

电工、安装工、调试员、安防、网络、光伏、HVAC、维护人员共享 `field_worker_h5` 代码，但根据 Task、Capability、Certification、Assignment 生成不同界面和清单。

### 2.3 主要使用 PC

| 体验 | Physical Frontend | 说明 |
|---|---|---|
| Internal Operations / AISLOS OS | `frontend-admin` | CRM、采购、项目、现场、资产、财务、审计等权限化工作台 |
| AI Supervisor / Agent Console | `frontend-admin` | AI 运行、人工审核、异常、Prompt、成本、成功率 |
| Developer Portal | `frontend-pc` | API、SDK、Agent 与集成文档 |
| Cebu Admin parity | `frontend-admin` | 原 Cebu Admin 全部能力迁入对应工作台 |

### 2.4 当前实际缺口

当前 Portal Registry 和页面实现不能视为最终完成：

- 已有 PC Registry：`aislos`、`store`、`developer`、`procurement`、`cebu`。
- 已有 H5 Registry：`customer`、`cebu_buyer`、`partner_company`、`field_worker`、`supplier`、`marketing`、`kiosk`。
- `cebu` PC 当前已有 29 个 Core 页面，但仍不能只按页面数量宣称替代原 59 个 Cebu PC 页面。
- Buyer 与 Supplier H5 当前分别已有 15 与 14 个页面，但仍需逐项验证原 41 个 Cebu H5 页面背后的操作和异常流程。
- `admin_marketing` 已有 PC 工作台；Marketing H5 已新增 7 个真实页面和独立布局，支持 Brief 创建/编辑/审核、媒体请求导出、导入资产审核与发布排期。独立浏览器验收仍未完成。
- Partner Company PC/H5 已接入真实 WorkPackage、FieldTask、Crew、Worker、Assignment 与 Evidence 工作流；仍需独立浏览器和跨 Partner 验收。
- Customer Workspace PC/H5 已形成独立布局，并接入需求、采购、Quote/Delivery 审批、项目、安装进度、现场证据、资产与售后；仍需独立浏览器验收。
- Supplier PC/H5 已完成 Core 迁移并保持独立布局；Supplier Team 已支持同公司邀请、停用、恢复、Portal Access 撤销与审计，细粒度匹配规则仍需持续增强。
- Field Worker H5 已实现真实拍照、二维码扫描、定位、签名、IndexedDB 离线队列、冲突恢复和登出清理；Crew Lead H5 已形成独立任务、人员、交接、异常和完工体验。真实设备与断网浏览器验收仍未完成。
- Cebu Admin 当前已有 29 个 Core 工作台页面；是否覆盖原 24 个界面文件及其全部行为仍需 parity 与浏览器验收。
- Shared Core 已将核心业务通知收敛到事务性 Outbox，并增加提交后 Telegram 投递任务；Cebu 历史迁移页已增加非破坏性 Cutover Readiness，实际退役仍被独立验证、数据核对、只读观察和创始人批准阻塞。

ZL02 必须明确新增或映射目标 Portal Key，不能把缺失 Portal 标记为“由响应式页面自动覆盖”。

---

## 3. CebuProjects 不可丢失基线

当前最低界面基线：

| Surface | 源目录 | 基线数量 | 迁移规则 |
|---|---|---:|---|
| Cebu PC | `CebuProjects/pc-frontend/pages/**` | 59 个 Vue 页面 | 全部进入 PC parity ledger |
| Cebu H5 | `CebuProjects/h5-frontend/pages/**` | 41 个 Vue 页面 | 全部进入 H5 parity ledger |
| Cebu Admin | `CebuProjects/admin-frontend/src/**` | 24 个 Vue 界面文件 | 全部进入 Admin parity ledger |

这 124 个界面文件只是最低可见基线，不代表完整功能数量。还必须继续盘点：

- Legacy backend 与 admin-backend API。
- 买家、供应商、管理员的完整状态机和异常流程。
- Marketplace、广告、钱包、托管、支付、纠纷、KYC、风控、通知、消息和物流。
- Seed、后台任务、定时任务、webhook、集成和数据导入导出。
- 原有账号、公司、订单、项目、消息、附件和审计数据迁移。

---

## 4. 多 Agent 执行控制板

任何时刻只有一个任务可以是 `READY`；完成实现后必须由独立验证 Agent 验证。

| 完成 | 栏目 | 名称 | 状态 | 依赖 |
|---|---|---|---|---|
| `[x]` | ZL00 | 零损失原则与完整 Portal 矩阵冻结 | `VERIFIED` | 无 |
| `[ ]` | ZL01 | 全项目 Feature Parity Ledger 与能力盘点 | `READY_FOR_VERIFY` | ZL00 |
| `[ ]` | ZL02 | Portal Registry 扩展与 PC/H5 契约 | `LOCKED` | ZL01 |
| `[ ]` | ZL03 | Cebu Buyer/Public PC + H5 全量迁移 | `LOCKED` | ZL02 |
| `[ ]` | ZL04 | Cebu Supplier PC + H5 全量迁移 | `LOCKED` | ZL03 |
| `[ ]` | ZL05 | Cebu Admin、API、任务与数据全量迁移 | `LOCKED` | ZL04 |
| `[ ]` | ZL06 | AinerWise Consumer / Customer PC + H5 完整体验 | `LOCKED` | ZL05 |
| `[ ]` | ZL07 | Partner Company PC + H5 完整体验 | `LOCKED` | ZL06 |
| `[ ]` | ZL08 | Marketing Operations PC + H5 完整体验 | `LOCKED` | ZL07 |
| `[ ]` | ZL09 | Field Worker 与 Crew Lead H5 完整现场闭环 | `LOCKED` | ZL08 |
| `[ ]` | ZL10 | Shared Core、中间件、身份、数据迁移与兼容退场 | `LOCKED` | ZL09 |
| `[ ]` | ZL11 | 全角色、全 Portal、零损失发布闸门 | `LOCKED` | ZL10 |

ZL01 完成后，协调 Agent 可以将 ZL03-ZL09 拆成互不覆盖的并行子任务；每个子任务仍必须独立验证，且不得绕过依赖的 Core API 和权限契约。

---

# ZL01 全项目 Feature Parity Ledger 与能力盘点

状态：`READY_FOR_VERIFY`

## 目标

建立唯一、可计算、可追踪的零损失迁移账本。盘点不是只列页面名称，而是把每个页面背后的操作、API、数据、角色、状态和异常流程拆出来。

## 必须读取

- `CebuProjects/pc-frontend`
- `CebuProjects/h5-frontend`
- `CebuProjects/admin-frontend`
- `CebuProjects/backend`
- `CebuProjects/admin-backend`
- `Ainerwise/frontend-pc`
- `Ainerwise/frontend-h5`
- `Ainerwise/frontend-admin`
- `Ainerwise/backend`
- `Ainerwise/docs/AISLOS_MARKETING_INTEGRATION_V4_TASKS.md`
- `Ainerwise/docs/PORTAL_FIELD_SERVICE_V1_TASKS.md`
- `SHARED_PLATFORM_MIDDLEWARE_PLAN.md`

## 必须产出

- `docs/parity/FEATURE_PARITY_LEDGER.md`
- `docs/parity/feature-parity-ledger.json`
- `docs/parity/PORTAL_ROUTE_MATRIX.md`
- `docs/parity/API_DATA_MIGRATION_MATRIX.md`
- `docs/parity/PARALLEL_AGENT_WORK_PACKAGES.md`

JSON 账本必须可由验证脚本检查：每条源能力只能处于明确状态，不能缺少 target、owner 或 verification。

## 验收

- Cebu 59 PC、41 H5、24 Admin 界面文件覆盖率为 100%。
- Ainerwise 与 AISLOS 当前页面、API、后台任务和集成全部入账。
- 每个旧能力都有目标 Portal/Core API，或有创始人批准的退役记录。
- 识别官网、Customer、Marketing、Partner 的 PC/H5 缺口。
- 输出可并行 Agent 包，并明确文件所有权，避免互相覆盖。

## 实现交付记录

第一次独立验证结果：`FAILED_VERIFY`。实现 Agent 已完成失败项修复并重新提交
`READY_FOR_VERIFY`；不得由实现 Agent 自行改为 `VERIFIED`。

失败复验修复范围：

- 独立验证证据必须使用结构化 attestation 并绑定源码指纹、验证 Agent、命令与结果，
  不能只检查非空字符串。
- 指纹必须覆盖 ZL01 必读架构/任务文档与 Cebu seed。
- 页面交互操作、状态机、异常流程必须逐项入账。
- Celery task 必须按真实 task 函数入账，不能只按文件计数。

产出：

- `docs/parity/FEATURE_PARITY_LEDGER.md`
- `docs/parity/feature-parity-ledger.json`
- `docs/parity/PORTAL_ROUTE_MATRIX.md`
- `docs/parity/API_DATA_MIGRATION_MATRIX.md`
- `docs/parity/PARALLEL_AGENT_WORK_PACKAGES.md`
- `docs/parity/VERIFICATION_RISK_REGISTER.md`
- `docs/parity/ZL01_IMPLEMENTATION_REPORT.md`
- `docs/parity/runtime-api-manifest.json`
- `docs/parity/status-overrides.json`
- `docs/parity/verification-attestations.json`
- `scripts/parity/export_runtime_api_manifest.py`
- `scripts/parity/generate_feature_parity_ledger.py`
- `scripts/parity/validate_feature_parity_ledger.py`
- `scripts/parity/verify_feature_parity_ledger.sh`

当前自动盘点：

- 总能力条目：5176。
- Cebu PC 页面：59 / 59。
- Cebu H5 页面：41 / 41。
- Cebu Admin 界面文件：24 / 24。
- Ainerwise 运行时 API：676 / 676，其中 backend 669、AI Orchestrator 4、
  Channel Gateway 3；动态 Router 与 Cebu Trade 模块接口均按真实运行态入账。
- Ainerwise Celery task：14 / 14，按真实 task 函数入账。
- Cebu 页面交互操作：480；状态机标记：415；异常流程标记：423。
- Cebu seed script：1 / 1。
- 共享基础设施清单：Ainerwise 11、Cebu 8。
- 同时盘点 Ainerwise 与 Cebu 的 API、数据模型、服务、migration、角色、
  前端工作流、后台任务与集成边界。
- 运行时 API 清单带源码指纹；源码变更后未重新导出清单时，生成和验证都会失败。
- 46 个源码能力面使用精确数量校验；ZL01 必读架构/任务文档也进入指纹。
- 任何现有 Ainerwise 能力最高只自动进入 `READY_FOR_VERIFY`。
- 任何带 placeholder / 静态 demo 风险的能力自动回退到 `TODO`。
- 任何 `VERIFIED` 状态必须由 `status-overrides.json` 引用结构化独立验收
  attestation；attestation 必须绑定源码指纹、不同的验证/实现 Agent、命令结果、
  证据文件哈希与完整性哈希。
- 当前账本验证通过；具体源码指纹以生成后的
  `docs/parity/feature-parity-ledger.json` 为准，避免任务文档自引用导致指纹漂移。

验证命令：

```bash
cd /Users/mac/Code_Start/Aislos
bash scripts/parity/verify_feature_parity_ledger.sh
```

当前风险记录在 `docs/parity/VERIFICATION_RISK_REGISTER.md`。Ainerwise PC/H5
Products 已移除 demo/coming-soon 故障回退，测试质量扫描当前无风险；剩余风险来自
只读 CebuProjects 源工程中的静态 demo 依赖，必须通过 Core 迁移映射和独立验收关闭，
不得修改 CebuProjects 源工程伪造完成。

---

## 5. 最终发布闸门

ZL11 只有同时满足以下条件才能 `VERIFIED`：

- Feature Parity Ledger 中不存在 `NOT_STARTED`、无目标或无验证的源能力。
- Cebu 124 个最低界面基线全部映射并通过页面/流程验收。
- AinerWise 官网、Customer、Marketing、Partner 都同时拥有已验证的 PC 与 H5 体验。
- Field Worker 与 Crew Lead H5 完成拍照、定位、扫码、签名、离线和幂等同步验证。
- 所有 Portal 的菜单、布局、路由、权限和对象级数据隔离明显不同且正确。
- 共享 Core API、中间件与数据迁移完成；新功能不再写 Legacy 数据库。
- 浏览器 E2E、API 契约、数据迁移回放、权限失败路径和回滚演练全部通过。
- 创始人对旧工程退役清单逐项批准。

---

## 6. 给其他 Agent 的提示词

### 实现 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md
/Users/mac/Code_Start/Aislos/Ainerwise/docs/ARCHITECTURE_CONSTITUTION.md
/Users/mac/Code_Start/Aislos/SHARED_PLATFORM_MIDDLEWARE_PLAN.md
/Users/mac/Code_Start/Aislos/Ainerwise/AGENTS.md

只领取唯一 READY 栏目。开始前将栏目改为 IN_PROGRESS。
原功能只能增加不能减少；不得删除、覆盖或静默忽略任何旧页面或能力。
物理前端最多三套，但每个 Logical Portal 必须有独立布局、菜单、路由、权限和流程。
完成后填写实现记录并改为 READY_FOR_VERIFY，不得自行标记 VERIFIED。
```

### 验证 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md

只验证 READY_FOR_VERIFY 栏目。
对照 Feature Parity Ledger 检查页面、按钮、API、数据、权限、任务和集成。
正常路径与失败路径都必须验证；不得以页面存在代替功能 parity。
通过后标记 VERIFIED，并只解锁下一栏目。
```

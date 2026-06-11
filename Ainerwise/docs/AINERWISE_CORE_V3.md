# Ainerwise Core V3 — 一个底座 · 多个 Portal · Agent 插件生态

> 创始人 2026-06-10 批准的 V2 升级改造最终版本。原则：**不重写现有系统** ——
> A–E 五个 Phase 交付的全部资产（事件总线、RAG、RFQ、账本、签约、验收闭环、
> 122 个测试）原地升级为 Core Platform。
> 宪法 v3 见 `ARCHITECTURE_CONSTITUTION.md`；v1/v2 文档保留作为 Core 的实现记录。

---

## 1. 三层总图

```
┌─ Portals（Logical Portal，复用 3 套 Nuxt 代码基座）──────────┐
│ AISLOS Website · AISLOS Admin Console · Agent Console         │
│ Marketing Portal · Customer Project Portal · Partner Portal   │
│ Ainerwise Store Frontend · Store Admin · Developer Portal     │
│ Experience Center Kiosk（设计冻结，店租签订开工）              │
├─ Ainerwise Core Platform（一个底座 = 现有 backend 升级）───────┤
│ Auth/RBAC · CRM · Product · Project · Marketing               │
│ Data Hub（八大资产表）· Knowledge Hub（pgvector RAG）          │
│ Agent Runtime（agents/runs/memory/grants）· Workflow（事件总线）│
│ Marketplace registry/review/install · Tenant Isolation（Phase I）│
├─ Infrastructure（不变）───────────────────────────────────────┤
│ PostgreSQL+pgvector · Redis · MinIO · FastAPI · Nuxt · Celery │
│ 卫星进程：ai_orchestrator · channel_gateway · celery workers   │
└───────────────────────────────────────────────────────────────┘
```

**Core 不拆微服务**（方案原文："底层服务不要乱拆太多，先模块化单体也可以"）。
卫星进程维持现状三个，新进程仍按三问触发（故障域/伸缩/发布节奏）。

## 2. Logical Portal 与当前兼容入口（宪法第 5/10 条）

以下端口是当前兼容入口，不是“每个角色必须一个前端工程”的目标架构。

| # | 当前 Logical Portal | 用户 | 兼容端口 | 共享代码基座 |
|---|--------|------|------|--------------|
| 1 | AISLOS Website | 潜在企业客户 | 4099 | `frontend-pc` |
| 2 | Ainerwise Store Frontend | 零售/企业买家 | 4096 | `frontend-pc` |
| 3 | Developer Portal | 第三方开发者 | 4092 | `frontend-pc` |
| 4 | AISLOS Admin Console | 内部项目管理者 | 4097 | `frontend-admin` |
| 5 | Ainerwise Store Admin | 店内/供应链运营 | 4095 | `frontend-admin` |
| 6 | Marketing Portal | 真人运营 | 4094 | `frontend-admin` |
| 7 | Agent Console | AI 员工配置与治理者 | 4093 | `frontend-admin` |
| 8 | Customer Project Portal | 企业客户 | 4098 | `frontend-h5` |
| 9 | Partner Portal | 安装/施工/维护商 | 4091 | `frontend-h5` |
| 10 | AISLOS Experience Center (Kiosk) | 到店客户（实时语音，多语言） | 4090 | `frontend-h5`（kiosk 布局） |

Portal 10 设计冻结于 `AISLOS_EXPERIENCE_CENTER.md`；**EC-0 代码骨架已交付**
（2026-06-11）：迁移 022（stores/kiosk_devices/showroom_sessions/showroom_orders
+ 5 个 showroom 人格入 agents 注册表）、`/showroom/kiosk/*` 设备 token API 面、
`/admin/showroom/*` 管理面（POS 确认 = 库存扣减 + 复式账本）、kiosk-portal
进程（4090，文本管线 + 确定性 D1 Canvas）。实时语音（方案 A）与实体部署等店租
签订开工。语音终端 = Web Kiosk PWA + speech-to-speech 工具桥，零新核心系统 ——
全部挂接既有 Agent Runtime 授权门。

**目标拆分方式**：物理代码基座只有 `frontend-pc`、`frontend-h5` 和
`frontend-admin`。Logical Portal 使用独立 Layout、URL/hostname、品牌、首页、菜单、
路由白名单、PWA Manifest 和 Permission Grant，但不因角色或菜单差异自动新增工程或
运行进程。细粒度运营角色仍受权限发布门约束。

`frontend-h5` 的目标 Logical Portal 包含 Customer、Partner Company、Field Worker、
Supplier 和 Kiosk。完整迁移与现场服务任务见 `PORTAL_FIELD_SERVICE_V1_TASKS.md`。

**2026-06-10 创始人解锁指令**：为立即验证 Store 与开发者需求，7–8 的最小数据
闭环提前上线。此解锁不等于商业 Marketplace 发布：第三方 Agent 执行、数据授权、
订阅收费、分成结算仍受 Phase I 发布门约束。

## 3. Agent Runtime（v3 核心新增）

**Agent = 数字员工岗位，不是业务模块的改名。** Core 模块继续负责稳定的数据、
规则与工具；Agent 以明确身份、最小权限和审核边界组合这些工具：

```
agents          员工档案：slug/名称/职位/简介/vendor(official|third_party)
                /workflows_json(绑定运行时工作流)/config_json(人设)
                /price_monthly(Marketplace 预留)/status
agent_grants    八项授权开关（产品/客户/项目/报价/邮件/广告/支付/Partner）
                核心官方工作流执行前校验；API 变更写 audit_logs
ai.agent_runs   已有 — 每次执行的 agent_slug/workflow/token/延迟/输入输出
ai.memories     已有 — 当前按 subject_type 命名；目标分类为五环：
                subject_type ∈ global|company|project|agent|lead|user
ai.ai_reviews   已有 — Agent 产出审核队列（宪法第 2 条）
```

`subject_type` 命名不是权限隔离。对象级授权、Tenant 边界、第三方运行沙箱和安装/
卸载生命周期是 Phase H/I 发布门。当前 Agent Runtime 可验证能力是：官方 Agent
注册、暂停/激活、核心入口授权校验、显式运行归属、变更审计和人工审核。

**官方首批数字员工**（绑定既有 workflow，零新运行时）：

| Agent | 职位 | 绑定 workflows | 数据来源 |
|-------|------|----------------|----------|
| Marketing Agent | Marketing Manager | content_gen, publish_jobs, seo | 案例库/产品库/转化数据 |
| Sales Agent | Sales Consultant | consult, lead_score, quote_draft | 知识库/案例/定价引擎 |
| Procurement Agent | Procurement Manager | bid_evaluation | partner_metrics/报价历史 |
| Business Brain | Chief of Staff | daily_briefing | 全量运营数据 |
| Support Agent | Support Engineer | ticket_triage, mission_task（Phase H 已绑定） | 资产/维保/工单历史 |

**Agent Team（Phase H 首版已交付）**：Mission → deterministic Planner → Task
Queue → allowlisted Workers → Reviewer checks → human-approved Final Report。首版不做
无限聊天，也不声称 Agent 自主承诺或自主执行外部动作。
**Project Space（Phase H 首版已交付）**：h5 客户项目页聚合 Files/CAD revisions/
Tasks/Agents/Missions/Timeline。Chat 与可写 Project Memory 仍是后续能力，不冒充已完成。

## 4. Marketing 双层（第一个强 Agent 场景）

```
Marketing Portal（人用工具）   = 现 marketing-studio：素材/排期/SEO/Campaign/线索
Agent Console → Marketing Agent（数字员工）
  人设配置：品牌语气/目标客户/产品重点/禁词（config_json + region_marketing_profiles）
  自动任务：内容生成→审核→发布（已有管线）+ 每周营销汇报（briefing 扩展）
  执行日志：agent_runs 过滤 · 效果：UTM 归因转化（已有）
  训练数据沉淀：每次审核通过/拒绝即反馈信号（ai_reviews 即标注集）
```

## 5. Data Hub = 八大资产表（已在积累，仅确认归属）

Product / Project / Marketing / Case / Knowledge / Agent Memory /
Pricing&Cost / Partner —— 全部已有表与管线。**v3 不新建 Data Hub 系统，
Data Hub 是这些表的总称与授权视图。**

## 6. Marketplace（治理闭环已上线，商业发布仍属 Phase I）

售卖对象：Agent / Workflow / Connector / Knowledge Pack / Template /
Industry Solution。Human Partner Service 保持独立目录与合同模型，不与可安装 Agent
混为同一实体。当前已交付 Agent 上架申请、人工审核、公开目录、安装/卸载记录；
第三方 Agent 获批后保持 `paused` 且八项数据权限默认全拒绝。分成结算走 PSP
（宪法第 3 条），在 tenant isolation、第三方执行沙箱和 PSP 接入完成前不开放收费执行。

## 7. V3 路线图（接续 A–E）

```
Phase G（已交付并硬化）：Agent Runtime 地基
  agents + agent_grants 表 · 官方 5 员工注册 · Agent Console（目录+配置台）
  AISLOS 首页重定位（Install AI Employees For Your Business）
  核心工作流授权门 · 显式 agent_slug 运行归属 · Agent 配置/授权审计

Phase H（第一个真实客户运营期，基础闭环已交付）：
  Project Space v1（h5 客户工作台）· Agent Team 结构化编排（Planner→Workers→Reviewer）
  Support Agent 工单预审 · Marketing Agent 周报 · exact-project 对象授权
  Smart Building/Solar/Security 行业 Agent 包：等待第一个真实客户范围后解锁

  注意：exact-project 授权只是五环授权体系的第一层可执行边界。Company/User/Agent/
  Global 的完整隔离、多租户和第三方沙箱仍是 Phase I 发布门。

Phase I（收入解锁）：
  已交付：Store 需求单闭环 · Developer Portal · Marketplace 上架/审核/安装记录
  发布门：第三方 Agent 执行沙箱 · tenant isolation · PSP 订阅/分成 · 数据导出/删除
  细粒度 Portal 运营角色 · 多租户 SaaS（原 Phase F 并入）

Experience Center（物理触发，独立于 H/I 时序）：
  EC-0 试点（触发条件：实体店租约签订，~3 周）：
    1 台平板 Web Kiosk · 实时语音(speech-to-speech)+Core 工具桥 · 确定性
    Presentation Canvas · shopping-assistant 人格 · 店内 POS 过渡成交流
    · showroom_sessions 转化数据集（设计冻结：AISLOS_EXPERIENCE_CENTER.md）
  EC-1 全量：5 平板 ×5 人格 · 门店转化指标进 Business Brain 晨报
  EC-2 体验升级（依赖 Phase H 能力）：房间照片→效果图 · Agent Team 会议视图
```

## 8. 不变的防腐底线

不自建钱包 · 不做拖拽编辑器/大屏动画 · 不上 Kafka/K8s/图数据库 ·
AI 产出必过审 · 第三方 Agent 默认零权限 · 没有真实用户的 Portal 不建。

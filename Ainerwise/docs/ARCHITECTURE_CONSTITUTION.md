# AinerWise Architecture Constitution v3（架构宪法 · 第三版）

> **Ainerwise** is the real business and the data source.
> **AISLOS** is the Enterprise AI Operating System that platformizes it.
> **Ainerwise Agents** are AI employees — built from real operational data,
> serving Ainerwise first, sold on the AISLOS Marketplace later.
>
> Mission: **AISLOS — Connecting Artificial Intelligence with the Physical
> World Through Real Lifecycle Experience.**

**修宪记录**：v2 冻结宪法于 2026-06-10 由创始人明确决定全盘解冻并修订
（保留条款 / 修订条款 / 废止条款逐条列于文末）。本版即日生效。

---

## Rule #1（不变，仍是最高规则）

**Every feature must accumulate a unique data asset. Otherwise it will never be implemented.**

Agent 生态时代它更重要：真实业务数据 → Agent 能力 → 平台价值。
数据资产必须合法、最小化、经授权、可追溯并有保留/删除规则；不得为了积累数据而
扩大采集范围或绕过客户同意。

---

## The Ten Articles (v3)

| # | Article | 含义 |
|---|---------|------|
| 1 | **Sell outcomes and AI employees — never bare software.** | 客户买的是结果与"数字员工"，不是功能清单。首页一句话主张，不堆功能图标。 |
| 2 | **AI recommends. Human approves.** （不变） | Agent 再多，authorize 边界不变：授标、放款、对外承诺、广告投放永不自动免审。 |
| 3 | **Never own customer money. Only ledger + PSP.** （不变） | Marketplace 分成、Agent 订阅费同样走 PSP。 |
| 4 | **No feature without data asset.** （不变） | = Rule #1。 |
| 5 | **One Core, many Portals.** （修订） | 底层永远一个 Core（模块化单体 + 既有卫星进程）；上层 Portal 可多个，但每个新 Portal 必须回答：哪个真实用户群体今天就要用它？没有真实用户的 Portal 不建。 |
| 6 | **Prefer configuration over visual builders.** （不变） | Agent 人设/授权/工作流 = 配置与数据，不做拖拽编辑器。 |
| 7 | **Prefer an accountable partner network over fixed expansion.** （扩展） | Human Partner 与 AI Agent 是两类不同主体、合同和目录；平台分别做准入、授权、风控与评价，不混成一个实体。 |
| 8 | **Multi-region is current; tenant isolation is a release gate.** （扩展） | 当前不得宣称已完成多租户隔离。Marketplace 可先开放公开目录、人工审核和无权限安装记录；任何第三方 Agent 执行、数据访问、收费订阅或商业 SaaS 发布前，必须完成 tenant_id、对象级授权、隔离测试和数据导出/删除能力。 |
| 9 | **Agent tools are allowlisted and least-privilege.** （强化） | 新能力评估是否适合注册为 Agent 工具；读取、建议和草稿优先。授标、放款、付款、合同承诺等高风险动作可保持不可调用或只生成待审请求。每次 Agent 执行明确记录 agent_slug。 |
| 10 | **Growth must not outrun maintainability.** （修订自"一人可维护"） | 扩张按真实用户与收入解锁：第三方 Agent、Developer SDK、新 Portal、电商前台 —— 每一项的开工条件都写在 V3 路线图里，不提前建空城。 |

### Physical Frontend 与 Logical Portal Interpretation（强制）

冻结物理前端代码基座只有 **3 套 Nuxt：`frontend-pc`、`frontend-h5`、
`frontend-admin`，加 1 个 Core API**。不得为 Customer、Supplier、Partner Company、
Field Worker、电工、安装工或某个后台部门复制新的前端工程。

Logical Portal 必须拥有独立 Layout、Home、Menu、Route Allowlist、Theme、PWA Manifest
和 Permission Grant。不同 Logical Portal 可以使用独立 hostname；是否需要独立运行进程
由真实隔离、伸缩或发布需求决定，不能仅因菜单不同而新增进程。

一个 `frontend-h5` 必须生成 Customer、Partner Company、Field Worker、Supplier 和
Kiosk 等不同体验。Partner Company 与 Field Worker 绝不能共用同一菜单；电工、安装工、
调试员与维保员则复用 Field Worker PWA，由任务类型、技能、证书和 Assignment 决定界面。

一个 `frontend-admin` 根据 Membership 和 Grant 提供多个业务工作台，用户不应为了使用
Marketing、AI Supervisor、Field Operations 或 Finance 重复登录外观相同的后台。

完整执行规则见 `docs/PORTAL_FIELD_SERVICE_V1_TASKS.md`。

---

## 品牌三层（v3 新增，冻结）

```
Ainerwise          真实业务品牌：精品电子产品、智能生活、项目交付、数据来源
AISLOS             平台品牌：Enterprise AI Operating System with a governed Agent Marketplace
Ainerwise Agents   AI 员工生态：官方 Agent + 经审核但默认暂停/零权限的第三方 Agent
```

商业闭环：**真实业务 → 数据 → Agent → 平台 → Marketplace → 订阅/抽成/服务费。**
飞轮：**真实客户 → 真实项目 → 真实数据 → Agent 越来越强 → 更好的体验（线上 +
门店）→ 更多客户。**

## 物理触点：AISLOS Experience Center（v3 增补，冻结设计）

数字员工的实体岗位（Portal 10，设计冻结于 `AISLOS_EXPERIENCE_CENTER.md`，
开工条件 = 实体店租约签订）：实时语音多语言接待（Web Kiosk + speech-to-speech
工具桥，事实全部来自 Core 工具调用）、确定性演示画布、店内零售保底现金流、
项目漏斗入口、showroom 转化数据集（Rule #1 资产）。

**物理世界 AI 交互三条红线**：
1. AI 必须自报身份（AI Act Art.50），开场白写死、不可被人设配置覆盖；
2. 按钮唤醒，禁止常开麦克风；只存文本转写，不存原始音频；
3. 禁止人脸/生物识别与客流摄像分析。

平板是哑终端：长期密钥与数据库永不下发到设备；showroom 工具集为设备 token 可达
的唯一 API 面；每会话 token 预算硬上限。

## 数据授权五环（v3 新增，冻结）

```
Global Knowledge > Company Data > Project Data > Agent Memory > Private Data
```

第三方 Agent 默认零权限；八项授权逐项显式开关（产品/客户/项目/报价/邮件/
广告/支付/Partner）。官方 Agent 同样走授权表，核心官方工作流执行前强制校验，
授权变更写入 audit_logs，执行身份写入 agent_runs。

五环是目标数据分类，不等于当前安全隔离。Company/Project/User/Private 的对象级
授权、租户隔离和第三方沙箱必须通过 Phase H/I 发布门，未通过前不得对外宣称完成。

## Capability 与 Agent 边界（v3 澄清，冻结）

业务模块负责数据所有权、规则、API 和可测试能力；Agent 是带身份、最小权限和审核
约束去组合这些能力的岗位。**Agent 不是模块的改名，模块也不等于一名员工。**
同一能力可被多个 Agent 或人工流程复用，所有 Agent 调用必须可归属、可撤权、可审计。

---

## 修宪对照（v2 → v3）

**保留**：Rule #1 · AI推荐人批准 · 不碰客户资金 · 配置优先 · 多区域 · Agent-ready ·
账本/事件总线/审核队列等全部已交付资产。

**修订**：
- "六大一级模块冻结" → **模块能力可被 Agent 编排**：模块继续承担稳定的数据与业务边界，Agent 以岗位身份组合 allowlisted tools。
- "不做第四个前端" → **One Core, many Portals**（按真实用户解锁，见第 5 条）。
- "一人可维护" → **可维护性随收入扩张**（第 10 条）。
- 对外定位 "AI General Contractor Platform" → 当前 **AISLOS — The Enterprise
  AI Operating System**；Phase I 发布门通过后可升级为 **with an Agent
  Marketplace**（总承包能力降级为 AISLOS 的首个官方行业解决方案：
  Smart Building / Solar / Security）。

**废止**：
- "NOT e-commerce" —— Ainerwise Store（精品电子/智能设备前台+后台）成为
  正式业务线（开工条件见路线图）。
- "2~3 年不增一级模块" 冻结令。

目标架构详见 `AINERWISE_CORE_V3.md`。

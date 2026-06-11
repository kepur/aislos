# AinerWise OS v2 — AI General Contractor 架构（FROZEN）

> 🔒 **本架构已于 2026-06-10 冻结 2~3 年。** 不再新增一级模块、不再改定位、
> 不再开 v2.1/v2.2 文档 —— 一切演进只发生在本文档的 Phase C/D/E/F 内，
> 且必须通过 `ARCHITECTURE_CONSTITUTION.md` 十条审查。
> Business Brain、Voice Agent、Payments、Workflow 是能力（capability），
> 不是一级模块；一级模块永远只有六个（见下）。当前指令：停止设计，开始交付。

> 定位升级：从「AI + CRM」→「AI 总承包商平台」。卖的不是产品，是结果（Outcome）。
>
> **对外品牌**：AinerWise — AI General Contractor Platform。
> "We connect customers, AI solution design, certified local partners and premium
> suppliers into one intelligent delivery platform."
> （客户和 Partner 不关心 CRM/RAG/Workflow，只关心：多少钱、谁来装、什么时候装、有没有售后。
> "AI Smart Living OS" 是内部架构名，不是营销语。）
>
> **六大核心模块**：AI Solution Engine · CRM & Lead · RFQ & Partner ·
> Product Knowledge · Project & AMC · AI Digital Marketing（见 3.10，可独立 SaaS 化）
>
> **核心思想：Outcome Platform，不是 Software。** 对外永远不讲 "AI 软件"——
> 客户买的是结果：AI 设计 → AI 预算 → 认证 Partner 施工 → 验收 → 持续维保。
> 官网文案、销售话术、融资材料一律以 Outcome 叙事。
>
> **八大护城河资产**（系统设计始终为它们积累数据）：
> ① AI 能力 ② Product Database ③ Partner Network（partner_metrics 历史）
> ④ Living Case Dataset（见 3.7）⑤ Pricing & Cost Data（product_costs × price_lists 跨国数据）
> ⑥ Maintenance Asset Data（assets 全生命周期）⑦ 多国家运营经验（region 化的一切）
> ⑧ **Operational Dataset** —— 每个交付项目沉淀的真实运营数据（预算/产品组合/
> Partner/工期/返修/满意度/毛利）。未来 AI 最值钱的不是模型，是别人没有的数据。
> 决策准则：**每加一个模块，必须沉淀一种别人复制不了的数据资产，否则不加。**
> 本文档是 v1（AISLOS_ENTERPRISE_ARCHITECTURE.md）的增量演进，不推翻它：
> **进程拓扑、数据层、事件总线、AI 中台（Phase A/B 已交付）全部保留。**

---

## 0. 核心结论

1. **v2 不是重写，是加模块。** 所有新能力（RFQ、资产、定价、文档、支付）都是 backend 模块化单体里的新模块 + 新表。进程数量不变。
2. **真正的新核心只有一个：RFQ 竞价撮合**（询价→竞价→AI 比价→授标→里程碑交付）。这是「总承包商」与「CRM」的本质区别，其余 14 个模块大半已存在或是它的配套。
3. **第一阶段不做支付**（你的判断完全正确）：人工确认 + 线下转账 + 系统记账。但**支付的表结构和状态机现在就锁定**，Phase 2 接 PSP 时零重构。
4. **绝不自建钱包持有客户资金。** 自己持币做 escrow 在欧盟（PSD2）和塞尔维亚（NBS）都需要支付机构牌照。"钱包"在系统里只是**复式记账账本视图**，真钱永远在银行或 PSP（详见第 5 节）。

---

## 1. 十五模块差距分析（诚实版）

| # | 模块 | 现状 | 结论 |
|---|------|------|------|
| 1 | Solution 方案中心 | ✅ **已存在** — `solutions` 表含 budget_tiers / recommended_products / architecture / delivery_flow / lifecycle_content / regions，AI 分析已在用它匹配 | 补 Solution Template 字段（工期/利润率），不用新建 |
| 2 | Project Design 设计中心 | ❌ 缺 | Phase D：design_revisions 表 + files 模块挂 CAD/平面图；AI 读图是远期 |
| 3 | Workflow Engine | ◐ 代码式自动化已有（lifecycle/marketing_automation + Phase A 事件总线） | 做**配置式状态机**（JSON 定义的 workflow_definitions 表），不做拖拽编辑器——一人公司维护不动可视化引擎 |
| 4 | Asset 资产管理 | ◐ lifecycle 有 Warranty/AMC/MonitoringPoint，缺统一登记 | ★ **Phase C 新建 assets 表**，层级即 Digital Twin 预留（见 3.2） |
| 5 | Document Generator | ◐ quote_pdf 已有 | Phase D：document_templates + 变量渲染 + AI 草稿（进 ai_reviews 审核） |
| 6 | AI Memory | ◐ conversations/messages 已有（Phase B） | ★ **Phase C 新建 ai.memories**（成本低价值高，见 3.4） |
| 7 | Knowledge Graph | — | **不建图数据库。** Postgres 外键就是图；给 Agent 加 SQL 多跳查询工具（客户→项目→设备→保修→推荐）即可达到示例中的效果 |
| 8 | Pricing Engine | ◐ Region.tax_rules_json + PlatformFeeRule + 产品 price_options 已有 | ★ **Phase C 新建 price_lists + exchange_rates + pricing service** 统一计算（见 3.3） |
| 9 | Rule Engine | — | **不做通用规则引擎**（Drools 之路是深渊）。定价规则放 pricing、流程规则放 workflow_definitions，各自 JSON 条件即可 |
| 10 | Scheduler 日程 | ◐ MaintenanceSchedule 已有 | Phase D：partner_calendar + 派单；与 RFQ 授标联动 |
| 11 | Notification Center | ◐ = v1 既定的 channel-gateway（Phase D）+ notification_preferences 已有 | 按 v1 计划走，不重复设计 |
| 12 | Integration Hub | ✅ integration_settings 插件模式已有（SMTP/Telegram/AI） | 新集成（Stripe/Calendar）按同一模式加 category |
| 13 | Analytics | ◐ ProjectFinance/recurring_revenue 已有 | Phase E：AI 问数 = Agent 的只读 SQL 工具 + 物化视图，不买 BI |
| 14 | Marketplace | ◐ service_partners（技能/半径/费率/评分/认证）+ vendors 已有 | ★ 缺的是交易流程本身 = **RFQ 模块（v2 核心，见 3.1）** |
| 15 | Digital Twin | — | 不开发，但 assets 表用 building/floor/room/device 层级建模，未来 3D 化不需迁移 |

**结论：15 项里 2 项已完整存在、8 项部分存在只需补强、3 项明确不做（用更便宜的等价物）、真正全新的是 RFQ + Assets + Pricing + AI Memory + 支付。**

---

## 2. v2 分层架构（映射到现有代码）

```
Presentation   frontend-pc(官网+AI顾问✅) · frontend-h5(客户门户✅ + Partner角色视图🔨)
               frontend-admin(后台✅) · Mobile PWA(远期)
─────────────────────────────────────────────────────────────
AI Layer       ai_orchestrator✅ · RAG✅ · ai.memories🔨 · Agent工具(SQL多跳/比价评分)🔨
─────────────────────────────────────────────────────────────
Business       CRM✅ Lead✅ Solution✅ Quote✅ Project✅ Lifecycle✅ Partner✅ Marketing✅
(backend 单体)  RFQ/Bidding🔨 Assets🔨 Pricing🔨 Payments(记账先行)🔨 Documents🔨
─────────────────────────────────────────────────────────────
Platform       Product DB✅ pgvector✅ 事件总线✅ Celery队列✅ integration_settings✅
               workflow_definitions🔨 channel-gateway(Phase D)
─────────────────────────────────────────────────────────────
Infra          PostgreSQL+pgvector · Redis · MinIO · FastAPI · Nuxt · Celery（全部不变）
```

**Partner Portal 不做第四个前端应用** — service_partner/vendor 角色已存在于 RBAC，
在 frontend-h5 加 partner 布局（接单/报价/日历/收款页），省一套构建和部署。

### 端结构与角色矩阵（2026-06-10 冻结，与四端一一对应）

```
frontend-pc     官网/SEO/AI顾问/公开签署页（成交前 + 验收签字）
frontend-h5     客户门户 + Partner 门户 + 施工现场 PWA（按角色切布局）
frontend-admin  内部运营后台（控制中心）
backend         统一 API + RBAC
```

九角色（`app/core/permissions.py`）：
super_admin / admin / sales_manager / project_manager / finance（内部，admin 端；
细粒度菜单待真实雇员）· buyer(=customer_owner) / customer_user（客户，h5）·
vendor / service_partner(=partner_owner) / partner_worker / maintenance_worker
（供给网络，h5 partner 布局；任务按 assigned_to 鉴权，worker 无需 Partner 主档案）。
**不拆 partner-admin / customer-portal / field-app 等独立系统 —— 一人维护会炸。**

### 验收闭环（已实装，事件驱动）

```
Partner 手机提交完工（照片/设备序列号/测试结果 → completion_json）
  → 验收文档自动渲染 → 自动发客户签署链接（手机签字）
  → document.signed 事件 → 消费者自动：
      释放 on_acceptance 里程碑（账本）· 注册资产（site/floor/room）
      · 生成 Case 草稿并嵌入知识库 · 任务关单 · project.completed 事件
```

PWA：h5 已带 manifest 可安装；拍照=capture 输入、签名=canvas 已有；
离线缓存/扫码/定位随真实施工队需求加（Rule #1：先有现场数据需求再建）。

---

## 3. 新模块设计

### 3.1 RFQ 竞价撮合（v2 的心脏）

业务流（你的"真实流程"的系统化）：

```
Lead/方案确认 → RFQ 创建（按 Solution 拆工种包：KNX/电工/光伏/安防）
  → AI 筛 Partner（skills∩、service_radius、availability、rating、国家）
  → 邀请发送（Phase C: Telegram/邮件 · Phase D: channel-gateway 推送）
  → Partner 报价（金额/工期/备注）或拒绝
  → AI 比价评分 → 推荐授标（admin 一键确认，不自动授标）
  → 授标 → 生成 Project 任务 + 付款计划
```

表设计：

```sql
rfqs (
  id, region_id, lead_id FK, project_id FK NULL, solution_id FK NULL,
  trade TEXT,                    -- knx|electrical|solar|security|hvac|general
  scope_json JSONB,              -- 工作量描述、设备清单、现场信息
  budget_hint NUMERIC(12,2) NULL, currency,
  status TEXT,                   -- draft|inviting|bidding|evaluating|awarded|cancelled
  bid_deadline TIMESTAMPTZ, created_by FK users
)

rfq_invitations (
  id, rfq_id FK CASCADE, partner_id FK service_partners,
  status TEXT,                   -- sent|viewed|declined|bid_submitted|expired
  sent_via TEXT, responded_at
)  -- UNIQUE(rfq_id, partner_id)

partner_bids (
  id, rfq_id FK, partner_id FK,
  amount NUMERIC(12,2), currency, lead_time_days INT,
  notes TEXT, attachments_json JSONB,
  ai_score NUMERIC(5,2) NULL,    -- AI 比价综合分（价格/评分/距离/准时率/返修率）
  ai_score_breakdown_json JSONB, -- 可解释：每个因子的得分
  status TEXT                    -- submitted|shortlisted|awarded|rejected|withdrawn
)
```

AI 比价 = orchestrator 新 workflow `bid_evaluation`：输入 bids + partner 历史
（rating_internal、SupplierScorecard、工单返修记录），输出排序 + 理由，落
`ai_reviews`（target_type='bid_award'）等 admin 批准 —— **AI 推荐，人授标**，
与既有 preliminary 审核惯例一致。

事件：`rfq.created / rfq.bid_received / rfq.awarded`（沿用 Phase A 事件总线命名）。

### 3.2 Assets 资产登记（Digital Twin 预留）

```sql
sites (   -- 客户的建筑/场所
  id, region_id, company_id FK NULL, contact_user_id FK NULL,
  name, address, city, country,
  building_meta_json JSONB       -- 面积/楼层数/建造年份/平面图 file_id
)
assets (
  id, site_id FK, project_id FK NULL, product_id FK NULL,
  parent_asset_id FK NULL,       -- 层级：gateway 下挂 device
  floor TEXT NULL, room TEXT NULL,           -- Digital Twin 维度
  serial_no TEXT, installed_at DATE,
  customer_warranty_id FK NULL, amc_contract_id FK NULL,   -- 接通 lifecycle 已有体系
  status TEXT,                   -- active|faulty|replaced|retired
  meta_json JSONB
)
```

工单（tickets）和维保（MaintenanceSchedule）加可空 `asset_id` 列 —— 维修历史、
保修、换件、"一年后门锁电池该换了"的自动维保收入全部挂在资产上。

### 3.3 Pricing Engine

```sql
price_lists (id, region_id FK, product_id FK, list_price NUMERIC(12,2), currency,
             partner_price NUMERIC NULL, vip_price NUMERIC NULL,
             valid_from DATE, valid_to DATE NULL)   -- UNIQUE(region_id, product_id, valid_from)
exchange_rates (id, base CHAR(3), quote CHAR(3), rate NUMERIC(14,6), as_of DATE)
```

`pricing.py` service 统一入口：`quote_price(region, product, qty, customer_tier)`
→ 取 price_list → 叠加 Region.tax_rules_json（VAT，含"波兰光伏 8%"这类条件规则，
JSON 条件就放在 tax_rules_json 里）→ PlatformFeeRule 抽成 → 汇率换算。
Quote 模块改为只调用 pricing，不再自己拿 product.list_price。

### 3.4 AI Memory

```sql
ai.memories (
  id, region_id NULL,
  subject_type TEXT, subject_id UUID,   -- lead|company|contact|partner
  kind TEXT,                            -- preference|fact|constraint|plan
  content TEXT,                         -- "老婆喜欢白色开关；预算5万；明年想加光伏"
  source_conversation_id FK NULL, confidence NUMERIC(3,2),
  expires_at NULL, status TEXT          -- active|stale|invalidated
)
```

consult workflow 结束时由 LLM 抽取记忆候选 → 落 ai_reviews（低风险可自动激活，
价格承诺类必须人审）→ 下次对话按 subject 注入 system prompt。这就是
"半年后还记得 John 喜欢白色开关"的实现，成本极低。

### 3.5 Cost Engine（成本引擎，置于 Pricing 之前）

**已有基础**：`ProjectFinance` 已经有项目级成本全分解（supplier/shipping/customs/
local_installer/labor/travel/spare_parts/warranty_reserve）+ 毛利/LTV 派生计算
（`services/finance.py compute_finance`）—— 这是**事后实际成本**。
缺的是**事前产品级 landed cost**：报价之前就知道真实成本和毛利。

```sql
product_costs (
  id, region_id FK, product_id FK, supplier_id FK NULL,
  purchase_cost NUMERIC(12,2), currency,
  freight_pct NUMERIC(5,2), customs_pct NUMERIC(5,2),     -- 比例或固定额二选一
  freight_fixed NUMERIC NULL, customs_fixed NUMERIC NULL,
  warehousing_pct NUMERIC(5,2), labor_estimate NUMERIC NULL,
  landed_cost NUMERIC(12,2),                              -- 派生缓存
  valid_from DATE, valid_to NULL
)  -- UNIQUE(region_id, product_id, valid_from)
```

计算链路：**Cost Engine → Pricing Engine → Quote**。`pricing.py` 报价时同时返回
`landed_cost + margin`，Quote 上每行可见毛利；授标后 Partner 实际报价回写
ProjectFinance 形成"预估 vs 实际"闭环。"波兰利润比塞尔维亚高 12%" = 跨
region 对 product_costs × price_lists 的一条聚合查询，Phase E 进 Business Brain。

### 3.6 Partner Score（复合评分，喂给 RFQ 排序）

**已有基础**：供应商侧 `SupplierScorecard`（七维评分）已存在；Partner 侧只有
`rating_internal` 单值。新增计算型指标表，celery-beat 每日重算：

```sql
partner_metrics (
  id, partner_id FK UNIQUE,
  response_hours_avg NUMERIC, completion_rate NUMERIC(5,2),
  cancellation_rate NUMERIC(5,2), on_time_rate NUMERIC(5,2),
  warranty_claim_rate NUMERIC(5,2),         -- 来自 tickets×assets 关联
  customer_review_avg NUMERIC(3,2), revenue_total NUMERIC(14,2),
  ai_risk_score NUMERIC(5,2) NULL,          -- orchestrator 异常模式分析
  composite_score NUMERIC(5,2),             -- 加权综合 0-100
  breakdown_json JSONB, computed_at
)
```

权重放 settings（region 可覆盖）。RFQ 比价（3.1 的 `bid_evaluation` workflow）
的输入就是 composite_score + breakdown —— 排序可解释，不是黑盒。数据冷启动期
（项目少）以 rating_internal + 响应速度为主，权重随数据量自动倾斜。

### 3.7 Living Case Dataset（案例库 = 成交武器 + 护城河资产）

不是 Blog，是**活的运营数据集**：每个交付项目自动回填一条结构化记录
（面积/预算/产品组合/Partner/工期/返修次数/满意度/毛利/AI 摘要 + 向量），
这是第⑧护城河 Operational Dataset 的主载体。目标体验：客户说"180㎡ 别墅"，
AI 直接给出相似度 96% 的 Case、对应预算、推荐 Partner 和预计工期。

```sql
cases (
  id, region_id, project_id FK NULL,        -- 可回填真实项目，也可手工录入
  title, country, city, property_type TEXT, -- villa|apartment|office|hotel|factory
  area_sqm INT, budget NUMERIC(12,2), currency,
  products_json JSONB, partner_id FK NULL,
  duration_days INT, gross_margin_pct NUMERIC(5,2),  -- 内部字段，不对外
  rework_count INT, satisfaction_score NUMERIC(2,1), -- 运营数据：返修/满意度
  ai_summary TEXT,                           -- AI 生成的卖点摘要（审核后）
  photos_json JSONB, customer_feedback TEXT,
  summary TEXT,                              -- 用于嵌入
  public_visible BOOL, embedding_document_id FK ai.knowledge_documents NULL
)
```

复用 Phase B 全部基建：case 摘要进知识库（source_type='case_study' 已支持）→
向量化；相似推荐 = 结构化过滤（国家/类型/面积±30%/预算±30%）+ 向量相似度，
consult workflow 新增 `find_similar_cases` 工具 —— "200㎡、5 万欧、华沙 →
Case #204 相似度 96%" 就是这一条查询。官网案例页从 cases 渲染（隐藏利润字段）。

### 3.8 AI Business Brain（CEO 晨报，最高层）

不建新系统 —— 它是**编排层**：Memory + Analytics + Forecast + Risk 的聚合 workflow。

```
celery-beat 每日 07:00 → orchestrator workflow `daily_briefing`
  → 只读 SQL 聚合：昨日 lead/quote/授标/营收、维保到期、风险 Partner
    （partner_metrics 恶化）、待跟进（ai.memories + renewal_queue）
  → LLM 生成自然语言晨报（未配置 LLM 则纯数据模板）
  → Telegram 推送（复用既有通道）+ admin Dashboard 卡片
  → 落 ai.agent_runs 审计
```

Forecast（趋势预测）数据攒够两个季度后再加，先把"每天早上主动汇报"跑起来。

### 3.9 AI Procurement（采购，Phase F 预留）

**已有基础**：`InventoryItem` 有 product/supplier/min_stock/reorder 字段，
缺货检测今天就能写。流程复用 RFQ 模式（对象从 service_partners 换成 vendors）：

```
项目授标 → BOM 对库存 → 缺口 → procurement_requests（draft）
  → vendor 询价（RFQ 同构）→ 采购建议进 ai_reviews → admin 审批 → 下单跟踪
```

表（`procurement_requests` + `vendor_quotes`）设计同 3.1，Phase F 实现。

### 3.10 AI Digital Marketing（一级核心模块）

定位：六大核心之一（AI Solution Engine / CRM&Lead / RFQ&Partner / Product
Knowledge / Project&AMC / **AI Digital Marketing**），未来可单独 SaaS 收费。
**行业专用，不做万能营销平台** —— 内容全部从产品库/案例库/知识库生成，这是
对通用 AI 营销工具的代差优势。

**已有基础（诚实盘点）**：`marketing_automation` 已在产出多语言跟进草稿（带
pending_approval 审批门 + 按 lead_score 定跟进节奏）；UTM 归因已通到 leads/
inquiries；marketing_contacts 自带 GDPR consent_status；lead 级 AI 评分已有。
缺的是：生成式内容升级、图片/视频、社媒分发、SEO 引擎、访客级评分。

#### 八个子能力与实现方式

| 子模块 | 现状 | 实现 | Phase |
|--------|------|------|-------|
| Content Studio | ◐ 规则草稿已有 | orchestrator `content_gen` workflow：输入 product/case/knowledge → 输出 LinkedIn 长文/FB 图文/TikTok 脚本/Blog/Email 多语言变体 → `marketing_assets` → **全部进 ai_reviews** | C |
| Localized Marketing | ◐ i18n+region 已有 | `region_marketing_profiles`（每国 tone/卖点/合规话术：波兰=节能+欧盟认证，塞尔维亚=价格+本地服务，德国=DIN+隐私+质保），注入 content_gen prompt | C |
| Image Studio | ❌ | integration_settings 加 `ai_media` category（gpt-image / Flux API，接口可换），品牌套件（logo/色板/字体）放 settings，产物入 MinIO `marketing-assets` | D |
| SEO Engine | ◐ Nuxt SSR 天然友好 | `seo_pages` 表（keyword→FAQ/对比页/落地页，从知识库生成，审核后发布），frontend-pc 动态路由渲染；Search Console 关键词回流 | D（关键词自动化 E）|
| Social Distribution | ❌ | **不自建 8 个 OAuth 集成**（一人维护不动 Meta/TikTok 审核流程）：用聚合层（自托管 Mixpost 或 Ayrshare API）做发布后端，自己只建 `publish_jobs` 表 + adapter 接口（可替换）。LinkedIn/FB/IG/Google Business 先行 | D（TikTok/YouTube E）|
| Video Studio | ❌ | 分两步走：脚本+字幕生成（文本，便宜）→ D；真实视频渲染（模板化幻灯+配音，或外部 API）→ F。"每天几十条"是 F 的目标不是起点 | D/F |
| AI Lead Scoring | ✅ lead 级已有 | 访客级评分需要行为事件流：用 **Plausible/Matomo（cookieless，EU 合规）**，不用 GA4（多国 DPA 已裁定违反 GDPR） | F |
| Campaign Agent | ❌ | 先做只读：广告数据（Meta/Google/LinkedIn API）日报进 Business Brain（E）；自动 AB test/预算调配（F） | E/F |

#### 表设计

```sql
marketing_assets (
  id, region_id, campaign_id FK NULL, product_id FK NULL, case_id FK NULL,
  kind TEXT,        -- post|article|image|video_script|video|email|landing_page
  channel TEXT,     -- linkedin|facebook|instagram|tiktok|youtube|gbp|x|blog|email
  lang, title, content TEXT NULL, media_minio_key NULL,
  ai_generated BOOL DEFAULT true,    -- EU AI Act 透明标识源头
  review_id FK ai.ai_reviews NULL,
  status TEXT       -- draft|in_review|approved|scheduled|published|failed
)
publish_jobs (id, asset_id FK, platform, account_ref TEXT,
              scheduled_at, published_at NULL, external_post_id NULL,
              status, error_message NULL)
seo_pages (id, region_id, lang, slug UNIQUE, target_keyword,
           title, content_md, status, published_at NULL)
region_marketing_profiles (id, region_id FK UNIQUE,
                           tone_json, emphasis_json, compliance_notes TEXT)
```

#### 欧洲合规（必须内建，不是事后贴补丁）

- **GDPR**：邮件营销 double opt-in；consent_status 已有，发送前强制校验；不做
  冷采集个人数据外呼。
- **EU AI Act（2026-08 起透明义务生效）**：AI 生成内容需可机读标识 ——
  `ai_generated` 字段贯穿到发布元数据，对外页面带标注。
- **Cookie/追踪**：官网分析用 cookieless 方案（Plausible 自托管），避免 GA4
  的 EU 合规风险，也省 cookie banner 摩擦。
- **平台政策**：Meta/TikTok 商业账户验证走聚合器可部分规避自建 App 审核。

#### 营销闭环（与 v2 各模块的接合点）

```
产品库/知识库/案例库(3.7) → content_gen → ai_reviews → 发布(publish_jobs)
  → UTM 归因(已有) → Lead → AI 顾问(Phase B) → 方案/报价 → RFQ → 交付
  → 项目回填 Case(3.7) → 新素材 → 再营销     ← 数据闭环，每单交付反哺获客
```

进程拓扑依旧不变：content_gen 在 orchestrator，生成与发布任务在 celery
`automation` 队列，聚合器只是 HTTP 调用。

### 3.11 AI Voice Agent（语音接待 = channel-gateway 的一个 adapter）

装修/集成行业大量客户直接打电话，不写邮件 —— 语音是欧洲市场的关键入口。
**架构上它不是新系统**：语音只是 channel-gateway 的又一个 adapter，
复用 Phase A/B/C 的全部管线：

```
来电（波兰/塞尔维亚本地号码）
  → 电话服务商 webhook（Twilio/Telnyx，不自建电信栈）
  → channel-gateway voice adapter
     ├─ 实时 STT（多语言：PL/EN/SR/DE，Whisper 级别）
     ├─ → orchestrator consult workflow（同一个 RAG/产品/案例/lead 捕获）
     ├─ ← TTS 回复（Azure/ElevenLabs，sr-RS 有现成语音）
     ├─ 转写落 ai.messages（channel='voice'），录音入 MinIO
     └─ 收集：面积/预算/城市/联系方式 → /internal/v1/leads → 预约回访
```

数据模型零新增：channel_accounts(channel='voice') 存号码配置，
channel_threads = 一通电话（meta_json 存 call SID/时长/录音 key），
转写进 ai.messages，lead 走既有内部 API。

**合规红线（实现前必须满足）**：
- **AI Act Art.50**：必须开场告知"您正在与 AI 助手通话"（与人机交互的 AI 系统强制透明义务）。
- **录音同意**：按国别播报录音提示（波兰/塞尔维亚均要求知情）；录音保留期限入 GDPR 数据清单。
- 听不懂/客户要求 → 立即转人工（Phase 早期 = 留言+回电承诺，事件通知 admin）。

**实现节奏**：Phase D 做 channel-gateway 时预留 adapter 接口；
Phase D.5 上第一条线路（建议波兰号码 + 英语/波兰语，Twilio 实时双向流 +
语音管线用现成 speech-to-speech API，成本约 €0.1-0.3/分钟，对 B2B lead 完全可接受）；
塞尔维亚语 TTS 与本地号码随塞尔维亚业务量跟进。

### 3.12 Self-learning Marketing Loop（营销自学习闭环）

3.10 的发布链路闭合成回路：

```
内容发布 → publish_jobs → UTM 归因（已有）→ Lead → 成交 → Case 回填
   ↑                                                        ↓
   └── 内容效果反馈（哪类案例/渠道/语言带来高分 lead）←──────┘
```

实现：marketing_assets 加发布效果回流（Phase E 广告/分析 API 只读接入后），
content_gen 的 prompt 注入"历史高转化内容特征"——不是玄学自学习，
是把转化数据变成生成上下文。Phase F 再考虑自动权重调整。

### 3.13 Workflow Definitions（配置式，不可视化）

```sql
workflow_definitions (id, region_id NULL, key TEXT, version INT,
                      definition_json JSONB, is_active BOOL)
-- definition_json: {states:[...], transitions:[{from,to,on_event,conditions,actions}]}
workflow_instances (id, definition_id FK, subject_type, subject_id,
                    current_state, context_json, history_json)
```

执行器订阅事件总线（Phase A 已就绪），按国家选 definition —— 波兰流程 A、
塞尔维亚流程 B 改 JSON 不改代码。拖拽编辑器 = Phase 3 SaaS 化以后的事。

---

## 4. 支付与 Escrow（Phase 2 实现，设计现在锁定）

### 4.1 牌照现实（最重要）

- **自建钱包持有客户/Partner 资金 = 需要支付机构牌照**（EU: PSD2 EMI/PI；塞尔维亚: NBS 支付机构法）。一人公司不可能合规自营，**这条路线直接排除**。
- **Stripe 不支持塞尔维亚实体**（支持波兰、罗马尼亚）。Escrow 式分账要用
  **Stripe Connect**（destination charges + manual payouts：钱由 Stripe 持有，
  平台控制何时放款给 Partner —— 天然实现里程碑放款 + retention 延迟释放）。
  前提：**平台运营主体注册在 PL/RO（或 EE 等 Stripe 国家）**。
- EU 替代：Mangopay / Lemonway（真 wallet 托管模式，marketplace 专用牌照覆盖）。
- 塞尔维亚本地客户：Phase 1-2 银行转账 + 系统记账（本来就是你的计划）；
  本地卡收单远期再说（本地收单行/2Checkout 等）。

### 4.2 记账先行（Phase C 就建表，不动真钱）

```sql
payment_plans (id, project_id FK, quote_id FK, currency,
               total NUMERIC(12,2), retention_pct NUMERIC(4,2),      -- 工程保留金 e.g. 5.00
               retention_release_days INT,                            -- 90
               status TEXT)        -- draft|active|completed|cancelled
payment_milestones (
  id, plan_id FK, seq INT, label TEXT,        -- deposit|midterm|acceptance|retention
  pct NUMERIC(5,2), amount NUMERIC(12,2),
  trigger TEXT,                               -- on_accept|on_schedule|on_acceptance|days_after
  status TEXT,                                -- pending|invoiced|funded|released|refunded
  funded_at, released_at, external_ref TEXT   -- Phase 2: Stripe payment_intent / transfer id
)
ledger_entries (                              -- 复式记账，"钱包"只是这个账本的视图
  id, entry_group UUID,                       -- 同一笔业务的双边分录同组
  account TEXT,        -- customer:{id} | partner:{id} | platform:revenue | escrow:psp | bank:offline
  direction TEXT,      -- debit|credit
  amount NUMERIC(12,2), currency,
  milestone_id FK NULL, memo TEXT
)
partner_deposits (id, partner_id FK, amount, currency,
                  status TEXT,                -- requested|held|partially_forfeited|refunded
                  external_ref NULL, forfeiture_log_json JSONB)
```

30/40/30 + 5% retention 就是 milestones 的四行数据；Phase 1 人工线下收款时
admin 点"已到账" → milestone=funded + ledger 记账 → 事件 `payment.milestone_funded`
→ 自动通知 Partner 开工。**Phase 2 接 Stripe 只是把"admin 点确认"换成 webhook。**

### 4.3 状态机与事件

```
milestone: pending → invoiced → funded → released（给 partner）
                                  └→ refunded（争议）
retention: funded → (验收后 N 天 celery-beat 检查) → released
事件: payment.milestone_funded / payment.milestone_released /
      payment.retention_released / partner.deposit_forfeited
```

---

## 5. 修订路线图（合并你的 Phase 1/2/3）

```
Phase C = 你的 Phase 1 MVP（人工收款、人工确认授标）✅ 已完成 2026-06-10
  Cost Engine（product_costs landed cost）→ Pricing Engine + price_lists 多币种
  RFQ 竞价撮合（邀请走 Telegram/邮件）+ Partner Score（partner_metrics 每日重算）
    + AI 比价评分（进 ai_reviews）
  Assets 资产登记（接通 lifecycle 既有保修/AMC）
  Case Library 建表 + 嵌入知识库（复用 Phase B 摄取管道）
  AI Memory + lead_score / quote_draft / content_gen workflows（消费事件总线）
  Marketing：marketing_assets + region_marketing_profiles（文本内容多语言草稿，
    审核后人工发布）
  payment_plans/milestones/ledger 建表（记账先行，线下转账）
  跑通：官网→AI→方案(引用相似案例)→报价(带毛利)→RFQ→评分排序→人工授标
        →线下收款→项目→资产→维保

Phase D（交付与渠道 + 业务大脑）✅ 已完成 2026-06-10
  （Voice 第一条线路与 WhatsApp adapter 需真实账号：Twilio 号码 / Meta Business
   认证 —— 网关 adapter 接口已就绪，账号到位即接入）
  channel-gateway（v1 既定）：WhatsApp/邮件双向 + Partner 接单推送
  Partner 角色视图（frontend-h5）：接单/报价/日历/任务
  AI Business Brain：daily_briefing 晨报（Telegram + Dashboard 卡片）
  Case 相似推荐进 consult workflow（find_similar_cases 工具）
  Marketing：Image Studio（ai_media 集成）+ SEO Engine v1（seo_pages）
    + 社媒定时发布（聚合器：LinkedIn/FB/IG/GBP）+ 视频脚本生成
  Document Center（合同/验收单/维保报告模板 + AI 草稿）
  Scheduler/派单 + Design Center（CAD 归档）
  Voice Agent 第一条线路（波兰号码，EN/PL，AI Act 告知 + 录音同意内建）

Phase E = 你的 Phase 2 ✅ 机制已交付 2026-06-10（Stripe 激活待 EU 实体 + 密钥）
  在线签约（文档中心 + 签名）
  Stripe Connect：定金/里程碑/retention/Partner 保证金线上化
  自动派单（授标→日历→任务）
  跨国利润分析进 Business Brain（"波兰利润高于塞尔维亚 12%"）
  Marketing：TikTok/YouTube 分发 + 广告数据只读日报进 Business Brain
    + SEO 关键词自动发现（Search Console 回流）

Phase F = 你的 Phase 3（平台化/SaaS）
  Partner Marketplace 公开化 · 多租户 SaaS · AI Procurement（采购询价闭环）
  拖拽 Workflow 编辑器 · AI 问数 · Forecast 预测
  Marketing：Campaign Agent（自动 AB test/预算调配）· 视频自动渲染
    · 访客级评分（Plausible 事件流）· Marketing 模块 SaaS 化单独售卖
```

## 6. 未来模块储备（5-10 年价值层，只留种子不开发）

> 终极定位：**欧洲 AI General Contractor OS** —— 面向智能建筑/光伏/安防/自动化/
> 系统集成公司的 AI 操作系统。先在自己的垂直里做成行业标准，Phase F SaaS 化时
> 泛化到任何 Solution Company（solution_line/trade 保持为数据而非代码，
> 现在的 SOLUTION_LINES 常量届时迁为配置表）。

关键认知：**这十个模块有九个是读侧分析层** —— 它们的"接口"就是已经在积累的
数据资产。所以"预留"的实际含义是：维度一致（region_id/solution_line/
property_type 贯穿所有表 ✅）+ 历史不可变（账本 append-only ✅、价格按
valid_from 版本化 ✅、快照见下）。

| 模块 | 读什么（已有数据资产） | 现在需要预留什么 | Phase |
|------|------------------------|------------------|-------|
| ① Business Benchmark | cases × project_finances × partner_metrics × rfqs 聚合（"波兰200㎡均价42000、成交率74%"）；未来可单卖 Market Intelligence | 无 — 维度已一致 | E 起步报表，F 产品化 |
| ② Supplier Intelligence | SupplierScorecard + product_costs 历史 + Phase F 采购单（延迟/缺货数据从采购闭环才开始产生） | 无 — 随 AI Procurement 落地 | F |
| ③ Risk Engine | **partner_metrics 时间序列** + 工单/投诉 | ⚠️ 快照表（migration 014，已落） | E |
| ④ Expansion Engine | 内部 benchmark + 外部市场数据（公司名录/竞争密度） | 无 — 纯分析层 | F |
| ⑤ Revenue Engine | ledger_entries + ProjectFinance + AMC 续费（收入结构与预测） | 无 — 账本已 append-only | E（进 Business Brain）|
| ⑥ Partner Academy | service_partners.certifications_json 已有 | 无 — 课程/考试/Badge 表届时新建 | F |
| ⑦ Compliance Center | ai_generated 标识 ✅ consent_status ✅ audit_logs ✅ | 无 — 检查规则届时写 | E/F |
| ⑧ AI Simulation | quote_price() × cases 先验 × partner_metrics（方案 A/B 模拟 = 纯计算层） | 无 — 输入全在 | E/F |
| ⑨ CEO Dashboard | = Business Brain 的 UI 形态（admin 首页即晨报 + Approve 流） | 无 — Phase D 落地 | D |
| ⑩ 泛行业 OS | 全部以上 | solution_line 保持数据化 | F |

## 7. v2 明确不做（新增防腐条目）

- ❌ 自建钱包/自持资金（牌照）— 账本记账 + PSP 托管
- ❌ 图数据库（Neo4j 等）— SQL 多跳工具等价
- ❌ 通用规则引擎 — 领域内 JSON 条件
- ❌ 拖拽流程编辑器（Phase F 前）— JSON workflow 定义
- ❌ 第四个前端应用 — partner 用 h5 角色视图
- ❌ AI 自动授标/自动放款 — AI 推荐 + 人确认（与 preliminary 审核惯例一致）
- ❌ 3D Digital Twin 开发 — 只做 assets 层级建模预留
- ❌ 自建 8 个社媒 OAuth 集成 — 聚合层（Mixpost/Ayrshare）起步，adapter 可换
- ❌ 万能 AI 营销平台 — 只做智能建筑行业专用（内容源 = 自己的产品/案例/知识库）
- ❌ GA4 — cookieless 分析（Plausible/Matomo 自托管），EU 合规
- ❌ AI 内容免审发布 — 一律过 ai_reviews + AI Act 透明标识（ai_generated 贯穿）
- ❌ 自建电信/STT/TTS 栈 — Voice Agent 用 Twilio/Telnyx + 现成语音 API
- ❌ Voice AI 不自报身份 — AI Act Art.50 强制告知，开场白写死在 adapter 里
- ❌ 漂亮的大屏动画 / 炫酷 3D Twin / 花哨 CRM 界面 — 不沉淀数据资产的一律不做
- ❌ 不沉淀新数据资产的任何功能（铁律：先回答"它积累什么别人没有的数据"）

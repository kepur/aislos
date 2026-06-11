# AinerWise OS — 企业级目标架构设计

> ⚠️ 2026-06-10 起定位升级为 AI General Contractor 平台 —— 增量设计见
> `AISLOS_V2_GENERAL_CONTRACTOR.md`（RFQ 竞价撮合、资产登记、定价引擎、支付/Escrow）。
> 本文档的进程拓扑、数据层、事件总线、ADR 与 Phase A/B 交付物继续有效。

> AI Smart Living Business OS（AISLOS）
> 本文档是目标架构（Target Architecture），描述从当前代码库演进到企业级 Business OS 的完整设计。
> 当前实现状态见 `docs/ARCHITECTURE.md`（注意：该文档中"单一前端三布局"的描述已过时，现为三个独立 Nuxt 应用）。

---

## 0. 核心结论（先读这个）

1. **官网和 OS 不是两个系统。** `frontend-pc` 就是官网，它是 OS 的获客前端。官网上的表单、AI 顾问对话，全部直接落入同一个数据库的 Lead/CRM 表。不需要再建一个"官网系统"。
2. **不做微服务。** 一人运营 + AI 自动化的模式下，运维带宽是最稀缺资源。采用 **模块化单体 + 少量卫星进程** 架构。
3. **进程总数不变或只加一个。** 现有 docker compose 已经是正确的拓扑，需要做的是：
   - 实装 `ai_orchestrator`（目前是空壳）
   - 把 `telegram_bot` 升级为 `channel_gateway`（统一消息渠道网关）
   - 其余所有业务模块（CRM/Lead/Quote/Project/Lifecycle/Marketing/Partner/Finance/Knowledge）**全部留在 backend 单体内**，以 Python 模块为边界，不拆进程。
4. **一个 PostgreSQL 实例，用 schema 划分服务边界**：`public`（业务核心）、`ai`（对话/向量/知识）、`channels`(消息渠道)。数据共享，但写入权限按服务隔离。

---

## 1. 三层定位

```
第一层  获客前台（客户看到的）
        frontend-pc 官网 + AI 顾问入口 + WhatsApp/Telegram/Email
第二层  业务后台（你和团队用的）
        frontend-admin + backend 模块化单体 = Business OS
第三层  AI 知识中台（两边共用的大脑）
        ai_orchestrator + pgvector 知识库 + Product Database
```

| 层 | 职责 | 不做什么 |
|---|---|---|
| 官网 frontend-pc | 品牌展示、方案/案例、SEO 内容、表单、AI 顾问聊天窗口 | 不是商城，无购物车、无支付 |
| 客户门户 frontend-h5 | 客户查看自己的报价、项目进度、工单、设备档案 | 不做设备控制（不是 Smart Home OS） |
| 管理后台 frontend-admin | 全部业务操作：CRM、报价、项目、派单、维保、营销、伙伴 | — |
| backend | 所有业务逻辑与数据 | 不直接调 LLM（委托给 orchestrator） |
| ai_orchestrator | LangGraph Agent、RAG、内容生成、AI 摘要 | 不直接写业务表（走 backend 内部 API） |
| channel_gateway | Telegram/WhatsApp/Email 消息收发 | 不含业务逻辑，只做协议转换 |

---

## 2. 架构决策记录（ADR）

### ADR-1：模块化单体，不是微服务

**决定**：CRM、Lead、Quotation、Project、Lifecycle、Marketing、Partner、Finance、Knowledge 全部作为 backend 内的模块（现有 `app/models/*.py` + `app/api/v1/endpoints/*.py` + `app/services/*.py` 的结构），共享一套 SQLAlchemy 事务和外键。

**理由**：
- 这些模块之间是强事务关系：Lead 转 CRM、Quote 引用 Product、Project 引用 Quote、Ticket 引用 Device。拆开进程 = 分布式事务 + 数据不一致 + N 倍运维成本。
- 单人团队，每多一个服务就多一份部署、日志、监控、版本协调成本。
- Postgres 单实例可以轻松支撑到几万客户、几十万文档级别，瓶颈远未到来。

**什么时候才拆**（触发条件，满足任意一条再说）：
- 某模块的伸缩曲线明显不同（如向量检索 QPS 是业务 API 的 100 倍）
- 某模块的故障必须隔离（如 LLM 调用超时不能拖垮报价接口 → 这正是 orchestrator 独立的原因）
- 某模块发布节奏完全不同（每天改 prompt vs 每周改业务）

### ADR-2：ai_orchestrator 独立进程（已预留，需实装）

**理由**：满足上面全部三条触发条件——依赖重（langgraph/LLM SDK）、LLM 调用慢且不稳定需要故障隔离、prompt 迭代节奏远快于业务代码。token 成本核算也独立。

### ADR-3：telegram_bot 升级为 channel_gateway

**理由**：消息渠道是 webhook/长轮询模式，与请求-响应式 API 生命周期不同；渠道会持续增加（Telegram → WhatsApp Business API → Email/IMAP → Facebook Messenger）；渠道挂掉不能影响核心业务。一个网关进程统一所有渠道，而不是每个渠道一个进程。

### ADR-4：单 Postgres 实例 + schema 边界

**决定**：不上独立向量数据库（Qdrant/Weaviate），用已有的 pgvector。

**理由**：数据量级（万级文档、百万级 chunk 以内）pgvector 完全够；省一个有状态服务；向量与业务数据可以 JOIN（"只检索该客户所在国家可售产品的文档"一条 SQL 解决——这是独立向量库做不到的核心优势）。

### ADR-5：多国家用 row-level region 隔离，不是多库

详见第 6 节。SaaS 化之前不引入 schema-per-tenant。

---

## 3. 进程拓扑（docker compose 服务清单）

| # | 服务 | 状态 | 职责 |
|---|------|------|------|
| 1 | `postgres` (pgvector/pg16) | ✅ 已有 | 唯一数据源：业务 + 向量 + 消息 |
| 2 | `redis` | ✅ 已有 | 缓存、Celery broker、事件流、限流 |
| 3 | `minio` | ✅ 已有 | 文件存储（见 bucket 规划） |
| 4 | `backend` | ✅ 已有 | FastAPI 模块化单体，所有业务 API |
| 5 | `celery-worker` | ✅ 已有 | 异步任务，按队列拆分（见 5.3） |
| 6 | `celery-beat` | ✅ 已有 | 定时调度（续费提醒、保修到期、营销发布） |
| 7 | `frontend-pc` :4099 | ✅ 已有 | 官网（获客前台） |
| 8 | `frontend-h5` :4098 | ✅ 已有 | 客户门户 |
| 9 | `frontend-admin` :4097 | ✅ 已有 | 业务后台 |
| 10 | `nginx` | ✅ 已有 | 唯一对外入口，路由 + TLS + webhook 转发 |
| 11 | `ai-orchestrator` :8100 | 🔨 实装（现为空壳） | LangGraph Agent / RAG / 内容生成，仅内网可达 |
| 12 | `channel-gateway` :8200 | 🔨 由 telegram_bot 升级 | 全部消息渠道收发，仅内网可达 + nginx webhook 路由 |

**不再新增任何进程。** 安装技工 App（后期）是 frontend-h5 的一个角色视图或 PWA，不是新服务。

### 网络规则

- 对外只暴露 nginx（80/443）。
- `ai-orchestrator`、`channel-gateway` 只在 docker 内网，backend 通过 service token 调用。
- 渠道 webhook（Telegram/WhatsApp/Meta）由 nginx 路由到 `channel-gateway`，路径 `/webhooks/{channel}`。

---

## 4. 数据架构

### 4.1 一个 Postgres，三个 schema

```
public    业务核心（现有 24+ 表：users, products, leads, crm, quotes,
          projects, tickets, lifecycle, marketing, finance, regions ...）
ai        conversations, messages, knowledge_documents, document_chunks,
          agent_runs, prompt_templates, ai_reviews
channels  channel_accounts, channel_threads, channel_messages, delivery_log
```

### 4.2 写入权限矩阵（用不同的 PG role 强制执行）

| 服务 | public | ai | channels |
|------|--------|-----|----------|
| backend | 读写 | 读写 | 只读 |
| ai-orchestrator | **只读** | 读写 | 只读 |
| channel-gateway | 无 | 无 | 读写 |
| celery-worker | 读写 | 读写 | 只读 |

关键规则：**orchestrator 不直接写业务表**。AI 要创建 Lead、更新 CRM、生成报价草稿时，调用 backend 的内部 API（`/internal/v1/...`，service token 鉴权）。这样：业务校验只有一份、审计日志（现有 audit 模块）不被绕过、AI 输出保持 preliminary 状态等待 admin review（项目既有惯例）。

### 4.3 ai schema 表设计

```sql
-- 知识源：每份上传/抓取的原始资料
ai.knowledge_documents (
  id UUID PK, region_id UUID NULL,          -- NULL = 全球共享
  source_type TEXT,                          -- pdf|manual|faq|case_study|email|chat|url
  title, lang, minio_key, checksum,
  product_id UUID NULL REFERENCES public.products,  -- 可挂产品
  status TEXT,                               -- pending|chunked|embedded|failed
  meta JSONB, created_at, updated_at
)

-- 切块 + 向量
ai.document_chunks (
  id UUID PK, document_id FK,
  chunk_index INT, content TEXT,
  embedding vector(1536),                    -- 维度按所选 embedding 模型定
  tsv tsvector,                              -- 混合检索：向量 + 全文
  meta JSONB
)
-- 索引：HNSW on embedding, GIN on tsv

-- 对话（官网 AI 顾问、WhatsApp、Telegram 全部进这里）
ai.conversations (
  id UUID PK, region_id, channel TEXT,       -- web|whatsapp|telegram|email
  visitor_id / user_id / crm_contact_id,     -- 渐进式身份绑定
  lead_id UUID NULL,                         -- AI 判定有商机后回填
  status, lang, created_at
)
ai.messages (conversation_id FK, role, content, tool_calls JSONB, tokens INT, created_at)

-- Agent 执行审计：每次 AI 动作可追溯、可计费
ai.agent_runs (id, conversation_id, workflow, input, output,
               tool_trace JSONB, tokens_in, tokens_out, cost_usd, latency_ms, status)

-- AI 产出审核队列（preliminary → approved/rejected）
ai.ai_reviews (id, run_id, target_type, target_id, draft JSONB,
               status, reviewed_by, reviewed_at)
```

### 4.4 Redis 用途划分

| DB/前缀 | 用途 |
|---------|------|
| `celery:*` | 任务队列 broker |
| `cache:*` | API 响应缓存、产品目录缓存 |
| `rate:*` | 官网 AI 顾问限流（按 IP/session） |
| `stream:events` | 领域事件流（见 5.2） |
| `conv:*` | 对话短期状态（当前会话上下文指针） |

### 4.5 MinIO bucket 规划

```
product-assets/     产品图片、datasheet、CAD、BIM
knowledge-source/   知识库原始文件（PDF/手册/案例）
quotes-pdf/         生成的报价单 PDF（按 region 分目录）
project-photos/     安装前后照片、签收单
documents/          合同、证书（现有 certification/file 模块）
```

---

## 5. 服务间通信

### 5.1 同步：内部 HTTP + service token

- backend → orchestrator：`POST /agent/chat`、`POST /agent/generate`（报价草稿、营销文案、CRM 摘要）
- orchestrator → backend：`/internal/v1/leads`、`/internal/v1/quotes/draft`、`/internal/v1/products/search` 等
- channel-gateway → orchestrator：`POST /agent/chat`（客户消息直达 AI）
- orchestrator → channel-gateway：`POST /send`（AI 回复发回对应渠道）
- 所有内部调用带 `X-Service-Token`，每个服务一个 token，env 注入。

### 5.2 异步：outbox 事件 + Redis Stream

backend 已有 `integration_events` 雏形，正式化为事件总线：

1. 业务事务内写 `public.integration_events` 表（outbox 模式，保证不丢）
2. Celery 任务把 outbox 推到 Redis Stream `stream:events`
3. 消费者：celery-worker（通知/自动化）、orchestrator（AI 跟进）、channel-gateway（消息推送）

事件命名规范 `域.动作`：

```
lead.created          → AI 评分 + Telegram 通知 admin
lead.scored           → 高分线索自动进跟进队列
quote.sent            → 3 天未读自动提醒（celery-beat）
quote.accepted        → 创建 project
project.completed     → 创建维保档案 + 触发 AMC 报价
ticket.opened         → 派单通知
device.warranty_expiring  → 续费营销流程（现有 renewal_queue 服务）
knowledge.uploaded    → 触发 ingestion 流水线
ai.draft_ready        → admin 审核队列通知
```

### 5.3 Celery 队列拆分

```
default        业务异步（邮件、PDF 生成、通知）
ai_ingestion   知识库摄取（抽取/切块/嵌入），低优先级、可积压
automation     营销自动化、生命周期自动化（现有 *_automation 服务）
```

一个 worker 进程监听多队列即可；量大后同一镜像按 `-Q` 参数分容器，**不需要改代码**。

---

## 6. 多国家 / 多租户架构

### 6.1 现阶段（自营，塞尔维亚 → 波兰 → 罗马尼亚）

Row-level 隔离，基于现有 `regions` 表：

```
共享（无 region_id 或 region_id=NULL）:
  products, product_categories, vendors(中国供应商),
  knowledge_documents(通用部分), prompt_templates, 营销素材模板

按 region 隔离（带 region_id 列）:
  leads, crm, quotes, projects, tickets, invoices,
  service_partners(本地安装商), price_lists, tax_rules,
  channel_accounts(每国独立 WhatsApp 号)
```

实现：FastAPI dependency 从 JWT/请求上下文解析当前 region，CRUD 层统一注入过滤。报价金额存 `amount + currency`，汇率表挂 region。

### 6.2 SaaS 化阶段（卖给其他集成商时）

触发条件：第一个外部付费客户签约。届时升级为 `tenant_id` 双层隔离（tenant → region），敏感客户可选 schema-per-tenant。**现在只需要保证所有隔离表同时预留 `region_id`，并且查询永远走统一的过滤中间件**，未来加 `tenant_id` 是机械改造。

共享层（所有租户共用，这是 SaaS 的护城河）：产品数据库、知识库向量、AI 能力、供应商网络、营销模板。

---

## 7. AI / RAG 管道

### 7.1 知识摄取（celery `ai_ingestion` 队列，不是独立服务）

```
上传/抓取 → MinIO(knowledge-source) → knowledge.uploaded 事件
  → 抽取文本（pypdf/unstructured，扫描件走 OCR）
  → 按语义切块（512-1024 token，重叠 64）
  → 调 embedding API → 写 ai.document_chunks (embedding + tsv)
  → 状态机：pending → chunked → embedded / failed（可重试）
```

### 7.2 检索（orchestrator 内）

混合检索一条 SQL：向量相似度 + 全文 tsv + 业务过滤（region 可售、产品在档、语言匹配）→ RRF 融合 → top-k → 重排（可选）→ 进 prompt。

### 7.3 Agent 工作流（LangGraph，orchestrator 内）

| Workflow | 触发 | 工具 |
|----------|------|------|
| `consult` | 官网/渠道客户对话 | 产品检索、知识 RAG、需求收集、lead 创建 |
| `lead_score` | lead.created 事件 | CRM 历史、对话质量分析 |
| `quote_draft` | admin 一键/对话触发 | 产品库、价格表、报价模板 → 草稿（不直接发送） |
| `crm_summary` | 定时/查看时 | 对话+邮件+工单历史 → 摘要、情绪、概率 |
| `content_gen` | 营销日历定时 | 案例库、产品库 → 多语言文章/帖子草稿 |
| `maintenance_advisor` | 设备数据异常事件 | 设备档案、手册 RAG → 维保建议 |

**铁律（项目既有惯例）**：所有 AI 产出落 `ai.ai_reviews`，状态 preliminary，admin 审核后才生效/发出。对外自动回复仅限知识问答类，涉及价格承诺、合同条款一律转人工。

---

## 8. 渠道网关（channel_gateway）

```
Telegram webhook ─┐
WhatsApp Business ─┤→ nginx /webhooks/{channel} → channel-gateway
Email (IMAP poll) ─┘        │
                            ├─ 统一 Message 模型 → channels.channel_messages
                            ├─ 绑定/创建 ai.conversations
                            ├─ → orchestrator /agent/chat（客户消息）
                            └─ → backend 通知接口（admin 提醒，复用现有 telegram 通知）
```

- 每个渠道一个 adapter（同进程内的 Python 模块），实现 `receive() / send() / normalize()` 三个接口。
- 阶段：Telegram（已有代码迁入）→ WhatsApp Business Cloud API → Email。
- 发送侧幂等：`delivery_log` 记录 message_id，重试不重发。

---

## 9. 脑暴模块 → 现有代码映射（缺口清单）

| 模块 | 现状 | 缺口 |
|------|------|------|
| Product Database | ✅ `products.py` + categories + compatibility | 补 datasheet/manual 关联到 knowledge_documents |
| Vector DB / RAG | ❌ pgvector 镜像已用但无表 | 新建 ai schema + ingestion 管道（第一优先级） |
| AI Agent | ❌ orchestrator 空壳；backend 有 ai_agent/ai_graph 雏形 | LangGraph 实装，backend 内 AI 代码迁出 |
| CRM | ✅ `crm.py` | 加 AI 摘要字段（关联 agent_runs） |
| Lead | ✅ `leads.py` + `inquiries.py` | 接 AI 评分 workflow |
| Quotation | ✅ `quotes.py` + `proposals.py` + quote_pdf | 接 quote_draft workflow、多语言 PDF |
| Project / Installation | ✅ `projects.py` | 安装 checklist + 照片上传（用现有 file 模块） |
| Maintenance | ✅ lifecycle + tickets + warranty + amc + spare_parts | 已经超出脑暴范围，无缺口 |
| Partner | ✅ `service_partners.py` + `vendors.py` | — |
| Marketing | ✅ `marketing.py` + marketing_automation | 接 content_gen workflow |
| 多国家 | ✅ `regions.py` | 隔离表逐步补 region_id + 统一过滤中间件 |
| Document Center | ✅ `files.py` + certifications | — |
| Workflow Automation | ✅ lifecycle_automation 等 | 事件总线正式化（5.2） |
| Customer Portal | ✅ frontend-h5 | — |
| Analytics | 部分（finance/recurring_revenue） | 后期加 dashboard 聚合 API |
| 渠道（WhatsApp/Email） | ❌ 仅 Telegram 通知 | channel-gateway（第二优先级） |

**结论：脑暴清单里约 90% 的业务模块已有代码。真正要建的是三样：ai schema + RAG 管道、orchestrator 实装、channel-gateway。**

---

## 10. 安全

- 现有 JWT + RBAC（5 角色）不变；内部服务间 service token。
- PG role 按 4.2 矩阵授权，schema 边界数据库层强制。
- AI 工具调用白名单：orchestrator 只能调注册过的 internal API，每次调用落 agent_runs 审计。
- 官网 AI 顾问：匿名 session + IP 限流 + 每会话 token 预算上限（防刷成本）。
- prompt injection 防线：RAG 内容标记为不可信数据段；AI 永远无法直接执行写操作（preliminary 审核兜底）。

---

## 11. 实施路线图

```
Phase A（地基）✅ 已完成 2026-06-10
  ai/channels schema 迁移 + PG role 权限      → alembic 011, scripts/setup_service_roles.sql
  outbox 事件正式化（复用 integration_events）  → app/services/event_bus.py + relay_outbox_events (beat 30s)
  Celery 队列拆分                              → default / ai_ingestion / automation

Phase B（AI 中台）✅ 已完成 2026-06-10
  knowledge ingestion 管道       → app/services/knowledge.py + embeddings.py（OpenAI 兼容 + hash 降级）
  orchestrator 实装              → ai_orchestrator/（consult workflow + hybrid RAG 检索 + lead 捕获）
  官网 AI 顾问 + admin 审核页    → AiConsultant.vue / ai-reviews / knowledge 管理页
  备注：LLM/embedding 凭据在 Admin → Integrations (AI) 配置；未配置时全链路以
  extractive 降级模式运行（hash 向量 + 全文检索 + 正则 lead 捕获），配置后自动升级。

Phase C（业务 AI 化, ~3-4 周）
  lead_score / quote_draft / crm_summary workflows
  事件驱动自动化接通（lead.created → 评分 → 通知）

Phase D（渠道, ~2-3 周）
  telegram_bot → channel-gateway 重构（先 Telegram 双向对话）
  WhatsApp Business API 接入

Phase E（增长）
  content_gen 营销自动化、多语言报价 PDF、
  波兰/罗马尼亚 region 开通、Analytics dashboard

SaaS 化：第一个外部客户签约后再启动 tenant 改造（见 6.2）
```

---

## 12. 明确不做（防止架构腐化）

- ❌ 微服务全家桶：每个业务模块一个服务
- ❌ Kafka / RabbitMQ（Redis Stream + outbox 足够）
- ❌ Kubernetes（docker compose 单机 → 量大后 compose 多机/swarm）
- ❌ 独立向量数据库（pgvector 够用，见 ADR-4）
- ❌ API Gateway 产品（Kong/Traefik——nginx 够了）
- ❌ database-per-country / schema-per-tenant（SaaS 签约前不做）
- ❌ GraphQL / BFF 层（REST + 三前端直连够用）
- ❌ 商城、购物车、在线支付、复杂库存（业务定位明确排除）
- ❌ Smart Home 设备控制平面（不是 Home Assistant 竞品）

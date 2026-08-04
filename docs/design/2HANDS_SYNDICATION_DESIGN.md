# 2Hands 二手平台 + 多渠道推流/广告自动化 — 设计方案

> 起草 2026-07-06。目标:先用二手业务跑通现金流(规避高关税),同时把"多地区推流 + 广告自动化 + 统一数据分析"做成可复用的**平台能力**,后续 AinerWise 主业与其他项目都能调用。

---

## 0. 一句话结论

**2Hands 不是新系统,是 AISLOS 里的一个 Portal;推流不是新服务,是 `channels` schema 的自然扩展;分析不是新数据库,是现有 outbox 事件总线上加一层 `analytics` schema。**

三件事都走"扩展既有资产"的路,不违反架构宪法(单 Postgres、模块化单体、无微服务/Kafka/K8s)。

---

## 1. 现有可复用资产(已核实)

盘点结论:**推流所需的骨架已经存在 70%**,主要是缺映射表、驱动契约和事件粒度。

| 已有资产 | 位置 | 在本方案中的角色 |
|---|---|---|
| **Portal 注册机制**(20+ portal) | `app/core/portal_registry.py` + nginx 注入 `X-Portal-Key` | 直接加 `2hands` portal,子域名路由是成熟路径 |
| **`channels` schema** | `app/models/channels.py` | `ChannelAccount(channel, **region_id**, credentials_json, status, meta_json)` = "某地区某平台的一个账号",正是推流渠道注册表 |
| **`ChannelDeliveryLog`** | 同上 | `attempt/status/error_message` — 重试与失败日志已成型 |
| **`channel_gateway` 独立进程** | `channel_gateway/` | 推流 worker 的天然归宿(不新开进程) |
| **`IntegrationEvent` 事务性 outbox** | `app/models/integration.py` | 业务事务内写 outbox → `published_at` 中继到 **Redis Stream 事件总线**。**这就是统一数据管理的主干,已建好** |
| **`AdCampaign`** | `app/modules/cebu_trade/models.py` | 站内广告(listing_id/定向/预算/竞价/曝光点击转化)。但计数是聚合列,**缺创意粒度** |
| **`CreativeBrief` + 版本 + `ExternalExport`** | `app/schemas/marketing.py` | AI 生成广告文案的既有接口(provider-neutral + content_hash) |
| **`integration_settings`** | `app/services/integrations.py` | 分 category 的配置 + 密钥掩码 → 各渠道凭据配置 |
| **Celery worker + beat** | docker-compose | 推流任务队列、限流、定时同步 |
| **records-first 支付**(本周刚做) | `cebu_compat` | **与二手当面取货天然契合** —— 平台不碰钱,现场直付+记录 |
| **`Region` + region_id 隔离** | 全局 | 多国多地区推流的隔离维度已存在 |

---

## 2. 架构决策

### 决策 1 — 2Hands 作为 Portal,不新建系统

```
ainerwise.com          → 官网(AI 智能建筑主业,后启)
market.aislos.com      → AISLOS Market(B2B 采购)
2hands.ainerwise.com   → 2Hands 二手(先跑,现金流)   ← 新增
admin.aislos.com       → 统一后台(含推流控制台)      ← 扩展
```

- 新 `portal_key = "secondhand"`(对外品牌 2Hands,内部 key 不可改名 —— 遵循 cebu 的教训)
- 复用:listing / category / order / messaging / admin / auth / 支付记录
- 前端:复制 `modules/procurement/pc` 的独立产品化模式(已验证可行),而不是从零起 Nuxt

**为什么不做独立系统**:二手 SKU 卖掉后要**立刻全渠道下架**,库存唯一性要求数据强一致;分开建库会立刻遇到跨库事务问题。而且"后面统一分析"这个诉求,数据分家就直接破产。

### 决策 2 — 二手业务字段与取货流

商品扩展(`SupplierListing.attributes_json` 或新建 `secondhand_details` 表):

| 字段 | 说明 |
|---|---|
| `condition_grade` | A/B/C/D 成色分级(影响定价与推流文案) |
| `purchase_year` / `usage_hours` | 使用年限 |
| `serial_no` / `imei` | 序列号(防赃物、防重复上架的关键) |
| `warranty_left_months` | 剩余保修 |
| `defects[]` | 瑕疵清单(图 + 描述,二手信任的核心) |
| `original_packaging` | 是否原包装 |
| `quantity = 1` | **二手默认唯一库存** → 触发全渠道下架的前提 |

履约模式 `fulfillment_mode`:
- `SELLER_PICKUP` — 联系卖家拿地址,到地方取货(你描述的主流程)
- `PICKUP_POINT` — 自提点/驿站
- `PARTNER_CHANNEL` — 渠道方代收代发
- `SHIP` — 寄送

**地址披露流(GDPR + 人身安全,必须做)**:
```
卖家上架(地址加密存储,前台只显示城市/区)
  → 买家表达购买意向
  → 双方在站内确认成交意向
  → 系统才向该买家披露完整地址 + 联系方式(记录披露事件)
  → 买家到场取货 → 买家在 App 确认"已取货"
  → 现场直付(平台不托管资金,仅记录)→ 交易闭环
```
披露动作要写审计事件;卖家可随时撤回。

### 决策 3 — 推流引擎:渠道驱动契约(**这是"开放接口标准化"的落点**)

**数据层**(扩展 `channels` schema):

```python
# 复用 ChannelAccount,加 kind='syndication'
#   channel='kupujemprodajem' | 'olx' | 'facebook_marketplace' | ...
#   region_id=<塞尔维亚>       credentials_json=<该平台账号凭据>

class ChannelListing(Base):          # 新增:推流映射表(核心)
    __tablename__ = "channel_listings"
    __table_args__ = {"schema": "channels"}

    listing_id        # 我们的 SKU
    account_id        # 推到哪个渠道账号(= 平台 × 地区)
    external_id       # 对方平台的帖子 ID
    external_url      # 对方帖子链接(用于回流统计与人工核查)
    status            # DRAFT/PENDING_REVIEW/PUBLISHED/FAILED/DELISTED
    content_hash      # 内容指纹 → 判断是否需要重推(幂等,避免刷屏被封)
    last_synced_at
    last_error
    stats_json        # 回拉的浏览/联系数
```

**驱动契约**(所有渠道统一,AI 代理只是其中一种实现):

```python
class ChannelDriver(Protocol):
    kind: Literal["api", "feed", "assisted", "agent"]
    capabilities: set[str]      # publish/update/delist/stats/messages

    def map_listing(listing, mapping) -> ChannelPayload   # 我方类目/字段 → 对方类目/表单
    async def publish(payload) -> ExternalRef
    async def update(ref, payload) -> None
    async def delist(ref) -> None
    async def fetch_stats(ref) -> dict          # 浏览/点击/联系数
    async def fetch_messages(ref) -> list       # 对方站内信 → 汇入 ChannelThread(已有!)
```

四种驱动类型(**按合规优先级排序**):

| 类型 | 做法 | 何时用 |
|---|---|---|
| `api` | 官方 API / 合作伙伴计划 | **首选**,稳定合规 |
| `feed` | 生成 XML/CSV 商户 feed 供对方拉取 | 次选,多数平台支持商户批量 |
| `assisted` | 系统备好文案+图片包+类目映射,**人工一键确认发布** | **无 API 时的合规解**,效率仍提升 ~80% |
| `agent` | 交给 `ai_orchestrator` 的 AI 代理 | 后期,受 `ai_reviews` 人工闸门约束 |

> **"后面由 AI 代理接入"在架构上零成本**:AI 代理就是第四种 driver,契约不变、映射表不变、任务队列不变。

**类目/字段映射**:`channel_category_map(account_id, our_category_id, their_category_code, field_map_json)` —— 每个平台一份,后台可编辑。这是推流最脏的活,必须做成配置而不是硬编码。

**任务编排**(复用 Celery):
- 队列:`syndication.publish / update / delist / pull_stats / pull_messages`
- **每渠道限流**(令牌桶),避免触发对方风控
- 指数退避重试,失败写 `ChannelDeliveryLog`(已有表)
- **卖出即下架**:`listing.sold` 事件 → 扇出 delist 到所有 `PUBLISHED` 的 channel_listings(二手唯一库存的刚需)

### 决策 4 — 事件脊柱:统一数据管理与分析

现状问题:`AdCampaign.impressions/clicks` 是**聚合列**,回答不了"**哪张广告图 CTR 高**"。

新增 `analytics` schema(第四个 schema,与 public/ai/channels 并列):

```python
class AnalyticsEvent(Base):        # append-only,永不 UPDATE
    __tablename__ = "events"
    __table_args__ = {"schema": "analytics"}

    occurred_at, event_type        # impression/click/view_detail/contact_seller/
                                   # lead/offer/order/delivered/cancelled
    region_id, portal_key          # 地区 × 门户(天然多租户切片)
    channel_account_id             # 站内 or 哪个外部渠道 ← 渠道归因
    listing_id, sku                # ← SKU 归因
    creative_id                    # ← 广告图/文案变体归因(关键!)
    campaign_id                    # 关联 AdCampaign
    session_id, actor_hash         # 匿名化访客(GDPR:哈希,不存原始 PII)
    value_minor, currency          # 成交额
    source_app                     # 哪个外部项目推来的 ← 开放 API 归因
    idempotency_key                # 去重
    meta_json

class Creative(Base):              # 广告创意(图/文案变体)
    __tablename__ = "creatives"
    listing_id, image_url, copy_text, variant_label
    generated_by                   # human | ai
    content_hash
```

**数据流(全部复用既有基础设施)**:
```
业务事务 ──写──> integration_events (outbox,同事务,不丢)
                      │ published_at 中继(已有)
                      ▼
               Redis Stream 事件总线(已有)
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   analytics.events 消费者      通知/推流消费者
          │
          ▼ (Celery beat 夜间/近实时)
   analytics.daily_sku_stats / channel_stats / creative_stats  ← 物化视图
```

**这样才能回答你要的三个问题**:

| 你的问题 | 查询对象 |
|---|---|
| 哪些 SKU 好卖 | `daily_sku_stats`:曝光→详情→联系→成交漏斗 + 周转天数 + GMV |
| 哪个渠道获客转化率高 | `channel_stats`:按渠道×地区的 lead 成本、转化率、ROI |
| 哪张广告图点击率高 | `creative_stats`:`clicks/impressions` by `creative_id` → 自动淘汰低效创意 |

### 决策 5 — 开放 API(其他项目调用统一数据)

```
POST /api/v1/events                     # 事件批量摄取(带 idempotency_key)
GET  /api/v1/syndication/channels       # 渠道列表
POST /api/v1/syndication/listings/{id}/publish   # 请求推流(异步,返回 job)
GET  /api/v1/syndication/listings/{id}/status    # 各渠道状态
GET  /api/v1/analytics/sku|channel|creative      # 只读看板数据
Webhook out: listing.sold / listing.updated / lead.created
```

- **API Key per 外部应用**,scope 限定 `region_id + portal_key`,所有写入打 `source_app` 标签
- 版本化 + 幂等键 —— 这样"后面 AI 代理接入"和"其他项目调用"都是同一套契约

### 决策 6 — AI 介入的边界(遵守宪法)

AI 可以做:生成广告文案变体、挑选/裁剪主图、定价建议、类目映射建议、回复话术草稿。
AI **不可以**做:未经人工确认就对外发布、自动成交、自动降价。

→ 所有**对外发布**动作(外部平台发帖、投放广告花钱)必须先落 `ai_reviews` 由管理员批准。
这既是宪法要求,也是现实需要:对外发布不可逆,发错内容伤品牌、还可能封号。

---

## 3. ⚠️ 必须提前处理的商业/法律风险

**多数二手平台的 ToS 明文禁止自动化发帖与爬取**(KupujemProdajem、OLX、Facebook Marketplace 都是)。这是本方案最大的落地风险,建议:

1. **先谈合作,再写代码** —— KupujemProdajem 有商业客户/商户方案,先接触拿官方 feed 或 API 授权。谈成一家,后面所有地区都好谈。
2. **无 API 时默认走 `assisted` 模式** —— 系统把内容、图片、类目全部准备好,人工点一下发布。合规、零封号风险,效率已经大幅提升。
3. **headless 浏览器自动化当最后手段**,并且逐渠道单独评估:账号一旦被封,这个渠道就永久失去了 —— 用短期效率换长期渠道,不划算。
4. **GDPR**:塞尔维亚已生效 GDPR 对标法规。卖家地址加密存储 + 最小化披露 + 披露审计;分析事件里访客标识必须哈希,不存原始 PII。
5. **赃物合规**:序列号/IMEI 登记 + 卖家实名,这在欧洲二手交易是硬要求,也是差异化信任优势。

---

## 4. 分期路线(建议)

| 阶段 | 内容 | 产出 |
|---|---|---|
| **P0**(2-3 周) | 2Hands portal + 子域名 + 二手类目 + 成色/序列号字段 + 取货流 + 地址披露 | **能卖货、有现金流** |
| **P1**(2 周) | `ChannelListing` 映射表 + driver 契约 + `feed`/`assisted` 驱动 + 后台推流控制台 | **半自动多平台上架**、卖出自动全渠道下架 |
| **P2**(2 周) | `analytics` schema + 事件摄取 + outbox 消费者 + 3 张看板(SKU/渠道/创意) | **能看清什么好卖、哪个渠道值得投** |
| **P3** | 首个真 `api` driver(先谈成合作)+ 开放 API + API Key + Webhook | **其他项目可接入** |
| **P4** | `agent` driver:AI 文案/选图/定价建议 + `ai_reviews` 闸门 | **AI 代理接入,人工把关** |

P0 先跑起来收钱,P1/P2 才是护城河。**不要在 P0 就做 AI 和自动化** —— 没有数据的时候 AI 没有原料,自动化也没有验证过的流程可自动化。

---

## 5. 待你确认的开放问题

1. **子域名定名**:`2hands.ainerwise.com` / `polovno.ainerwise.com`(塞语"二手")/ 独立域名?
2. **首发地区**:只做塞尔维亚,还是同时波黑/黑山(语言相通,可共用渠道驱动)?
3. **卖家来源**:平台自营囤货,还是 C2C 撮合(卖家自主上架)?—— 这决定了库存模型和审核工作量
4. **首批渠道优先级**:KupujemProdajem 之外,是否还要 OLX / Facebook Marketplace / Instagram?
5. **是否先接触 KupujemProdajem 商业合作** —— 这个谈判结果直接决定 P1 走 `api` 还是 `assisted`

---

## P0 落地记录(2026-07-06 完成)

| 项 | 产出 |
|---|---|
| 数据模型 | `secondhand_listings`(成色/序列号/瑕疵/取货字段)、`secondhand_address_disclosures`(披露审计)、`secondhand_deals`(C2C 成交,records-first)。迁移 079 + 080 |
| Portal | `portal_key="secondhand"`(内部 key,不可改名),layout=secondhand,theme=2hands |
| 域名 | nginx `2hands.localhost / 2hands.ainerwise.com`,注入 `X-Portal-Key: secondhand`;前端 :4105 |
| 后端 API | `/api/v1/secondhand/*` 13 条:公开浏览/详情、卖家上架改价、地址披露申请-授权-撤回-读取、预订、确认取货、取消、我的清单/交易 |
| 前端 | `modules/secondhand/pc`(独立 Nuxt,**标准 Tailwind JIT**,不用预编译 compiled.css):浏览/详情/上架/我的/登录 |
| 测试 | `tests/test_secondhand_2hands.py` 4 条,覆盖隐私不变量、唯一库存、序列号查重;teardown 已加 2Hands 清理 |

### P0 三条硬不变量(已测试固化)
1. **地址不外泄** — 公开浏览/详情/上架响应均不含 `pickup_address / pickup_note / contact_phone`;未授权买家取地址 403;**按字段授权**(只授权 address 就拿不到 phone);卖家可撤回,撤回后立即 403。
2. **唯一库存** — 一件商品只能被预订一次(重复 409);确认取货后 `status=sold` 并从公开列表消失(P1 接推流后同步全渠道下架)。
3. **平台不碰钱** — 确认取货只记录 `payment_method + payment_reference`,资金由买卖双方现场直付。

### ⚠️ P1 必须补的硬化项
- **地址静态加密**:当前 `pickup_address/contact_phone` 是明文列,靠 API 层严格管控 + 审计留痕。代码库暂无字段级加密工具,**上生产前需接 pgcrypto 或应用层加密并做密钥管理**。
- 卖家实名与序列号核验(目前只做重复拦截,未对接失窃库)。

---

## P1 落地记录(2026-07-06)

**约束:纯增量,不得变更原版系统流程。** 与 `p0-2hands` 标签对比,P1 仅触碰 4 个文件:
`api.py`(+2 行 include_router)、`models/__init__.py`(+模型导出)、`conftest.py`(+测试清理)、
`secondhand.py`(2Hands 自有端点接入下架扇出)。**原版系统零改动,全量 418 测试通过。**

| 项 | 产出 |
|---|---|
| 映射表 | `channels.channel_listings`(SKU × 渠道账号 → external_id/状态/内容指纹)、`channels.channel_category_maps`(类目+字段映射,可后台编辑)。迁移 081 |
| 复用不改表 | 渠道账号复用现有 `channels.channel_accounts`,靠 `meta_json.kind="syndication"` 区分 —— **零 schema 变更** |
| 驱动契约 | `ChannelDriver` Protocol:publish/update/delist(+stats/messages 能力位)。**AI 代理接入 = 加第四种 driver,契约与任务路径不变** |
| 已实现驱动 | `feed`(渲染商户 feed 供渠道自行拉取)、`assisted`(生成人工发布内容包)。**两者均不对第三方发起任何请求** |
| API | `/api/v1/syndication/*` 10 条:渠道 CRUD、类目映射、推流、状态、待办队列、回填帖子ID、确认撤下、feed 导出、全渠道下架 |

### 合规姿态(架构级保证)
`get_driver()` 对 `api` / `agent` / 未知类型**一律降级为 assisted**。没有官方合作协议就不可能自动发帖 ——
这不是靠规范约束,是代码默认行为。要启用 `api` 驱动必须显式注册该渠道实现。

### 测试固化的不变量
1. **地址永不出境** — 推流响应、feed XML、人工内容包中均无完整地址/电话,只带 `国家/城市/区`
2. **幂等防封号** — 内容指纹未变则跳过重推(重复发帖是账号被封的主因)
3. **卖出即下架** — 确认取货自动扇出:可自动化渠道直接 `delisted`,人工渠道进 `pending_takedown` 待办队列
4. **扇出失败不影响成交** — 推流异常被吞并记录,不回滚已完成的线下交易

### 测试中发现并修正的建模缺陷
最初 assisted 渠道下架后停留在 `pending_review`,与「待人工发布」同状态,运营看板**无法区分该发还是该撤**。
已拆分出 `pending_takedown`,并新增 `/syndication/queue` 待办队列(action = post / take_down / retry)
+ `confirm-takedown` 人工确认端点。否则人工渠道的活会静默堆积,已售商品继续挂在外部平台。

### P2 之前仍需的
- Celery 队列化 + 每渠道限流(当前推流同步执行,适合小批量;上量需异步化)
- `analytics` 事件脊柱(P2 本体)
- 后台推流控制台 UI(当前仅 API)

### P1-5 运营控制台(2026-07-06)

推流的待办队列此前只有 API,人看不见 —— assisted 渠道的活会静默堆积:该发的没发、已售的还挂在外部平台。
补齐后台页面(admin SPA `/syndication`,导航「渠道推流 / Syndication」):

- **待办队列**:每行明确标注该做什么 —— `Publish`(去发)/ `Take down`(已售,去撤)/ `Failed`(重试)
- **就地处理**:人工发布后回填对方帖子 ID、确认已撤下、失败强制重推
- **渠道管理**:创建渠道时用大白话说明发布方式,并提示 api/agent 在注册集成前一律降级 assisted
- **类目映射**:每渠道可视化维护,不用发版
- feed 渠道直接链到生成的 `.xml`

改动仅 5 个共享文件共 +5 行(路由/导航/i18n/Vite 代理)+ 1 个新页面。**原版流程零变更,418 测试仍全过。**

### 回溯标签
`p0-2hands` → `p1-syndication` → `p1-console`(分支 `feat/2hands-secondhand`)

### P1 仍缺(不影响使用)
- **Celery 队列化 + 每渠道限流** —— 当前推流同步执行,小批量够用;批量上量必须异步化,否则请求会超时
- 渠道回拉浏览/联系数(`fetch_stats`),这是 P2 分析的输入之一

---

## P2 落地记录(2026-07-06):分析事件脊柱

**约束照旧:纯增量。** 原版系统只多了 14 行,全是注册(路由 include、模型导出、Celery imports/schedule),**零业务逻辑改动**。全量 425 测试通过。

| 项 | 产出 |
|---|---|
| Schema | 新增第四个 schema `analytics`:`events`(append-only 脊柱)、`creatives`(广告图/文案变体)、`projection_cursors`(投影水位线)。迁移 082 |
| 记录服务 | `record_event` 幂等 + `record_event_safe` 尽力而为(分析故障绝不影响成交) |
| 埋点 | 2Hands 全链路(曝光/浏览/索要地址/授权/预订/成交)+ 推流(渠道发布/下架)。**都在自有代码内** |
| **原版接入** | `analytics_projection.py` 按水位线读 `integration_events` 投影 —— **既有生产者一行不改**,`source_app='core'`。Celery beat 每 60s |
| 读 API | `/analytics/funnel`、`/sku`、`/channel`、`/creative`、`/health`,外加 `/events` 批量摄取与 `/creatives` 管理 |

### 实测能回答的三个问题
```
问题一 哪些SKU好卖    Laptop 浏览5 线索1 成交1 收入550EUR 看→问20%  |  Phone 浏览2 线索0 成交0
问题二 哪个渠道转化高  Our storefront 浏览7 线索1 成交1 ...(推流渠道带来的流量按 channel_account_id 归因)
问题三 哪张图CTR高     场景使用图(AI) 曝光100 点击12 CTR=12.0%  |  白底正面图(人工) 100/3 CTR=3.0%
漏斗                  曝光10 → 浏览7(70%) → 索要地址1(14.3%) → 预订1(100%) → 成交
```

### 关键设计选择
- **按需聚合,不物化**:当前量级 Postgres 走复合索引毫秒级返回,且实时查询不会过期或与事件漂移。等看板真的慢了再物化 —— 事件粒度不变,随时可加。
- **GDPR**:`actor_hash` 用 app secret 加盐单向哈希(测试断言不可逆),`session_id` 是浏览器本地生成的不透明 token。不存任何原始访客 PII,所以数据可长期保留。
- **幂等**:`idempotency_key` 唯一索引。重放批次返回 `duplicates` 计数而非重复计收入(已测)。

### 测试中发现并修正的三个缺陷
1. **`source_app` 可为空** → 外部摄取全落 "unknown",跨项目归因(这个 API 存在的理由)直接失效。已改为**批次级必填**。
2. **漏斗转化率 >100% 显示为裸数字** → 外部渠道成交本就不经过我方浏览/预订步骤,200% 是真实的,但看板上像算错。已加 `exceeds_previous_step` 标记,让 UI 能注明"含未经上游追踪的活动"。
3. **漏斗顶端恒为 0** → 浏览列表没埋点,缺曝光就没有"多少人看过才点进来"的分母。已在浏览接口埋点,前端配发本地 `session_id`。

### P2 仍缺
- **开放 API 的 API Key**(外部项目接入现在复用登录态;`MarketingIntegrationClient` 的 key_prefix/secret_hash/scopes 模式可直接照搬)
- 后台分析看板 UI(现有只有 API)
- 渠道回拉浏览/联系数(`fetch_stats`),让外部渠道的曝光也进漏斗

---

## P2 补完(2026-07-06):看板 / 开放 API Key / 渠道回拉

430 测试全过。原版系统本轮零改动。

### 1. 后台分析看板(admin `/analytics`)
漏斗条形图(含 >100% 的 ⓘ 说明)、渠道对比、创意 CTR(带缩略图、AI/human 标签、best 标记)、SKU 排行、数据来源分布。
UI 里两处刻意的判断:曝光多但 `view→lead=0` 的 SKU 标红(说明看得到但没人要,问题在价格或图片);CTR 最高的创意标 best。

### 2. 开放 API Key(`analytics.clients`,迁移 083)
照搬 `MarketingIntegrationClient` 的成熟模式(key_prefix + secret_hash + scopes + region/portal 围栏)。

**关键决策:`source_app` 绑定在密钥上,不取请求体。** 否则任何客户端都能把流量归因到别的项目,跨项目报表就失去意义。已测:请求体里塞 `"source_app":"我想冒充别人"` 被忽略,实际记为密钥own的 `ads-rs`。

安全边界全部测过:无密钥 401、用户 JWT 冒充 401(两套认证不混用)、scope 不足 403、吊销后立即 403。密钥明文只在签发时返回一次。

### 3. 渠道 fetch_stats 回拉
驱动契约新增 `fetch_stats() -> StatsResult`。**`available` 是这个契约里最重要的字段** —— 拿不到数据的渠道必须明说,而不是返回 0;0 会变成分母,让所有转化率算错。feed 是单向拉取、assisted 帖子在别人账号里,两者都诚实返回 `available=False` 并提示人工录入。

**累计值只计增量**:渠道给的是累计数,重复读取必须只记增长部分,否则每刷新一次就重复计一遍曝光。已测:120→150 只新增 30,不是再记 150。

现在渠道报表终于有曝光分母:`KupujemProdajem 曝光1260 浏览210` vs `自有店面 浏览85 成交2` —— 可以看出外部渠道流量大但意向弱。

### 回溯标签
`p0-2hands` → `p1-syndication` → `p1-console` → `p2-analytics` → `p2-complete`

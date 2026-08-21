# Growth 模块：采集 · 本地化 · 自动定价 · 分发 —— 底层标准 (V1)

> 一个可登录配置的 PC 后台模块。目标：**从中国货源（闲鱼/淘宝/1688）采集商品 → LLM 翻译文案 + 图片翻译/生成 → 按「成本+运费+汇率+目标毛利+平台费率」自动加价定价 → 生成推广图文/视频 → 定时批量发布到 IG/FB 等渠道**，全部走一套统一契约，后面接任何 API 只是"实现一个适配器"，也可让 LLM 按标准直接调用。

契约的**权威定义在代码**里：[`backend/app/modules/growth/contracts.py`](../backend/app/modules/growth/contracts.py)。本文件是它的说明书 + 复用地图 + 落地计划。

---

## 0. 关键结论：一半已经有了

本平台**已经存在**"生成 → 定时多平台发布 → 外部/LLM worker 按标准认领交付 → 凭证配置"的骨架，**不要重复造**：

| 已有能力 | 现有实现 | 在标准里的角色 |
|---|---|---|
| 凭证/开关配置（含 `social`/`ai`/`voice` 的 api_key，密钥脱敏） | `models/settings.py` `IntegrationSetting` + `SECRET_KEYS` | **provider 配置存储**，直接复用，新增 `source`/`pricing` 两个 category |
| 创意简报 → 生成图/视频的**认领队列** | `models/marketing.py` `MarketingCreativeBrief(+Version)`、`MarketingMediaRequest`（available→claimed→completed，`external_job_ref`/`progress_percent`/`failure_code`） | **异步 Job 标准**（`ProviderJob`/`JobStatus` 直接对齐它） |
| 生成的图文/视频资产（`kind=post/article/image/video_script`，含 mime/宽高/时长/sha256） | `MarketingAsset` | `MediaAsset` / `CopyResult` 落库目标 |
| 外部 worker 注册 + 幂等 | `MarketingIntegrationClient(+Idempotency)` | provider 作为"外部客户端"的既有对接方式 |
| **定时多平台发布** | `models/content.py` `PublishJob`（`platform`/`account_ref`/`scheduled_at`/`external_post_id`/`status`）+ `tasks/publishing_tasks.py::dispatch_publish_jobs`（Ayrshare 式聚合器 `/post`） | `Publisher` 契约 + `PublishRequest` 1:1 映射，复用聚合器 |
| **成本/落地价/汇率/平台费率** | `models/costing.py`（`ProductCost.freight_pct/freight_fixed/landed_cost`、`ExchangeRate`）、`models/finance.py` `platform_fee_rules`、订单 `platform_fee_minor` | `PriceInputs`/`compute_sell_price` 的底层数据来源 |
| LLM/Agent 编排 | `services/agent_team.py`（含 `marketing-agent`） | `TOOL_SIGNATURES` 里每个能力方法 = 一个 agent 工具 |
| 已有推广规划 | `docs/AUTOMATED_PROMOTION_PLAN.md`、`docs/AISLOS_MARKETING_INTEGRATION_V4_TASKS.md` | 本标准是它的"采集+套利定价+统一适配器"扩展 |

**真正要新建的只有 4 块**：① 采集层（闲鱼/淘宝/1688）；② 图片翻译（抠字重排）；③ 自动加价 + 定时重算；④ 把上面所有东西收敛到一套 provider 适配器注册表 + 后台配置页。

---

## 1. 能力分类 (Capability)

每种能力 = 一个 Protocol，一个 provider 声明自己实现哪些能力。见 `Capability` 枚举：

`source` · `translate_text` · `translate_image` · `gen_copy` · `gen_image` · `gen_video` · `price` · `publish`

后台配置、provider 注册表、LLM 工具面全部以这套值为 key。

## 2. Provider 适配器契约

一个 provider 只需实现它声称的能力对应的 `Protocol`，然后 `registry.register(spec, impl)`。**调用方永远不写死厂商名**。切 ByteDance→OpenAI、1688→闲鱼，只是新增一个 adapter 文件。

```
SourceAdapter    .search(SourceQuery)->[SourcedItem]  .fetch(url_or_id)->SourcedItem
TextTranslator   .translate(TranslateRequest)->TranslateResult
ImageTranslator  .translate_image(ImageTranslateRequest)->MediaAsset
CopyGenerator    .generate_copy(CopyRequest)->CopyResult
ImageGenerator   .generate_image(ImageGenRequest)->[MediaAsset]
VideoGenerator   .generate_video(VideoGenRequest)->MediaAsset
Repricer         .price(PriceInputs)->PriceQuote
Publisher        .publish(PublishRequest)->PublishResult
```

所有出入参都是 **pydantic v2 DTO、JSON 可序列化**，因此同一套方法既能被服务层调，也能作为 **LLM 工具**（`TOOL_SIGNATURES`）自动调用。

## 3. 异步 Job 标准（认领队列）

长耗时能力（采集、图/视频生成、图片翻译、批量翻译）统一走 `ProviderJob`：`available → claimed → running → completed | failed`，字段与现有 `MarketingMediaRequest` 对齐。**同一个 Job，既能被平台内 adapter 直接跑，也能被外部 worker/LLM 认领后回传**——两种对接方式零差异。

## 4. 自动加价定价标准（套利核心）

`compute_sell_price(PriceInputs) -> PriceQuote`，公式即契约（自定义 Repricer 可覆盖，但以此为准）：

```
landed  = 采购价*汇率*(1+运费%) + 固定运费
landed += landed * 关税/税费%
pre_fee = landed / (1 - 目标毛利%)      # 保住毛利
sell    = pre_fee / (1 - 平台费率%)      # 为平台抽成做 gross-up
sell    = 四舍五入(round_to_minor) 后 clamp(min,max)
```

金额一律 **整数 minor units + 币种**（与全站 `*_minor` 一致）。已验证：CNY 80 采购、汇率 0.13、运费 15%、目标毛利 30%、平台费 8%、取整到 €1 → 落地 **€11.96**、售价 **€19.00**、实得毛利 **31.6%**。

**定时重算**：一条 `PriceRule`（每商品/每类目）+ 一个 celery beat 任务，按汇率变动/竞品/库存周期性重跑 `compute_sell_price`，超过阈值才写新价（避免抖动）。复用 `ExchangeRate` + `platform_fee_rules`。

## 5. 后台配置面（可登录设置）

- **provider 凭证/开关**：复用 `IntegrationSetting`，新增 category：`source`（采集源 cookie/token/第三方数据 API key）、`pricing`（默认毛利/运费表/取整规则）。密钥继续走 `SECRET_KEYS` 脱敏。
- **权限**：admin 门户里新增一个 workbench grant，比如 `admin_growth`（并入 `portal_access.py` 的 super_admin/admin 授权列表，参照本轮修复超管授权的做法），后台按 grant 显示菜单。
- **页面（frontend-admin PC）**：`采集源管理` / `翻译&图片&视频 provider` / `定价规则` / `发布渠道&排期` / `任务队列(ProviderJob)` / `套利看板(成本→售价→毛利)`。全部四语（已接 `/admin/translate-draft` LLM 翻译）。

## 6. LLM 工具映射

`TOOL_SIGNATURES` 是 agent 允许调用的 `工具名 ↔ 能力` 白名单：`source.search/fetch`、`translate.text/image`、`generate.copy/image/video`、`price.quote`、`publish.post`。运行时用各 `*Request` DTO 生成 JSON-Schema 挂到 `agent_team.py` 的 `marketing-agent`，即可让 LLM 端到端跑"采集→翻译→定价→出图文→排期发布"。

## 7. 模块布局（建议）

```
backend/app/modules/growth/
  contracts.py     ← 本标准（已建，纯契约，无副作用）✅
  models.py        ← SourcedListing / PriceRule / ProviderJob(如需独立表) / SyndicationPost
  schemas.py       ← API 出入参（可直接复用 contracts 的 DTO）
  service.py       ← 编排：采集→翻译→定价→生成→发布；解析启用的 provider
  registry_boot.py ← 各 adapter 的 register() 汇总
  api.py           ← /admin/growth/* 后台接口
  adapters/
    source_xianyu.py  source_1688.py  ...
    translate_llm.py   translate_image_*.py
    gen_openai.py      gen_video_*.py
    publish_ayrshare.py  (复用现有聚合器)
    reprice_default.py   (compute_sell_price 包一层)
复用：models/marketing.py · models/content.py(PublishJob) · models/costing.py · models/settings.py · tasks/publishing_tasks.py · services/agent_team.py
```

## 8. 分期落地

- **P0（地基，本次已起头）**：`contracts.py` 契约 + `compute_sell_price` ✅；`models.py`（`SourcedListing`/`PriceRule`）+ alembic 迁移；`IntegrationSetting` 增 `source`/`pricing`；后台加 `admin_growth` grant。
- **P1（能跑通一条链）✅**：`source_manual`（合规安全的归一化 adapter，不爬取）+ `translate_llm`（复用现有 LLM，未配置时安全 passthrough）+ `reprice_default` + `service.run_pipeline`（采集→翻译→定价→建 `MarketingAsset` 草稿）+ `/api/v1/growth/*` 后台接口（`admin.growth.read` 守卫）。已 E2E 验证：1688 样品 SKU → 定价 €19.00/毛利31.58% → 生成 instagram 草稿。真实采集源（官方 API/持牌第三方）后续作为另一个 `SourceAdapter` 直接替换 `source_manual`。
- **P2（生成+发布）**：接 `gen_image`/`gen_video`（走现有 `MarketingMediaRequest` 认领队列）→ 复用 `PublishJob` 定时发 IG/FB。
- **P3（自动化）**：`PriceRule` 定时重算 + LLM 端到端编排 + 套利看板/指标。

## 9. 合规红线（必须先明确）

闲鱼/淘宝/1688 **直接爬取违反其 ToS、反爬严、且可能涉数据合规**。标准里 `SourceAdapter` 刻意抽象成"给我一个标准化 `SourcedItem`"——**推荐走官方开放平台 API 或持牌第三方数据源**，而不是无授权爬虫。是否采用爬虫、用哪种数据源，是需要你（业务方）先拍板的决策，本标准不预设。

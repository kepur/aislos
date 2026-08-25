# Growth 模块 · 使用手册与扩展标准

> **一句话**:从货源采集商品 → LLM 翻译文案 → 按「成本+运费+汇率+目标毛利+平台费率」自动加价定价 → 生成营销草稿 → 定时批量发布到 IG/FB,再按汇率定时重算价格。全部走一套统一契约,接任何外部 API 只是「实现一个适配器」。
>
> 契约权威定义在代码:[`backend/app/modules/growth/contracts.py`](../backend/app/modules/growth/contracts.py)
> 设计标准与落地计划:[`GROWTH_SOURCING_SYNDICATION_STANDARD.md`](./GROWTH_SOURCING_SYNDICATION_STANDARD.md)

---

## 1. 访问地址与登录

本地开发环境(Docker),各服务端口:

| 服务 | 地址 | 说明 |
|---|---|---|
| **管理后台(Growth 在这里)** | http://localhost:4097 | frontend-admin 控制台 |
| **↳ Growth 页面** | **http://localhost:4097/growth** | 采集/定价/套利/发布队列 |
| 后端 API | http://localhost:8000 | FastAPI |
| **↳ 交互式 API 文档** | http://localhost:8000/docs | Swagger UI(可直接试所有接口) |
| 客户端 PC 站 | http://localhost:4099 | frontend-pc |
| 商城后台 / 前台 | http://localhost:4095 / :4096 | store-admin / store-frontend |
| 采购后台 / PC / H5 | http://localhost:4108 / :4106 / :4107 | procurement-* |
| 营销 / 合作伙伴 / 开发者 / Agent 门户 | :4094 / :4091 / :4092 / :4093 | *-portal |
| 网关(统一入口) | http://localhost:80 | nginx |
| Postgres / Redis / MinIO | :5432 / :6379 / :9000·:9001 | 基础设施 |

**登录管理后台**:打开 http://localhost:4097/login

- 账号:`admin@ainerwise.com`
- 密码:`Aahozin.123`
- 角色 `super_admin`,已授予 `admin_growth` 门户权限(否则会 403)。

> Growth 页面受 `admin.growth.read` 门户授权守卫。新管理员需要该 grant 才能进入(见 §7 权限)。

---

## 2. 快速开始(启动 / 迁移 / 定时任务)

```bash
# 在仓库根目录
cd /Users/mac/Code_Start/Aislos/Ainerwise

# 起全栈(或只起用到的)
docker compose up -d

# 只起 Growth 需要的最小集合
docker compose up -d postgres redis backend frontend-admin celery-worker celery-beat
```

- 后端启动时会自动执行 `alembic upgrade head`(Growth 的表在迁移 `085`)。
- 手动迁移:`docker exec ainerwise-backend-1 alembic upgrade head`
- 定时重算依赖 `celery-beat` + `celery-worker` 两个容器在跑(已随全栈启动)。

---

## 3. 后台功能使用(逐标签)

进入 http://localhost:4097/growth,共 4 个标签页。

### 3.1 Import & Pipeline —— 一键跑全链
填一个货源条目,点 **Run pipeline**,系统一次跑完:**采集归一化 → 翻译 → 自动定价 → 生成营销草稿**。

| 字段 | 说明 |
|---|---|
| Source | 来源标识(`1688` / `taobao` / `manual`…),仅作标记 |
| External ID * | 货源内唯一 ID,`(source, external_id)` 用于去重幂等 |
| Title / Description | 原文标题/描述(源语言) |
| Source price (minor) | 采购价,**最小货币单位**(`8000` = ¥80.00) |
| Source currency | 源币种(`CNY`) |
| Target language | 目标市场语言(en/sr/pl/zh) |
| FX rate | 源→售 汇率;留空则查 `ExchangeRate` 表 |
| Price rule * | 选一条定价规则(先在 Price Rules 建) |
| Publish channel | 草稿投放渠道(`instagram`) |

跑完自动跳到 **Arbitrage / Listings**,可看到定价结果。

> 翻译在**未配置 AI provider 时是 passthrough(原样保留)**,链路照常完成;配置了 AI key 后自动变真翻译(见 §6)。

### 3.2 Price Rules —— 定价规则(套利核心)
新建 / **编辑** / **删除** / **Reprice now**(立即重算)。字段即定价公式的入参:

- Freight %(运费占比) · Freight fixed(固定运费,minor)
- Duties %(关税/税费) · Target margin %(目标毛利) · Platform fee %(平台费率)
- Round to(取整到多少 minor,`100`=取整到整元) · Reprice cadence(manual/daily/weekly) · Reprice threshold %(变动超过才改价,防抖)

定价公式(见 §5)。删除规则时会自动解绑引用它的 listing,不留孤儿外键。

### 3.3 Arbitrage / Listings —— 套利看板
表格逐行展示 **成本 → 售价 → 毛利**,毛利 ≥20% 显示绿色。每行操作:

- **Translate** — 重新翻译(passthrough 规则同上)
- **Draft→Publish** — 建草稿并排期到 Instagram + Facebook
- **Archive** — 归档(status=archived) · **Delete** — 永久删除

### 3.4 Publish Queue —— 发布队列
展示 Growth 来源资产的 `PublishJob`:平台 / 排期时间 / 状态 / 外部帖 ID。

- 未配置社媒聚合器时,任务转 **manual_required**(管理员手动发,不会静默丢失)。
- 调度器每 5 分钟扫一次到期任务(`dispatch_publish_jobs`)。
- 配置社媒聚合器:后台 → Integrations → `social`(填 `base_url` + `api_key`)。

---

## 4. API 参考

前缀 `http://localhost:8000/api/v1`,全部需 `Authorization: Bearer <token>`,守卫 `admin.growth.read`(或 admin/super_admin 角色)。完整可试:http://localhost:8000/docs

**登录取 token**
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@ainerwise.com","password":"Aahozin.123"}'
# → { "access_token": "...", ... }
```

| 方法 & 路径 | 作用 |
|---|---|
| `GET /growth/providers` | 已安装 provider 列表(能力/配置分类) |
| `POST /growth/price/preview` | **无副作用**试算售价(传 `PriceInputs`) |
| `POST /growth/price-rules` | 建定价规则 |
| `GET /growth/price-rules` | 规则列表 |
| `PUT /growth/price-rules/{id}` | 改规则 |
| `DELETE /growth/price-rules/{id}` | 删规则(解绑 listing) |
| `POST /growth/price-rules/{id}/reprice` | 手动/定时重算该规则下所有 listing |
| `POST /growth/listings` | 导入一条货源(归一化 upsert) |
| `GET /growth/listings?status_filter=` | listing 列表 |
| `GET /growth/listings/{id}` | listing 详情 |
| `POST /growth/listings/{id}/translate` | 翻译 |
| `POST /growth/listings/{id}/price` | 定价(指定规则 + 可选 fx) |
| `POST /growth/listings/{id}/draft` | 建营销草稿(marketing_assets) |
| `POST /growth/listings/{id}/archive` | 归档 |
| `DELETE /growth/listings/{id}` | 删除 |
| `POST /growth/publish` | 排期发布(asset_id + platforms[]) |
| `GET /growth/publish-jobs` | 发布队列 |
| `POST /growth/pipeline` | **一键全链**(导入→翻译→定价→草稿) |

**一键全链示例**
```bash
TOKEN=...   # 上面拿到的
curl -s -X POST http://localhost:8000/api/v1/growth/pipeline \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{
    "source":"1688","external_id":"SKU-001",
    "title":"智能门锁","description":"指纹密码锁",
    "price_minor":8000,"price_currency":"CNY",
    "target_lang":"en","fx_rate":0.13,
    "price_rule_id":"<规则ID>","channel":"instagram"
  }'
```

---

## 5. 定价公式(套利核心)

`compute_sell_price(PriceInputs) -> PriceQuote`,公式即契约:

```
landed  = 采购价 * 汇率 * (1 + 运费%) + 固定运费
landed += landed * 关税/税费%
pre_fee = landed / (1 - 目标毛利%)      # 保住毛利
sell    = pre_fee / (1 - 平台费率%)      # 为平台抽成做 gross-up
sell    = 四舍五入(round_to_minor) 后 clamp(min, max)
```

金额一律 **整数 minor units + 币种**。已验证样例:采购 CNY 80、汇率 0.13、运费 15%、目标毛利 30%、平台费 8%、取整到 €1 → 落地 **€11.96**、售价 **€19.00**、实得毛利 **31.58%**。

---

## 6. 配置项(IntegrationSetting)

后台凭证/开关统一存 `IntegrationSetting`,密钥自动脱敏(`SECRET_KEYS`)。Growth 相关分类:

| 分类 | 用途 | 关键字段 |
|---|---|---|
| `ai` | LLM 翻译/文案 | `api_key`(填了翻译才真正生效,否则 passthrough) |
| `social` | 社媒发布聚合器 | `base_url` + `api_key` |
| `source` | 采集源凭证(接真实数据源时用) | `api_key` / `cookie` / `access_token` |
| `pricing` | 定价默认值(可选,规则本身已是定价配置) | — |

---

## 7. 权限

- Growth 门户 key:`admin_growth`,所需 grant:`admin.growth.read`。
- 已并入 `ROLE_ACCESS_PROFILES` 的 `admin` / `super_admin`(见 [`portal_access.py`](../backend/app/services/portal_access.py))。
- 给某用户补授权(参照修复超管的做法):

```bash
docker exec ainerwise-backend-1 python -c "
import asyncio
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.user import User
from app.services.portal_access import sync_role_portal_access
async def m():
    async with async_session_factory() as db:
        u=(await db.execute(select(User).where(User.email=='admin@ainerwise.com'))).scalar_one()
        await sync_role_portal_access(db, user_id=u.id, role=u.role); await db.commit()
asyncio.run(m())
"
```

---

## 8. 定时任务(celery beat)

| 任务 | 频率 | 作用 |
|---|---|---|
| `reprice_due_growth_rules` | 每日 05:15 UTC | 重算所有 active 非 manual 规则,fx 自动查 `ExchangeRate`,超阈值才改价 |
| `dispatch_publish_jobs` | 每 5 分钟 | 发送到期的 `PublishJob` |

手动触发重算(测试用):
```bash
docker exec ainerwise-backend-1 python -c "from app.tasks.growth_tasks import reprice_due_growth_rules; print(reprice_due_growth_rules())"
```

---

## 9. 后续扩展标准 —— 如何接一个真实 API

**核心思想**:每种能力 = 一个 `Protocol`,一个 provider 只需实现它声称的能力,注册进 registry。**调用方永不写死厂商名**,换厂商 = 加一个 adapter 文件。

能力清单(`Capability` 枚举):`source` · `translate_text` · `translate_image` · `gen_copy` · `gen_image` · `gen_video` · `price` · `publish`

Protocol 签名:
```
SourceAdapter    .search(SourceQuery)->[SourcedItem]   .fetch(url_or_id)->SourcedItem
TextTranslator   .translate(TranslateRequest)->TranslateResult
ImageTranslator  .translate_image(ImageTranslateRequest)->MediaAsset
CopyGenerator    .generate_copy(CopyRequest)->CopyResult
ImageGenerator   .generate_image(ImageGenRequest)->[MediaAsset]
VideoGenerator   .generate_video(VideoGenRequest)->MediaAsset
Repricer         .price(PriceInputs)->PriceQuote
Publisher        .publish(PublishRequest)->PublishResult
```

**接一个真实采集源的步骤(以替换 `source_manual` 为例):**

1. 新建 `backend/app/modules/growth/adapters/source_<vendor>.py`,实现 `SourceAdapter`:
   ```python
   class VendorSourceAdapter:
       key = "vendor"
       async def search(self, query): ...   # 调厂商 API,返回 [SourcedItem]
       async def fetch(self, url_or_id): ...  # 返回单个 SourcedItem
   ```
   把厂商返回的任意结构**归一化成标准 `SourcedItem`**——下游(翻译/定价/发布)零改动。
2. 在 [`registry_boot.py`](../backend/app/modules/growth/registry_boot.py) 注册它的 `ProviderSpec`(声明能力 + `settings_category="source"`)。
3. 凭证填到后台 `IntegrationSetting` 的 `source` 分类。
4. 在 [`service.py`](../backend/app/modules/growth/service.py) 里让采集步骤解析启用的 provider(目前 P1 直接用 `source_manual`)。

其它能力同理:翻译换成专业 MT → 加一个 `TextTranslator`;接图像生成 → 加 `ImageGenerator`(走现有 `MarketingMediaRequest` 认领队列);发布换平台 → 加 `Publisher`。

**LLM 端到端编排**:`TOOL_SIGNATURES`(contracts.py)是 agent 可调用的「工具名 ↔ 能力」白名单。把它挂到 `services/agent_team.py` 的 `marketing-agent`,即可让 LLM 自己跑「采集→翻译→定价→出图文→排期发布」。

**分期进度**(详见标准 §8):P0 契约+模型 ✅ · P1 全链打通 ✅ · P2 发布+看板 ✅ · P3 定时重算 ✅ · 待做:真实采集源、AI key、图像/视频生成、LLM 编排(均为「接 adapter / 填 key」)。

---

## 10. 合规红线

闲鱼/淘宝/1688 **直接爬取违反其 ToS、反爬严、涉数据合规**。`SourceAdapter` 刻意抽象成「给我一个标准化 `SourcedItem`」——**推荐走官方开放平台 API 或持牌第三方数据源**,而非无授权爬虫。是否采用爬虫、用哪种数据源,是业务方需先拍板的决策,本标准不预设。

---

## 11. 数据模型 & 关键文件

| 文件 | 作用 |
|---|---|
| `backend/app/modules/growth/contracts.py` | 契约:DTO / Protocol / `compute_sell_price` / registry / `TOOL_SIGNATURES` |
| `backend/app/modules/growth/models.py` | 表:`SourcedListing`(货源+流水状态)、`PriceRule`(定价规则) |
| `backend/app/modules/growth/service.py` | 编排:normalize/translate/price/draft/publish/reprice/pipeline |
| `backend/app/modules/growth/adapters/` | `source_manual` · `translate_llm` · `reprice_default` |
| `backend/app/modules/growth/registry_boot.py` | provider 注册 |
| `backend/app/api/v1/endpoints/growth.py` | `/api/v1/growth/*` 接口 |
| `backend/app/tasks/growth_tasks.py` | `reprice_due_growth_rules` beat 任务 |
| `frontend-admin/pages/growth/index.vue` | 后台四标签页 |
| `backend/alembic/versions/085_growth_sourcing_pricing.py` | 建表迁移 |

复用的既有骨架:`models/marketing.py`(MarketingAsset/MediaRequest)· `models/content.py`(PublishJob)· `models/costing.py`(ExchangeRate)· `tasks/publishing_tasks.py`(发布调度)· `services/agent_team.py`(agent 编排)。

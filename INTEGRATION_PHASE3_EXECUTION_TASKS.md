# Integration Phase 3 — Portal 收敛

更新：2026-06-11

## 状态

| 栏目 | 名称 | 状态 |
|------|------|------|
| P3-01 | Portal Registry：Cebu PC + Buyer H5 manifest | `VERIFIED` |
| P3-02 | 共享 `useCommerce` composable（H5 / Admin） | `VERIFIED` |
| P3-03 | Supplier H5：订单 + 通知页 | `VERIFIED` |
| P3-04 | Admin：Commerce 对账页 | `VERIFIED` |
| P3-05 | Cebu PC 页面壳 + design tokens 统一 | `VERIFIED` |
| P3-06 | Legacy API 兼容层 + parity 测试 | `VERIFIED` |
| P3-07 | Cebu PC 首批 3 页切 Core API | `VERIFIED` |
| P3-08 | Cebu PC/H5/Admin 全界面与功能盘点 | `LOCKED` |
| P3-09 | Cebu Buyer/Public PC + H5 全量迁移 | `LOCKED` |
| P3-10 | Cebu Supplier PC + H5 全量迁移 | `LOCKED` |
| P3-11 | Cebu Admin 迁入统一后台 | `LOCKED` |
| P3-12 | Cebu API、任务与数据全量 parity | `LOCKED` |
| P3-13 | Cebu 全量验收与 Legacy 退役闸门 | `LOCKED` |
| IP2-10 | Stripe webhook 自动结算 | `VERIFIED` |

## P3-01 Manifest

新增 Logical Portal：

| portal_key | 前端 | 说明 |
|------------|------|------|
| `cebu` | frontend-pc | Cebu 采购 PC 品牌入口 |
| `cebu_buyer` | frontend-h5 | Cebu 买家 H5 |
| `supplier`（扩展） | frontend-h5 | 增加 `/commerce/**` 路由与通知菜单 |

`MANIFEST_VERSION` → **2**

验证：

```bash
cd Ainerwise/backend
pytest -q tests/test_portal_manifest.py
curl http://localhost:8000/api/v1/portal-manifests/cebu
```

## P3-02 共享 Commerce Client

| 路径 | 用途 |
|------|------|
| `frontend-h5/composables/useCommerce.ts` | 订单、通知、线程 |
| `frontend-admin/composables/useCommerce.ts` | 结算、对账、风险 |

原则：**共享 API 契约与 composable，不强制共享 UI 组件**。

## 与 Phase 2 衔接

- Commerce API 前缀：`/api/v1/commerce/*`
- IP2-09 Settlement：`confirm-funding` → `settlements/settle` → `reconciliation-runs`
- 站内通知：`/commerce/notifications`

## P3-05 Cebu PC 壳 + Design Tokens

| 项 | 说明 |
|----|------|
| Layout | `layout: procurement` + `procurement-layout--cebu` 橙色渐变 |
| Shell | `useCebuPortalShell` 加载 manifest + portal policy |
| 导航 | procurement header 内 Cebu 子导航（工作台 / 需求 / 工程采购） |
| 组件 | `pc-card` / `input-field` / `brand.accent` 与 Phase 1 采购 workspace 一致 |

验证：浏览器访问 `http://cebu.localhost/cebu`；`pytest -q tests/test_cebu_portal_e2e.py`

## P3-06 Legacy API 兼容层

前缀：`/api/v1/cebu-compat/*`（Intent 别名 → Core commerce）

| Legacy | 兼容路由 |
|--------|----------|
| `POST /intents` | `POST /cebu-compat/intents` |
| `POST /intents/{id}/publish` | `POST /cebu-compat/intents/{id}/publish` |
| `GET /intents/{id}/supplier-candidates` | 同名兼容 |
| `POST .../bind` | `catalog_item_id` → `listing_id` |

完整切换清单：[`CEBU_LEGACY_API_PARITY.md`](../CEBU_LEGACY_API_PARITY.md)

验证：`pytest -q tests/test_cebu_legacy_parity.py`

## P3-07 Cebu 前端切 Core API

本栏目仅代表 Cebu PC **首批 3 个页面**接入 Core API，不代表原 Cebu PC 已全量迁移。

原 Cebu PC 仍在 `CebuProjects/pc-frontend`，当前有 59 个 Vue 页面；它是后续逐页迁移的功能与视觉验收基线。Ainerwise 当前迁移页面位于 `Ainerwise/frontend-pc/pages/cebu/**`。

| 项 | 说明 |
|----|------|
| API Base | `useApiBase()`：`cebu.localhost` → `{host}/api/v1`（nginx 注入 `X-Portal-Key: cebu`） |
| Commerce 路径 | `useCommerce` 使用 `/commerce/*`（`apiBase` 已含 `/api/v1`，避免双重前缀） |
| 兼容层 | `useCebuCompat` → `/cebu-compat/*`（迁移窗口可选） |
| 页面 | `/cebu`、`/cebu/intents`、`/cebu/intents/:id` |

本地访问：

```bash
# docker compose up 后
open http://cebu.localhost/cebu
# API 经 nginx :80，勿直连 backend:8000（无 Portal Context）
```

`.env`：`NUXT_PUBLIC_API_BASE=http://localhost/api/v1`（或保留 `localhost:8000`，`useApiBase` 在浏览器侧改走 nginx）

验证：

```bash
cd Ainerwise/backend
pytest -q tests/test_cebu_portal_e2e.py tests/test_cebu_legacy_parity.py
```

## P3-08 Cebu PC/H5/Admin 全界面与功能盘点

状态：`LOCKED`

解锁条件：根任务板 `FULL_PORTAL_ZERO_LOSS_EXECUTION_TASKS.md` 的 ZL01 完成。ZL01 是
全项目盘点，必须同时产出本栏目的 Cebu parity 内容；不得由另一个 Agent 重复盘点。

目标：先建立可执行的全功能迁移清单，明确每个原页面和后台能力的目标 Portal、Core API、数据迁移、权限和验收方式。

必须产出：

- 盘点 `CebuProjects/pc-frontend/pages/**` 全部 59 个页面、布局、composable、API 和关键用户流程。
- 盘点 `CebuProjects/h5-frontend/pages/**` 全部 41 个页面及移动端特有流程。
- 盘点 `CebuProjects/admin-frontend/src/**` 全部 24 个 Vue 界面文件。
- 盘点 Legacy backend、admin-backend、后台任务、通知、webhook、支付和集成。
- 建立功能 parity 矩阵，至少按 Buyer、Supplier、Admin、Public/Marketplace/Auth、API/Data/Jobs 分组。
- 每个页面标记目标归属：
  - Buyer / Supplier / Public PC → `Ainerwise/frontend-pc` 中的 Cebu Logical Portal。
  - Buyer / Supplier / Public H5 → `Ainerwise/frontend-h5` 中对应的 Cebu Logical Portal。
  - Admin PC → `Ainerwise/frontend-admin` 中的权限化工作台。
- 每个页面标记 `NOT_STARTED / IMPLEMENTED / VERIFIED / RETIRED`。
- 为 P3-09 至 P3-12 给出可并行、互不覆盖文件范围的 Agent 任务包。
- 记录 Legacy API 到 Core API 的差异；缺失能力必须新增任务，不能静默删功能。

验收：

- 矩阵覆盖原 Cebu PC、H5、Admin 全部界面和后台能力，最低 124 个界面文件全部入账。
- 每个页面都有目标路径、目标 API、权限、数据迁移和验证方法。
- 不允许用 `/cebu` 当前 3 页代替原 59 页的验收。

## P3-09 至 P3-13 执行顺序

| 栏目 | 解锁条件 | 核心验收 |
|------|----------|----------|
| P3-09 Buyer/Public PC + H5 | P3-08 VERIFIED | Buyer、公开页面、Marketplace、Auth 与完整采购流程 parity |
| P3-10 Supplier PC + H5 | P3-08 VERIFIED | Supplier 页面、报价和履约流程 parity |
| P3-11 Admin | P3-08 VERIFIED | Admin 能力迁入 `frontend-admin` 且权限隔离 |
| P3-12 API/Jobs/Data | P3-08 VERIFIED | Legacy API、后台任务、集成与数据全部有 Core 归属 |
| P3-13 全量验收与退役闸门 | P3-09 至 P3-12 VERIFIED | PC/H5/Admin、数据迁移、浏览器 E2E、业务签收全部通过 |

P3-13 VERIFIED 前：

- 禁止删除、覆盖或归档 `CebuProjects/pc-frontend`、`h5-frontend` 或 `admin-frontend`。
- 禁止声明 Cebu PC 已全量迁移或已退役。
- 原 Cebu PC 允许本地运行于 `http://localhost:3399`，用于逐页对照验证。
- 新功能只写入 Ainerwise Core；Legacy 代码仅用于迁移、对照和必要修复。

## IP2-10 Stripe 自动结算

| 步骤 | API / 事件 |
|------|------------|
| 创建 payment intent | `POST /commerce/orders/{id}/payment-intent` |
| Stripe Checkout | `POST /commerce/orders/{id}/checkout` |
| Webhook 入账 | `POST /webhooks/stripe` → `checkout.session.completed` + `kind=commerce_order` |
| 账本 | `confirm_order_funding(source_account=escrow:psp)` |

验证：`pytest -q tests/test_commerce_stripe_webhook.py`

## 禁止

- 不要把 Cebu 全部页面塞进 AISLOS 官网
- 不要把 Cebu PC 的品牌体验替换成通用 Procurement 壳
- 不要在 P3-13 VERIFIED 前删除或退役原 Cebu PC/H5/Admin
- 不要共用 AI `conversations` 表存业务消息
- Portal manifest 仅描述 UX，不授予权限（权限仍走 Grant + role）
- 不要长期依赖 `/cebu-compat`（需设退役日期）

# Cebu PC 59 页 → AISLOS 目标页/API/权限/状态 差距表

生成：2026-06-24 · 维护者手工核对（非 generator 自动产物）

> 本表是「按页复刻」的执行清单。源基准 = `CebuProjects/pc-frontend/pages`（恰好 59 页，与 `feature-parity-ledger.json` 的 `CebuProjects/PC/page=59` 守卫一致）。
> 目标 = `Ainerwise/frontend-pc`（buyer/public/supplier）+ `Ainerwise/frontend-admin`（admin）。

## 核心结论（先看这段）

实测后，当前迁移状态与「整站没迁」或「已 1:1 复刻」都不一样，真实情况是：

- **路由 / 门户 / 权限 / Core API 接线 ≈ 已完成**：buyer 走 `cebu_buyer_pc`、public 走 `cebu_public_pc`、supplier 走 `supplier_pc`、admin 走 `cebu_admin`；页面普遍 `definePageMeta({ layout, middleware:['auth'], alias:['/buyer/...'] })` + `useCommerce()` / `apiFetch('/cebu-trade/*')` 已接到 Core。
- **UI / 功能"深度" ≈ 未完成**：原版页面 100–1788 行的富交互，当前多被压成「单行模板 + 一次 `useCommerce` 拉取」的功能骨架，个别页直接 `<pre>{{ obj }}</pre>` 打印原始 JSON。**这就是肉眼看到「完全不一样」的根因，不是入口跳错。**
- 真正的"从零"缺口很少，集中在 **supplier/inbox** 和 **cebu-admin 的几页空壳**。

> ⚠️ 行数只是富度参考。当前很多页写成单物理行，`wc -l`=2 但其实已接线渲染数据，**不要据行数判定为空壳**。

### 状态码

| 码 | 含义 | 该做什么 |
|---|---|---|
| **S0 BY-DESIGN** | 按设计不复刻，复用 AISLOS 共享能力 | 不动，确认共享页/Core 后台已覆盖即可 |
| **S1 CONTENT-OK** | 静态营销/说明页，已可用 | 仅做品牌/文案润色 |
| **S2 SKELETON-WIRED** | 路由+权限+API 已接，渲染基础数据，但远低于原版富度 | **主战场**：逐页补 UI/子功能到 parity |
| **S3 STUB / MISSING** | 近空壳或目标缺失 | 从骨架/零开始建 |

### 汇总

| 分组 | 页数 | S0 | S1 | S2 | S3 |
|---|---:|---:|---:|---:|---:|
| Public | 13 | 5 | 3 | 5 | 0 |
| Buyer | 17 | 0 | 0 | 17 | 0 |
| Supplier | 16 | 0 | 0 | 16 | 0 |
| Admin | 13 | 2 | 0 | 6 | 5 |
| **合计 (PC)** | **59** | **7** | **3** | **44** | **5** |

> 📱 **范围**：PC **和 H5 都要做**。H5 原版 41 页，当前 `frontend-h5` 路由覆盖见 [§E](#e-h541--frontend-h5)。
>
> **已确认决策（2026-06-24）**：
> 1. `supplier/inbox` 由新增 `/supplier/pings`（匹配需求收件箱）取代 → 不再当缺口。
> 2. cebu-admin 的 `users` / `categories` 复用 Core 后台（`/users` `/categories`），不在 cebu-admin 重做。

---

## A. Public（13）→ `cebu_public_pc` / `frontend-pc` / layout `default`

| 源页（行） | 目标路由 | 目标实现（行） | API | 状态 | 差距要点 |
|---|---|---|---|---|---|
| `index.vue` (251) | `/cebu` | `cebu/index.vue` (21) | — | S2 | 仅落地骨架，缺 hero/分区/AI 顾问入口 |
| `categories.vue` (129) | `/cebu/categories` | → `CebuPublicMarketplace` (87) | `useCommerce` listings | S2 | 类目筛选/分面缺失 |
| `marketplace/index.vue` (351) | `/cebu/marketplace` | → `CebuPublicMarketplace` (87) | `useCommerce` listings | S2 | 搜索/排序/分页/卡片富度不足 |
| `marketplace/[id].vue` (549) | `/cebu/marketplace/[id]` | `cebu/marketplace/[id].vue` (8) | `useCommerce` | S2 | 详情页用 `<pre>` 打印 JSON，需做真正详情/规格/CTA |
| `post-request.vue` (429) | `/cebu/post-request` | → `CebuRequestForm` (90) | `useCommerce` create | S2 | 多步表单/上传/AI 解析缺失 |
| `how-it-works.vue` (61) | `/cebu/how-it-works` | 静态 (内联) | — | S1 | 文案/品牌润色 |
| `pricing.vue` (55) | `/cebu/pricing` | 静态 (内联) | — | S1 | 同上 |
| `trust-safety.vue` (40) | `/cebu/trust-safety` | 静态 (内联) | — | S1 | 同上 |
| `login.vue` (215) | `/login` | `pages/login.vue` (108) | `useAuth` | S0 | 用 AISLOS 共享登录，勿复制 |
| `register-buyer.vue` (205) | `/register-buyer` | `pages/register-buyer.vue` (69) | `useAuth` | S0 | 共享注册 |
| `register-role.vue` (88) | `/register-role` | `pages/register-role.vue` (30) | — | S0 | 共享 |
| `register-supplier.vue` (233) | `/register-supplier` | `pages/register-supplier.vue` (2) | `useAuth` | S0 | 共享（当前壳薄，但属共享 auth 体系，按 S0 处理） |
| `supplier-onboarding.vue` (37) | `/supplier-onboarding` | `pages/supplier-onboarding.vue` (2) | — | S0 | 共享 onboarding |

> 额外（原版无、当前新增）：`/cebu/intents/index`(114)、`/cebu/intents/[id]`(88) —— 公开/供应商浏览 intent，属正向增益。

## B. Buyer（17）→ `cebu_buyer_pc` / `frontend-pc` / layout `procurement` / `middleware:['auth']` / `useCommerce`

> 🔁 **2026-06-24 现状重审（本表早期"目标实现行数"已过时）**。Buyer 组件真实状态：
> - ✅ **已丰满**：`CebuBuyerRequestDetail`(471)、`CebuBuyerOffers`(291, 报价对比+授标)、`CebuBuyerOrderDetail`(379)、`CebuBuyerDashboard`(232)、`CebuBuyerOrders`(订单列表)、`CebuBuyerRequestList`(需求列表)、`CebuBuyerPaymentLedger`(账本)、`CebuBuyerDisputes`、`CebuBuyerMessages`(两栏聊天)、`CebuRequestForm`(4步向导)、`CebuPublicMarketplace`(选品门面) —— 均 P1 重建。
> - 🟡 **仍待 parity**：pages `settings`(4→404)、`team`(2→135)、`company-profile`(60→150)、`projects/[id]`(60→1788 ★)、`projects/index`(23→257)、`notifications`。
> - 验证方式：demo 买家 token SSR 渲染各页 HTTP 200、无 `__NUXT_ERROR__`。
> - 主题/语言基座：P0-5 主题 token（亮/暗，默认暗）+ EU locale 集(en/zh/sr/pl) 已就绪；新页用深色靛蓝 + Core 接线。

| 源页（行） | 目标路由 (`/cebu/buyer/...`) | 目标实现（行） | 状态 | 差距要点 |
|---|---|---|---|---|
| `dashboard.vue` (392) | `/dashboard` | → `CebuBuyerDashboard` (65) | S2 | 概览卡片/图表/待办流缺失 |
| `company-profile.vue` (150) | `/company-profile` | `company-profile.vue` (60) | S2 | 资质/区域/认证字段不全 |
| `projects/[id].vue` (**1788**) | `/projects/[id]` | `projects/[id].vue` (60) | S2 | ★最大缺口：BOQ/估价/版本/报告/选型全套未复刻 |
| `projects/index.vue` (257) | `/projects` | `projects/index.vue` (23) | S2 | 列表筛选/指标缺失 |
| `requests/[id]/index.vue` (412) | `/requests/[id]` | → `CebuBuyerRequestDetail` (32) | S2 | 需求详情/时间线/操作集缺失 |
| `requests/[id]/offers.vue` (381) | `/requests/[id]/offers` | → `CebuBuyerOffers` (22) | S2 | 报价对比/评分/授标流缺失 |
| `requests/index.vue` (98) | `/requests` | → `CebuBuyerRequestList` (27) | S2 | 状态筛选/分页 |
| `offers/[id].vue` (125) | `/offers/[id]` | `offers/[id].vue` (4) | S2 | `<pre>` 打印 JSON，需做报价详情 |
| `orders/[id].vue` (387) | `/orders/[id]` | → `CebuBuyerOrderDetail` (33) | S2 | 交付/签收/争议/评价流缺失 |
| `orders/index.vue` (142) | `/orders` | → `CebuBuyerOrders` (23) | S2 | 列表富度不足 |
| `messages.vue` (208) | `/messages` | → `CebuBuyerMessages` (19) | S2 | 会话列表/线程/附件缺失 |
| `disputes/index.vue` (63) | `/disputes` | → `CebuBuyerDisputes` (7) | S2 | 极薄，几乎仅占位骨架 |
| `disputes/new.vue` (94) | `/disputes/new` | `disputes/new.vue` (已接线表单) | S2 | 基础表单已通，缺校验/证据上传 |
| `ideal-list.vue` (43) | `/ideal-list` | `ideal-list.vue` (已接 `listWatchlist`) | S2 | ≈接近，缺目标价提醒 |
| `settings.vue` (404) | `/settings` | `settings.vue` (已接线表单) | S2 | 仅账户基础字段，缺通知/安全/团队设置 |
| `team.vue` (135) | `/team` | `team.vue` (已接 `listBuyerTeam`) | S2 | 只读表，缺邀请/角色管理 |
| `wallet.vue` (228) | `/wallet` | → `CebuBuyerPaymentLedger` (7) | S2 | 极薄；账本/里程碑/充值视图缺失 |

> 额外新增：`/cebu/buyer/notifications`(4)、`/cebu/buyer/requests/new`(2)。

## C. Supplier（16）→ `supplier_pc` / `frontend-pc` `/supplier/*` / `useCommerce` + `/cebu-trade/*`

| 源页（行） | 目标路由 (`/supplier/...`) | 目标实现（行） | 状态 | 差距要点 |
|---|---|---|---|---|
| `dashboard.vue` (162) | `/supplier` | → `SupplierDashboard` (已接 `getSupplierDashboard`) | S2 | 4 卡片骨架，缺趋势/待办 |
| `catalog/index.vue` (**461**) | `/supplier/catalog` | `catalog/index.vue` (42) | S2 | ★大缺口：目录 CRUD/规格/上下架/批量 |
| `settings.vue` (404) | `/supplier/settings` | `settings.vue` (76) | S2 | 公司/结算/资质设置不全 |
| `offers/new.vue` (258) | `/supplier/offers/new` | `offers/new.vue` (已接线) | S2 | 报价构成/明细/附件缺失 |
| `messages.vue` (209) | `/supplier/messages` | `messages.vue` (已接线) | S2 | 线程/附件缺失 |
| `orders/[id].vue` (208) | `/supplier/orders/[id]` | `orders/[id].vue` (已接 `apiFetch`) | S2 | 履约/发货/凭证流缺失 |
| `notifications.vue` (161) | `/supplier/notifications` | `notifications.vue` (19) | S2 | 分类/已读/跳转缺失 |
| `ads/create.vue` (131) | `/supplier/ads/create` | `ads/create.vue` (已接线) | S2 | 投放参数/预算/预览缺失 |
| `reviews.vue` (125) | `/supplier/reviews` | `reviews.vue` (已接线) | S2 | 回复/评分分布缺失 |
| `ads/index.vue` (119) | `/supplier/ads` | `ads/index.vue` (已接 `apiFetch`) | S2 | 列表/数据/状态切换缺失 |
| `triggers.vue` (108) | `/supplier/triggers` | `triggers.vue` (87) | S2 | ≈接近 parity |
| `team.vue` (69) | `/supplier/team` | `team.vue` (105) | S2 | ≈达到/超过 parity（当前更全） |
| `payouts.vue` (65) | `/supplier/payouts` | `payouts.vue` (接 `/cebu-trade/payouts`) | S2 | 结算明细/导出缺失 |
| `offers/index.vue` (62) | `/supplier/offers` | `offers/index.vue` (已接线) | S2 | 筛选/批量缺失 |
| `orders/index.vue` (59) | `/supplier/orders` | `orders/index.vue` (已接线) | S2 | 列表富度不足 |
| `inbox.vue` (137) | `/supplier/pings` | `pings/index.vue`（已接线） | S2 | ✅RESOLVED：由新增 `/supplier/pings` 取代，PC+H5 均已有 |

## D. Admin（13）→ `cebu_admin` / `frontend-admin` `/cebu-admin/*`

| 源页（行） | 目标路由 (`/cebu-admin/...`) | 目标实现（行） | 状态 | 差距要点 |
|---|---|---|---|---|
| `dashboard.vue` (165) | `/index` | `index.vue` (38) | S2 | 运营总览/指标缺失 |
| `disputes.vue` (112) | `/disputes` | `disputes.vue` (24) | S2 | 仲裁流程/证据视图缺失 |
| `orders.vue` (67) | `/orders` | `orders.vue` (31) | S2 | 列表/筛选/操作缺失 |
| `settings.vue` (48) | `/settings` | `settings.vue` (179) | S2 | 当前更全，需核对字段覆盖 |
| `risk.vue` (51) | `/risk` | `risk.vue` (29) | S2 | 风控规则/命中列表缺失 |
| `verifications.vue` (84) | `/verification` | `verification.vue` (20) | S2 | 审核队列/动作缺失 |
| `categories.vue` (46) | （Core `/categories`） | Core 类目后台 | S0 | 复用 Core，不在 cebu-admin 重做 |
| `audit.vue` (87) | `/audit` | `audit.vue` (2) | S3 | 疑似空壳，待核实/重建 |
| `intents.vue` (57) | `/intents` | `intents.vue` (2) | S3 | 疑似空壳 |
| `offers.vue` (60) | `/offers` | `offers.vue` (2) | S3 | 疑似空壳 |
| `users.vue` (174) | （Core `/users`） | Core 用户后台 | S0 | ✅决策：复用 Core `/users`，不在 cebu-admin 重做 |
| `pricing-intel.vue` (56) | — | **缺失** | S3 | 价格情报无目标页 |
| `ranking.vue` (228) | — | **缺失** | S3 | 排名/评分无目标页（评估并入 Core `supplier-scorecards`） |

> 正向增益：`frontend-admin/cebu-admin` 另有 ~16 页超出原 13 admin 页（`migrations`(190)/`payments`(83)/`regions`(82)/`kyc-media`(61)/`project-metric-templates`(66)/`staff`(54)/`shipping`(40)/`backups`(38)/`companies`(35)/`deposits`/`escrow`/`payouts`/`trade`/`trust`/`ad-campaigns`/`notifications`）—— 来自 `cebu_trade`/`cebu_admin` 模块的扩展后台覆盖。

---

## 建议复刻顺序（按业务主线 + 缺口大小）

1. **Buyer 主线深度**（S2，价值最高）：`requests/[id]` → `requests/[id]/offers`（授标）→ `orders/[id]`（交付）→ `projects/[id]`（★1788 行，BOQ/估价/报告，建议拆子任务）。
2. **Public 转化漏斗**：`marketplace/[id]` 详情 + `post-request` 表单 + `/cebu` 落地页。
3. **Supplier 履约闭环**：`catalog/index`（★461）→ `offers/new` → `orders/[id]`。
4. **Admin S3 空壳/缺失**：先核实 `audit/intents/offers` 是否真空壳，再补 `pricing-intel`、`ranking`（或并入 Core `supplier-scorecards`）。`users`/`categories` 已定复用 Core。
5. **H5 同步**：每条 buyer/supplier 主线在 PC 落地后，同步补对应 H5 页深度（见 §E）。

## 每页"完成"判据（移入 VERIFIED 前）

参照既有 `PARALLEL_AGENT_WORK_PACKAGES.md`：每页须留存 **旧路由 → 新路由 → 新 API → 权限规则（membership / portal grant / workspace / region / 对象级）→ 测试 → 截图**，且不得自评 VERIFIED。PC 与 H5 各自留证。

---

## E. H5（41）→ `frontend-h5`

H5 路由覆盖已较全（buyer 走 `/buyer/*`，supplier 走 `/supplier/*`，公共 `/marketplace/*`，认证复用共享）。`/supplier/pings/index` 已存在 → 印证 pings 取代 inbox。深度审计与 PC 同理（骨架已接线、富度待补），逐页深度待按主线补齐。

| 原版 H5 分组 | 源页数 | 当前 `frontend-h5` 目标 | 覆盖 | 备注 |
|---|---:|---|---|---|
| `auth/*`（login/register/reset） | 3 | 共享 auth | S0 | 复用 AISLOS 共享登录注册 |
| `buyer/*`（home/requests/offers/orders/projects/messages/wallet/profile/compare/post-request） | 16 | `/buyer/*`（index/requests/offers/orders/projects/messages/wallet/profile/compare/post-request/notifications/disputes/new） | S2 | 路由齐，深度待补；原 `home`→`index`，新增 disputes/notifications |
| `supplier/*`（home/catalog/offers/orders/pings/ads/messages/wallet/profile/make-offer） | 14 | `/supplier/*`（index/catalog/offers/orders/pings/ads/messages/wallet/profile/make-offer/notifications/team/triggers） | S2 | 路由齐，深度待补 |
| 公共/通用（index/marketplace/notifications/verification/wallet/settings/messages） | 8 | `/marketplace/*` `/messages/[order_id]` 等 | S2 | 部分通用页待核实落点 |

> 正向增益：`frontend-h5` 另有 `/marketing-mobile/*`（营销移动端）等超出原版 41 页的能力。
> H5 逐页深度审计（骨架 vs parity）建议在对应 PC 主线复刻完成后立即跟做，复用同一套组件/composable。

---

## F. 主题 / 品牌 / 域名整合方案（已确认 2026-06-24）

### 现状
- `useProcurementBrand` 已有 `aislos`(emerald→cyan) 与 `cebu`(orange→amber) 双品牌，按 hostname (`includes('cebu')`)/portal_key 切换；
- **两套均为纯深色**：`main.css` `body @apply text-slate-200 bg-transparent`、`bg-slate-950`；`tailwind.config.ts` 无 `darkMode`、无 CSS 变量色板，颜色硬编码 `primary`(蓝)/`accent`(绿) + 工具类。

### 已确认决策
1. **主题**（2026-06-24 修订 — 否决了早期"暖橙/冷青绿双模 token"提案）：**保留各 surface 原有色调，不换配色，只统一风格/布局**。
   - 官网：保留天蓝 3D 粒子背景（`Global3DBackground`，sky-500 `#0ea5e9`，全局 `app.vue` client-only 渲染）。
   - 采购/Market：统一到「官网调」= `slate-950` + 蓝紫 `blue→indigo` 强调色 + 同款天蓝 3D 背景。
   - 做法：① 采购 layout 背景改透明，露出全局 3D；② 去掉 `procurement.vue` 的橙(cebu)/teal(aislos) 背景分叉；③ 品牌强调色 `orange-`→`indigo-`（`useProcurementBrand` 统一为 `from-blue-500 to-indigo-500`）。
   - **语义色保留**：`amber`(警告/评分)、`StatusBadge` 优先级橙等不动。
   - **H5**：保留移动端浅色底（`#f5f7fa`，不加 3D），只做强调色 `orange-`→`indigo-`。
   - **Admin**：深色工作台 + `primary` 蓝本就是官网调，cebu-admin 仅含语义 amber，**无需改色**。
2. **改名**：`/cebu/* → /market/*`，旧 `/cebu/*` 一段时间 301 兼容；`useProcurementBrand` 的 `hostname.includes('cebu')` 改认 `market`/portal_key。
3. **域名三子域**：`ainerwise.com`(官网, frontend-pc default) / `market.ainerwise.com`(市场=公开+买家+供应商, frontend-pc procurement + frontend-h5) / `admin.ainerwise.com`(后台, frontend-admin)。买家/供应商走 `/market/buyer`、`/market/supplier` 路径，不另拆子域。
4. **官网→买家**：`default` layout 的 `AppHeader` 增「进入市场 / 买家工作台」入口（→ market 子域 `/buyer`，未登录走共享登录）。

### 执行顺序（Phase 0 基座先行，避免页面 parity 后返工重做主题）
- **P0-1 frontend-pc** ✅DONE：`procurement.vue` 背景改透明（露全局 3D）+ 去橙/teal 分叉 + 导航 active 橙→靛；`useProcurementBrand` 双品牌统一 `from-blue-500 to-indigo-500`；20 个 cebu/supplier 页面/组件 `orange-`→`indigo-`（39 处）。HMR 干净重编、SSR 实测 indigo×N/orange×0。
- **P0-2 frontend-h5 / frontend-admin** ✅DONE：h5 16 文件 `orange-`→`indigo-`（37 处，保留浅色底/amber/StatusBadge），HMR 干净；admin 确认已是官网调（蓝 primary + 深色台 + 仅语义 amber），无需改色。
- **P0-3 改名+路由** ✅DONE：`pages/cebu`→`pages/market`（57 处路由串 `/cebu`→`/market`，正则绕开 API `/cebu-compat`、`/cebu-trade` 与 portal_key `'cebu'`）；新增 `middleware/cebu-redirect.global.ts` 把旧 `/cebu/*` 301→`/market/*`；品牌 label 改 **AinerWise Market**（en/zh）；hostname 判断（`portal.global.ts`/`useApiBase.ts`/`useProcurementBrand.ts`）新增认 `market.*`。**后端协同**：`portal_registry.py` 的 3 个门户 `route_allowlist`/`home_route` 加 `/market`（保留 `/cebu` 过渡项；`/cebu-admin` 不动）。验证：`/market*`=200、`/cebu`→301、`Host: market.localhost`→/market、`/market/buyer/*`→302 login。
- **P0-4 域名+导航** ✅本地完成 / ⏳生产 DNS 待办：`AppHeader` 已含「Procurement→/market」入口；本地三子域靠 `.localhost` + hostname 判断已生效（运行栈无 nginx 容器，前端直连端口）。**生产**需在注册商配 `ainerwise.com` / `market.ainerwise.com` / `admin.ainerwise.com` + 反代到 4099/4099/4097（部署侧，仓外）。
- **P1+ 页面 parity**：在基座之上按 §「建议复刻顺序」逐页深化（PC→H5 同步）。

> 📌 本表 §A/§B 的目标路由 `/cebu/*` 现已全部为 `/market/*`（P0-3 改名；`/cebu-admin` §D 不变；source 列为历史原版，保持 `/cebu`）。
> ⚠️ 仅剩生产 DNS/反代（对外、注册商侧）未做——动手前确认部署环境。

---

## Records-first 支付改造 + 后台区域/语言配置(2026-07-03)

### 支付:去托管(硬约束落地「平台不托管资金/无在线钱包/仅台账」)
- **审计结论**:继承的 Cebu 链路 = 手工存款(汇到平台账户)→ admin 核验 → 内部余额 → pay-from-wallet 划入 escrow → 验收放款给供应商内部钱包 = **真实资金托管**,违背 AISLOS 约束。
- **后端(cebu_compat.py)**:
  - 新增 `POST /orders/{id}/record-payment`(买家直付供应商后记录参考号;escrow 记录 `provider=DIRECT_RECORDED` + `provider_reference`,状态机不变 → 前端派生 PAID_IN_ESCROW 兼容)。
  - `POST /wallets/deposits` + `POST /orders/{id}/pay-from-wallet` 加守卫:`wallet_payments_enabled=false`(默认)→ 409 direct-payment 提示。开关存 IntegrationSetting `market` category。
  - accept 放款路径:`provider==DIRECT_RECORDED` 时**不**给供应商内部钱包记账(钱从未经过平台)。
  - `GET/PUT /admin/market-settings`(仅 `wallet_payments_enabled`)。
  - `/system-mode` 增发 `direct_payments_only` + `locales/regions/default_locale`(来自 localization 事实源)。
- **前端(modules/procurement/pc)**:
  - `buyer/wallet.vue` 重写为 **Payments Ledger**(订单支付记录表 + 只读历史;去掉存款创建 UI);导航标签 Wallet & Escrow → Payments Ledger/支付台账。
  - 订单页:Pay from Wallet → **Record Payment**(prompt 参考号 → record-payment);状态标签统一走 `composables/useOrderStatus.ts`(PAID_IN_ESCROW→Payment Recorded、PAYOUT_RELEASED→Settled;**枚举值不动**,仅显示层)。
  - 营销文案全站去 escrow 承诺(首页/pricing/post-request/offers/register-role/supplier-onboarding/disputes/marketplace 详情)。
  - **未动**(管理侧/历史数据视图):admin escrow/deposits/payouts 运营页、供应商 payouts 历史页。
- **测试**:fastapi 0.138 懒挂载 `_IncludedRouter` 破坏 `app.routes` 内省 → 新增 `tests/route_utils.py`(递归展开),25 个测试文件迁移;**全套 409 passed**。

### 区域+语言后台配置(与并行 locale 工作会师)
- 事实源 = `endpoints/localization.py`(GET/PUT `/localization/config`,PlatformSetting 存储)——并行工作已建;**我最初在 IntegrationSetting `market` 里重复建的 locales/regions 已收敛移除**,`market` 只留 wallet_payments_enabled。
- Market PC 启动即 `fetchMarketLocalizationConfig()` 过滤 `languageOptions`(已有);admin SPA `Settings.vue` 已有语言/区域勾选 UI,本轮**新增 Wallet Payments(Legacy Custody Mode)开关卡片**(默认 OFF,开启需 confirm)。
- E2E 验证:PUT 开关 → 存款守卫放行/封禁、system-mode 反映、复位 OK。

> ⚠️ **样式机制(2026-07-04 踩坑)**:`modules/procurement/pc` 不跑 Tailwind JIT——样式来自**预编译的** `assets/css/compiled.css`(`nuxt.config` 里 `tailwindcss.cssPath:false` + `ui.disableGlobalStyles`)。**模板里新增任何 Tailwind 类后必须重建**:
> `docker compose exec procurement-pc npx tailwindcss -c tailwind.config.cjs -i assets/css/main.css -o assets/css/compiled.css --minify`
> 否则新类静默失效(渐变变白块、任意值不生效)。h5/admin 是否同机制未查,改样式前先确认。

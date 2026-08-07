# AinerWise Market H5 与 2Hands 整合执行计划 V1

## Summary

本任务书用于把原 Cebu 移动采购能力升级为可独立运营的 `AinerWise Market H5`，并补齐 `2Hands` 二手/企业回收再售商品域。它和官网是“淘宝 / 阿里巴巴”式关系：前台产品可以独立运营，但账号、商品、订单、采购、分析、SEO 和后台治理都写入 AinerWise Core。

当前根目录 `CebuProjects` 仍然是只读参考源，不能修改。所有实现必须落在 `Ainerwise` 目录。

## Architecture Decision

- `AinerWise Official PC/H5`：品牌官网、解决方案、官方推荐商品、SEO 承接和跳转。
- `AinerWise Market H5`：独立移动市场产品，原 Cebu Buyer H5 能力在这里零损失升级。
- `Marketing Operations H5`：内部营销运营工作台，只负责 Creative Brief、审核、素材回流和发布排期。
- `2Hands`：Market 的独立频道，服务个人二手、企业回收再售、翻新/质保再售。
- `AinerWise Core`：统一认证、账户、Portal Grant、商品、供应商、二手、订单、支付台账、分析和 SEO 数据底座。

严禁把 `Marketing Operations H5` 当作对外 Market H5。两者名称相似但产品目标不同。

## Physical Entrypoints

| Product | Physical App | Local Address | Purpose |
| --- | --- | --- | --- |
| Official PC | `frontend-pc` | `http://localhost:4099` | 官网、解决方案、官方推荐产品、SEO |
| Official H5 | `frontend-h5` | `http://localhost:4098` | 移动官网、移动 SEO、跳转 Market H5 |
| AinerWise Market PC | `modules/procurement/pc` | `http://localhost:4106` | PC 市场/采购，保留原 Cebu PC 能力 |
| AinerWise Market H5 | `modules/procurement/h5` | `http://localhost:4107` | 独立移动市场，保留原 Cebu H5 能力 |
| AinerWise Market Admin | `modules/procurement/admin` | `http://localhost:4108` | 市场/采购后台，保留原 Cebu Admin 能力 |
| Marketing Operations PC | `frontend-admin` | `http://localhost:4094` | 内部营销运营 |
| Marketing Operations H5 | `frontend-h5` logical portal | `/marketing-mobile` | 内部移动营销运营 |

建议域名：

- `m.market.localhost` → `AinerWise Market H5`
- `market.localhost` → `AinerWise Market PC`
- `procurement-h5.localhost` 作为兼容入口保留
- `cebu.localhost` / `cebu-h5.localhost` 仅允许兼容 redirect 或测试用途

## Product Surface Rules

商品必须标记来源/销售域，不允许所有商品混成一类：

- `official`：官网推荐/官方供应链产品。
- `market`：Market 市场商品，由供应商或平台运营发布。
- `official_recommended`：官网重点推荐，但仍可进入 Market。
- `enterprise_recycled`：企业回收、翻新、再销售，必须支持保修/质保说明。
- `personal_secondhand`：个人二手，可无保修，但必须清楚展示成色、缺陷、取货方式和隐私规则。

用户发布商品时必须选择：

- `New`
- `Personal second-hand`
- `Enterprise recycled / refurbished`

个人二手可以无保修；企业回收再售必须提供 `warranty_left_months` 或 warranty policy。

## Zero-Loss Rules

- 原 Cebu PC/H5/Admin/backend 功能必须进入迁移账本。
- 不得删除 Buyer、Supplier、RFQ、Offer、Order、Wallet、Message、Dispute、KYC、Ads、Catalog、Notification 能力。
- 不得把官网 `products` 页面当成 Market 完整迁移。
- 不得把内部 `marketing-mobile` 当成对外市场 H5。
- 不得用 placeholder、静态假数据或只可打开的空页面冒充完成。

## Implementation Ledger

| Column | Scope | New Location | Status | Verification Evidence |
| --- | --- | --- | --- | --- |
| Market H5 branding | Cebu H5 → AinerWise Market H5 | `Ainerwise/modules/procurement/h5` | READY_FOR_VERIFY | `npm run build`; `curl http://127.0.0.1:4107/cn` -> 200, title `AinerWise Market H5` |
| Market H5 language parity | en/cn/sr/pl + browser detect + user override | `modules/procurement/h5/plugins/i18n.ts` | READY_FOR_VERIFY | `npm run build`; supported locale list restricted to completed languages to avoid raw key leakage |
| Official H5 Market jump | 官网 H5 跳转独立 Market H5 | `Ainerwise/frontend-h5` | READY_FOR_VERIFY | `npm run build`; `curl http://127.0.0.1:4098/cn/products` -> 200 |
| Official PC product surfaces | 官方推荐/Market/2Hands/回收再售入口 | `Ainerwise/frontend-pc/pages/products` | READY_FOR_VERIFY | `npm run build`; product surface filter implemented against Core API |
| Product API surface filter | `surface=official|market|recycled|all` | `backend/app/api/v1/endpoints/products.py` | READY_FOR_VERIFY | `curl http://127.0.0.1:8000/api/v1/products?limit=1&surface=official` -> 200, `surface=official` |
| 2Hands mobile browse | 二手移动频道 | `modules/procurement/h5/pages/secondhand` | READY_FOR_VERIFY | `npm run build`; `curl http://127.0.0.1:4107/cn/secondhand` -> 200 |
| 2Hands listing origin | personal vs enterprise recycled | `backend/app/api/v1/endpoints/secondhand.py` | READY_FOR_VERIFY | `curl http://127.0.0.1:8000/api/v1/secondhand/listings?page_size=1` -> 200, `listing_origin=personal_secondhand`; warranty validation implemented for enterprise origins |
| Supplier catalog item type | New / recycled / market metadata | `modules/procurement/h5/pages/supplier/catalog.vue` | READY_FOR_VERIFY | `npm run build`; authenticated create/edit payload requires independent verifier login test |
| Backend product governance | Admin 控制国家、商品 surface、SEO batch | `frontend-admin` + backend | TODO | admin test evidence |

## Status Rules

- `TODO`
- `IN_PROGRESS`
- `READY_FOR_VERIFY`
- `VERIFIED`
- `FAILED_VERIFY`
- `BLOCKED`

实现 Agent 只能把任务推进到 `READY_FOR_VERIFY`。独立验证 Agent 才能打 `VERIFIED`。

## Verification Gates

每个栏目必须记录：

- 修改文件
- 页面地址
- API 地址
- 登录角色
- 测试命令
- 构建结果
- 权限正向测试
- 权限负向测试
- 截图或 curl 日志
- 状态只能从 `IN_PROGRESS` 改为 `READY_FOR_VERIFY`

## Current Execution Slice

本轮目标：

1. 把 4107 明确升级为 `AinerWise Market H5`。
2. 补 `pl` 语言入口，保持浏览器自动识别、用户手动选择、localStorage/cookie 持久化一致。
3. 新增移动 `2Hands` 频道入口，真实调用 Core `secondhand` API。
4. 后端补产品 `surface` 查询和二手 `listing_origin` / warranty 口径。
5. 官网 PC/H5 只新增 Market 跳转和官方推荐口径，不把 Market 直接并入官网。

完成后本轮状态只能记为 `READY_FOR_VERIFY`，等待独立验证 Agent 验收。

## Current Verification Evidence

Build commands completed:

- `cd Ainerwise/modules/procurement/h5 && npm run build` -> passed.
- `cd Ainerwise/frontend-h5 && npm run build` -> passed.
- `cd Ainerwise/frontend-pc && npm run build` -> passed.
- `cd Ainerwise/modules/procurement/pc && npm run build` -> passed with non-blocking Nuxt UI Tailwind warning.
- `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/products.py Ainerwise/backend/app/api/v1/endpoints/secondhand.py Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py Ainerwise/backend/app/crud/product.py Ainerwise/backend/app/core/portal_registry.py` -> passed.

Runtime smoke completed after service restart:

- `docker compose up -d --build procurement-h5` -> running.
- `curl -L http://127.0.0.1:4107/cn` -> `200`.
- `curl -L http://127.0.0.1:4107/cn/secondhand` -> `200`.
- `curl -L http://127.0.0.1:4106/cn/marketplace` -> `200`.
- `curl -L http://127.0.0.1:4098/cn/products` -> `200`.
- `curl http://127.0.0.1:8000/api/v1/products?limit=1&surface=official` -> `200`, returns `surface: official`.
- `curl http://127.0.0.1:8000/api/v1/secondhand/listings?page_size=1` -> `200`, returns `listing_origin: personal_secondhand`.

Important notes for verifier:

- `Ainerwise/modules/procurement/pc` does not define `/cn/products`; PC Market product browsing is `/cn/marketplace`, with buyer/supplier/admin workflows under their existing Cebu-compatible routes.
- Root `CebuProjects` must remain unchanged. Confirm with `git status --short CebuProjects`.
- This implementation does not mark anything `VERIFIED`; independent verifier must test authenticated supplier listing create/edit, enterprise recycled warranty rejection, and buyer contact disclosure rules.

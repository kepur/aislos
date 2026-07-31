# Integration Phase 2 — Cebu 交易域迁入

更新：2026-06-11

## 状态

| 栏目 | 名称 | 状态 |
|------|------|------|
| IP2-01 | Category Schema + Supplier Listing | `VERIFIED` |
| IP2-02 | Procurement Request (Intent) + Matching | `VERIFIED` |
| IP2-03 | Supplier Offer + Commerce Order | `VERIFIED` |
| IP2-04 | Legacy Bridge 扩展 | `VERIFIED` |
| IP2-05 | Parity API（supplier-candidates / bind） | `VERIFIED` |
| IP2-06 | Order Delivery + Dispute | `VERIFIED` |
| IP2-07 | Trust / Payment / FX | `VERIFIED` |
| IP2-08 | Message / Notification | `VERIFIED` |
| IP2-09 | Payment Settlement / Reconciliation | `VERIFIED` |
| IP2-10 | Stripe Webhook 自动结算 | `VERIFIED` |

Migration: **040**（在 039 基础上新增 `commerce_settlements`, `commerce_reconciliation_runs`）

API 前缀：`/api/v1/commerce/*`

新增端点：

```text
GET    /commerce/orders/{order_id}
POST   /commerce/orders/{order_id}/complete
GET    /commerce/orders/{order_id}/deliveries
POST   /commerce/orders/{order_id}/deliveries
PATCH  /commerce/deliveries/{delivery_id}/status
GET    /commerce/orders/{order_id}/disputes
POST   /commerce/orders/{order_id}/disputes
POST   /commerce/disputes/{dispute_id}/resolve   (Staff)
GET    /commerce/trust-profiles/{company_id}
GET/POST /commerce/orders/{order_id}/reviews
GET    /commerce/risk-flags                      (Staff)
POST   /commerce/risk-flags/{flag_id}/resolve    (Staff)
POST   /commerce/orders/{order_id}/payment-intent
GET    /commerce/orders/{order_id}/payment-intent
GET    /commerce/orders/{order_id}/fx-quote?quote_currency=USD
GET    /commerce/notifications
GET    /commerce/notifications/unread-count
POST   /commerce/notifications/{id}/read
POST   /commerce/notifications/read-all
GET    /commerce/orders/{order_id}/thread
GET/POST /commerce/threads/{thread_id}/messages
GET    /commerce/orders
POST   /commerce/orders/{order_id}/confirm-funding   (Staff)
GET    /commerce/settlements
POST   /commerce/settlements/{id}/settle           (Staff)
POST   /commerce/reconciliation-runs               (Staff)
```

IP2-09 规则：

- `confirm-funding` → `mark_milestone_funded` + 写 `commerce_settlements`（账本双分录）
- `settle` → 记录 PSP settlement ref，intent → completed
- `reconciliation-runs` → 比对 milestone ledger 借贷平衡，标记 reconciled / mismatch
- 平台不自持资金；真实资金在 PSP / 银行

IP2-10：

- `POST /commerce/orders/{id}/checkout` → Stripe Checkout Session
- `POST /webhooks/stripe` 处理 `commerce_order` → 自动 `confirm_order_funding(escrow:psp)`
- 未配置 Stripe 时 checkout 返回 `configured: false`，可继续 offline `confirm-funding`

Bridge 事件：`procurement.request.created|published`, `commerce.order.completed`, `commerce.dispute.opened`

IP2-08 规则：

- `portal_notifications`：站内收件箱（与 AI Conversation 分离）
- `commerce_threads` / `commerce_messages`：买卖双方业务线程
- 自动通知：offer 提交、award、配送 shipped/delivered、纠纷、订单完成、新消息
- 纠纷开启 → `queue_admin_telegram` 入队 Admin Telegram（同事务）

IP2-07 规则：

- 订单完成 → 更新供应商 `trust_profiles`（completed_orders、trust_score）
- 纠纷开启 → 自动创建 `risk_flags` 并降低 trust_score
- 买家评价 → `transaction_reviews` 回写 avg_rating
- `payment-intent` 创建 `PaymentPlan` + milestone（不自持资金，对接 PSP）
- `fx-quote` 复用 Core `ExchangeRate` 表

业务规则：

- 配送状态机：`scheduled → shipped → in_transit → delivered → accepted`
- 存在 open/under_review 纠纷时不可 `complete` 订单
- 有配送记录时须至少一条 `delivered` 或 `accepted` 才能完成订单
- 纠纷解决后订单回到 `in_delivery`

验证：

```bash
cd Ainerwise/backend
alembic heads   # 040
pytest -q tests/test_commerce_settlement.py tests/test_commerce_messaging_notifications.py tests/test_commerce_trust_payment_fx.py tests/test_commerce_delivery_dispute.py tests/test_commerce_trade.py tests/test_legacy_bridge.py
```

## Field Worker 离线 PWA（并行）

| 栏目 | 状态 |
|------|------|
| IndexedDB 任务缓存 + 离线队列 | `VERIFIED` |
| Service Worker shell 缓存 | `VERIFIED` |
| `/field/sync` 批量同步 + 版本冲突 409 | `VERIFIED` |
| 任务详情页（导航/清单/状态/证据） | `VERIFIED` |
| 二维码/签字/完整 SW 离线 API | `VERIFIED` |

验证：`pytest -q tests/test_field_worker_offline.py`

Field Worker 扩展（二维码 / 签字 / SW API 缓存）：

| 能力 | 路径 |
|------|------|
| QR 绑定 | `POST /field/tasks/{id}/bind-qr` |
| 客户签字 | `POST /field/tasks/{id}/signature` |
| 离线同步 | `POST /field/sync`（evidence_type: `qr` / `signature`） |
| SW API 缓存 | `frontend-h5/public/field-worker-sw.js` 缓存 `GET /api/v1/field/*` |

# ProcurePing 系统完成度追踪

> 本文件追踪所有需求的实现与验证状态，供多个 AI agent 或工程师接力使用。  
> 勾选规则：`[x]` 已实现并验证 · `[~]` 部分实现 · `[ ]` 未开始  
> 最后更新：2026-05-06

---

## 一、项目结构总览

| 模块 | 路径 | 技术栈 | 端口 | 状态 |
|------|------|--------|------|------|
| Backend API | `backend/` | FastAPI + SQLAlchemy async + PostgreSQL | 8088 | [x] 运行中 |
| PC Frontend | `pc-frontend/` | Nuxt 3 + Nuxt UI + Pinia + Tailwind | 3399 | [x] 运行中 |
| H5 Mobile Frontend | `h5-frontend/` | Nuxt 3 + Vant 4 + Pinia + Tailwind | 3011 | [x] 运行中 |
| Admin Frontend | `admin-frontend/` | Vite + Vue 3 + Vue Router 4 + Pinia + Tailwind | 3012 | [x] 运行中 |
| Admin Backend | `admin-backend/` | 未创建，当前复用 backend 的 /admin/* 路由 | — | [ ] 未拆分 |

---

## 二、后端 API 完成度

### 2.1 认证与用户

| 功能 | API | 状态 |
|------|-----|------|
| 用户注册 | `POST /auth/register` | [x] |
| 用户登录 | `POST /auth/login` | [x] |
| Token 刷新 | `POST /auth/refresh` | [x] |
| 获取当前用户 | `GET /auth/me` | [x] |
| 修改个人资料 | `PATCH /auth/me` | [x] |
| 修改密码 | `POST /auth/me/password` | [x] |
| Telegram 绑定 | `PATCH /auth/me/telegram` | [x] |
| 系统模式（Demo） | `GET /auth/system-mode` | [x] |
| 用户列表 | `GET /users` | [x] |
| 用户详情 | `GET /users/{id}` | [x] |

### 2.2 公司与认证

| 功能 | API | 状态 |
|------|-----|------|
| 创建公司 | `POST /companies` | [x] |
| 获取我的公司 | `GET /companies/me` | [x] |
| 修改公司信息 | `PATCH /companies/me` | [x] |
| 公司文档上传 | `POST /companies/me/documents` | [x] |
| 获取公司文档 | `GET /companies/me/documents` | [x] |
| 分支创建 | `POST /companies/me/branches` | [x] |
| 分支列表 | `GET /companies/me/branches` | [x] |
| 分支修改 | `PATCH /companies/me/branches/{id}` | [x] |
| 提交认证 | `POST /companies/me/verification/submit` | [x] |

### 2.3 分类与目录

| 功能 | API | 状态 |
|------|-----|------|
| 分类列表 | `GET /categories` | [x] |
| 分类 schema | `GET /categories/{id}/schema` | [x] |
| 后台创建分类 | `POST /admin/categories` | [x] |
| 后台修改分类 | `PATCH /admin/categories/{id}` | [x] |
| 供应商目录 CRUD | `GET/POST/PATCH/DELETE /supplier/catalog/items` | [x] |

### 2.4 需求与报价

| 功能 | API | 状态 |
|------|-----|------|
| 发布需求 | `POST /intents` | [x] |
| 我的需求列表 | `GET /intents/my` | [x] |
| 需求详情 | `GET /intents/{id}` | [x] |
| 修改需求 | `PATCH /intents/{id}` | [x] |
| 取消需求 | `POST /intents/{id}/cancel` | [x] |
| 供应商匹配需求 | `GET /supplier/intents/matching` | [x] |
| 提交报价 | `POST /intents/{id}/offers` | [x] |
| 报价列表 | `GET /intents/{id}/offers` | [x] |
| 我的报价 | `GET /supplier/offers` | [x] |
| 报价详情 | `GET /offers/{id}` | [x] |
| 撤回报价 | `POST /offers/{id}/withdraw` | [x] |
| 选择报价 | `POST /offers/{id}/award` | [x] |
| 内容审核 | `POST /intents/{id}/moderate` | [x] |

### 2.5 订单与交付

| 功能 | API | 状态 |
|------|-----|------|
| 我的订单列表 | `GET /orders/my` | [x] |
| 订单详情 | `GET /orders/{id}` | [x] |
| 订单状态变更 | `POST /orders/{id}/status` | [x] |
| 确认收货 | `POST /orders/{id}/accept` | [x] |
| 暂停订单 | `POST /orders/{id}/hold` | [x] |
| 提交交付证明 | `POST /orders/{id}/delivery` | [x] |
| 查看交付记录 | `GET /orders/{id}/delivery` | [x] |

### 2.6 纠纷

| 功能 | API | 状态 |
|------|-----|------|
| 发起纠纷 | `POST /orders/{id}/dispute` | [x] |
| 我的纠纷列表 | `GET /disputes/my` | [x] |
| 纠纷详情 | `GET /disputes/{id}` | [x] |
| 提交证据 | `POST /disputes/{id}/evidence` | [x] |

### 2.7 消息与通知

| 功能 | API | 状态 |
|------|-----|------|
| 发送消息 | `POST /messages/threads/{type}/{id}/messages` | [x] |
| 消息列表 | `GET /messages/threads/{type}/{id}/messages` | [x] |
| 我的通知 | `GET /notifications/my` | [x] |
| 标记已读 | `POST /notifications/{id}/read` | [x] |
| 全部已读 | `POST /notifications/read-all` | [x] |

### 2.8 钱包与充值

| 功能 | API | 状态 |
|------|-----|------|
| 我的钱包 | `GET /wallets/me` | [x] |
| 交易记录 | `GET /wallets/transactions` | [x] |
| 创建充值 | `POST /wallets/deposits` | [x] |
| 充值详情 | `GET /wallets/deposits/{id}` | [x] |
| 提交 TX Hash | `POST /wallets/deposits/{id}/submit-tx` | [x] |
| 余额支付订单 | `POST /orders/{id}/pay-from-wallet` | [x] 已实现：钉包USDT钱包扣款+创建托管+订单状态推进 FUNDED |

### 2.9 地图与区域

| 功能 | API | 状态 |
|------|-----|------|
| 地址自动补全 | `GET /maps/autocomplete` | [x] |
| 地理编码 | `GET /maps/geocode` | [x] |
| 反向地理编码 | `GET /maps/reverse-geocode` | [x] |
| 覆盖估算 | `GET /maps/coverage/estimate` | [x] |
| Place Details | `GET /maps/place-details` | [ ] 未实现 |
| 后台 Maps 配置读取 | `GET /admin/maps/config` | [ ] 未实现 |
| 后台 Maps 配置更新 | `PUT /admin/maps/config` | [ ] 未实现 |
| Maps Key 连通性测试 | `POST /admin/maps/test-connection` | [ ] 未实现 |

### 2.10 信誉体系

| 功能 | API | 状态 |
|------|-----|------|
| 我的信誉 | `GET /trust/me` | [x] |
| 用户信誉摘要 | `GET /users/{id}/trust-summary` | [x] |
| 公司信誉摘要 | `GET /companies/{id}/trust-summary` | [x] |

### 2.11 后台管理 API

| 功能 | API | 状态 |
|------|-----|------|
| Dashboard 概览 | `GET /admin/dashboard` | [x] |
| Live Ops | `GET /admin/live-ops` | [x] |
| 用户列表/详情 | `GET /admin/users`, `GET /admin/users/{id}` | [x] |
| 用户状态变更 | `POST /admin/users/{id}/status` | [x] |
| 员工列表 | `GET /admin/staff` | [x] |
| 员工邀请 | `POST /admin/staff/invite` | [x] |
| 员工角色修改 | `PUT /admin/staff/{id}/role` | [x] |
| 公司列表/详情 | `GET /admin/companies`, `GET /admin/companies/{id}` | [x] |
| 公司状态变更 | `PATCH /admin/companies/{id}/status` | [x] |
| 公司认证变更 | `PATCH /admin/companies/{id}/verification` | [x] |
| 认证队列 | `GET /admin/verification/queue` | [x] |
| 认证文档 | `GET /admin/verification/{id}/documents` | [x] |
| 认证审批 | `POST /admin/verification/{id}/decide` | [x] |
| 认证提交 | `POST /admin/verification/{id}/submit` | [x] |
| 需求列表/详情 | `GET /admin/intents`, `GET /admin/intents/{id}` | [x] |
| 报价列表 | `GET /admin/offers` | [x] |
| 订单列表/详情 | `GET /admin/orders`, `GET /admin/orders/{id}` | [x] |
| 订单状态变更 | `POST /admin/orders/{id}/status` | [x] |
| 纠纷列表/详情 | `GET /admin/disputes`, `GET /admin/disputes/{id}` | [x] |
| 纠纷裁决 | `POST /admin/disputes/{id}/resolve` | [x] |
| 纠纷请求证据 | `POST /admin/disputes/{id}/request-evidence` | [x] |
| 托管列表/详情 | `GET /admin/escrow`, `GET /admin/escrow/{id}` | [x] |
| 托管释放 | `POST /admin/escrow/{id}/release` | [x] |
| 托管退款 | `POST /admin/escrow/{id}/refund` | [x] |
| 托管人工验证 | `POST /admin/escrow/{id}/manual-verify` | [x] |
| 支付事件 | `GET /admin/payment-events` | [x] |
| Payout 列表 | `GET /admin/payouts` | [x] |
| 充值列表 | `GET /admin/deposits` | [x] |
| 充值验证 | `POST /admin/deposits/{id}/verify` | [x] |
| 充值拒绝 | `POST /admin/deposits/{id}/reject` | [x] |
| 风控标记 CRUD | `GET/POST /admin/risk-flags`, `POST /admin/risk-flags/{id}/action` | [x] |
| 审计日志 | `GET /admin/audit-logs`, `GET /admin/audit-logs/{id}` | [x] |
| 通知模板 | `GET/PUT /admin/notification-templates` | [x] |
| 通知测试 | `POST /admin/notifications/test-email`, `test-telegram` | [x] |
| 平台设置 | `GET/PUT /admin/settings` | [x] |
| 内部备注 | `GET/POST /admin/notes` | [x] |
| 区域 CRUD | `GET/POST/PATCH /admin/regions` | [x] |
| 服务区域 CRUD | `GET/POST/PATCH /admin/service-areas` | [x] |
| 信誉管理 | `GET /admin/trust/users`, 重算, 调整 | [x] |
| AI 配置 | `GET /admin/ai/config` | [x] |
| AI 测试 | `POST /admin/ai/test` | [x] |
| AI 文档分析 | `POST /admin/ai/analyze-document` | [x] |
| KYC 媒体库列表 | `GET /admin/kyc-media/files` | [ ] 未实现 |
| KYC 媒体详情 | `GET /admin/kyc-media/files/{id}` | [ ] 未实现 |
| KYC 风险标记 | `POST /admin/kyc-media/files/{id}/flag-risk` | [ ] 未实现 |
| KYC AI 单文件分析（增强） | `POST /admin/ai/analyze-kyc-document` | [ ] 未实现 |
| KYC AI 批量分析 | `POST /admin/ai/batch-analyze-kyc` | [ ] 未实现 |
| KYC AI 分析结果查询 | `GET /admin/kyc-media/files/{id}/analysis` | [ ] 未实现 |
| 备份配置 | `GET/PUT /admin/backups/config` | [ ] 未实现 |
| 备份计划管理 | `GET/POST/PATCH/DELETE /admin/backups/schedules` | [ ] 未实现 |
| 手动备份 | `POST /admin/backups/manual` | [ ] 未实现 |
| 备份任务查询 | `GET /admin/backups/jobs` | [ ] 未实现 |
| 备份ZIP下载 | `GET /admin/backups/jobs/{id}/download` | [ ] 未实现 |

### 2.12 Marketplace / 广告（第14/18章 — 已部分实现）

| 功能 | API | 状态 |
|------|-----|------|
| Marketplace Feed | `GET /marketplace/feed` | [x] 已实现，支持分类/关键词/market_mode/排序 |
| 分类 Feed | `GET /marketplace/categories/{id}/feed` | [x] 已实现 |
| 筛选项 | `GET /marketplace/filters` | [x] 已实现 |
| 位置上下文 | `POST /marketplace/location-context` | [ ] 待实现 |
| 商品详情（Public） | `GET /marketplace/items/{id}` | [x] 已实现于 marketplace.py:145 |
| 游客访问无需登录 | Feed + 商品详情 public 路由 | [x] 已移除 auth middleware |
| 商户广告 CRUD | `GET/POST/PATCH /merchant/ad-campaigns` | [x] 已实现含 submit/pause/metrics |
| 商户广告付款 | `POST /merchant/ad-campaigns/{id}/pay` | [ ] 待实现 |
| 商户广告指标 | `GET /merchant/ad-campaigns/{id}/metrics` | [x] 已实现 |
| 后台广告管理 | `GET/PATCH /admin/ad-campaigns` | [x] 已实现 |
| 后台广告审批 | `POST /admin/ad-campaigns/{id}/approve\|reject\|pause` | [x] 已实现 |
| 排名规则 CRUD | `GET/POST/PATCH /ranking/profiles` | [x] 已实现（ranking.py）|
| 排名配置管理 | `GET /admin/ranking/summary` | [x] 已实现 |
| 候选卖家排名 | `GET /intents/{id}/supplier-candidates` | [x] 已实现（ranking_service.py）|
| 买家排序偏好 | `POST /intents/{id}/ranking-preferences` | [x] 已实现 |
| 账户类型 | `PATCH /auth/me/account-type` | [x] 已实现（第18章）|
| 账户上下文 | `GET /auth/me/account-context` | [x] 已实现（第18章）|
| 登录回跳机制 | `return_url` 参数支持 | [x] PC+H5 均已支持 |
| 投放位 | `GET /marketing/placements` | [ ] 待实现 |

---

## 三、PC Frontend 完成度

### 3.1 公共页面

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| 首页 | `index.vue` | 静态 | [x] 页面完成，静态内容 |
| 登录 | `login.vue` | [x] 接 /auth/login | [x] |
| 注册角色选择 | `register-role.vue` | — | [x] |
| 买家注册 | `register-buyer.vue` | [x] | [x] 2步骤 + account_type + 真实 API |
| 供应商注册 | `register-supplier.vue` | [x] | [x] account_type 选择 + KYB 文件上传 |
| 供应商入驻 | `supplier-onboarding.vue` | [~] | [~] |
| 分类浏览 | `categories.vue` | [x] 接真实 /categories | [x] 25个分类+emoji+跳转 marketplace |
| How it Works | `how-it-works.vue` | — | [x] 静态页 |
| 价格说明 | `pricing.vue` | — | [x] 静态页 |
| 信任安全 | `trust-safety.vue` | — | [x] 静态页 |
| 发布需求 | `post-request.vue` | [~] | [~] 需接真实分类+地图+支付 |
| Marketplace Feed | `marketplace.vue` | [x] 接 /marketplace/feed | [x] 筛选/排序/Sponsored/Seller Type/Verified Only/CTA auth guard |
| Marketplace 商品详情 | `marketplace/[id].vue` | [~] | [~] 页面存在，待验证真实 API |


### 3.2 买家页面

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| Dashboard | `buyer/dashboard.vue` | [~] 信誉接口 | [~] KPI 仍为硬编码 |
| 我的需求列表 | `buyer/requests/index.vue` | [x] 接 /intents/my | [x] |
| 需求详情 | `buyer/requests/[id]/index.vue` | [x] 接 /intents/{id} | [x] |
| 需求报价对比 | `buyer/requests/[id]/offers.vue` | 静态 | [~] |
| 报价详情 | `buyer/offers/[id].vue` | 静态 | [~] |
| 订单列表 | `buyer/orders/index.vue` | [x] 接 /orders/my | [x] 真实 API + 状态筛选 + 分页 |
| 订单详情 | `buyer/orders/[id].vue` | [x] 接 /orders/{id} + delivery | [x] 真实 API + 进度条 + 确认收货 + 钉包支付 |
| 消息 | `buyer/messages.vue` | 静态 | [~] |
| 纠纷列表 | `buyer/disputes/index.vue` | 静态 | [~] |
| 新建纠纷 | `buyer/disputes/new.vue` | 静态 | [~] |
| Ideal List | `buyer/ideal-list.vue` | 静态 | [~] |
| 账户设置 | `buyer/settings.vue` | [x] 地址管理 | [x] 接 /addresses CRUD |
| 钉包 | `buyer/wallet.vue` | 静态 | [~] 需接 /wallets/me |

### 3.3 供应商页面

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| Dashboard | `supplier/dashboard.vue` | 静态 | [~] |
| Ping Inbox | `supplier/inbox.vue` | 静态 | [~] |
| 我的报价 | `supplier/offers/index.vue` | 静态 | [~] |
| 新建报价 | `supplier/offers/new.vue` | 静态 | [~] |
| 订单列表 | `supplier/orders/index.vue` | 静态 | [~] |
| 订单详情 | `supplier/orders/[id].vue` | 静态 | [~] |
| 消息 | `supplier/messages.vue` | 静态 | [~] |
| 目录管理 | `supplier/catalog/index.vue` | [x] 接 /supplier/catalog/items | [x] CRUD 弹窗+状态切换+分页+统计卡 |
| 匹配触发 | `supplier/triggers.vue` | 静态 | [~] |
| Payout 设置 | `supplier/payouts.vue` | 静态 | [~] |
| 评价与信誉 | `supplier/reviews.vue` | 静态 | [~] |
| 设置 | `supplier/settings.vue` | 静态 | [~] |

### 3.4 PC Admin 页面（在 pc-frontend 中，与 admin-frontend 重叠）

| 页面 | 文件 | 状态 |
|------|------|------|
| admin/dashboard | `admin/dashboard.vue` | [~] 静态演示，需迁移到 admin-frontend |
| admin/users | `admin/users.vue` | [x] 真实 API + 四维筛选 + 分页 |
| admin/orders | `admin/orders.vue` | [~] |
| admin/disputes | `admin/disputes.vue` | [~] |
| admin/intents | `admin/intents.vue` | [~] |
| admin/offers | `admin/offers.vue` | [~] |
| admin/verifications | `admin/verifications.vue` | [~] |
| admin/categories | `admin/categories.vue` | [~] |
| admin/risk | `admin/risk.vue` | [~] |
| admin/settings | `admin/settings.vue` | [~] |
| admin/audit | `admin/audit.vue` | [~] |
| admin/pricing-intel | `admin/pricing-intel.vue` | [~] |
| admin/ranking | `admin/ranking.vue` | [x] 权重可视化+range slider编辑+实时总和验证 |

### 3.5 PC 导航修复

| 问题 | 状态 |
|------|------|
| 登录后侧边栏导航点击 URL 变化页面不变 | [x] 已修复：移除 app.vue 的 router.beforeEach(next) 冲突，添加 page-key |
| 买家侧边栏 active 高亮不随路由变化 | [x] 已修复：改为动态 isActive() |
| 供应商侧边栏 active 高亮不随路由变化 | [x] 已修复 |
| buyer middleware 重定向到错误 /auth/login | [x] 已修复为 /login |
| supplier middleware 重定向到错误 /auth/login | [x] 已修复为 /login |

### 3.6 PC 多语言

| 功能 | 状态 |
|------|------|
| 语言切换 UI（header + footer） | [x] EN/ZH/JA/ES 四种 |
| 扩展到 10 国语言 | [x] 新增 TL/KO/TH/VI/ID/AR，AR 支持 RTL，10 种全量完整翻译 |
| 内页 i18n | [ ] 买家/供应商内页标签均为英文硬编码 |

---

## 四、H5 Mobile Frontend 完成度

### 4.1 认证

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| 登录 | `auth/login.vue` | [x] | [x] |
| 注册 | `auth/register.vue` | [x] | [x] |
| 重置密码 | `auth/reset-password.vue` | [~] | [~] 后端无重置密码 API |

### 4.2 买家 H5

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| 首页 / 发现 | `buyer/home.vue` | [~] | [~] |
| 发布需求 | `buyer/post-request.vue` | [~] | [~] 缺地图步骤 |
| 需求列表 | `buyer/requests/index.vue` | [~] | [~] |
| 需求详情 | `buyer/requests/[id].vue` | [~] | [~] |
| 报价列表 | `buyer/offers.vue` | [~] | [~] |
| 报价对比 | `buyer/compare.vue` | [~] | [~] |
| 订单列表 | `buyer/orders/index.vue` | [~] | [~] |
| 订单详情 | `buyer/orders/[id].vue` | [~] | [~] |
| 消息 | `buyer/messages.vue` | [~] | [~] |
| 钱包 | `buyer/wallet.vue` | [~] | [~] 需接充值/USDT |
| 买家资料 | `buyer/profile.vue` | [~] | [~] |

### 4.3 供应商 H5

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| Ping 列表 | `supplier/pings.vue` | [~] | [~] |
| Ping 详情 | `supplier/pings/[id].vue` | [~] | [~] |
| 提交报价 | `supplier/make-offer.vue` | [~] | [~] |
| 我的报价 | `supplier/offers.vue` | [~] | [~] |
| 订单列表 | `supplier/orders.vue` | [~] | [~] |
| 订单详情 | `supplier/orders/[id].vue` | [~] | [~] |
| 目录管理 | `supplier/catalog.vue` | [~] | [~] |
| 消息 | `supplier/messages.vue` | [~] | [~] |
| 供应商钱包 | `supplier/wallet.vue` | [~] | [~] |
| 供应商资料 | `supplier/profile.vue` | [~] | [~] |

### 4.4 通用 H5

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| 首页 | `index.vue` | — | [x] |
| 个人中心 | `profile/index.vue` | [x] 信誉 | [x] |
| 编辑资料 | `profile/edit.vue` | [~] | [~] |
| 修改密码 | `profile/change-password.vue` | [x] | [x] |
| 公司资料 | `profile/company.vue` | [~] | [~] |
| 通知列表 | `notifications.vue` | [~] | [~] |
| 消息详情 | `messages/[order_id].vue` | [~] | [~] |
| 认证状态 | `verification.vue` | [~] | [~] |
| 钱包 | `wallet.vue` | [~] | [~] |
| 语言设置 | `settings/language.vue` | [x] | [x] |
| 通知设置 | `settings/notifications.vue` | [~] | [~] |

### 4.5 H5 多语言

| 功能 | 状态 |
|------|------|
| vue-i18n 插件集成 | [x] |
| 10 国语言文件（en/zh/tl/ja/ko/es/th/vi/id/ar） | [x] |
| 语言切换页 | [x] |
| RTL 阿拉伯语支持 | [x] |
| 内页全面 i18n 替换 | [~] 部分页面仍有英文硬编码 |

---

## 五、Admin Frontend 完成度

### 5.1 页面

| 页面 | 文件 | 接真实API | 状态 |
|------|------|-----------|------|
| 登录 | `Login.vue` | [x] | [x] |
| Dashboard | `Dashboard.vue` | [x] /admin/dashboard | [x] |
| 用户管理 | `Users.vue` | [x] | [x] |
| 员工管理 | `Staff.vue` | [x] | [x] |
| 公司管理 | `Companies.vue` | [x] | [x] |
| 认证审核 | `Verification.vue` | [x] + AI KYC | [x] |
| 需求管理 | `Intents.vue` | [x] | [x] |
| 订单管理 | `Orders.vue` | [x] | [x] |
| 纠纷管理 | `Disputes.vue` | [x] | [x] |
| 托管管理 | `Escrow.vue` | [x] | [x] |
| 支付管理 | `Payments.vue` | [x] Events + Payouts + Deposits | [x] |
| 区域管理 | `Regions.vue` | [x] | [x] |
| 风控管理 | `Risk.vue` | [x] | [x] |
| 信誉管理 | `Trust.vue` | [x] | [x] |
| 通知管理 | `Notifications.vue` | [x] | [x] |
| 集成配置 | `Integrations.vue` | [x] + AI Provider | [x] |
| 系统设置 | `Settings.vue` | [x] |
| KYC 媒体库 | `KYCMedia.vue` | [ ] 未实现 |
| 备份管理 | `Backups.vue` | [ ] 未实现 | [x] |
| 审计日志 | `Audit.vue` | [x] | [x] |

### 5.2 Admin 多语言

| 功能 | 状态 |
|------|------|
| vue-i18n 集成 | [x] |
| 10 国语言文件 | [x] en/zh/tl/ja/ko/es/th/vi/id/ar |
| 语言切换 UI | [x] Header + Login |
| RTL 阿拉伯语 | [x] |
| 所有页面 i18n 替换 | [x] |

### 5.3 Admin AI 功能

| 功能 | 状态 |
|------|------|
| AI Provider 配置（模型/密钥/URL） | [x] |
| AI 能力开关（KYC/Fraud/Moderation） | [x] |
| AI 连接测试 | [x] |
| KYC 文档 AI 分析（真伪/提取/置信度） | [x] |
| KYC 文档 PS/篡改识别 | [ ] 未实现 |
| KYC 图文一致性校验 | [ ] 未实现 |
| KYC AI 分析结果落库追溯 | [ ] 未实现 |
| KYC 批量AI分析 | [ ] 未实现 |

---

## 六、后端服务层完成度

| 服务 | 文件 | 状态 |
|------|------|------|
| AI 服务 | `services/ai_service.py` | [x] OpenAI/Anthropic/Azure |
| 审计服务 | `services/audit_service.py` | [x] |
| 托管服务 | `services/escrow_service.py` | [x] |
| 匹配服务 | `services/matching_service.py` | [x] |
| 通知服务 | `services/notification_service.py` | [x] |
| 信誉服务 | `services/trust_service.py` | [x] |
| 钱包服务 | `services/wallet_service.py` | [x] |
| Marketplace Feed 服务 | `services/marketplace_service.py` | [x] 已实现，含 account_type/verified_only 筛选 |
| 广告 Campaign 服务 | `services/marketplace_service.py` | [x] 已内嵌实现（Sponsored 注入） |
| 排名计算服务 | `services/ranking_service.py` | [x] 10维度排名 + score breakdown + why_recommended |

---

## 七、数据模型完成度

| 模型 | 文件 | 状态 |
|------|------|------|
| User | `models/user.py` | [x] |
| Company | `models/company.py` | [x] |
| CompanyDocument | `models/company_document.py` | [x] |
| Category | `models/category.py` | [x] |
| CatalogItem | `models/catalog.py` | [x] |
| Intent | `models/intent.py` | [x] |
| Offer | `models/offer.py` | [x] |
| Order | `models/order.py` | [x] |
| Delivery | `models/delivery.py` | [x] |
| Dispute | `models/dispute.py` | [x] |
| EscrowTransaction | `models/escrow.py` | [x] |
| PaymentEvent | `models/payment_event.py` | [x] |
| Payout | `models/payout.py` | [x] |
| Message | `models/message.py` | [x] |
| Notification | `models/notification.py` | [x] |
| NotificationTemplate | `models/notification_template.py` | [x] |
| PlatformSetting | `models/platform_setting.py` | [x] |
| AuditLog | `models/audit_log.py` | [x] |
| AdminNote | `models/admin_note.py` | [x] |
| RiskFlag | `models/risk_flag.py` | [x] |
| VerificationReview | `models/verification_review.py` | [x] |
| TrustProfile / TrustScoreEvent | `models/trust.py` | [x] |
| Wallet / WalletTransaction / DepositIntent | `models/wallet.py` | [x] |
| Region / ServiceArea | `models/maps.py` | [x] |
| MarketplaceFeedItem | `schemas/marketplace.py` | [x] FeedItemResponse schema 已实现 |
| AdCampaign | `models/ad_campaign.py` | [x] 已实现 |
| AdPlacement | `models/ad_campaign.py` | [x] AdPlacementType 枚举已实现 |
| AdTargetingRule | — | [ ] 未实现（target_keywords/categories 用 JSON 字段代替）|
| AdMetricsDaily | — | [ ] 未实现（当前计数字段直接在 ad_campaigns 表）|
| RankingRule | `migrations/0006_marketplace_ads.py` | [x] ranking_rules 表已迁移 |

---

## 八、第14章需求追踪（Marketplace + 广告 + B2B/B2C）

### 8.1 Marketplace Feed

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端 MarketplaceFeedItem 模型 | P0 | [x] schemas/marketplace.py |
| 后端 MarketLocationContext schema | P0 | [ ] 待实现 |
| 后端 GET /marketplace/feed API | P0 | [x] 含 account_type/verified_only 筛选 |
| 后端 GET /marketplace/categories/{id}/feed API | P0 | [x] 已实现 |
| 后端 GET /marketplace/filters API | P0 | [x] 已实现 |
| 后端 POST /marketplace/location-context API | P0 | [ ] 待实现 |
| PC 分类页改造为 feed 入口 | P0 | [x] 25分类 + 跳转 marketplace |
| PC marketplace feed 页面（网格+筛选+无限滚动） | P0 | [x] Seller Type/Verified/CTA auth guard |
| H5 marketplace feed 页面（瀑布流+筛选） | P0 | [x] Seller Type/Verified/auth guard |
| H5 区域/位置选择组件 | P0 | [x] LocationPicker.vue：3标签页（GPS/地区/手动）+ 底部抽屉动画 + 集成到 H5 marketplace |
| Feed 卡片组件（商品/商户/价格/距离/信誉/标签） | P0 | [x] PC+H5 均已实现 |

### 8.2 广告投放

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端 AdCampaign / AdPlacement / AdTargeting 模型 | P0 | [x] ad_campaign.py |
| 后端 AdMetricsDaily 模型 | P1 | [ ] 当前用计数字段代替 |
| 后端商户广告 CRUD API | P0 | [x] /merchant/ad-campaigns |
| 后端商户广告付款 API | P0 | [ ] 待实现 |
| 后端后台广告管理 API（审核/暂停/拒绝） | P0 | [x] /admin/ad-campaigns |
| 后端广告指标统计 API | P1 | [x] /merchant/ad-campaigns/{id}/metrics |
| PC 商户广告购买页面 | P0 | [ ] 待实现 |
| PC 商户广告效果页面 | P1 | [ ] 待实现 |
| Admin 广告管理页面 | P0 | [ ] 待实现（pc admin 未接真实数据）|
| Feed 中 Sponsored 标签渲染 | P0 | [x] PC+H5 均已实现 |

### 8.3 排名规则

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端 RankingRule 模型 | P1 | [x] ranking_rules 表已迁移（0006）|
| 后端排名规则 CRUD API | P1 | [x] /ranking/profiles CRUD |
| 后端排名计算服务 | P1 | [x] ranking_service.py 10维度 |
| Admin 排名规则配置页面 | P1 | [x] admin/ranking.vue 权重可视化 |
| Feed 排名集成（广告权重+距离+信誉+成交率） | P1 | [x] 已集成于 ranking_service |

### 8.4 B2B + B2C 双模式

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端 MarketMode 枚举 (B2B/B2C/BOTH) | P0 | [x] 已实现 |
| CatalogItem 增加 market_mode 字段 | P0 | [x] 已实现（迁移 0006）|
| Feed 按 market_mode 筛选 | P0 | [x] 已实现 |
| Feed 卡片展示不同 CTA（RFQ vs Buy Now） | P0 | [x] 已实现（PC + H5）|
| B2C 立即购买链路 | P1 | [ ] 待实现 |
| B2C 库存扣减 | P1 | [ ] 待实现 |
| B2C 规格选择 | P1 | [ ] 待实现 |
| B2C 购物车 | P2 | [ ] 待实现 |

---

## 九、跨领域任务

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端 OpenAPI 与三端类型统一 | P0 | [~] 后端 OpenAPI 完整，前端未完全同步 |
| PC 页面从静态 mock 改为接真实 API | P0 | [~] 少数页面接了 API，大多数仍为硬编码 |
| H5 页面从静态 mock 改为接真实 API | P0 | [~] 同上 |
| Admin 后台独立部署（admin-backend 拆分） | P0 | [ ] 当前复用 backend |
| pc-frontend/pages/admin/* 迁移到 admin-frontend | P0 | [ ] 两套后台共存 |
| 余额支付订单 (`POST /orders/{id}/pay-from-wallet`) | P0 | [ ] |
| USDT deposit 完整闭环（前端→后端→审核→入账） | P0 | [~] 后端完成，前端待对接 |
| Google Maps 前端集成（地址搜索/Pin/半径） | P0 | [ ] 后端 API 完成，前端未集成 |
| 端到端测试 & seed 数据 | P1 | [~] demo 模式有基础 seed |
| PC 10 国语言 | P1 | [ ] 当前仅 4 种 |
| Capacitor 打包 | P2 | [ ] |

---

## 十、进度统计

### 后端 API

- **已实现**: ~95 个端点
- **待实现**: ~15 个端点（Marketplace feed、广告、排名、place-details、pay-from-wallet）
- **完成度**: **~86%**

### Admin Frontend

- **已实现**: 18/18 页面，全部接真实 API
- **待实现**: 广告管理页、排名配置页（新增需求）
- **完成度**: **~90%**（现有需求 100%，加上新增需求约 90%）

### PC Frontend

- **页面数**: 47 个 .vue 文件
- **接真实 API 的页面**: ~5 个（login、部分 dashboard）
- **仍为静态/Mock 的页面**: ~42 个
- **完成度**: **~25%**（页面 UI 存在但大多未接真实数据）

### H5 Frontend

- **页面数**: 35 个 .vue 文件
- **接真实 API 的页面**: ~8 个（auth、profile、language）
- **仍为静态/Mock 的页面**: ~27 个
- **完成度**: **~30%**（页面 UI 存在但大多未接真实数据）

### 总体评估

| 层面 | 完成度 | 说明 |
|------|--------|------|
| 后端 API 覆盖 | 86% | 核心业务完整，Marketplace/广告未开始 |
| 后端数据模型 | 85% | 核心模型完整，缺 Marketplace/广告模型 |
| Admin 前端 | 90% | 功能最完整的前端 |
| PC 前端 UI | 80% | 页面都在，但多数是静态 mock |
| PC 前端真实数据 | 25% | 大量页面需从 mock 改为真实 API |
| H5 前端 UI | 75% | 核心页面在，缺 marketplace/feed |
| H5 前端真实数据 | 30% | 大量页面需从 mock 改为真实 API |
| 多语言 | 70% | Admin 100%、H5 80%、PC 60%（10种语言） |
| Marketplace/广告/B2C | 0% | 第14章全部未开始 |
| 独立 Admin 后端 | 0% | 尚未拆分 |

---

## 十一、建议接力顺序

### Phase 1: PC/H5 核心流程接真实 API（P0）

1. PC buyer 发布需求 → 接 `/intents` + `/categories` + `/maps`
2. PC buyer 需求列表/详情 → 接 `/intents/my`
3. PC buyer 报价对比/award → 接 `/intents/{id}/offers` + `/offers/{id}/award`
4. PC buyer 订单/交付/纠纷 → 接 `/orders/my` + delivery + dispute
5. PC buyer 钱包/充值 → 接 `/wallets/me` + deposits
6. PC supplier 目录 → 接 `/supplier/catalog/items`
7. PC supplier 报价 → 接 `/intents/{id}/offers`
8. PC supplier 订单/交付 → 接 `/orders/my` + delivery
9. H5 同步以上核心流程

### Phase 2: Marketplace + 广告（P0）

10. 后端 Marketplace feed API + 模型
11. 后端广告 Campaign API + 模型
12. PC/H5 marketplace feed 页面
13. PC/H5 分类页改造
14. 商户广告购买页面
15. Admin 广告管理页面

### Phase 3: 增强（P1）

16. 排名规则后台
17. 广告效果统计
18. B2B/B2C mode 完整实现
19. PC 10 国语言
20. Admin 后端独立拆分
21. 端到端测试

---

## 十二、本轮接力更新（2026-05-06）

### 12.1 后端：第15/16/17章增量

| 任务 | 状态 | 备注 |
|------|------|------|
| 分类模型字段增强（level/name_zh/name_tl/icon/description/sort_order/typical_weight_kg/customs_hs_code） | [x] | 已通过 `0005` 迁移落库 |
| 地址簿模型 `Address` | [x] | 已新增模型与迁移 |
| 地址簿 API `/addresses` CRUD + `set-default` | [x] | 已接入主应用路由 |
| 物流模型（`ShippingRoute`/`ShippingRate`/`OrderShipping`） | [x] | 已新增模型与迁移 |
| 物流估算服务 `shipping_service` | [x] | 支持重量、体积重、附加费、保险费 |
| 用户物流 API `/shipping/methods` `/shipping/routes` `/shipping/estimate` | [x] | 已实现 |
| 后台物流 API `/admin/shipping/routes` `/admin/shipping/rates` | [x] | 已实现（使用 admin/super_admin 权限） |
| 分类 seed 从 3 个扩充到 25 个一级分类 | [x] | `seed.py` 已扩充并实测写入 |

### 12.2 验证记录

- [x] `PYTHONPATH=. .venv/bin/alembic upgrade head` 成功
- [x] `PYTHONPATH=. .venv/bin/python seed.py` 成功
- [x] `PYTHONPATH=. .venv/bin/python -c "from app.main import app"` 成功
- [~] 自动化测试（pytest）：已安装并执行，但项目当前无测试用例（`no tests ran`）
- [x] 自动化语法校验：`python -m compileall app` 通过

### 12.3 前端：Admin 物流管理页

| 任务 | 状态 | 备注 |
|------|------|------|
| 物流管理页面（路线/费率） | [x] | 新增 `admin-frontend/src/pages/Shipping.vue` |
| 费率附加费 `surcharges_json` 可视化编辑 | [x] | 支持新增/删除附加费项、编辑回填、结构化提交 |
| 路由接入 | [x] | 新增 `/shipping` 页面路由 |
| 侧边栏导航接入 | [x] | 新增 `nav.shipping` 菜单项 |
| 中英文文案补充 | [x] | 新增 `shipping.*` 文案键 |
| 前端构建验证 | [x] | `admin-frontend` 执行 `npm run build` 通过 |

### 12.4 物流统计与报价联动（本轮）

| 任务 | 状态 | 备注 |
|------|------|------|
| 后台物流统计占位（`/admin/shipping/statistics`） | [x] | 后端接口与 Admin Shipping 统计卡片已接通 |
| 报价端联动物流估算（H5） | [x] | `h5-frontend/pages/buyer/compare.vue` 调用 `/shipping/estimate`，展示预估物流费与含物流总价 |
| H5 构建验证 | [x] | `h5-frontend` 执行 `npm run build` 通过 |

### 12.5 PC/H5 一致性补充（地址 + 比价）

| 任务 | 状态 | 备注 |
|------|------|------|
| PC 比价页物流估算展示 | [x] | `pc-frontend/pages/buyer/requests/[id]/offers.vue` 增加预估物流费与含物流总价 |
| PC 买家设置地址管理 | [x] | `pc-frontend/pages/buyer/settings.vue` 接入 `/addresses` 列表、新增、删除、设默认 |
| H5 个人资料地址管理 | [x] | `h5-frontend/pages/profile/edit.vue` 接入 `/addresses` 列表、新增、删除、设默认 |
| PC 构建验证 | [x] | `NUXT_IGNORE_LOCK=1 npm run build` 通过 |
| 附加费结构化编辑 | [x] | 费率表单支持 `surcharges_json` 键值编辑 |
| 物流统计占位卡片 | [x] | 基于 routes/rates 数据展示总量与启用量 |
| 后端统计接口 `/admin/shipping/statistics` | [x] | 已返回路线/费率总量与启用量 |
| 统计卡片接真实接口 | [x] | `Shipping.vue` 改为调用统计 API 渲染 |
| 后端验证 | [x] | `python -c from app.main import app` + `python -m compileall app` 通过 |
| 统计维度增强 | [x] | 新增方式分布、平均费率、最近更新时间 |
| 前端统计可视化增强 | [x] | 统计卡片展示均价/更新时间/方式分布 |
| 前端验证 | [x] | `admin-frontend` 执行 `npm run build` 通过 |
| Top N 路线统计 | [x] | 新增最贵/最便宜/最慢路线 Top5 |
| Top N 前端展示 | [x] | `Shipping.vue` 新增三组 Top 卡片 |
| 本轮后端验证 | [x] | `python -c from app.main import app` + `python -m compileall app` 通过 |

### 12.6 买家需求页接真实 API（本轮）

| 任务 | 状态 | 备注 |
|------|------|------|
| PC 买家需求列表接真实数据 | [x] | `pc-frontend/pages/buyer/requests/index.vue` 接入 `/intents/my` |
| PC 买家需求详情接真实数据 | [x] | `pc-frontend/pages/buyer/requests/[id]/index.vue` 接入 `/intents/{id}` |
| API 鉴权修复 | [x] | 新增 `auth.client.ts` 插件以确保刷新后 `authStore` Token 被正确 Hydrate |
| useApi `auth_token` 修复 | [x] | `useApi.ts` 修改为从 `authStore` 获取 Token 而非 Cookie 以匹配存储方案 |
| 浏览器自动化验证 | [x] | 实测登录、列表渲染及详情跳转页面渲染正常，无 403 / 401 报错 |

### 13.1 本轮接力更新（2026-05-07）

| 任务 | 状态 | 备注 |
|------|------|------|
| 迁移 0005 修复（使用 postgresql.ENUM + create_type=False） | [x] | 成功运行 |
| 迁移 0006 marketplace_ads | [x] | 新增 market_mode、ad_campaigns、ranking_rules |
| CategoryResponse 增加新字段（level/name_zh/name_tl 等） | [x] | schema 已更新 |
| 分类中英文翻译（25个分类） | [x] | name_zh/name_tl 已补全并验证 |
| 物流 seed 数据 | [x] | 20条路线+20条费率（PH↔CN/US/JP/KR/SG/HK） |
| CatalogItem 增加 market_mode/min_order_qty/weight_kg/origin_country/view_count/order_count | [x] | 迁移+模型均已更新 |
| AdCampaign 模型 | [x] | 新增 ad_campaign.py |
| Marketplace Feed API `/marketplace/feed` | [x] | 支持排序/分类/关键词/market_mode 筛选 |
| 分类 Feed API `/marketplace/categories/{id}/feed` | [x] | 已实现 |
| Feed 筛选项 API `/marketplace/filters` | [x] | 已实现 |
| 商户广告 CRUD API `/merchant/ad-campaigns` | [x] | 已实现 CRUD+submit+pause+metrics |
| 后台广告管理 API `/admin/ad-campaigns` | [x] | 已实现 approve/reject/pause |
| PC categories 页面接真实 API | [x] | 25个分类含 emoji + 中文 + 跳转 marketplace |
| PC Marketplace Feed 页面 | [x] | 完整筛选/排序/网格布局/Sponsored 标签/CTA |
| H5 Marketplace Feed 页面 | [x] | `/marketplace` 瀑布流+筛选+bottom nav 已加入 |
| 后端验证 | [x] | `python -c from app.main import app` 通过 |
| PC/H5 构建验证 | [x] | 均 `npm run build` 通过 |
| Feed + Sponsored 注入逻辑 | [x] | 页面1 rank 排序时注入最高出价广告（最多3个） |

---

## 十三、第18章需求追踪（个人/企业账户 + 游客 Marketplace + 智能排名）

> 对应 `额外需求2.0.md` 第 18 章。更新时间：2026-05-07。

### 13.2 个人/企业账户区分（AccountType）

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `users` 表新增 `account_type` 字段迁移 | P0 | [x] 迁移 0007_account_type 已运行 |
| `AccountType` 枚举（INDIVIDUAL / BUSINESS） | P0 | [x] models/user.py |
| 注册 API `POST /auth/register` 支持 `account_type` | P0 | [x] schemas/auth.py + routers/auth.py |
| `PATCH /auth/me/account-type` 升级端点 | P0 | [x] 已实现，INDIVIDUAL→BUSINESS 允许，反向拒绝 |
| `GET /users/me/account-context` 返回功能开关列表 | P0 | [x] 已实现，返回 features JSON |
| PC 买家注册页增加个人/企业选择步骤 | P0 | [x] 2步骤注册流程：Step1选类型，Step2填信息，调用真实API |
| PC 供应商注册页增加个人/企业选择步骤 | P0 | [x] 表单顶部新增个人/企业选择器，提交时同步 account-type |
| PC Buyer Dashboard 根据 `account_type` 动态显隐企业入口 | P0 | [x] 已接 /auth/me/account-context，BUSINESS 显 Company/Team/KYB/Contracts 4个入口 |
| H5 Profile 根据 `account_type` 动态显隐 KYB 和团队入口 | P0 | [x] MobileAccount.vue 已接 /auth/me/account-context，BUSINESS 显 KYB/公司 |
| Admin 用户列表支持 `account_type` 筛选 | P1 | [x] admin/users.vue 重写：真实 API + account_type/role/status/keyword 四维筛选 |
| 个人卖家默认 `market_mode = B2C`，企业卖家支持 B2B/B2C/BOTH | P1 | [~] 注册页已选类型，market_mode 引导待后续实现 |

### 13.3 游客 Marketplace 访问与登录回跳

| 任务 | 优先级 | 状态 |
|------|--------|------|
| PC `marketplace.vue` 移除登录 middleware 拦截（改为 public） | P0 | [x] 已确认无 auth middleware |
| H5 `/marketplace/index.vue` 确认无 auth middleware | P0 | [x] 已移除 buyer middleware |
| 交易按钮点击时检查登录状态（非页面级拦截） | P0 | [x] handleCta 加入 authStore.isLoggedIn 检测 |
| PC `/login?return_url=` 参数支持登录后回跳 | P0 | [x] login.vue 已支持 return_url |
| H5 登录页同样支持 `return_url` 回跳 | P0 | [x] h5/pages/auth/login.vue 已支持 return_url |
| 后端 `/marketplace/feed` 改为可选认证（`Optional[User]`） | P0 | [x] 已是 public，无 auth 依赖 |
| 后端 `GET /marketplace/items/{id}` public 端点 | P1 | [x] 已实现于 marketplace.py:145 |
| `POST /marketplace/actions/require-auth-return` 记录操作意图 | P2 | [ ] 可选，延后实现 |

### 13.4 Buyer/Supplier Dashboard Marketplace 入口

| 任务 | 优先级 | 状态 |
|------|--------|------|
| Buyer Dashboard 新增 "Browse Marketplace" 快速入口按钮 | P1 | [x] buyer/dashboard.vue 已添加 |
| Buyer Dashboard 新增 "Today's Recommendations" 推荐模块（3-6条） | P1 | [x] 从 marketplace/feed 拉取 top-6 商品，显示卡片网格 |
| Supplier Dashboard 新增 "Browse Market" 入口 | P1 | [x] supplier/dashboard.vue 已添加 |

### 13.5 Feed 账户类型与交易模式联合筛选

| 任务 | 优先级 | 状态 |
|------|--------|------|
| Feed API 新增 `account_type` 筛选参数 | P1 | [x] 已实现（marketplace.py + marketplace_service.py）|
| Feed API 新增 `verified_only` 认证企业筛选 | P1 | [x] 已实现 |
| PC marketplace 筛选器增加"商户类型"选项 | P1 | [x] 侧边栏已加 Seller Type + Verified Only 筛选器 |
| H5 marketplace 筛选器增加"商户类型"选项 | P1 | [x] Filter drawer 已加 Seller Type（All/Individual/Business）+ Verified Only |

### 13.6 需求发布后候选卖家智能排名

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `intent_candidates` 表 / 缓存结构设计 | P1 | [x] 无独立表，实时计算返回（轻量方案）|
| 后端 `GET /intents/{id}/supplier-candidates` 端点 | P1 | [x] 已实现于 intents.py |
| 后端 `POST /intents/{id}/ranking-preferences` 端点 | P1 | [x] 已实现于 intents.py |
| 多维度排名计算（分类匹配/距离/信誉/成交率/物流/库存/广告权重） | P1 | [x] ranking_service.py 10维度 |
| Score breakdown 字段返回（`score_breakdown` JSON） | P1 | [x] 已包含所有维度数据 |
| `why_recommended` 文字说明生成 | P1 | [x] 动态生成理由文字 |
| PC 需求详情页展示候选卖家列表（`supplier-candidates`） | P1 | [x] buyer/requests/[id]/index.vue 新增「Matched Suppliers」面板，含排序切换和 score breakdown |
| 买家可切换排序方式（综合/成本/信誉/距离/交期） | P1 | [x] API 支持 5 种排序方式 |

### 13.7 排名配置后台

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `ranking_profiles` 表（已有 `ranking_rules`，需扩展或新增 profile） | P1 | [x] 内存 profile 存储 + SORT_WEIGHTS 实时同步（无需 DB 迁移）|
| `GET /ranking/profiles` 端点 | P1 | [x] 已实现，返回5个内置 profile |
| `POST /ranking/profiles` 端点 | P1 | [x] 已实现，支持创建自定义 profile |
| `PATCH /ranking/profiles/{id}` 端点 | P1 | [x] 已实现，实时更新 SORT_WEIGHTS，权重之和校验 |
| `GET/POST/PATCH /admin/ranking-rules` 端点（marketplace feed 排名） | P1 | [x] /admin/ranking/summary 返回所有模式权重 |
| Admin 排名规则配置页面 | P2 | [x] admin/ranking.vue：权重条可视化 + range slider 编辑 + 实时总和验证 |

### 13.8 匹配供应商详情 / 绑定 / Demo 模式收口

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后端候选供应商详情端点 `GET /intents/{id}/supplier-candidates/{catalog_item_id}` | P0 | [x] 返回单个候选供应商 score breakdown 和推荐理由 |
| 后端候选供应商绑定端点 `POST /intents/{id}/supplier-candidates/{catalog_item_id}/bind` | P0 | [x] 写入 `Intent.attrs_jsonb`，记录审计并通知供应商 |
| PC 需求详情页候选供应商可点击查看详情 | P0 | [x] 候选卡片、Details、Item、Bind 操作补齐 |
| H5 需求详情页候选供应商可点击查看详情 | P0 | [x] 移动端底部详情面板、View item、Bind supplier 补齐 |
| Demo/mock 前端开关收口到后端 `DEMO_MODE` | P0 | [x] H5 本地 fallback 不再自行开启，必须跟随 `/auth/system-mode` |
| 文档区分生产 `deploy/` 与本地开发四端 | P0 | [x] 根 README、PROJECT_ARCHITECTURE、backend/deploy 文档已更新 |

---

## 十四、第21章需求追踪（AI Project Forge / 项目需求分析）

> 对应 `额外需求2.0.md` 第 21 章。目标是新增 buyer 侧 AI 项目需求分析工作台，将项目描述、文档、图片拆解为可编辑采购清单，再发布为现有 `Intent`，复用当前供应商匹配、报价、订单、支付与物流链路。

### 14.1 后端 Project 基础模型

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 新增 `buyer_projects` 模型与迁移 | P0 | [x] 已实现 |
| 新增 `project_files` 模型与迁移 | P0 | [x] 已实现 |
| 新增 `project_ai_runs` 模型与迁移 | P0 | [x] 已实现 |
| 新增 `project_line_items` 模型与迁移 | P0 | [x] 已实现 |
| `Intent` 增加 `project_id`、`project_line_item_id` 可选关联字段 | P0 | [x] 已实现 |
| Project 状态枚举与 line item 状态枚举 | P0 | [x] 已实现 |

### 14.2 Buyer Project API

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `POST /buyer/projects` 创建项目 | P0 | [x] 已实现 |
| `GET /buyer/projects` 项目列表 | P0 | [x] 已实现 |
| `GET /buyer/projects/{id}` 项目详情 | P0 | [x] 已实现 |
| `PATCH /buyer/projects/{id}` 更新项目基础信息 | P0 | [x] 已实现 |
| `DELETE /buyer/projects/{id}` 删除或取消项目 | P1 | [x] 软删除 → CANCELED |
| 项目权限校验：买家只能访问自己的项目 | P0 | [x] 已实现 |

### 14.3 文件上传与资料抽取

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `POST /buyer/projects/{id}/files` 绑定上传文件到项目 | P0 | [x] 已实现 |
| `DELETE /buyer/projects/{id}/files/{file_id}` 删除项目文件 | P0 | [x] 已实现 |
| 上传类型补齐 `text/plain` | P0 | [x] 已实现 |
| 上传类型补齐 DOCX | P0 | [x] 已实现 |
| PDF/TXT/DOCX 文本抽取服务 | P0 | [x] 已实现 |
| 图片多模态摘要能力（provider 支持时） | P1 | [ ] 未实现 |
| 文件抽取失败状态与错误信息落库 | P0 | [x] 已实现 |

### 14.4 AI Project Analysis

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 后台 AI 项目分析配置读取 | P0 | [x] 已实现 |
| `POST /buyer/projects/{id}/ai/analyze` 启动异步分析 | P0 | [x] 已实现 |
| `GET /buyer/projects/{id}/ai-runs/{run_id}` 查询分析状态 | P0 | [x] 已实现 |
| `POST /buyer/projects/{id}/ai-runs/{run_id}/retry` 重试分析 | P1 | [x] 已实现 |
| AI 输出 JSON schema/parser 校验 | P0 | [x] 已实现 |
| 失败 run 保留输入快照、错误原因与重试入口 | P0 | [x] 已实现 |
| 缺失问题 `missing_questions` 生成与保存 | P0 | [x] 已实现 |
| 假设条件 `assumptions` 生成与保存 | P0 | [x] 已实现 |
| 质量档位 `BUDGET/MID_RANGE/PREMIUM` 评估 | P0 | [x] 已实现 |
| 预算估算与风险提示输出 | P0 | [x] 已实现 |

### 14.5 Project Line Items 与发布采购

| 任务 | 优先级 | 状态 |
|------|--------|------|
| AI 分析结果生成 `project_line_items` | P0 | [x] 已实现 |
| `PATCH /buyer/projects/{id}/line-items/{line_item_id}` 编辑分项 | P0 | [x] 已实现 |
| `DELETE /buyer/projects/{id}/line-items/{line_item_id}` 移除分项 | P0 | [x] 已实现 |
| line item 支持分类映射 `category_id` | P0 | [x] 已实现 |
| line item 支持数量、单位、规格、质量档位、预算编辑 | P0 | [x] 已实现 |
| `POST /buyer/projects/{id}/publish` 将 confirmed line items 生成 `Intent` | P0 | [x] 已实现 |
| 发布后回写 line item 的 `intent_id` | P0 | [x] 已实现 |
| `GET /buyer/projects/{id}/matches` 聚合每个分项的匹配供应商 | P1 | [x] 已实现 |

### 14.6 PC Project Forge

| 任务 | 优先级 | 状态 |
|------|--------|------|
| PC Buyer Dashboard 增加 AI Project Forge / 项目添加入口 | P0 | [x] 已实现 |
| PC 项目列表页 | P0 | [x] 已实现 |
| PC 项目创建向导：项目类型、地点、面积/规模、预算、质量档位、描述 | P0 | [x] 已实现 |
| PC 文件上传：图片/PDF/TXT/DOCX | P0 | [x] 已实现 |
| PC AI 分析中状态与失败重试 | P0 | [x] 已实现 |
| PC Project Preview：摘要、缺失问题、物料清单、预算、风险、验收标准 | P0 | [x] 已实现 |
| PC line items 编辑与确认 | P0 | [x] 已实现 |
| PC 发布项目分项为采购需求 | P0 | [x] 已实现 |
| PC 项目详情显示已生成的 `Intent` 和匹配供应商 | P1 | [x] Published Requests 面板 + Check Matches |

### 14.7 H5 Project Forge

| 任务 | 优先级 | 状态 |
|------|--------|------|
| H5 底部或 buyer 页面增加项目入口 | P0 | [x] 已实现 |
| H5 项目创建分步向导 | P0 | [x] 已实现 |
| H5 手机拍照/图片/PDF/TXT/DOCX 上传 | P0 | [x] 已实现 |
| H5 AI 分析状态展示 | P0 | [x] 已实现 |
| H5 物料清单卡片展示与编辑 | P0 | [x] 已实现 |
| H5 发布 confirmed line items 为采购需求 | P0 | [x] 已实现 |
| H5 项目详情与 PC 使用同一套 API 数据 | P0 | [x] 已实现 |

### 14.8 Admin 后台配置与审计

| 任务 | 优先级 | 状态 |
|------|--------|------|
| `GET /admin/integrations/ai-project` 查询项目 AI 配置 | P0 | [x] 已实现 |
| `PATCH /admin/integrations/ai-project` 更新项目 AI 配置 | P0 | [x] 已实现 |
| 配置项：`ai_project_estimation_enabled` | P0 | [x] 已实现 |
| 配置项：`ai_project_model` | P0 | [x] 已实现 |
| 配置项：`ai_multimodal_enabled` | P1 | [ ] 未实现 |
| 配置项：`ai_multimodal_model` | P1 | [ ] 未实现 |
| 配置项：`ai_project_prompt_version` | P0 | [x] 已实现 |
| `GET /admin/project-ai-runs` AI run 列表 | P1 | [ ] 未实现 |
| `GET /admin/project-ai-runs/{id}` AI run 详情 | P1 | [ ] 未实现 |
| Admin AI run 审计页：输入摘要、文件、原始输出、结构化输出、错误原因 | P1 | [ ] 未实现 |

### 14.9 验收场景

| 场景 | 优先级 | 状态 |
|------|--------|------|
| 买家创建“200 平米别墅”项目，AI 生成钢筋、混凝土、PVC、灯具清单 | P0 | [ ] 未验证 |
| 买家创建“光伏项目”，AI 追问屋顶面积、目标功率、预算、地区 | P0 | [ ] 未验证 |
| 买家创建“科技硬件项目”，AI 生成开发板、电源、传感器、外壳等组件 | P1 | [ ] 未验证 |
| 用户编辑 AI 生成数量、规格、质量档位后发布 | P0 | [ ] 未验证 |
| 发布后每个 confirmed line item 自动生成 `Intent` | P0 | [ ] 未验证 |
| 生成的 `Intent` 可继续查看匹配供应商、报价、成交 | P0 | [ ] 未验证 |
| PC/H5 查看同一个 project 数据完全一致 | P0 | [ ] 未验证 |
| 后台关闭 AI 项目分析后，前端隐藏入口，API 返回 disabled | P0 | [ ] 未验证 |
| AI 分析失败时保留草稿、上传文件、失败原因并允许重试 | P0 | [ ] 未验证 |

### 14.10 本轮增量升级：LangGraph 对话收集 + 真实价格分层估算（2026-05-15）

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 新增 `project_messages` 模型与迁移 | P0 | [x] 0013_project_conversation_metrics_pricing |
| 新增 `project_metric_templates` 模型与迁移 | P0 | [x] 支持不同 project_type 的抽象指标模板 |
| 新增 `project_metric_values` 模型与迁移 | P0 | [x] 保存聊天/文件/用户修正提取出的指标 |
| 新增 `project_price_snapshots` 模型与迁移 | P0 | [x] 保存真实价格样本、均价、中位价和三档报价 |
| `GET/POST /buyer/projects/{id}/messages` | P0 | [x] 项目对话收集入口 |
| `GET/PATCH /buyer/projects/{id}/metrics` | P0 | [x] 读取/修正项目指标 |
| `POST /buyer/projects/{id}/freeze-form` | P0 | [x] 将 AI 结果冻结为待发布需求表单 |
| `POST /buyer/projects/{id}/price-estimate` | P0 | [x] 真实 catalog/offer 样本优先，AI 估算兜底 |
| `GET /buyer/projects/{id}/comparison` | P0 | [x] 返回每个 line item 的三档价格、样本和供应商信息 |
| `GET/POST/PATCH /admin/project-metric-templates` | P1 | [x] 后台可配置项目指标模板 |
| `GET /admin/projects/{id}/conversation-audit` | P1 | [x] 后台可审计 messages 和 AI runs |
| PC Project Detail 增加 Project Forge Conversation | P0 | [x] 聊天收集 + 指标展示 |
| PC Project Detail 增加 Refresh Prices / Freeze Form / Comparison | P0 | [x] 接真实新增 API |
| H5 Project Detail 增加聊天收集、指标展示、价格比较 | P0 | [x] 与 PC 同 API |
| Admin Integrations 增加 AI Project Forge 配置项 | P0 | [x] Project AI、多模态、模型、prompt version、文件限制 |
| 后端语法检查 | P0 | [x] `python3 -m compileall backend/app` 通过 |
| PC 构建验证 | P0 | [x] `NUXT_IGNORE_LOCK=1 npm run build` 通过，保留既有 CSS/map URL warning |
| H5 构建验证 | P0 | [x] `NUXT_IGNORE_LOCK=1 npm run build` 通过 |
| Admin 构建验证 | P0 | [x] `npm run build` 通过 |

# ProcurePing — 项目架构规划 V1

> 反向电商/采购撮合平台  
> 买家发布需求 → 供应商匹配 → 报价竞争 → 托管交易 → 交付确认

---

## 1. 整体项目结构

> 当前仓库约定：`backend/`、`admin-backend/`、`pc-frontend/`、`h5-frontend/`、`admin-frontend/` 是本地开发/测试四端代码；`deploy/` 只用于生产部署。不要让 AI agent 把 `deploy/` 里的生产 compose/nginx 反向套到本地开发环境。

```text
procureping/
├── backend/                    # FastAPI 后端 API
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # 配置、安全、数据库、依赖
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic v2 请求/响应模型
│   │   ├── services/          # 业务逻辑层
│   │   ├── routers/           # API 路由
│   │   └── migrations/        # Alembic 数据库迁移
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── seed.py
├── admin-backend/              # 独立后台管理服务端，复用 backend 模型/路由
├── admin-frontend/             # 独立后台管理前端
├── pc-frontend/               # PC 端 (Vue 3 / Nuxt 3)
│   ├── nuxt.config.ts
│   ├── pages/
│   │   ├── index.vue          # 公开首页
│   │   ├── auth/              # 登录/注册
│   │   ├── buyer/             # 买家面板
│   │   ├── supplier/          # 供应商面板
│   │   └── admin/             # 管理后台
│   ├── components/
│   ├── composables/
│   ├── stores/                # Pinia 状态管理
│   ├── i18n/                  # 国际化
│   ├── layouts/
│   └── plugins/
├── h5-frontend/               # 移动 H5 端 (Vue 3 / Nuxt 3)
│   ├── nuxt.config.ts
│   ├── pages/
│   │   ├── index.vue          # 移动首页
│   │   ├── auth/
│   │   ├── buyer/
│   │   ├── supplier/
│   │   └── admin/             # 仅紧急操作
│   ├── components/
│   ├── composables/
│   ├── stores/
│   ├── i18n/
│   └── layouts/
├── deploy/                    # 生产部署 compose/nginx/env/scripts
├── stitch_pc/, stitch_h5/      # 设计稿/参考，不是运行时代码
└── *.md                       # 需求、架构、追踪文档
```

### 1.1 Demo / Mock 数据边界

- 后端 `platform_settings.DEMO_MODE` 是唯一可信开关。
- 默认本地 seed 创建 `DEMO_MODE=true`，方便测试 demo 账号。
- 后台 Settings 关闭后，后端拒绝 `@demo.procureping` 登录，PC/H5 也不得继续启用本地模拟数据。
- 生产环境必须关闭 `DEMO_MODE`；生产部署文档在 `deploy/` 内单独维护。

---

## 2. 技术栈

### 2.1 后端

| 层 | 技术 |
|---|---|
| 框架 | FastAPI |
| 数据库 | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| 迁移 | Alembic |
| 验证 | Pydantic v2 |
| 认证 | JWT (access + refresh token) |
| 密码 | bcrypt / argon2 |
| 通知 | SMTP + Telegram Bot API |
| 运行 | Uvicorn / Gunicorn |
| 可选 | Redis (限流/黑名单) |

### 2.2 PC 前端

| 层 | 技术 |
|---|---|
| 框架 | Nuxt 3 (Vue 3 + TypeScript) |
| 样式 | Tailwind CSS |
| 组件库 | Naive UI / shadcn-vue |
| 状态 | Pinia |
| 国际化 | Vue I18n |
| HTTP | Axios / ofetch |
| 地图 | Map SDK 抽象层 |

### 2.3 H5 移动端

| 层 | 技术 |
|---|---|
| 框架 | Nuxt 3 (Vue 3 + TypeScript) |
| 样式 | Tailwind CSS |
| 组件库 | Vant 4 / 自定义移动组件 |
| 状态 | Pinia |
| PWA | @vite-pwa/nuxt |
| 未来打包 | Capacitor (Android/iOS) |

---

## 3. 后端模块架构

```text
模块化单体架构 (Modular Monolith)

app/
├── core/
│   ├── config.py          # 环境变量、Settings
│   ├── security.py        # JWT 生成/验证、密码哈希
│   ├── database.py        # 数据库引擎、Session
│   ├── deps.py            # 依赖注入 (当前用户、角色检查)
│   ├── audit.py           # 审计日志辅助
│   └── notifications.py   # 通知发送抽象
├── models/
│   ├── user.py            # User, 角色枚举
│   ├── company.py         # Company, Branch
│   ├── category.py        # Category (动态 schema)
│   ├── catalog.py         # CatalogItem
│   ├── intent.py          # Intent (买家需求)
│   ├── offer.py           # Offer (供应商报价)
│   ├── order.py           # Order
│   ├── escrow.py          # EscrowTransaction
│   ├── delivery.py        # Delivery
│   ├── dispute.py         # Dispute
│   ├── message.py         # Message (线程消息)
│   ├── notification.py    # Notification
│   └── audit_log.py       # AuditLog
├── schemas/               # 每个模型对应 Create/Update/Response schema
├── services/
│   ├── auth_service.py    # 注册、登录、Token 管理
│   ├── matching_service.py # V1 简单匹配算法
│   ├── notification_service.py # 多渠道通知
│   ├── escrow_service.py  # 托管抽象 + 模拟实现
│   ├── order_service.py   # 订单状态机
│   ├── dispute_service.py # 纠纷处理
│   └── audit_service.py   # 审计日志记录
└── routers/
    ├── auth.py
    ├── users.py
    ├── companies.py
    ├── categories.py
    ├── catalog.py
    ├── intents.py
    ├── offers.py
    ├── orders.py
    ├── deliveries.py
    ├── disputes.py
    ├── messages.py
    ├── notifications.py
    └── admin.py
```

---

## 4. 用户角色 (RBAC)

| 角色 | 说明 |
|---|---|
| BUYER | 发布需求、查看报价、授予订单、确认收货、发起纠纷 |
| SUPPLIER_ADMIN | 管理公司、分支、目录、报价、订单 |
| SUPPLIER_AGENT | 查看匹配需求、提交报价、管理分配订单 |
| ADMIN | 全平台运营控制、验证、纠纷裁决 |
| AUDITOR | 只读访问报告、审计日志 |

---

## 5. 核心状态机

### Intent: DRAFT → ACTIVE → AWARDED / EXPIRED / CANCELED
### Offer: SUBMITTED → AWARDED / REJECTED / WITHDRAWN / EXPIRED
### Order: CREATED → AWAITING_PAYMENT → PAID_IN_ESCROW → IN_PROGRESS → DELIVERED → ACCEPTED → PAYOUT_RELEASED
### Escrow: AUTH_PENDING → AUTH_HELD → CAPTURED → RELEASED / REFUNDED

---

## 6. 前端页面规划

### 6.1 PC 端

| 区域 | 页面 |
|---|---|
| 公开 | 首页、分类浏览、工作原理、登录/注册 |
| 买家 | 仪表盘、发布需求向导、需求列表、报价对比、订单管理、纠纷、消息、通知 |
| 供应商 | 仪表盘、匹配需求(Pings)、目录管理、报价管理、订单管理、公司设置、消息 |
| 管理后台 | 仪表盘、用户管理、公司审核、订单监控、纠纷处理、审计日志、通知测试 |

### 6.2 H5 移动端

| 区域 | 页面 |
|---|---|
| 买家 Tabs | 首页、我的需求、收到报价、订单、消息 |
| 供应商 Tabs | Pings、报价、订单、目录、消息 |
| 管理(精简) | 仪表盘、纠纷、审核、风险 |

---

## 7. 实施顺序

### Phase 1: 后端 MVP (当前)
1. 项目搭建、配置、数据库、健康检查
2. 用户模型、认证、JWT、RBAC
3. 公司和分支模型
4. 分类和动态 Schema
5. 目录项模型
6. 需求(Intent)模型和买家端点
7. 匹配服务 V1
8. 通知模型 + 应用内通知
9. Email 和 Telegram 发送
10. 报价(Offer)模型和供应商端点
11. 授予报价 → 创建订单
12. 模拟托管(Escrow)
13. 交付更新和证据上传
14. 纠纷模块
15. 审计日志集成
16. 管理面板 API
17. 测试和种子数据

### Phase 2: PC 前端
### Phase 3: H5 移动前端

---

## 8. 需求文档补充说明

以下文件内容与项目无关，为占位文件：
- `AI总结SKILL需求1.0.md` — 内容为 Apple Core ML 贡献指南
- `工程师润色.md` — 内容为 Apple Core ML Stable Diffusion 文档
- `额外需求2.0.md` — 内容为 MIT License

有效需求文档：
- `backendv1_skill.md` — 后端 V1 完整技术规格
- `h5_frontend_requirements_v1.md` — H5 移动前端需求
- `pc_frontend_requirements_v1.md` — PC 前端需求
- `客户需求.md` — 产品愿景（反向电商概念）

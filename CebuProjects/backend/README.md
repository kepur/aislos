# ProcurePing Backend V1

FastAPI + PostgreSQL 反向采购撮合平台后端。

## 快速开始

### 1. 环境准备

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，设置 DATABASE_URL 等变量
```

### 2. 数据库

```bash
# 本项目本地 compose 的 PostgreSQL 暴露在宿主机 5433
docker compose up -d db
export DATABASE_URL=postgresql+asyncpg://procureping:procureping@localhost:5433/procureping

# 运行迁移
alembic upgrade head

# 导入种子数据
python seed.py
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 测试账号（种子数据）

| 角色 | Email | 密码 |
|---|---|---|
| Admin | admin@procureping.local | Admin1234! |
| Buyer | buyer@procureping.local | Buyer1234! |
| Supplier Admin | supplier@procureping.local | Supplier1234! |

## 项目结构

```
app/
├── core/           # 配置、安全、数据库、依赖注入
├── models/         # SQLAlchemy ORM 模型（14个表）
├── schemas/        # Pydantic v2 请求/响应 Schema
├── services/       # 业务逻辑（审计、匹配、通知、托管）
├── routers/        # API 路由（13个模块）
└── migrations/     # Alembic 迁移
```

## 核心 API 端点

| 分组 | 端点 |
|---|---|
| 认证 | POST /auth/register, /auth/login, /auth/refresh |
| 用户 | GET/PATCH /users/me |
| 公司 | POST/GET/PATCH /companies/me, /me/branches |
| 分类 | GET /categories |
| 目录 | CRUD /supplier/catalog/items |
| 需求 | POST /intents, GET /intents/my, GET /intents/{id}/supplier-candidates |
| 匹配绑定 | GET /intents/{id}/supplier-candidates/{catalog_item_id}, POST /intents/{id}/supplier-candidates/{catalog_item_id}/bind |
| 报价 | POST /intents/{id}/offers, POST /offers/{id}/award |
| 订单 | GET /orders/my, POST /orders/{id}/accept |
| 交付 | POST/GET /orders/{id}/delivery |
| 纠纷 | POST /orders/{id}/dispute, POST /admin/disputes/{id}/resolve |
| 消息 | POST/GET /threads/{type}/{id}/messages |
| 通知 | GET /notifications/my |
| 管理 | GET /admin/dashboard, /admin/audit-logs |
| 信誉 | GET /trust/me, GET /users/{id}/trust-summary, GET /companies/{id}/trust-summary |

## 独立后台服务端

后台管理服务端已拆出独立入口：

```bash
cd ../admin-backend
PYTHONPATH=../backend uvicorn main:app --reload --port 8010
```

后台服务只允许平台 admin/staff 角色登录，暴露 `/auth/login`、`/users/me`、`/admin/*` 和 `/admin/trust/*`。

## Demo / Mock 全局开关

`seed.py` 默认写入 `platform_settings.DEMO_MODE=true`，方便本地演示。后台 Settings 可关闭。

- `DEMO_MODE=true`：允许 `buyer@demo.procureping / 123`、`supplier@demo.procureping / 123` 登录，前端可展示 demo 辅助数据。
- `DEMO_MODE=false`：后端拒绝 demo 账号登录，PC/H5 不应再启用本地 mock fallback。
- 生产环境必须关闭 `DEMO_MODE`，并避免运行会写入测试账号/测试目录数据的本地 seed 流程。

## 环境变量

关键变量（详见 .env.example）：

```env
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=your-secret
EMAIL_ENABLED=false
TELEGRAM_ENABLED=false
ESCROW_PROVIDER=SIMULATED
ESCROW_AUTO_CAPTURE=true
```

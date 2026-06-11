# ProcurePing Local Workspace

ProcurePing 是一个反向采购 + Marketplace 平台：买家可发布需求、浏览商品瀑布流、匹配供应商、收报价、下单、托管和交付确认；供应商可维护目录、接收匹配需求、报价和履约；后台独立管理运营、风控、支付、地图、KYC 和全局设置。

## 目录边界

| 目录 | 用途 |
| --- | --- |
| `backend/` | 本地主业务 FastAPI API，开发端口通常为 `8088`。 |
| `admin-backend/` | 独立后台管理服务端，复用 backend 模型和路由，开发端口通常为 `8010`。 |
| `pc-frontend/` | PC 前台 Nuxt 3，本地开发/测试端口通常为 `3399`。 |
| `h5-frontend/` | H5 移动端 Nuxt 3，本地开发/测试端口通常为 `3011`。 |
| `admin-frontend/` | 独立后台前端 Vue/Vite，本地开发/测试端口通常为 `3012`。 |
| `docker-compose.yml` | 本地开发辅助 compose。当前主要用于 PostgreSQL，应用服务建议本地直接启动。数据库宿主机端口是 `5433`。 |
| `deploy/` | 生产部署目录，只服务线上 compose、nginx、环境变量模板、快照导出恢复，不代表本地开发入口。 |
| `stitch_pc/`, `stitch_h5/`, `pc_ui/`, `h5_ui/` | 设计稿和历史 UI 参考，不是运行时代码。 |

## 本地启动顺序

本地开发时优先只启动数据库容器，前后端用本机 Node/Python 运行：

```bash
docker compose up -d db

cd backend
DATABASE_URL=postgresql+asyncpg://procureping:procureping@localhost:5433/procureping PYTHONPATH=. python3 -m alembic upgrade head
DATABASE_URL=postgresql+asyncpg://procureping:procureping@localhost:5433/procureping PYTHONPATH=. python3 seed.py
DATABASE_URL=postgresql+asyncpg://procureping:procureping@localhost:5433/procureping PYTHONPATH=. python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
```

独立后台服务端：

```bash
cd admin-backend
DATABASE_URL=postgresql+asyncpg://procureping:procureping@localhost:5433/procureping PYTHONPATH=../backend python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8010
```

前端：

```bash
cd pc-frontend && npm run dev -- --port 3399
cd h5-frontend && npm run dev -- --port 3011
cd admin-frontend && npm run dev -- --port 3012
```

## 模拟模式

模拟模式由后端数据库表 `platform_settings` 的 `DEMO_MODE` 全局控制，后台路径为 Admin Settings。

- 默认 seed 会创建 `DEMO_MODE=true`，方便本地测试。
- 关闭 `DEMO_MODE=false` 后，后端会拒绝 `@demo.procureping` 模拟账号登录。
- PC/H5 前端不得自行启用 mock/demo 数据，只能跟随后端 `/auth/system-mode` 返回值。
- 线上生产必须在后台或数据库中关闭 `DEMO_MODE`，避免 demo 账号和前端模拟数据进入真实业务流。

Demo 账号：

| 端 | Email | Password |
| --- | --- | --- |
| Buyer | `buyer@demo.procureping` | `123` |
| Supplier | `supplier@demo.procureping` | `123` |
| Admin | `admin@procureping.com` | `admin123` |

## 匹配供应商与绑定

买家需求详情页的 Matched Suppliers 不是静态列表，应走统一后端接口：

- `GET /intents/{intent_id}/supplier-candidates`
- `GET /intents/{intent_id}/supplier-candidates/{catalog_item_id}`
- `POST /intents/{intent_id}/supplier-candidates/{catalog_item_id}/bind`

PC 和 H5 都应支持点击候选供应商查看详情、打开商品页、绑定候选供应商。绑定结果写入 `Intent.attrs_jsonb`，用于后续排名和报价流程。

## 生产部署

生产环境只看 `deploy/`：

- `deploy/compose/docker-compose.prod.yml`
- `deploy/env/.env.prod.example`
- `deploy/nginx/`
- `deploy/scripts/deploy.sh`

不要把本地 `docker-compose.yml`、本地端口、测试数据库端口 `5433` 当成生产配置。

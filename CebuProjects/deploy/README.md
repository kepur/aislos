# ProcurePing — 部署说明

## 目录结构

```
deploy/
├── compose/
│   └── docker-compose.prod.yml   # 生产环境 Compose 文件
├── db/
│   └── init/
│       └── 00-init.sql           # PostgreSQL 初始化扩展
├── docker/
│   └── admin-frontend.Dockerfile # 管理后台前端 Dockerfile
├── env/
│   └── .env.prod.example         # 生产环境变量模板
├── export/                       # 快照导出目录（gitignored 快照归档）
├── nginx/
│   ├── nginx.conf                # Nginx 主配置
│   └── conf.d/
│       └── sanaoll.conf          # 域名路由规则
└── scripts/
    ├── deploy.sh                 # 一键部署脚本
    ├── prepare.sh                # 创建持久化目录
    ├── export_snapshot.sh        # 导出迁移快照
    └── restore_snapshot.sh       # 从快照恢复
```

## 服务一览

| 服务               | 容器名                        | 内部端口 | 对外端口 | 说明                    |
|--------------------|-------------------------------|----------|----------|-------------------------|
| `postgres`         | procureping-postgres          | 5432     | —        | PostgreSQL 数据库        |
| `backend`          | procureping-backend           | 8000     | 8003     | 主业务 API (FastAPI)     |
| `admin-backend`    | procureping-admin-backend     | 8010     | —        | 管理后台 API (FastAPI)   |
| `pc`               | procureping-pc                | 3001     | 3001     | PC 端前台 (Nuxt 3)       |
| `h5`               | procureping-h5                | 3002     | 3002     | H5 移动端前台 (Nuxt 3)   |
| `admin`            | procureping-admin             | 80       | 8082     | 管理后台前端 (Vue 3)     |
| `edge`             | procureping-edge              | 80       | 8083     | Nginx 反向代理入口       |

## 域名路由规则（edge nginx）

| 域名                    | 路径              | 后端服务          |
|-------------------------|-------------------|-------------------|
| `sanaoll.com`           | `/api/`           | backend:8000      |
| `sanaoll.com`           | `/static/uploads/`| backend:8000      |
| `sanaoll.com`           | `/`               | pc:3001 或 h5:3002（UA 分流）|
| `manager.sanaoll.com`   | `/api/`           | admin-backend:8010|
| `manager.sanaoll.com`   | `/static/uploads/`| backend:8000      |
| `manager.sanaoll.com`   | `/`               | admin:80          |

## 快速部署

### 1. 准备环境变量

```bash
cp deploy/env/.env.prod.example .env.prod
# 编辑 .env.prod，填写真实密码和域名
vim .env.prod
```

### 2. 一键部署

```bash
bash deploy/scripts/deploy.sh
```

脚本会自动：
- 创建 `data/` 目录结构（`prepare.sh`）
- 执行数据库迁移（`alembic upgrade head`）
- 构建并启动所有容器

### 3. 查看运行状态

```bash
docker compose --env-file .env.prod -f deploy/compose/docker-compose.prod.yml ps
```

## 迁移 / 快照

**导出快照**（含 SQL dump + uploads + 配置）：
```bash
bash deploy/scripts/export_snapshot.sh
```

**从快照恢复**（新服务器）：
```bash
bash deploy/scripts/restore_snapshot.sh
```

详见 `deploy/export/README.md`。

## 环境变量说明

| 变量                            | 说明                                               |
|---------------------------------|----------------------------------------------------|
| `POSTGRES_*`                    | 数据库连接信息                                     |
| `DATABASE_URL`                  | SQLAlchemy 异步连接串                              |
| `JWT_SECRET`                    | JWT 签名密钥（64 字符随机串）                      |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token 有效期（分钟）                      |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token 有效期（天）                         |
| `CORS_ORIGINS`                  | 允许跨域的来源，backend 与 admin-backend 共用      |
| `UPLOAD_STORAGE`                | 文件存储方式，固定 `local`                         |
| `UPLOAD_DIR`                    | 容器内上传目录，固定 `/data/uploads`               |
| `PUBLIC_FILE_BASE_URL`          | 上传文件的公开访问基础 URL                         |
| `NUXT_PUBLIC_API_BASE`          | PC / H5 前端运行时 API 基址                        |
| `NUXT_PUBLIC_APP_DOMAIN`        | 站点主域名                                         |

## 注意事项

- `.env.prod` **不提交到 Git**（已在 `.gitignore` 中排除）。
- `deploy/` 是生产部署目录，不是本地开发入口；本地开发请看根目录 `README.md`。
- 生产 compose 只自动执行数据库迁移，不自动执行本地 `backend/seed.py`。seed 会写入 demo/test 账号和测试目录数据，生产执行前必须确认。
- 生产环境必须关闭 `DEMO_MODE`，否则 demo 账号与前端 demo 辅助数据可能进入真实业务流。
- `data/` 目录挂载宿主机持久化数据，**迁移时记得备份**。
- 修改 nginx 配置后需重启 edge 容器：
  ```bash
  docker compose --env-file .env.prod -f deploy/compose/docker-compose.prod.yml restart edge
  ```

# DEPLOY SKILL (Linux, One-Click)

本文件是给 AI/自动化代理直接读取并执行的部署规范。  
目标：在 Linux 服务器一键部署 `sanaoll.com`（主站）和 `manager.sanaoll.com`（后台），并完成数据库初始化、迁移、持久化目录映射。

## 1. 部署目标

- 主站域名：`sanaoll.com`
- 后台域名：`manager.sanaoll.com`
- 反向代理：Nginx
- 路由策略：
  - `sanaoll.com` 按 User-Agent 分流：移动端 -> H5，PC -> PC 前端
  - `manager.sanaoll.com` -> Admin 前端
  - `/api/*` -> Backend
- 数据库：PostgreSQL（自动初始化 SQL + 自动迁移）
- 编排：Docker Compose 一键启动
- 持久化：数据库与上传文件（头像/KYC/目录化）

## 2. 必须使用的文件（已打包在仓库内）

- Compose：`deploy/compose/docker-compose.prod.yml`
- Nginx 主配置：`deploy/nginx/nginx.conf`
- Nginx 站点配置：`deploy/nginx/conf.d/sanaoll.conf`
- 环境变量模板：`deploy/env/.env.prod.example`
- SQL 初始化：`deploy/db/init/00-init.sql`
- 初始化目录脚本：`deploy/scripts/prepare.sh`
- 一键部署脚本：`deploy/scripts/deploy.sh`
- Admin 前端 Dockerfile：`deploy/docker/admin-frontend.Dockerfile`

## 3. 服务器前置要求

- Linux（Ubuntu/CentOS/Debian 均可）
- 已安装 Docker + Docker Compose plugin
- 防火墙放行：`80`（和 `443` 如需 HTTPS）

## 4. 一键部署流程（严格按顺序）

```bash
cd /opt/procureping
cp deploy/env/.env.prod.example .env.prod
```

编辑 `.env.prod`，至少修改：
- `POSTGRES_PASSWORD`
- `JWT_SECRET`

执行：

```bash
bash deploy/scripts/deploy.sh
```

脚本会自动：
- 创建持久化目录
- 拉起所有容器
- Backend 启动前执行 `alembic upgrade head`
- Backend 启动前只执行 `alembic upgrade head`。生产环境不要自动执行本地 `seed.py`，除非明确需要初始化测试/演示数据。
- PostgreSQL 首次启动执行 `deploy/db/init/00-init.sql`

## 4.1 默认数据库与 demo 数据

默认数据库连接参数（来自 `.env.prod`）：
- `POSTGRES_DB=procureping`
- `POSTGRES_USER=procureping`
- `POSTGRES_PASSWORD=change-this-strong-password`（上线前务必改）

本地开发 seed 会导入 demo 账户并默认设置 `DEMO_MODE=true`：
- `admin@procureping.local / Admin1234!`
- `superadmin@procureping.local / SuperAdmin1234!`
- `buyer@procureping.local / Buyer1234!`
- `supplier@procureping.local / Supplier1234!`
- `buyer@demo.procureping / 123`
- `supplier@demo.procureping / 123`
- `admin@procureping.com / admin123`

生产环境必须关闭模拟模式。若曾导入 demo 数据，至少在后台 Settings 或数据库中设置：

```env
DEMO_MODE=false
```

当前生产 compose 不会自动运行 `python seed.py`。如果 AI agent 需要初始化生产基础数据，必须先让用户确认是否允许写入测试账号/测试商品；未经确认不得执行 seed。

## 5. 持久化目录规范（主机）

- `/opt/procureping/data/postgres`
- `/opt/procureping/data/uploads/avatars`
- `/opt/procureping/data/uploads/kyc`
- `/opt/procureping/data/uploads/catalog`
- `/opt/procureping/data/uploads/messages`
- `/opt/procureping/data/uploads/misc`

说明：上传文件统一挂载到后端容器的 `/data/uploads`。

## 6. 路由与代理规则（Nginx）

- `sanaoll.com`
  - `/api/` -> backend:8000
  - `/static/uploads/` -> backend:8000/static/uploads/
  - `/` -> 移动 UA 到 h5:3002，否则到 pc:3001
- `manager.sanaoll.com`
  - `/api/` -> backend:8000
  - `/` -> admin:80

## 7. 验收命令

```bash
docker compose --env-file .env.prod -f deploy/compose/docker-compose.prod.yml ps
curl -I http://127.0.0.1/
curl -I -H "Host: manager.sanaoll.com" http://127.0.0.1/
```

## 8. AI 执行约束

- 不要改动已有业务代码框架，优先使用现有部署文件。
- 仅在以下场景允许修改部署配置：
  - 域名变更
  - 端口冲突
  - HTTPS 证书接入
- 若 `.env.prod` 缺失，必须先从模板复制，不得跳过。
- 若容器启动失败，先执行：

```bash
docker compose --env-file .env.prod -f deploy/compose/docker-compose.prod.yml logs --tail=200
```

并根据日志修复，不得直接删除数据卷。

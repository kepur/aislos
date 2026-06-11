# ProcurePing Admin Backend

独立后台管理服务端入口。该服务复用 `backend/app` 的数据库、模型和后台业务 router，但只暴露后台认证、后台用户信息和 `/admin/*` 运营管理 API。

## Local Run

```bash
cd admin-backend
PYTHONPATH=../backend uvicorn main:app --reload --port 8010
```

## Docker

从仓库根目录构建：

```bash
docker compose up admin-backend
```

默认端口：`8010`。

## API Scope

- `POST /auth/login`：仅允许 admin/staff 角色登录。
- `GET /auth/me`：当前后台用户。
- `GET /users/me`：兼容当前 `admin-frontend`。
- `/admin/*`：后台运营 API。
- `/admin/trust/*`：信誉值管理 API。

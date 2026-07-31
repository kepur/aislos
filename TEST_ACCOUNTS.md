# 本地测试账户与入口

更新：2026-06-11

## 前端入口

| 端 | 地址 | 说明 |
|----|------|------|
| PC 官网 / 采购 | http://localhost:4099 | 直连 dev server |
| PC（经 nginx） | http://localhost | 含 Portal Context |
| Cebu 采购 PC | http://cebu.localhost/cebu | nginx 注入 `X-Portal-Key: cebu` |
| H5 客户/现场/供应商 | http://localhost:4098 | Field: `/field/today` |
| 管理后台 | http://localhost:4097 | Settings → Demo Mode |
| Core API 文档 | http://localhost:8000/docs | |

## 一键初始化 Demo 数据

```bash
cd Ainerwise
docker exec ainerwise-backend-1 python -m scripts.seed_demo_environment
```

或在 **Admin → Settings** 点击 **Seed demo data & enable**。

## 账户密码

| 角色 | 邮箱 | 密码 | 用途 |
|------|------|------|------|
| **Super Admin** | `admin@ainerwise.com` | `admin123456` | 后台全权限（始终可登录） |
| **Demo 买家** | `demo@ainerwise.com` | `demo123` | PC/H5 客户、采购、假项目数据；**Demo 关闭时禁止登录** |
| Customer Owner | `customer_owner@example.com` | `customer123` | H5 客户门户 |
| Partner 公司 | `partner_owner@example.com` | `partner123` | H5 `/partner` |
| 现场安装工 | `installer@example.com` | `worker123` | H5 `/field/today` |
| 供应商 | `supplier@example.com` | `supplier123` | H5 供应商 / Commerce |
| Cebu Demo 供应商 | `demo-supplier@ainerwise.com` | `supplier123` | Commerce 匹配/报价；**Demo 关闭时禁止登录** |
| 项目经理 | `pm@example.com` | `pm123456` | Admin Field Ops |

## Demo 模式（对标 Cebu `DEMO_MODE`）

- **开关**：Admin → Settings → Demo Mode（写入数据库，重启后仍有效）
- **API**：`GET/PATCH /api/v1/demo-mode`（Admin 用 `/demo-mode/admin`）
- **环境默认**：`.env` 中 `DEMO_MODE_ENABLED=true`
- **关闭后**：`demo@ainerwise.com`、`demo-supplier@ainerwise.com` 无法登录；前台隐藏一键 Demo 入口

## Demo 假数据包含

- Smart building / StorageGuard 示例 Lead & Project（`create_demo_buyer`）
- Portal 角色测试用户 + Grant
- Cebu 供应商目录样例（`Cebu LED Starter Kit`）

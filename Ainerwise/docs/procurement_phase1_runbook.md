# Procurement Phase 1 运行手册

Phase 1 采购栏目（C01–C09）端到端验证与本地演示指南。实现目录：`Ainerwise/`。

## 前置条件

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise
cp .env.example .env   # 首次
docker compose up -d
```

| 服务 | 地址 |
|------|------|
| Backend API | http://localhost:8000/docs |
| AISLOS Website（采购 Workspace） | http://localhost:4099 |
| Cebu 品牌（本地模拟） | 浏览器访问含 `cebu` 的 hostname，或 nginx 子域 |

演示账号（见 `docs/PORTAL_FIELD_SERVICE_V1_TASKS.md`）：

- 买家：`demo@ainerwise.com` / `demo123`
- 管理员：`admin@ainerwise.com` / `admin123456`

Alembic head：`032`（`commercial_snapshots_procurement_rfq`）。

## 自动化验证（发布闸门）

```bash
# 1. 迁移
cd Ainerwise/backend
docker compose exec backend sh -c "cd /app && alembic heads"
# 期望：032 (head) 且仅一个 head

# 2. 采购专项回归
docker compose exec backend sh -c "cd /app && pytest -q tests/test_procurement_*.py"
# 期望：82 passed, 1 skipped

# 3. E2E 闸门（C09）
docker compose exec backend sh -c "cd /app && pytest -q tests/test_procurement_e2e.py"
# 期望：8 passed

# 4. Backend 全量（采购外已知限制见下）
docker compose exec backend sh -c "cd /app && pytest -q"

# 5. AI Orchestrator
cd ../ai_orchestrator
docker compose exec ai-orchestrator sh -c "cd /app && pytest -q"

# 6. 前端双品牌构建
cd ../frontend-pc
npm run build
```

### 已知限制

1. **Docker bind mount**：若 `frontend-pc` 容器仍挂载旧路径，`:4099` dev 可能看不到新页面。用本地 `npm run build` + `node .output/server/index.mjs` 或按 SP02 重建容器。
2. **Redis outbox 测试**：`test_outbox_relay_publishes_to_redis_stream` 依赖 Redis relay，部分环境可能失败（与采购无关）。
3. **共享测试库**：采购测试会轮换 Portal Policy 版本；若 `test_procurement_portal_policy` 失败，在容器内重置默认策略：
   ```bash
   docker compose exec backend python -c "
   import asyncio
   from app.db.session import async_session_factory
   from app.services.portal_policy import retire_active_policy, ensure_default_policies
   async def main():
       async with async_session_factory() as db:
           for pk in ('aislos', 'cebu'):
               await retire_active_policy(db, pk)
           await ensure_default_policies(db)
           await db.commit()
   asyncio.run(main())"
   ```

## 浏览器：场景 A（AISLOS Villa Managed）

1. 打开 http://localhost:4099 ，登录买家账号。
2. 进入 **Procurement** → `/procurement`。
3. 新建项目：**Villa Smart Home**，国家 PH，标题如 `300㎡ Villa Smart Home`。
4. 确认品牌为 AISLOS（翠绿主题），默认模式 **managed**，价格规则 **customer_totals_only**。
5. 在 Facts 步骤运行 **Analyze**；低置信度时应出现追问（`needs_information`）。
6. 确认全部 Facts 后再次 Analyze → 三档方案 + `review_ready`。
7. 提交 BOQ Review，管理员在 Admin 审批后 Freeze BOQ。
8. **Generate Packages** → 应拆为 equipment / installation / maintenance，均为 **managed**。
9. 填写 Commercial Terms，对每个包 **Publish RFQ** → 项目状态 `rfq_published`，RFQ `portal_key=aislos`。

## 浏览器：场景 B（Cebu Small Hotel Self-service）

1. 使用 Cebu Portal 上下文访问（生产由 nginx 注入 `X-Portal-Key: cebu`；本地可改 hosts 为 `cebu.localhost` 并走对应网关，或依赖 API 返回的 policy）。
2. 新建项目：**Small Hotel Smart Upgrade**，30-room 描述。
3. 确认 **self_service** 模式与 **line_estimates** 价格可见性（橙色 Cebu 主题）。
4. 确认 Facts → Analyze → `estimate_ready` 或 `review_ready`。
5. Review + Freeze → Generate Packages：
   - equipment → **self_service**
   - installation / maintenance → **managed**
6. Publish RFQ → `portal_key=cebu`，Commercial Snapshot 含 line estimate 策略。

## API 快速冒烟

所有采购 API 前缀：`/api/v1/procurement`，需 JWT + Header `X-Portal-Key: aislos|cebu`。

```bash
TOKEN="<buyer_jwt>"
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Portal-Key: aislos" \
  http://localhost:8000/api/v1/procurement/portal-policy | jq .

curl -s -H "Authorization: Bearer $TOKEN" -H "X-Portal-Key: aislos" \
  http://localhost:8000/api/v1/procurement/projects | jq .
```

## E2E 测试覆盖摘要（C09）

| 类别 | 测试 |
|------|------|
| 场景 A | `test_e2e_aislos_villa_managed_full_flow` |
| 场景 B | `test_e2e_cebu_small_hotel_self_service_full_flow` |
| 跨 Portal 404 | `test_e2e_cross_portal_read_forbidden` |
| 冻结门禁 | `test_e2e_freeze_gates_enforced` |
| Frozen BOQ 不可变 | `test_e2e_frozen_boq_immutable_via_new_draft` |
| Snapshot 不可变/无泄漏 | `test_e2e_commercial_snapshot_immutable_and_no_leak` |
| 发布缺条款回滚 | `test_e2e_publish_without_commercial_terms_rolls_back` |
| Outbox 品牌 | `test_e2e_outbox_branding_on_publish` |

Fixtures：`backend/tests/fixtures/procurement_e2e.py`。

## Phase 1 明确不做

Office 采购、Supplier Bid、Award、Order、Escrow、Cebu 后端合并等 — 见 `PROCUREMENT_PHASE1_EXECUTION_TASKS.md` §6。

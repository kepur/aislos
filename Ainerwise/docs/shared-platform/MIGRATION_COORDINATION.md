# Alembic Migration Coordination

日期：2026-06-11  
适用范围：Ainerwise Core、Procurement Phase 1、Marketing Integration V4、Shared Platform

## 1. 全局规则

1. **任意时刻最多一个 Agent 拥有 migration 写权限。**
2. 创建 migration 前必须执行 `alembic heads`，且**只能有一个 head**。
3. 每个 revision 必须明确 `down_revision`。
4. migration 完成后必须执行：`upgrade` → `downgrade`（一步或到父版本）→ `upgrade`，并再次确认单一 head。
5. **Cebu migration 链不得合并进 Ainerwise migration 链。**
6. 并行任务中，凡涉及相同文件或 migration 目录的工作必须串行。

## 2. 当前状态

| 链 | 路径 | 当前 head | 单一 head |
|---|---|---|:---:|
| Ainerwise Core | `Ainerwise/backend/alembic/versions/` | `033` | ✅ |
| Cebu Legacy | （独立仓库/链，未并入） | — | 独立 |

### 近期 revision 归属

| Revision | 栏目 | 说明 |
|---|---|---|
| 024 | Procurement C01 | portal_policies |
| 025–027 | Marketing MI01–MI04 | creative briefs / media requests |
| 028 | Procurement C02 | audit_logs 扩展 |
| 029–032 | Procurement C03–C07 | projects / boq / packages / RFQ |
| 033 | Shared Platform SP03/SP04 | legacy bridge + identity mappings |

## 3. 领取 migration 写锁流程

```text
1. 确认 alembic heads → 仅一个 head
2. 在任务板标注「migration 写锁：{栏目 ID} / {Agent}」
3. 创建 revision，down_revision = 当前 head
4. alembic upgrade head
5. alembic downgrade {parent}
6. alembic upgrade head
7. alembic heads → 仍仅一个 head
8. 运行栏目测试 + 相关回归
9. 释放写锁，标记 READY_FOR_VERIFY
```

## 4. 禁止事项

- 禁止两个 Agent 同时 `alembic revision`
- 禁止未验证 head 数量即提交 PR
- 禁止将 Cebu alembic versions 复制进 `Ainerwise/backend/alembic/versions/`
- 禁止通过修改测试掩盖 migration 或业务缺陷

## 5. 与 Shared Platform 的衔接

- **SP01**：不创建 migration（文档 only）
- **SP02**：可新增 dev profile 文档与 compose overlay，database/role 隔离需新 migration 时单独领取写锁
- **SP04+**：数据迁移脚本可并存，但 schema migration 仍遵守本文件

## 6. 验证命令（标准）

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/backend
alembic heads
alembic current
# 栏目完成后：
alembic downgrade -1   # 或 downgrade <parent>
alembic upgrade head
alembic heads
```

## 7. 冲突处理

若 `alembic heads` 返回多个 head：

1. **立即停止**所有 migration 创建
2. 由单一 Agent 合并或重定 down_revision
3. 重新执行 upgrade/downgrade 循环
4. 记录冲突原因到相关任务板交付记录

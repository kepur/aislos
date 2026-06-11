# SP05: 采购域 Parity 与 Legacy 退役

## 写入路径（已冻结）

| 能力 | 权威实现 | Legacy Cebu |
|------|----------|-------------|
| Portal Policy / 双品牌 | Ainerwise Core C01 | 不写入 |
| Procurement Project / Facts | Core C03 | Bridge → Lead |
| BOQ / Freeze / Packages | Core C04–C06 | 不双写 |
| Commercial Snapshot / RFQ | Core C07 | 不双写 |
| Workspace UI | frontend-pc C08 | 品牌由 Portal 注入 |

## 验证闸门

```bash
./scripts/shared-platform/verify-procurement-parity.sh
```

## Legacy 退役条件（SP05 出口）

- [ ] Bridge 事件与 Core Lead/CRM 核对通过
- [ ] Cebu 前端可切换 Core API（按模块）
- [ ] `cebu` database 只读观察 ≥ 2 周
- [ ] 用户批准停用 `cebu-backend` compose profile

## 禁止

- 永久双写 Intent/Order 到 Core 与 Legacy
- 合并 Alembic 链

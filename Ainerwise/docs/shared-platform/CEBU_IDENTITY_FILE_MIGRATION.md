# SP04: Cebu 身份与文件迁移

## 身份映射

- 表：`legacy_identity_mappings`（migration `033`）
- **禁止**共享 Cebu JWT Secret 与 Core `SECRET_KEY`
- Legacy 用户通过 Bridge 事件 `legacy.identity.map` 登记映射
- Core 成为长期唯一 Token issuer（SSO exchange 在 Phase 2 扩展）

## 文件迁移

| 阶段 | 来源 | 目标 |
|------|------|------|
| 1 | `CebuProjects/backend/uploads/` | MinIO `cebu-import/legacy-uploads/` |
| 2 | 校验 checksum + owner | `FileAsset` 记录（SP04+ 脚本） |
| 3 | 观察期 | 只读 legacy 文件路径 |
| 4 | 退役 | 删除本地 uploads |

```bash
./scripts/shared-platform/init-minio-buckets.sh
./scripts/shared-platform/migrate-cebu-uploads-to-minio.sh
```

## 隔离

- Bucket `cebu-import` 仅迁移用途，非长期业务入口
- 应用使用 scoped service account，不用 MinIO root

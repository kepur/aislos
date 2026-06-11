# SP06: 配额、监控、备份与恢复

## 备份

| 资源 | 脚本 | RPO（dev 参考） |
|------|------|----------------|
| PostgreSQL `ainerwise` + `cebu` | `backup-postgres.sh` | 24h |
| MinIO | `mc mirror`（生产 cron） | 24h |

```bash
./scripts/shared-platform/backup-postgres.sh
./scripts/shared-platform/restore-drill.sh backups/<stamp>/ainerwise.dump
```

## 监控标签（生产）

`service`, `environment`, `portal`, `workspace`, `region`, `integration_client`, `correlation_id`

## 配额

- Integration Client / Legacy Bridge：超限返回 **429**（Marketing Integration 已示范）
- Legacy Bridge：`LEGACY_BRIDGE_MAX_SKEW_SECONDS` + 幂等键防重放

## 恢复演练

季度执行 `restore-drill.sh`，记录 RPO/RTO 于运维台账。

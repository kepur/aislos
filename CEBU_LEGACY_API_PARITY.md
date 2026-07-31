# Cebu Legacy API -> AinerWise Core Cutover

Updated: 2026-06-12

Status: `CORE_ACTIVE_LEGACY_RETIREMENT_NOT_APPROVED`

CebuProjects remains a read-only reference and rollback source. New writes,
permissions, migrations, and portal experiences belong to AinerWise Core.
Legacy retirement is forbidden until the zero-loss ledger and independent
verification gates pass.

## Active Core Contracts

| Cebu capability | AinerWise Core contract |
|---|---|
| Auth and account | `/api/v1/auth/*`, `/api/v1/users/me` |
| Intent / procurement request | `/api/v1/commerce/procurement-requests*` |
| Supplier candidates and bind | `/api/v1/commerce/procurement-requests/{id}/supplier-candidates*` |
| Offer submit / withdraw / award | `/api/v1/commerce/procurement-requests/{id}/offers`, `/api/v1/commerce/offers/{id}/*` |
| Orders, delivery, disputes, reviews | `/api/v1/commerce/orders*` |
| Messages and notifications | `/api/v1/commerce/threads*`, `/api/v1/commerce/notifications*` |
| Wallet, deposits, shipping, ads, escrow, payout | `/api/v1/cebu-trade/*` |
| KYC and verification | `/api/v1/kyc/*`, `/api/v1/admin/kyc/*` |
| Cebu Admin workbench | `/api/v1/admin/cebu/*`, `/api/v1/admin/cebu-trade/*` |
| Historical batch migration | `POST /api/v1/admin/cebu/migrations/import` |
| Buyer Project facts and metrics | `/api/v1/buyer/projects/{id}/metrics` |
| Buyer Project estimate and versioned BOQ | `/api/v1/buyer/projects/{id}/price-estimate`, `/api/v1/buyer/projects/{id}/report*` |
| Trust score history | `/api/v1/admin/cebu/trust-profiles/{id}/events` |

`/api/v1/cebu-compat/*` remains a temporary Intent compatibility alias. It is
not the data owner and must not become a permanent second API.

## Historical Migration

The importer is admin-only, dependency ordered, idempotent, and audited.

- Mapped objects are written into typed Core tables.
- Every source object stores a sanitized source snapshot and checksum.
- Passwords, password hashes, tokens, and secrets are removed.
- Imported users receive unusable random passwords and must reset access.
- Every currently known Cebu entity group has a typed importer. Unknown future
  entity groups are retained as `archived` migration records instead of being
  ignored.
- Batch-key checksum conflicts are rejected.

Typed mappings include companies, users, regions, branches, service areas,
categories, catalog items, Buyer Projects, metrics, price snapshots, reports,
report versions/columns/rows/change logs, intents, offers, orders, transaction
reviews, wallet/trade objects, delivery, disputes, trust profiles and score
events, payment configuration/quotes/settlements/reconciliation, KYC
documents/analysis/reviews/media risk, notifications/templates, messages,
admin notes, platform settings, audit logs, and backup schedules/jobs.

Buyer Project Core now provides real requirement facts, three-tier estimates,
versioned reports, row selection, and audited BOQ freeze. Automatic supplier
trust mutations also create typed score history events.

## Legacy Bridge

The event bridge is allowed only during the controlled dual-write/cutover
window. Current supported events include procurement request creation and
publish, order completion, and dispute opening. It does not authorize direct
new writes to the Legacy database.

## Release Gates

- No Cebu legacy service shutdown without founder-approved retirement.
- No platform custody of customer funds; PSP/webhook and ledger rules remain
  authoritative.
- All object operations must enforce user/company/workspace/portal/region
  boundaries.
- Final cutover requires migration replay, reconciliation, browser E2E,
  negative permission tests, rollback rehearsal, and independent verification.

## Repeatable Checks

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise
docker compose exec -T backend pytest -q
docker compose exec -T backend alembic current
docker compose exec -T backend alembic check
docker compose exec -T backend python - <<'PY'
from app.services.legacy_migration import ENTITY_ORDER, IMPORTERS
print(sorted(set(ENTITY_ORDER) - set(IMPORTERS)))
PY

cd /Users/mac/Code_Start/Aislos
bash scripts/parity/verify_feature_parity_ledger.sh
```

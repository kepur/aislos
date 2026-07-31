# ZL10 Shared Core, Middleware, Identity, Migration, And Compatibility Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_ZL04_ZL05_ZL06_ZL07_ZL08_ZL09_INDEPENDENT_VERIFY`

This is implementation evidence only. ZL10 remains `LOCKED`; the implementing
Agent does not authorize `READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Converged Core business notifications onto the transactional Outbox:
  Lead, Inquiry, Vendor, Product, internal AI intake, AI completion, lifecycle
  automation, and daily briefing no longer call the legacy immediate-commit
  integration helper.
- Added explicit transaction-scoped CRUD creation so business rows, audit
  records, and Outbox events can commit or roll back together without changing
  historical CRUD behavior.
- Added a scheduled Telegram Outbox dispatcher with concurrent-worker locking;
  external delivery now occurs after the business transaction commits.
- Split Telegram delivery into flush-only and legacy/admin commit-owning paths,
  removing hidden commits from new Core flows.
- Collapsed Commerce Dispute notification and domain publication into one
  shared Outbox event instead of producing duplicate events.
- Added non-destructive Cebu Cutover Readiness reporting:
  `GET /api/v1/admin/cebu/migrations/readiness`.
- Added Admin migration readiness cards and explicit blockers for failed rows,
  archive-only objects, typed objects without Core mappings, incomplete
  identities, independent verification, and founder approval.
- Kept Legacy retirement impossible from the UI/API. CebuProjects remains a
  read-only reference until all release gates and founder approval pass.
- Made the non-authoritative Legacy Redis mirror best-effort so a mirror outage
  cannot turn an already committed Core write into a false failure response.
- Updated the shared resource manifest to the observed canonical runtime:
  all running source bind mounts use `Aislos/Ainerwise`, Alembic is at single
  head `055`, and the Core stream is `ainerwise:stream:events`.

## Shared Boundaries Preserved

- Ainerwise Core remains the only target business-data owner.
- CebuProjects was not used as a runtime dependency or migration target.
- Legacy and Core migration chains remain separate.
- AinerN2D remains external and only consumes standard Marketing API/SDK
  contracts.
- No destructive Legacy stop, delete, DNS switch, or retirement action was
  added.

## Verification Evidence

```text
ZL10 + Legacy/Cebu focused tests: 12 passed
shared event/middleware regression group: 38 passed
backend full suite: 363 passed, 3 warnings
frontend-admin production build: passed with workspace Node 24.14.0
frontend-pc production build: passed with workspace Node 24.14.0
frontend-h5 production build: passed with workspace Node 24.14.0
alembic current: 055 (head)
alembic check: No new upgrade operations detected
feature parity ledger: 5176 entries
runtime API coverage: 676 / 676
source fingerprint: see docs/parity/feature-parity-ledger.json
git diff --check: passed
```

## Remaining Release Gates

- Independent verification must replay a representative production Cebu export,
  reconcile counts and ownership, and rehearse rollback.
- Archive-only objects must receive typed Core ownership before
  `implementation_ready` can become true.
- Cebu database and file sources require a documented read-only observation
  period before retirement.
- Founder approval is required before any Legacy service, data, route, or DNS
  retirement.
- ZL01 through ZL09 must be independently verified before ZL10 can be unlocked.

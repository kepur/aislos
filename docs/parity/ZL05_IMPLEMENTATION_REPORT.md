# ZL05 Cebu Admin, API, Tasks, And Data Migration Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_ZL04_INDEPENDENT_VERIFY`

This is implementation evidence only. ZL05 remains `LOCKED`; the implementing
Agent does not authorize `READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Migrated Cebu Admin into the shared `frontend-admin` build with distinct
  `admin_cebu` portal grants, menu, routes, and workbench.
- Added real Core-backed admin operations for users, companies, requests,
  offers, orders, disputes, risk, trust, notifications, audit, shipping,
  deposits, ads, escrow, payouts, KYC, verification, payments, and backups.
- Added audit events for critical Cebu Admin writes.
- Added real backup schedules, manual archive generation, authenticated
  download, retention metadata, and Celery execution.
- Added admin-only historical migration runs and row-level migration evidence.
- Added dependency-ordered typed migration for primary Cebu commerce, Buyer
  Project, KYC, review, risk, message, and notification objects.
- Added typed importers for every currently known Cebu migration entity group;
  the known archive-only group check returns an empty list. Unknown future
  groups still receive sanitized archive preservation. Legacy credentials and
  secrets are never stored.
- Added versioned Buyer Project reports, metrics, three-tier price estimates,
  row selection, BOQ freeze, and PC/H5 workspaces backed by Core APIs.
- Added typed payment configuration, quote, settlement, reconciliation,
  notification template, admin note, platform setting, branch, service-area,
  project metric template, KYC media, and trust event workflows.
- Added automatic trust score events for order completion, dispute opening,
  review submission, and audited manual adjustment.
- Kept CebuProjects unchanged as a reference source.

## Core Endpoints

- `GET/POST /admin/cebu/migrations*`
- `GET/PATCH /admin/cebu/users*`
- `GET/PATCH /admin/cebu/companies*`
- `GET/PATCH /admin/cebu/procurement-requests*`
- `GET/PATCH /admin/cebu/offers*`
- `GET/PATCH /admin/cebu/orders*`
- `GET/POST /admin/cebu/disputes*`
- `GET/PATCH /admin/cebu/risk-flags*`
- `POST /admin/cebu/trust-profiles/{id}/adjust`
- `GET /admin/cebu/trust-profiles/{id}/events`
- `GET/PATCH /buyer/projects/{id}/metrics`
- `POST /buyer/projects/{id}/price-estimate`
- `GET/POST/PATCH /buyer/projects/{id}/report*`
- `GET/POST/PATCH/DELETE /admin/cebu/backups*`
- `GET/POST/PATCH/DELETE /admin/cebu-trade/*`
- `GET/POST /admin/kyc/*`

## Verification Evidence

```text
historical migration dependency-chain test: passed (63 linked typed objects)
known Cebu entity groups without typed importer: []
typed historical importer count: 61
automatic trust event focused tests: 4 passed
backend full suite: 353 passed, 3 warnings
alembic current: 055 (head)
alembic check: No new upgrade operations detected
frontend-pc production build: passed
frontend-h5 production build: passed
frontend-admin production build: passed
parity ledger: 5176 entries
runtime API coverage: 676 / 676
Cebu visible baseline: 59 PC / 41 H5 / 24 Admin
source fingerprint: see docs/parity/feature-parity-ledger.json
```

## Known Gaps

- Unknown future Cebu object groups intentionally fall back to sanitized
  archives until an explicit typed importer is added.
- Full behavioral parity for every Cebu screen, operation, state machine, and
  exception flow remains subject to the ZL01-ZL04 dependency gates and
  independent verification.
- Independent browser/E2E comparison and migration replay against a production
  Cebu export, reconciliation, and rollback rehearsal remain required.
- ZL01 through ZL04 must be independently verified before ZL05 can be unlocked.

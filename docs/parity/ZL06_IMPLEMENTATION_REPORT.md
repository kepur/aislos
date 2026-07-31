# ZL06 AinerWise Consumer And Customer Workspace Implementation Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_ZL04_ZL05_INDEPENDENT_VERIFY`

This is implementation evidence only. ZL06 remains `LOCKED`; the implementing
Agent does not authorize `READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Kept AinerWise as the public Consumer Platform and added a distinct
  Customer Workspace PC and H5 experience inside the existing physical builds.
- Added a real `customer-workspace` PC layout and `customer-mobile` H5 layout.
- Added Customer Workspace pages for requirements, procurement, approvals,
  projects, installations, field evidence, installed assets, tickets, and
  profile.
- Replaced the broken Customer requirement-detail link with a real
  ownership-scoped `GET /leads/my/{id}` contract and detail page.
- Added customer-safe Core projections for workspace summary, pending
  quote/delivery approvals, installations, installation detail/evidence, and
  assets.
- Hardened Quote detail, response, and PDF access so customers cannot read or
  modify another company's Quote. Customer transitions are limited to accept,
  reject, or ask questions while a Quote is awaiting a response.
- Customer installation APIs never expose unrelated workspace packages or
  internal worker assignments.

## Core APIs

- `GET /customer/workspace/summary`
- `GET /customer/workspace/approvals`
- `GET /customer/workspace/installations`
- `GET /customer/workspace/installations/{package_id}`
- `GET /customer/workspace/assets`
- `GET /leads/my/{id}`

## Routes

PC:

- `/portal`
- `/portal/leads` and `/portal/leads/{id}`
- `/portal/procurement`
- `/portal/approvals`
- `/portal/projects` and `/portal/projects/{id}`
- `/portal/installations` and `/portal/installations/{id}`
- `/portal/assets`
- `/portal/tickets`
- `/portal/profile`

H5:

- `/dashboard`
- `/projects` and `/projects/{id}`
- `/customer/approvals`
- `/customer/installations` and `/customer/installations/{id}`
- `/customer/assets`

## Verification Evidence

```text
Customer + Field + security focused tests: 11 passed
frontend-pc production build: passed with workspace Node 24.14.0
frontend-h5 production build: passed with workspace Node 24.14.0
frontend-admin production build: passed with workspace Node 24.14.0
alembic current: 055 (head)
alembic check: No new upgrade operations detected
feature parity ledger: 5176 entries
runtime API coverage: 676 / 676
parity implementation checks: passed
git diff --check: passed
```

## Known Gaps And Dependency Gates

- Independent browser E2E must still verify Portal switching, responsive
  layouts, quote response, delivery acceptance, evidence display, and asset
  visibility.
- Customer approvals currently cover Quote response and Commerce delivery
  acceptance. Additional future approval types must use the same ownership
  projection rather than expose internal Admin APIs.
- ZL01 through ZL05 must be independently verified before ZL06 can be unlocked.

# ZL11 Full Role, Portal, And Zero-Loss Release Gate Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_ZL04_ZL05_ZL06_ZL07_ZL08_ZL09_ZL10_INDEPENDENT_VERIFY`

This is implementation evidence only. ZL11 remains `LOCKED`; the implementing
Agent does not authorize `READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Removed PC/H5 Products demo and coming-soon fallback behavior. API failures,
  loading, empty results, and retry are now explicit and cannot masquerade as
  a working catalog.
- Added real Supplier Team management to Core and both Supplier PC/H5:
  same-company invitation, inactive-member visibility, deactivate/restore,
  Portal Membership/Grant suspension, audit logging, and cross-company denial.
- Added the scoped `marketing_operator` role and role-derived access to
  Marketing PC/H5 only. Marketing, Creative Brief, and Media Integration admin
  APIs now accept the scoped role while unrelated Admin APIs reject it.
- Closed public role escalation: self-registration is restricted to buyer,
  vendor, developer, and service_partner. Internal staff and worker roles
  require administrator invitation.
- Replaced ambiguous permission tests with exact `401` unauthenticated and
  `403` authenticated-but-forbidden assertions.
- Refreshed the runtime API manifest and zero-loss parity ledger.
- Aligned scoped Sales, Project Manager, Finance, and Marketing workbench
  roles with their Core APIs, Portal Grants, login flow, and route manifests.
- Closed the unbound-project `None == None` ownership bypass and added exact
  cross-role positive/negative tests.
- Made protected Portal middleware fail closed across PC, H5, and Admin when
  Portal access cannot be verified.
- Removed silent empty-state failures from primary Admin dashboard, Companies,
  Categories, Products, Vendors, Leads, and Solutions workbenches.
- Corrected implemented Portal gap tracking to `READY_FOR_VERIFY` and fixed the
  Cebu Admin logical key to `admin_cebu`.

## Verification Evidence

```text
Supplier workspace focused test: 1 passed
Marketing V4/scoped-role regression group: 40 passed
Security focused regression group: 8 passed
backend full suite: 367 passed, 3 warnings
frontend-admin production build: passed with workspace Node 24.14.0
frontend-pc production build: passed with workspace Node 24.14.0
frontend-h5 production build: passed with workspace Node 24.14.0
alembic current: 055 (head)
alembic check: No new upgrade operations detected
feature parity ledger: 5176 entries
runtime API coverage: 676 / 676
test quality risks: none detected
git diff --check: passed
```

## Remaining Release Gates

- The six planned Ainerwise Portal gates remain `READY_FOR_VERIFY` until an independent
  verifier performs browser E2E, distinct layout/menu checks, unauthorized
  route rejection, and production-build replay.
- CebuProjects remains read-only. Its static demo dependencies remain source
  risks until each migrated Core target is independently verified.
- Representative production Cebu export replay, reconciliation, rollback
  rehearsal, read-only observation, and founder retirement approval remain
  mandatory.
- ZL01 through ZL10 must be independently verified in dependency order before
  ZL11 can be unlocked.

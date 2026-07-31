# ZL02 Implementation Report

Status: `IMPLEMENTED_AWAITING_ZL01_INDEPENDENT_VERIFY`

This report records implementation evidence only. ZL02 remains `LOCKED` on the
task board until an independent Agent verifies ZL01 and unlocks it.

## Delivered

- Added the final 15 logical Portal keys for Consumer, Customer, Cebu Buyer,
  Supplier, Partner Company, Marketing, Field Worker, Crew Lead, and Kiosk.
- Preserved previous Portal keys as directly resolvable compatibility entries
  while hiding superseded duplicates from normal portal pickers.
- Added Portal-scoped grant uniqueness with `NULLS NOT DISTINCT`.
- Enforced active Membership status, effective dates, and active Workspace
  status before Portal discovery, switching, and object grants.
- Added registration and role-change synchronization for Memberships and
  Portal Grants, including revocation of obsolete role-derived grants.
- Added migrations `041` and `042` for grant scope and existing-account
  backfill.
- Added shared Portal/Workspace switchers to `frontend-pc`, `frontend-h5`, and
  `frontend-admin`.
- Replaced legacy redirect-only middleware with Manifest and grant-aware route
  enforcement. Customer PC routes remain in `frontend-pc`; unauthorized H5
  roles fail closed.

## Verification Evidence

```text
backend full suite: 346 passed
frontend-pc production build: passed
frontend-h5 production build: passed
frontend-admin production build: passed
alembic current: 044 (head)
alembic check: No new upgrade operations detected
```

Browser checks:

- Admin login showed final workbench Portal picker.
- Switching `admin_executive` to `marketing_pc` navigated to `/marketing` and
  changed the sidebar/menu to the Marketing manifest.
- An admin session opening Field Worker H5 was redirected to
  `/access-denied`.

Independent verification is still required before changing ZL02 to
`READY_FOR_VERIFY` or `VERIFIED`.

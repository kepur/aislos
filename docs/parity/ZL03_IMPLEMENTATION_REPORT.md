# ZL03 Cebu Buyer/Public PC + H5 Implementation Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_INDEPENDENT_VERIFY`

This report records implementation evidence only. ZL03 remains `LOCKED` on the
task board because ZL01 has not been independently verified and ZL02 has not
been independently unlocked. The implementing Agent does not authorize
`READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Preserved the original Cebu Buyer PC routes through compatibility aliases
  while adding the final `/cebu/buyer/**` route family.
- Added real Core-backed PC and H5 Buyer experiences for requests, offers,
  orders, deliveries, messages, disputes, payment ledger, notifications,
  company profile, team, AI procurement projects, and price watchlist.
- Added anonymous public category and supplier-listing APIs and public Cebu
  marketplace pages.
- Added buyer-scoped read APIs for offers, disputes, payment ledger, messages,
  account, team, and watchlist. Cross-user access is rejected by object-level
  authorization.
- Added original Cebu authentication compatibility:
  - PC `/register-role`, `/register-buyer`, and `/forgot-password`.
  - H5 `/auth/login`, `/auth/register`, and `/auth/reset-password`.
- Replaced the original Cebu reset-password UI-only gap with a real one-time,
  hashed, 30-minute password reset token flow. Requests do not reveal whether
  an account exists; consumed tokens cannot be reused.
- Added real H5 account pages for `/profile/edit`, `/profile/company`,
  `/profile/change-password`, `/settings/language`, and
  `/settings/notifications`.
- Added self-service `PATCH /users/me`, notification preference persistence,
  and post-registration company profile creation for individual buyers.
- Updated Portal Manifest and route middleware so public, Buyer, auth, profile,
  and settings routes resolve to the correct logical Portal.

## Core Changes

- Migration `043`: buyer watchlist.
- Migration `044`: password reset tokens.
- Public commerce:
  - `GET /commerce/public/category-schemas`
  - `GET /commerce/public/listings`
  - `GET /commerce/public/listings/{listing_id}`
- Buyer commerce:
  - buyer offers, orders, deliveries, disputes, payment ledger, messages,
    notifications, account, team, projects, and watchlist APIs.
- Account and authentication:
  - `PATCH /users/me`
  - `POST /auth/request-password-reset`
  - `POST /auth/reset-password`
  - existing `PUT /auth/change-password` now enforces an eight-character
    minimum.

## Verification Evidence

```text
targeted Buyer/auth tests: 6 passed
backend full suite: 347 passed
frontend-pc production build: passed with Node 22.14.0
frontend-h5 production build: passed with Node 22.14.0
frontend-admin production build: passed with Node 22.14.0
alembic current: 044 (head)
alembic check: No new upgrade operations detected
parity ledger: 4630 entries
runtime API coverage: 609 / 609
Cebu visible baseline: 59 PC / 41 H5 / 24 Admin
```

The Browser plugin could not execute the local-page action because of its
security policy. Browser evidence is therefore still required from an
independent verifier; production builds and API tests are not represented as a
substitute for visual or interaction verification.

## Dependency And Remaining Gates

- ZL01 must be independently verified before ZL02 can be unlocked.
- ZL02 must then receive independent verification before ZL03 can be unlocked.
- ZL03 still requires independent browser/E2E comparison against the original
  Cebu Buyer/Public experiences.
- Supplier registration, supplier onboarding, Supplier PC/H5, Cebu Admin, and
  legacy data migration belong to ZL04/ZL05 and are not claimed by this report.

# ZL04 Cebu Supplier PC + H5 Implementation Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_INDEPENDENT_VERIFY`

This report records implementation evidence only. ZL04 remains `LOCKED` on the
task board. The implementing Agent does not authorize `READY_FOR_VERIFY` or
`VERIFIED`.

## Delivered

- Preserved and migrated every original Cebu Supplier PC and H5 route into the
  shared `frontend-pc` and `frontend-h5` builds.
- Added distinct Supplier layouts, menus, portal grants, onboarding, dashboard,
  pings, catalog, offers, orders, messages, notifications, payouts, campaigns,
  reviews, team, settings, and trigger-preference experiences.
- Replaced static supplier pages with Core-backed commerce APIs and persistent
  data.
- Added Supplier account and team reads, supplier-scoped dashboard metrics,
  matching procurement pings, offer submission and withdrawal, listing CRUD,
  transaction reviews, and private supplier catalog isolation.
- Enforced company ownership on Supplier listings, offers, orders, and account
  operations. A Supplier cannot impersonate or read another Supplier company.
- Kept one physical PC build and one physical H5 build; Supplier is a logical
  Portal generated from Membership, Portal Grant, Manifest, routes, layout,
  menu, and permission.

## Core APIs

- `GET/PATCH /commerce/supplier-account`
- `GET /commerce/supplier-team`
- `GET /commerce/supplier-dashboard`
- `GET /commerce/supplier-pings`
- `GET /commerce/supplier-offers`
- `POST /commerce/offers/{offer_id}/withdraw`
- `GET /commerce/supplier-reviews`
- `GET/POST /commerce/supplier-listings`
- `PATCH/DELETE /commerce/supplier-listings/{listing_id}`

## Verification Evidence

```text
Supplier + security boundary tests: 18 passed
backend full suite: 350 passed
frontend-pc production build: passed
frontend-h5 production build: passed
parity ledger: 4630 entries
runtime API coverage: 609 / 609
Cebu visible baseline: 59 PC / 41 H5 / 24 Admin
source fingerprint: efe7df7a08f444fa02e90f35c810221e6cd1bcbcbdee02fdb1c92e52fc630aa7
```

Admin production build requires Node `22.12+`; the repository pins `22.14.0`
in `.nvmrc`. Running it with the machine default Node `22.0.0` correctly fails
the version-sensitive Nuxt parser path and is not represented as a pass.

The Browser plugin could not execute the local-page action because of its
security policy. Independent browser/E2E comparison remains required.

## Known Gaps And Dependency Gates

- Real Supplier team invitation, deactivate/restore, Portal access suspension,
  and Supplier Owner/Operator separation were implemented in ZL11/ZL12 and
  remain awaiting independent verification.
- Category and geography-specific matching trigger rules were implemented in
  ZL12 and are awaiting independent verification with the rest of the supplier
  workspace.
  Current trigger preferences use persisted notification preferences.
- Legacy Cebu data import belongs to ZL05/ZL10.
- ZL01, ZL02, and ZL03 must receive independent verification before ZL04 can
  be unlocked or submitted for independent verification.

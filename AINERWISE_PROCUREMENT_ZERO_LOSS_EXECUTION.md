# AinerWise Procurement Zero-Loss Execution

Last updated: 2026-06-19

## One-Line Principle

AinerWise Procurement is a standalone procurement product copied from the CebuProjects baseline, then integrated into AinerWise Core without losing any original PC, H5, Admin, API, role, or workflow capability.

## Architecture Decision

- Root `CebuProjects` is the read-only legacy baseline. It is not the target runtime and must not receive business changes.
- `Ainerwise/modules/procurement` is the new implementation target.
- `AinerWise Procurement` is the user-visible procurement brand.
- AinerWise Core is the long-term shared business data base for users, companies, projects, RFQ, offers, orders, wallet, messages, KYC, audit, notifications, and AI.
- AinerWise Core Auth is the target account system. Procurement, Marketing, Admin, PC, and H5 must not create isolated user databases after the Core API migration.
- `frontend-admin` is the only physical backoffice. Procurement Admin can keep a standalone entrypoint during zero-loss replication, but long-term account/permission administration belongs to the AinerWise Access Center.
- Copy first, integrate second. Do not delete or simplify a legacy feature while the ledger still marks it as not migrated.
- Existing AinerWise internal Procurement Phase 1 can continue as Core workflow infrastructure, but it is not a replacement for the full CebuProjects PC/H5/Admin product.

## Shared Auth And Access Center Dependency

Shared Auth & SSO Middleware V1 lives in:

- `Ainerwise/shared/auth/useSharedAuth.ts`
- `Ainerwise/frontend-pc/composables/useAuth.ts`
- `Ainerwise/frontend-h5/composables/useAuth.ts`
- `Ainerwise/frontend-admin/composables/useAuth.ts`
- `Ainerwise/frontend-admin/pages/access-center/index.vue`

Current rule:

- PC/H5/Admin/Marketing on the same `localhost` host can reuse the Core auth cookie across ports.
- `procurement.localhost` aliases are standalone copied entrypoints, but their login/API calls now route through AinerWise Core Auth and Core compatibility APIs.
- Cross-subdomain cookie SSO for `*.localhost` and future production domains still requires the formal SSO bridge; token-based Core compatibility does not complete that item by itself.
- `/access-center` is the unified place to see which roles can open which logical backoffice workbench.

Status: READY_FOR_VERIFY for shared SDK extraction, Access Center shell, and Procurement copied module Core-auth/API bridge V1; TODO for formal cross-subdomain SSO bridge.

Verification evidence recorded on 2026-06-19:

- PC/H5/Admin production builds pass after shared Auth SDK extraction.
- The AinerWise Docker dev stack mounts `./shared:/shared:ro` into every PC/H5/Admin-derived portal container.
- `http://localhost:4097/access-center` is protected when unauthenticated and returns `302 /login?redirect=/access-center`.
- The demo admin Core cookie loads `http://localhost:4097/access-center` and `http://localhost:4094/marketing` with `HTTP 200`.
- Root `CebuProjects` remains the read-only baseline.
- Procurement copied PC/H5/Admin production builds pass from `Ainerwise/modules/procurement/{pc,h5,admin}`.
- `http://procurement.localhost`, `http://procurement-h5.localhost`, and `http://procurement-admin.localhost` return `HTTP 200`.
- `http://cebu.localhost` redirects to `http://procurement.localhost` and returns `HTTP 200`.
- `http://procurement.localhost/api/auth/system-mode` returns Core JSON with `app_name: AinerWise Procurement`.
- `http://procurement.localhost/api/payments/region-config?country=PH` returns Core payment region config.
- `http://procurement.localhost/api/marketplace/feed` returns Core supplier listing data.
- Unauthenticated `http://procurement.localhost/api/intents/my` returns `401 Not authenticated`.
- Demo login through `http://procurement.localhost/api/auth/login` with `demo@ainerwise.com / demo123` returns a Core buyer JWT; `/api/auth/me`, `/api/users/me`, and `/api/intents/my` work with that token.
- `http://procurement.localhost/api/wallets/me`, `/api/wallets/transactions`, `/api/wallets/deposits`, and `/api/wallets/deposits/{id}/submit-tx` now use the Core wallet/deposit tables through the compatibility adapter.
- Demo buyer can create and submit a PHP deposit through the PC API; another Core user token receives `404 Deposit not found` when trying to submit the buyer deposit.

## Physical Entrypoints

| Surface | New host | Port | Source path | Runtime role | Status |
| --- | --- | ---: | --- | --- | --- |
| PC | `http://procurement.localhost` | `4106` | `Ainerwise/modules/procurement/pc` | Buyer/Supplier public procurement PC | READY_FOR_VERIFY |
| H5 | `http://procurement-h5.localhost` | `4107` | `Ainerwise/modules/procurement/h5` | Mobile buyer/supplier procurement | READY_FOR_VERIFY |
| Admin | `http://procurement-admin.localhost` | `4108` | `Ainerwise/modules/procurement/admin` | Procurement admin console | READY_FOR_VERIFY |
| Legacy alias | `http://cebu.localhost` | n/a | redirect only | Alias to PC | READY_FOR_VERIFY |
| Legacy H5 alias | `http://cebu-h5.localhost` | n/a | redirect only | Alias to H5 | READY_FOR_VERIFY |
| Legacy Admin alias | `http://cebu-admin.localhost` | n/a | redirect only | Alias to Admin | READY_FOR_VERIFY |

## Source Control Guardrail

`CebuProjects` must remain clean after every implementation step.

Verification command:

```bash
git status --short CebuProjects
```

Expected output: empty.

Current status: READY_FOR_VERIFY.

## Implementation Status

| Step | Scope | Status | Evidence |
| --- | --- | --- | --- |
| Clean Safety Step | Restore root `CebuProjects`; remove accidental generated files | READY_FOR_VERIFY | `git status --short CebuProjects` returns empty |
| Copy Legacy Sources | Copy PC/H5/Admin into `Ainerwise/modules/procurement` | READY_FOR_VERIFY | PC 59 pages, H5 41 pages, Admin 23 pages copied |
| Brand Rename | User-visible `ProcurePing` renamed to `AinerWise Procurement` in copied module | READY_FOR_VERIFY | `rg "ProcurePing|>PP<|procureping.local"` only leaves intentional demo credential cases |
| Standalone Entrypoints | Add procurement compose, ports, Nginx host routing, legacy alias redirects | READY_FOR_VERIFY | `Ainerwise/docker-compose.procurement-standalone.yml`, `Ainerwise/nginx/default.conf` |
| Main Site Link | AinerWise PC header/home links to standalone Procurement PC | READY_FOR_VERIFY | `http://procurement.localhost` external link added |
| Core API Migration | Replace transitional Cebu API with AinerWise Core compatible API | IN_PROGRESS | Core bridge V1 is READY_FOR_VERIFY for auth, users, categories, marketplace feed, payment region config, buyer intents, supplier offers/orders/notifications adapters, and wallet/deposit compatibility; full admin/KYC/order/escrow/message parity still requires ledger gates |
| Ledger-Based Migration | Migrate Marketplace, Project Forge, RFQ, Order, Wallet, Message, KYC, Dispute, Admin panels | IN_PROGRESS | Legacy UI copied; public marketplace/auth/intent bridge verified; remaining workflows continue module by module |

## Status Rules

Allowed statuses:

- `TODO`: Not started.
- `IN_PROGRESS`: Implementation is actively changing.
- `READY_FOR_VERIFY`: Implementation agent finished code and provided reproducible evidence.
- `VERIFIED`: Independent verification agent passed all gates.
- `FAILED_VERIFY`: Independent verification agent found a reproducible failure.
- `BLOCKED`: Cannot continue without missing dependency, credentials, or explicit product decision.

Implementation agents must never mark their own work as `VERIFIED`.

## Strict Agent Rules

- Do not modify root `CebuProjects`.
- Do not delete or overwrite original CebuProjects behavior.
- Do not use placeholder, static mock pages, fake data, or empty shells to claim migration.
- Do not treat partial AinerWise Cebu/procurement pages as full migration.
- Do not mark `VERIFIED` unless you are the independent verification agent.
- Do not skip failing tests.
- Do not accept `403`, early `return`, or swallowed exceptions as passing tests.
- Do not say "page opens" equals complete.
- Do not collapse PC and H5 into one accidental mobile-only redirect.
- Keep PC, H5, and Admin as independent physical entrypoints even if they later share Core APIs.

## Compose And Runbook

Standalone copied frontend services:

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise
docker compose -f docker-compose.procurement-standalone.yml up -d
```

Optional legacy API overlay for unmapped parity investigations only. It is no longer the default runtime target for the copied Procurement PC/H5/Admin entrypoints:

```bash
cd /Users/mac/Code_Start/Aislos/CebuProjects
docker compose -f docker-compose.yml -f ../Ainerwise/docker-compose.procurement-legacy-api.yml up -d db backend admin-backend
```

Nginx lives in the AinerWise stack:

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise
docker compose restart nginx
```

## Verification Gates

Each completed column must record:

- Modified files.
- Page address.
- API address.
- Login role.
- Test command.
- Build result.
- Positive permission test.
- Negative permission test.
- Screenshot or curl log.
- Status transition from `IN_PROGRESS` to `READY_FOR_VERIFY`.

Global final acceptance:

- PC build succeeds.
- H5 build succeeds.
- Admin build succeeds.
- Root `CebuProjects` has no business changes.
- Every Cebu original page is present in the ledger.
- New user-visible pages do not show `ProcurePing`, except preserved demo email credentials until seed/login is migrated.
- AinerWise main site links to the standalone PC procurement site.
- `procurement.localhost`, `procurement-h5.localhost`, and `procurement-admin.localhost` are reachable.
- Buyer, Supplier, and Admin roles show different pages and menus.
- Data writes to AinerWise Core after API migration; the current legacy API overlay is temporary only.

## Zero-Loss Migration Ledger

### Module Ledger

| Legacy module | Original surface | Original APIs | Original roles | Original workflow | New path | New API target | Status | Verification command | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Public marketplace | PC/H5 | `/marketplace`, `/categories` | Guest, Buyer, Supplier | Browse categories/products/suppliers | `Ainerwise/modules/procurement/pc`, `h5` | Core `/api/v1/cebu-compat/categories`, `/marketplace/feed`, `/marketplace/items/*` | READY_FOR_VERIFY for UI copy and public Core read bridge | `curl http://procurement.localhost/api/marketplace/feed` | `HTTP 200`, Core listing JSON |
| Buyer Projects / AI Project Forge | PC/H5 | `/projects`, `/intents`, AI analysis endpoints | Buyer | Create project/request, AI analysis, requirements, compare offers | `Ainerwise/modules/procurement/pc/pages/buyer/projects`, `h5/pages/buyer/projects` | Core buyer project APIs plus `/api/v1/cebu-compat/intents/*` | IN_PROGRESS | `find .../buyer/projects` and authenticated `/api/intents/my` | UI copy present; demo buyer token returns Core intent list |
| RFQ / Intent / Offer | PC/H5/Admin | `/intents`, `/offers`, `/requests` | Buyer, Supplier, Admin | Request, match supplier, submit offer, award | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/intents`, `/offers`, `/orders` | IN_PROGRESS | `rg "offers|requests|intents" Ainerwise/modules/procurement` | UI copy present; main buyer intent read path verified |
| Orders / Escrow / Wallet | PC/H5/Admin | `/orders`, `/wallet`, admin payments/escrow | Buyer, Supplier, Finance/Admin | Create order, escrow, release, payout | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*`, `/api/v1/cebu-compat/wallets/*`, and admin `/api/v1/admin/cebu-trade/deposits` | IN_PROGRESS; Wallet/Deposit bridge READY_FOR_VERIFY | `curl http://procurement.localhost/api/wallets/me -H "Authorization: Bearer $token"` | PC/H5 wallet API, deposit create, submit tx, admin deposits read, and cross-user submit denial verified |
| Messages / Notifications | PC/H5/Admin | `/messages`, `/notifications` | Buyer, Supplier, Support/Admin | Chat, notification center, admin notification ops | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/notifications/*` plus commerce messaging services | IN_PROGRESS | `rg "messages|notifications" Ainerwise/modules/procurement` | UI copy present; compatibility adapter implemented |
| Supplier Catalog / Ads | PC/H5/Admin | `/catalog`, `/ads`, admin campaigns | Supplier, Admin | Manage products/services, supplier ads | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/supplier/*`, `/api/v1/cebu-trade/ads/*` | IN_PROGRESS | `rg "catalog|ads|campaign" Ainerwise/modules/procurement` | UI copy present; public listing read verified |
| Dispute / KYC / Risk | PC/H5/Admin | `/disputes`, `/verification`, `/risk`, KYC/KYB APIs | Buyer, Supplier, Admin, Risk, Verification | Submit dispute, verify company/docs, risk review | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*/dispute`, KYC/Core admin APIs | IN_PROGRESS | `rg "disputes|verification|risk|KYC|KYB" Ainerwise/modules/procurement` | UI copy present; dispute adapter implemented; KYC parity still needs verification |
| Admin all panels | Admin, PC admin pages | Admin backend APIs | Admin, Super Admin, Ops, Finance, Risk, Support, Auditor | Manage users, companies, orders, payments, regions, settings, audit | `Ainerwise/modules/procurement/admin`, `pc/pages/admin` | Core `/api/v1/admin/cebu/*`, `/api/v1/admin/cebu-trade/*`, `/api/v1/cebu-compat/*` | IN_PROGRESS | `curl http://procurement-admin.localhost/api/admin/dashboard` | `401 Not authenticated` confirms Core-protected admin route; full panel parity still requires role login tests |

### Page Ledger Summary

| Surface | Original count | New count | Status |
| --- | ---: | ---: | --- |
| PC pages | 59 | 59 | READY_FOR_VERIFY |
| H5 pages | 41 | 41 | READY_FOR_VERIFY |
| Admin pages | 23 | 23 | READY_FOR_VERIFY |

## PC Page Inventory

```text
pages/admin/audit.vue
pages/admin/categories.vue
pages/admin/dashboard.vue
pages/admin/disputes.vue
pages/admin/intents.vue
pages/admin/offers.vue
pages/admin/orders.vue
pages/admin/pricing-intel.vue
pages/admin/ranking.vue
pages/admin/risk.vue
pages/admin/settings.vue
pages/admin/users.vue
pages/admin/verifications.vue
pages/buyer/company-profile.vue
pages/buyer/dashboard.vue
pages/buyer/disputes/index.vue
pages/buyer/disputes/new.vue
pages/buyer/ideal-list.vue
pages/buyer/messages.vue
pages/buyer/offers/[id].vue
pages/buyer/orders/[id].vue
pages/buyer/orders/index.vue
pages/buyer/projects/[id].vue
pages/buyer/projects/index.vue
pages/buyer/requests/[id]/index.vue
pages/buyer/requests/[id]/offers.vue
pages/buyer/requests/index.vue
pages/buyer/settings.vue
pages/buyer/team.vue
pages/buyer/wallet.vue
pages/categories.vue
pages/how-it-works.vue
pages/index.vue
pages/login.vue
pages/marketplace/[id].vue
pages/marketplace/index.vue
pages/post-request.vue
pages/pricing.vue
pages/register-buyer.vue
pages/register-role.vue
pages/register-supplier.vue
pages/supplier-onboarding.vue
pages/supplier/ads/create.vue
pages/supplier/ads/index.vue
pages/supplier/catalog/index.vue
pages/supplier/dashboard.vue
pages/supplier/inbox.vue
pages/supplier/messages.vue
pages/supplier/notifications.vue
pages/supplier/offers/index.vue
pages/supplier/offers/new.vue
pages/supplier/orders/[id].vue
pages/supplier/orders/index.vue
pages/supplier/payouts.vue
pages/supplier/reviews.vue
pages/supplier/settings.vue
pages/supplier/team.vue
pages/supplier/triggers.vue
pages/trust-safety.vue
```

## H5 Page Inventory

```text
pages/auth/login.vue
pages/auth/register.vue
pages/auth/reset-password.vue
pages/buyer/compare.vue
pages/buyer/home.vue
pages/buyer/messages.vue
pages/buyer/offers.vue
pages/buyer/orders/[id].vue
pages/buyer/orders/index.vue
pages/buyer/post-request.vue
pages/buyer/profile.vue
pages/buyer/projects/[id].vue
pages/buyer/projects/index.vue
pages/buyer/requests/[id].vue
pages/buyer/requests/index.vue
pages/buyer/wallet.vue
pages/index.vue
pages/marketplace/[id].vue
pages/marketplace/index.vue
pages/messages/[order_id].vue
pages/notifications.vue
pages/profile/change-password.vue
pages/profile/company.vue
pages/profile/edit.vue
pages/profile/index.vue
pages/settings/language.vue
pages/settings/notifications.vue
pages/supplier/ads/create.vue
pages/supplier/ads/index.vue
pages/supplier/catalog.vue
pages/supplier/make-offer.vue
pages/supplier/messages.vue
pages/supplier/offers.vue
pages/supplier/orders.vue
pages/supplier/orders/[id].vue
pages/supplier/pings.vue
pages/supplier/pings/[id].vue
pages/supplier/profile.vue
pages/supplier/wallet.vue
pages/verification.vue
pages/wallet.vue
```

## Admin Page Inventory

```text
src/pages/AdCampaigns.vue
src/pages/Audit.vue
src/pages/Backups.vue
src/pages/Companies.vue
src/pages/Dashboard.vue
src/pages/Disputes.vue
src/pages/Escrow.vue
src/pages/Integrations.vue
src/pages/Intents.vue
src/pages/KYCMedia.vue
src/pages/Login.vue
src/pages/Marketplace.vue
src/pages/Notifications.vue
src/pages/Orders.vue
src/pages/Payments.vue
src/pages/Regions.vue
src/pages/Risk.vue
src/pages/Settings.vue
src/pages/Shipping.vue
src/pages/Staff.vue
src/pages/Trust.vue
src/pages/Users.vue
src/pages/Verification.vue
```

## Next Agent Assignments

### Agent A: Build Verification

Scope:

- Do not change business logic.
- Run PC, H5, and Admin builds.
- Fix only build/tooling issues inside `Ainerwise/modules/procurement`.
- Keep root `CebuProjects` clean.

Commands:

```bash
cd /Users/mac/Code_Start/Aislos/Ainerwise/modules/procurement/pc && npm install && npm run build
cd /Users/mac/Code_Start/Aislos/Ainerwise/modules/procurement/h5 && npm install && npm run build
cd /Users/mac/Code_Start/Aislos/Ainerwise/modules/procurement/admin && npm install && npm run build
```

### Agent B: Core API Migration

Scope:

- Implement AinerWise backend compatibility APIs.
- Migrate copied frontend API base from transitional Cebu API to AinerWise Core.
- Preserve ownership, workspace, portal, and region checks.
- Add positive and negative tests for every object-level API.

Do not touch UI unless an API contract requires it.

### Agent C: Independent Verification

Scope:

- Do not implement features.
- Verify all `READY_FOR_VERIFY` rows.
- Mark `VERIFIED` only with reproducible evidence.
- Mark `FAILED_VERIFY` with exact commands and failure output.

## Assumptions

- `CebuProjects` is a baseline, not the target runtime.
- The first milestone is full UI/entrypoint replication under AinerWise, not final Core API migration.
- Legacy API use is allowed only for parity investigation of unmapped endpoints. New runtime targets must use AinerWise Core or explicitly record a blocker in this ledger.
- Demo emails may temporarily retain legacy domains until seed/login migration is completed.

## Current Verification Evidence

Recorded by implementation agent on 2026-06-19. Status remains `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

### Build Evidence

| Surface | Command | Result | Notes |
| --- | --- | --- | --- |
| Admin | `docker compose -f Ainerwise/docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS | Vite production build completed |
| H5 | `docker compose -f Ainerwise/docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS | Nuxt production build completed |
| PC | `docker compose -f Ainerwise/docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS | Nuxt production build completed; runtime external asset warnings only |

### Runtime Smoke Evidence

| Check | Command | Result |
| --- | --- | --- |
| PC direct | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://localhost:4106/` | `200` |
| H5 direct | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://localhost:4107/` | `200` |
| Admin direct | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://localhost:4108/` | `200` |
| PC host | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://procurement.localhost/` | `200` |
| H5 host | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://procurement-h5.localhost/` | `200` |
| Admin host | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://procurement-admin.localhost/` | `200` |
| Legacy PC alias | `curl -sS -o /tmp/curl.out -w '%{http_code} %{redirect_url}' http://cebu.localhost/` | `301 http://procurement.localhost/` |
| Legacy H5 alias | `curl -sS -o /tmp/curl.out -w '%{http_code} %{redirect_url}' http://cebu-h5.localhost/` | `301 http://procurement-h5.localhost/` |
| Legacy Admin alias | `curl -sS -o /tmp/curl.out -w '%{http_code} %{redirect_url}' http://cebu-admin.localhost/` | `301 http://procurement-admin.localhost/` |
| AinerWise main site | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://localhost/` | `200` |
| AinerWise solutions API | `curl -sS -o /tmp/curl.out -w '%{http_code}' http://localhost/api/v1/solutions` | `200` |

### Browser Evidence

In-app browser opened the three standalone hosts and read visible DOM text.

| Surface | URL | Result |
| --- | --- | --- |
| PC | `http://procurement.localhost/` | Visible `AinerWise Procurement`; no visible `ProcurePing`; no console errors |
| H5 | `http://procurement-h5.localhost/` | Visible `AinerWise Procurement`; no visible `ProcurePing`; no console errors |
| Admin | `http://procurement-admin.localhost/` | Redirects to `/login`; visible `AinerWise Procurement`; no visible `ProcurePing`; no console errors |

### Login API Evidence

| Role | Command | Result |
| --- | --- | --- |
| Buyer | `curl -sS -X POST http://procurement.localhost/api/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@ainerwise.com","password":"demo123"}'` | PASS, returns Core buyer JWT |
| Buyer Core identity | `curl -sS http://procurement.localhost/api/auth/me -H "Authorization: Bearer $token"` | PASS, returns `demo@ainerwise.com`, role `buyer` |
| Buyer legacy UI identity | `curl -sS http://procurement.localhost/api/users/me -H "Authorization: Bearer $token"` | PASS, returns legacy-shaped role `BUYER` from the same Core user |
| Buyer intent list | `curl -sS http://procurement.localhost/api/intents/my -H "Authorization: Bearer $token"` | PASS, returns Core procurement request data |

### Core API Bridge Evidence

| API | Command | Result |
| --- | --- | --- |
| System mode | `curl -sS http://procurement.localhost/api/auth/system-mode` | `HTTP 200`, `app_name` is `AinerWise Procurement` |
| Payment region config | `curl -sS 'http://procurement.localhost/api/payments/region-config?country=PH'` | `HTTP 200`, reads Core `region_payment_configs` or Core fallback |
| Marketplace feed | `curl -sS http://procurement.localhost/api/marketplace/feed` | `HTTP 200`, returns Core supplier listing data |
| Unauthenticated buyer data | `curl -sS http://procurement.localhost/api/intents/my` | `HTTP 401`, not a failed fetch or legacy backend outage |
| Unauthenticated admin data | `curl -sS http://procurement-admin.localhost/api/admin/dashboard` | `HTTP 401`, Core-protected admin route |

### Wallet And Deposit Compatibility Evidence

| Check | Command | Result |
| --- | --- | --- |
| Unauthenticated wallet | `curl -sS -o /tmp/proc_wallet_unauth.json -w '%{http_code}' http://procurement.localhost/api/wallets/me` | `401` |
| Buyer wallet | `curl -sS http://procurement.localhost/api/wallets/me -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns `wallets[0].currency=PHP` |
| Buyer transactions | `curl -sS http://procurement.localhost/api/wallets/transactions -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns legacy flat transaction array |
| Create PHP deposit | `curl -sS -X POST http://procurement.localhost/api/wallets/deposits -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"amount_minor":12345,"currency":"PHP","network":"LOCAL_BANK","provider":"MANUAL_BANK","payment_method":"PHP_MANUAL_BANK"}'` | `HTTP 201`, returns Core `wallet_deposits` row with generated AinerWise payment instruction |
| Submit deposit reference | `curl -sS -X POST http://procurement.localhost/api/wallets/deposits/$deposit_id/submit-tx -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"tx_hash":"TEST-PHP-REF-20260619"}'` | `HTTP 200`, status becomes `SUBMITTED` |
| Cross-user submit denial | `curl -sS -o /tmp/proc_wallet_admin_cross.json -w '%{http_code}' -X POST http://procurement.localhost/api/wallets/deposits/$deposit_id/submit-tx -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"tx_hash":"ADMIN-SHOULD-NOT-OWN"}'` | `404`, `Deposit not found` |
| H5 wallet host | `curl -sS http://procurement-h5.localhost/api/wallets/me -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, same Core wallet data |
| Admin deposits | `curl -sS http://procurement-admin.localhost/api/admin/deposits -H "Authorization: Bearer $admin_token"` | `HTTP 200`, Core admin finance deposit list |

### Clean Baseline Evidence

| Check | Command | Result |
| --- | --- | --- |
| Root Cebu baseline | `git status --short CebuProjects` | empty |
| Page count | `find Ainerwise/modules/procurement/pc/pages -type f \| wc -l` | `59` |
| H5 count | `find Ainerwise/modules/procurement/h5/pages -type f \| wc -l` | `41` |
| Admin count | `find Ainerwise/modules/procurement/admin/src/pages -type f \| wc -l` | `23` |

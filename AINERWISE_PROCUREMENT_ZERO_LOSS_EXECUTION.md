# AinerWise Procurement Zero-Loss Execution

Last updated: 2026-06-20

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
- `http://procurement.localhost/api/buyer/projects` now uses Core `buyer_projects` tables through the compatibility adapter; create, message, AI analyze, report, line-item confirm, publish-to-intent, and cross-user denial are READY_FOR_VERIFY.

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
| Core API Migration | Replace transitional Cebu API with AinerWise Core compatible API | IN_PROGRESS | Core bridge V1 is READY_FOR_VERIFY for auth, users, categories, marketplace feed, payment region config, buyer intents, supplier offers/orders/notifications adapters, RFQ / Intent / Offer workflow, wallet/deposit compatibility, Buyer Projects / AI Project Forge main chain, Orders / Escrow / Delivery compatibility, order message-thread compatibility, Supplier Catalog / Ads compatibility, and Dispute / KYC / Risk compatibility; full admin parity still requires ledger gates |
| Ledger-Based Migration | Migrate Marketplace, Project Forge, RFQ, Order, Wallet, Message, KYC, Dispute, Admin panels | IN_PROGRESS | Legacy UI copied; public marketplace/auth/intent bridge verified; RFQ/Intent/Offer and Dispute/KYC/Risk workflows are READY_FOR_VERIFY; remaining admin panels continue module by module |

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
| Buyer Projects / AI Project Forge | PC/H5 | `/projects`, `/intents`, AI analysis endpoints | Buyer | Create project/request, AI analysis, requirements, compare offers | `Ainerwise/modules/procurement/pc/pages/buyer/projects`, `h5/pages/buyer/projects` | Core `/api/v1/cebu-compat/buyer/projects*` plus `/api/v1/cebu-compat/intents/*` | IN_PROGRESS; main project-analysis chain READY_FOR_VERIFY | `curl -X POST http://procurement.localhost/api/buyer/projects/.../ai/analyze -H "Authorization: Bearer $token"` | Create project, chat, Core rule analysis, line items, report, publish to procurement request, and cross-user 404 verified |
| RFQ / Intent / Offer | PC/H5/Admin | `/intents`, `/offers`, `/requests` | Buyer, Supplier, Admin | Request, match supplier, submit offer, award | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/intents`, `/intents/*/offers`, `/offers/*`, `/supplier/intents/matching`, `/supplier/offers`, `/admin/intents/*`, `/admin/offers/*` | READY_FOR_VERIFY for create/publish/match/offer/withdraw/award/admin moderation bridge | `curl -X POST http://procurement.localhost/api/intents -H "Authorization: Bearer $buyer_token" -d @intent.json` | Buyer create/publish, supplier matching, two supplier offers, buyer offer detail, cross-supplier 403, supplier withdraw, admin intent flag, admin offer remove, buyer award to order, supplier admin 403, PC/H5/Admin builds pass |
| Orders / Escrow / Wallet | PC/H5/Admin | `/orders`, `/wallet`, admin payments/escrow | Buyer, Supplier, Finance/Admin | Create order, escrow, delivery, accept, release, reviews, payout wallet credit | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*`, `/api/v1/cebu-compat/wallets/*`, and admin `/api/v1/admin/cebu-trade/deposits` | READY_FOR_VERIFY for Wallet/Deposit and Orders/Escrow/Delivery bridge; payout administration remains IN_PROGRESS | `curl -X POST http://procurement.localhost/api/orders/$order_id/pay-from-wallet -H "Authorization: Bearer $buyer_token"` | Wallet deposit/admin verify, wallet payment, escrow capture, supplier delivery, buyer acceptance, escrow release, supplier wallet credit, buyer/supplier reviews, and cross-supplier 403 verified |
| Messages / Notifications | PC/H5/Admin | `/messages`, `/notifications` | Buyer, Supplier, Support/Admin | In-site order chat, notification center, admin notification ops | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/threads/order/*/messages`, `/api/v1/cebu-compat/notifications/*`, plus commerce messaging services | READY_FOR_VERIFY for buyer/supplier order message threads and user notifications; admin template parity remains IN_PROGRESS | `curl -X POST http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $buyer_token" -d '{"body":"..."}'` | Buyer post, supplier read/reply, buyer read, cross-supplier 403, notification type mapping, and mark-read verified |
| Supplier Catalog / Ads | PC/H5/Admin | `/catalog`, `/ads`, admin campaigns | Supplier, Admin | Manage products/services, supplier ads | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/supplier/catalog/items`, `/api/v1/cebu-compat/merchant/ad-campaigns`, `/api/v1/cebu-compat/admin/ad-campaigns` | READY_FOR_VERIFY for supplier catalog CRUD, merchant ad campaign workflow, and admin campaign review bridge | `curl -X POST http://procurement.localhost/api/supplier/catalog/items -H "Authorization: Bearer $supplier_token" -d @catalog.json` | Supplier create/list/update/delete, campaign create/submit/admin approve/supplier pause, cross-supplier catalog 404, cross-supplier campaign 404, PC/H5/Admin builds pass |
| Dispute / KYC / Risk | PC/H5/Admin | `/disputes`, `/verification`, `/risk`, KYC/KYB APIs | Buyer, Supplier, Admin, Risk, Verification | Submit dispute, verify company/docs, risk review | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*/dispute`, `/disputes/*`, `/companies/me/documents`, `/companies/me/verification/*`, `/admin/disputes/*`, `/admin/risk-flags/*`, `/admin/verification/*`, `/admin/kyc-media/*` | READY_FOR_VERIFY for user/admin dispute workflow, KYC submission/review/media flagging, and risk flag workflow | `curl http://procurement-admin.localhost/api/admin/disputes -H "Authorization: Bearer $admin_token"` | Buyer dispute detail, evidence upload, unrelated supplier 403, admin evidence request/resolution, supplier KYC upload/submit, admin verification/media risk flag, admin risk action, PC/H5/Admin builds pass |
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

### RFQ / Intent / Offer Compatibility Evidence

Recorded by implementation agent on 2026-06-20. Status remains `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Buyer creates intent | `curl -sS -X POST http://procurement.localhost/api/intents -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d @intent_payload.json` | `HTTP 201`, Core `ProcurementRequest` created; new response returns `offer_count=0` |
| Buyer publishes intent | `curl -sS -X POST http://procurement.localhost/api/intents/$intent_id/publish -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, legacy status `ACTIVE`, `offer_count=0` |
| Admin lists active intents | `curl -sS 'http://procurement-admin.localhost/api/admin/intents?status=ACTIVE' -H "Authorization: Bearer $admin_token"` | `HTTP 200`, contains new intent `ac2f927f-f73b-4e67-8d97-367741cc344a` |
| Admin flags intent | `curl -sS -X POST http://procurement-admin.localhost/api/admin/intents/$intent_id/moderate -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"action":"flag","reason":"Codex RFQ moderation flag"}'` | `HTTP 200`, status remains `ACTIVE`, `moderation_flagged=true` |
| Supplier matching list | `curl -sS http://procurement.localhost/api/supplier/intents/matching -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, contains published intent |
| Supplier 1 submits offer | `curl -sS -X POST http://procurement.localhost/api/intents/$intent_id/offers -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier1_token" -d @offer1_payload.json` | `HTTP 201`, offer `2df5e9d8-ad71-4a99-8eb7-ea041219f8cd`, status `SUBMITTED`, total `215000 PHP` |
| Supplier 2 submits offer | `curl -sS -X POST http://procurement.localhost/api/intents/$intent_id/offers -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier2_token" -d @offer2_payload.json` | `HTTP 201`, status `SUBMITTED`, total `236000 PHP` |
| Buyer lists offers | `curl -sS http://procurement.localhost/api/intents/$intent_id/offers -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns both submitted offers |
| Buyer offer detail | `curl -sS http://procurement.localhost/api/offers/$offer_id -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, buyer can view offer on own intent |
| Cross-supplier offer denial | `curl -sS -o /tmp/proc_offer_forbidden.json -w '%{http_code}' http://procurement.localhost/api/offers/$offer1_id -H "Authorization: Bearer $supplier2_token"` | `403`, unrelated supplier cannot view competitor offer |
| Supplier withdraws own offer | `curl -sS -X POST http://procurement.localhost/api/offers/$offer2_id/withdraw -H "Authorization: Bearer $supplier2_token"` | `HTTP 200`, status `WITHDRAWN` |
| Admin lists submitted offers | `curl -sS 'http://procurement-admin.localhost/api/admin/offers?status=SUBMITTED' -H "Authorization: Bearer $admin_token"` | `HTTP 200`, contains supplier 1 submitted offer |
| Admin removes offer | `curl -sS -X POST http://procurement-admin.localhost/api/admin/offers/$offer2_id/remove -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"reason":"Codex remove withdrawn comparison offer"}'` | `HTTP 200`, status `REJECTED` |
| Buyer awards offer | `curl -sS -X POST http://procurement.localhost/api/offers/$offer1_id/award -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, creates order `1de2bdff-bb74-4888-bca8-cdbe97905ada`, status `AWAITING_PAYMENT`, amount `215000 PHP` |
| Admin gets awarded intent | `curl -sS http://procurement-admin.localhost/api/admin/intents/$intent_id -H "Authorization: Bearer $admin_token"` | `HTTP 200`, status `AWARDED`, `offer_count=2` |
| Supplier cannot access admin intents | `curl -sS -o /tmp/proc_admin_intents_forbidden.json -w '%{http_code}' http://procurement-admin.localhost/api/admin/intents -H "Authorization: Bearer $supplier_token"` | `403` |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Procurement PC build | `cd Ainerwise/modules/procurement/pc && npm run build` | PASS, Nuxt production build completed; known Tailwind/external asset warnings only |
| Procurement H5 build | `cd Ainerwise/modules/procurement/h5 && npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `cd Ainerwise/modules/procurement/admin && npm run build` | PASS, Vite production build completed |

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

### Orders / Escrow / Delivery Compatibility Evidence

| Check | Command | Result |
| --- | --- | --- |
| Buyer order list | `curl -sS http://procurement.localhost/api/orders/my -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns Core `commerce_orders`; unpaid confirmed order maps to legacy `AWAITING_PAYMENT` |
| Order delivery list | `curl -sS http://procurement.localhost/api/orders/$order_id/delivery -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns legacy delivery array |
| Buyer cannot create supplier delivery | `curl -sS -o /tmp/aw_buyer_delivery_post.json -w '%{http_code}' -X POST http://procurement.localhost/api/orders/$order_id/delivery -H "Authorization: Bearer $buyer_token" -d '{"status":"DISPATCHED"}'` | `403`, `Operation requires admin or supplier` |
| Insufficient wallet payment | `curl -sS -o /tmp/aw_pay_from_wallet.json -w '%{http_code}' -X POST http://procurement.localhost/api/orders/$order_id/pay-from-wallet -H "Authorization: Bearer $buyer_token"` | `409`, `Insufficient wallet balance` |
| Buyer deposit + admin verify | `POST /api/wallets/deposits` then `POST /api/admin/deposits/$deposit_id/verify` | `PENDING_TX -> VERIFIED`, amount `200000 EUR` |
| Wallet payment creates escrow | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/pay-from-wallet -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, order `PAID_IN_ESCROW`, escrow `CAPTURED`, captured `125000`, buyer EUR wallet `75000` |
| Supplier order ownership | `curl -sS http://procurement.localhost/api/orders/my -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, order visible to actual supplier company user `supplier-dae5ba47@example.com` |
| Supplier dispatch | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/delivery -H "Authorization: Bearer $supplier_token" -d '{"status":"DISPATCHED","tracking_number":"AW-TRACK-001"}'` | `HTTP 201`, delivery status `DISPATCHED` |
| Supplier delivered | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/delivery -H "Authorization: Bearer $supplier_token" -d '{"status":"DELIVERED","tracking_number":"AW-TRACK-001"}'` | `HTTP 201`, delivery status `DELIVERED`; buyer order maps to `DELIVERED` |
| Buyer accepts delivery | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/accept -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, order `ACCEPTED`, escrow `RELEASED`, released `125000`, supplier EUR wallet credited `125000` |
| Buyer reviews seller | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/reviews/seller -H "Authorization: Bearer $buyer_token" -d '{"product_quality_rating":5,"logistics_rating":4,"communication_rating":5}'` | `HTTP 201`, TransactionReview created and rating details stored in Core order JSON |
| Supplier reviews buyer | `curl -sS -X POST http://procurement.localhost/api/orders/$order_id/reviews/buyer -H "Authorization: Bearer $supplier_token" -d '{"buyer_rating":5,"communication_rating":5}'` | `HTTP 201`, supplier-to-buyer review persisted in Core order JSON |
| Supplier review summary | `curl -sS http://procurement.localhost/api/reviews/company/me -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, `total_reviews=1`, `average_overall_rating=5.0` |
| Cross-supplier delivery denial | `curl -sS -o /tmp/aw_other_supplier_delivery.json -w '%{http_code}' -X POST http://procurement.localhost/api/orders/$order_id/delivery -H "Authorization: Bearer $other_supplier_token"` | `403`, `Not a party to this order` |

### Messages / Notifications Compatibility Evidence

| Check | Command | Result |
| --- | --- | --- |
| Buyer reads order thread | `curl -sS http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, returns legacy message array |
| Buyer posts order message | `curl -sS -X POST http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $buyer_token" -d '{"body":"Codex verification buyer message"}'` | `HTTP 201`, Core `commerce_messages` row returned as legacy shape with `sender_id` |
| Supplier reads buyer message | `curl -sS http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, supplier sees buyer message |
| Supplier replies | `curl -sS -X POST http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $supplier_token" -d '{"body":"Codex verification supplier reply"}'` | `HTTP 201`, Core message created |
| Buyer sees supplier reply | `curl -sS http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, message count `2`, latest body is supplier reply |
| Message notifications | `curl -sS http://procurement.localhost/api/notifications/my -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, includes legacy `notification_type=MESSAGE_RECEIVED` mapped from Core `commerce.message.received` |
| Notification read | `curl -sS -X POST http://procurement.localhost/api/notifications/$notification_id/read -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, status `READ`, `read_at` populated |
| Cross-supplier thread denial | `curl -sS -o /tmp/aw_messages_other_supplier_get.json -w '%{http_code}' http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $other_supplier_token"` | `403`, `Not a party to this order` |

### Supplier Catalog / Ads Compatibility Evidence

| Check | Command | Result |
| --- | --- | --- |
| Supplier company identity | `curl -sS http://procurement.localhost/api/companies/me -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, returns Core company `Commerce Supplier dae5ba47`, type `supplier`, verification `verified` |
| Create catalog item | `curl -sS -X POST http://procurement.localhost/api/supplier/catalog/items -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier_token" -d @catalog_payload.json` | `HTTP 201`, created Core `supplier_listings` row `be46b2d8-39ef-4f74-a148-dce4fb4397ac`, status `ACTIVE`, price `12345`, stock `8` |
| List own catalog | `curl -sS 'http://procurement.localhost/api/supplier/catalog/items?keyword=Codex%20Verification&page_size=5' -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, `total=1`, first item status `ACTIVE` |
| Update own catalog | `curl -sS -X PATCH http://procurement.localhost/api/supplier/catalog/items/$item_id -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier_token" -d '{"stock_qty":11,"price_minor":13000,"tags":["codex","verified"]}'` | `HTTP 200`, item price `13000`, stock `11`, tags persisted |
| Cross-supplier catalog update denial | `curl -sS -o /tmp/other_patch.json -w '%{http_code}' -X PATCH http://procurement.localhost/api/supplier/catalog/items/$item_id -H "Authorization: Bearer $other_supplier_token" -d '{"price_minor":1}'` | `404`, other supplier cannot mutate catalog item |
| Create merchant ad campaign | `curl -sS -X POST http://procurement.localhost/api/merchant/ad-campaigns -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier_token" -d @ad_payload.json` | `HTTP 201`, campaign `8eb3966a-8f32-4056-ab8a-5a1e48cf1a7a`, status `DRAFT`, linked catalog item, budget `50000` |
| Submit campaign for review | `curl -sS -X POST http://procurement.localhost/api/merchant/ad-campaigns/$campaign_id/submit -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, status `PENDING_REVIEW` |
| Cross-supplier campaign denial | `curl -sS -o /tmp/other_pause.json -w '%{http_code}' -X POST http://procurement.localhost/api/merchant/ad-campaigns/$campaign_id/pause -H "Authorization: Bearer $other_supplier_token"` | `404`, other supplier cannot control campaign |
| Admin sees pending campaign | `curl -sS 'http://procurement-admin.localhost/api/admin/ad-campaigns?status=PENDING_REVIEW' -H "Authorization: Bearer $admin_token"` | `HTTP 200`, pending list contains campaign `8eb3966a-8f32-4056-ab8a-5a1e48cf1a7a` |
| Admin approves campaign | `curl -sS -X POST http://procurement-admin.localhost/api/admin/ad-campaigns/$campaign_id/approve -H "Authorization: Bearer $admin_token"` | `HTTP 200`, status `ACTIVE` |
| Supplier pauses approved campaign | `curl -sS -X POST http://procurement.localhost/api/merchant/ad-campaigns/$campaign_id/pause -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, status `PAUSED` |
| Delete catalog item | `curl -sS -X DELETE http://procurement.localhost/api/supplier/catalog/items/$item_id -H "Authorization: Bearer $supplier_token" -o /dev/null -w '%{http_code}'` | `204`, subsequent `GET /api/supplier/catalog/items/$item_id` returns `404` |
| Nginx config | `docker compose exec -T nginx nginx -t` | PASS |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Procurement PC build | `cd Ainerwise/modules/procurement/pc && npm run build` | PASS, Nuxt production build completed; known Tailwind/external asset warnings only |
| Procurement H5 build | `cd Ainerwise/modules/procurement/h5 && npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `cd Ainerwise/modules/procurement/admin && npm run build` | PASS, Vite production build completed |

### Dispute / KYC / Risk Compatibility Evidence

Recorded by implementation agent on 2026-06-20. Status remains `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Buyer dispute list/detail | `curl -sS 'http://procurement.localhost/api/disputes/my?status=OPEN' -H "Authorization: Bearer $buyer_token"` then `curl -sS http://procurement.localhost/api/disputes/$dispute_id -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, buyer sees Core `OrderDispute` as legacy shape; sample dispute `4fd13c5b-367a-4784-a6f0-8cf0fe479792` returned `status=OPEN` |
| Cross-supplier dispute denial | `curl -sS -o /tmp/proc_dispute_forbidden.json -w '%{http_code}' http://procurement.localhost/api/disputes/$dispute_id -H "Authorization: Bearer $other_supplier_token"` | `403`, unrelated supplier cannot view dispute |
| Buyer dispute evidence | `curl -sS -X POST http://procurement.localhost/api/disputes/$dispute_id/evidence -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"evidence":[{"description":"Codex buyer evidence","file_url":"https://example.test/evidence.jpg"}]}'` | `HTTP 200`, `evidence_json` count became `1` |
| Admin dispute detail | `curl -sS http://procurement-admin.localhost/api/admin/disputes/$dispute_id -H "Authorization: Bearer $admin_token"` | `HTTP 200`, admin sees dispute and evidence |
| Admin requests evidence | `curl -sS -X POST 'http://procurement-admin.localhost/api/admin/disputes/$dispute_id/request-evidence?from_party=BUYER' -H "Authorization: Bearer $admin_token"` | `HTTP 200`, status became `UNDER_REVIEW` |
| Admin resolves dispute | `curl -sS -X POST 'http://procurement-admin.localhost/api/admin/disputes/$dispute_id/resolve?decision=DISMISSED&resolution=Codex%20verification%20dismissed' -H "Authorization: Bearer $admin_token"` | `HTTP 200`, status became `DISMISSED`, Core status `closed` |
| Supplier cannot access risk admin | `curl -sS -o /tmp/proc_risk_forbidden.json -w '%{http_code}' http://procurement-admin.localhost/api/admin/risk-flags -H "Authorization: Bearer $supplier_token"` | `403` |
| Admin creates risk flag | `curl -sS -X POST http://procurement-admin.localhost/api/admin/risk-flags -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"entity_type":"USER","entity_id":"$buyer_user_id","risk_type":"OTHER","risk_level":"HIGH","description":"Codex risk flag verification"}'` | `HTTP 201`, created Core `RiskFlag`; admin list with `status=OPEN&entity_type=USER` contains it |
| Admin acts on risk flag | `curl -sS -X POST http://procurement-admin.localhost/api/admin/risk-flags/$flag_id/action -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"status":"MITIGATED","action_taken":"Codex mitigated during verification"}'` | `HTTP 200`, status `MITIGATED`, `action_taken` preserved in legacy response |
| Supplier cannot access verification admin | `curl -sS -o /tmp/proc_kyc_forbidden.json -w '%{http_code}' http://procurement-admin.localhost/api/admin/verification/queue -H "Authorization: Bearer $supplier_token"` | `403` |
| Supplier uploads KYC document | `curl -sS -X POST http://procurement.localhost/api/companies/me/documents -H 'Content-Type: application/json' -H "Authorization: Bearer $supplier_token" -d '{"doc_type":"BUSINESS_LICENSE","file_url":"https://example.test/codex-kyb.pdf","original_filename":"codex-kyb.pdf"}'` | `HTTP 201`, document `f4c06296-3e70-4304-9c09-4e81309d5ede`, status `PENDING` |
| Supplier submits verification | `curl -sS -X POST http://procurement.localhost/api/companies/me/verification/submit -H "Authorization: Bearer $supplier_token"` | `HTTP 201`, review status `SUBMITTED` |
| Admin verification queue/documents | `curl -sS http://procurement-admin.localhost/api/admin/verification/queue -H "Authorization: Bearer $admin_token"` and `curl -sS http://procurement-admin.localhost/api/admin/verification/$company_id/documents -H "Authorization: Bearer $admin_token"` | `HTTP 200`, queue contains supplier company; documents contain uploaded file |
| Admin KYC media detail | `curl -sS http://procurement-admin.localhost/api/admin/kyc-media/files/$document_id -H "Authorization: Bearer $admin_token"` | `HTTP 200`, returns file, document status, and analysis envelope |
| Admin decides verification | `curl -sS -X POST http://procurement-admin.localhost/api/admin/verification/$company_id/decide -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"decision":"NEEDS_INFO","decision_reason":"Codex verification requested more info","user_facing_note":"Please upload a clearer document"}'` | `HTTP 200`, status `NEEDS_INFO`, decision `REQUEST_MORE_INFO` |
| Admin flags KYC media risk | `curl -sS -X POST http://procurement-admin.localhost/api/admin/kyc-media/files/$document_id/flag-risk -H 'Content-Type: application/json' -H "Authorization: Bearer $admin_token" -d '{"reason":"Codex KYC media risk flag","severity":"high"}'` | `HTTP 200`, document status `REJECTED`, risk flag created |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Runtime health | `curl -sS -o /tmp/solutions_probe.json -w '%{http_code}' http://localhost/api/v1/solutions` | `200`, AinerWise website/backend chain healthy |
| Procurement PC build | `cd Ainerwise/modules/procurement/pc && npm run build` | PASS, Nuxt production build completed; known Tailwind/external asset warnings only |
| Procurement H5 build | `cd Ainerwise/modules/procurement/h5 && npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `cd Ainerwise/modules/procurement/admin && npm run build` | PASS, Vite production build completed |

### Buyer Projects / AI Project Forge Evidence

| Check | Command | Result |
| --- | --- | --- |
| Unauthenticated project list | `curl -sS -o /tmp/proj_unauth.json -w '%{http_code}' http://procurement.localhost/api/buyer/projects` | `401` |
| Buyer project list | `curl -sS http://procurement.localhost/api/buyer/projects -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, legacy array response |
| Create project | `curl -sS -X POST http://procurement.localhost/api/buyer/projects -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"title":"Codex Villa Smart Upgrade 20260619","project_type":"RENOVATION","country":"Philippines","city":"Cebu City","budget_max":1200000,"currency":"PHP","quality_preference":"MID_RANGE","description":"Villa smart lighting, CCTV, network and door lock upgrade."}'` | `HTTP 201`, Core `buyer_projects` row |
| Send intake message | `curl -sS -X POST http://procurement.localhost/api/buyer/projects/$project_id/messages -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"content":"We need smart lighting for 6 rooms, CCTV around the gate, and stable WiFi coverage."}'` | `HTTP 201`, returns user + assistant messages |
| Run analysis | `curl -sS -X POST http://procurement.localhost/api/buyer/projects/$project_id/ai/analyze -H "Authorization: Bearer $buyer_token"` | `HTTP 202`, Core AI run status `SUCCESS` |
| Project detail after analysis | `curl -sS http://procurement.localhost/api/buyer/projects/$project_id -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, includes `line_items.length=3` and `latest_ai_run` |
| Versioned report | `curl -sS http://procurement.localhost/api/buyer/projects/$project_id/report -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, includes `rows.length=3` |
| Publish confirmed item | `curl -sS -X PATCH http://procurement.localhost/api/buyer/projects/$project_id/line-items/$item_id -H 'Content-Type: application/json' -H "Authorization: Bearer $buyer_token" -d '{"status":"CONFIRMED"}' && curl -sS -X POST http://procurement.localhost/api/buyer/projects/$project_id/publish -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, creates one Core procurement request |
| Cross-user project denial | `curl -sS -o /tmp/proj_admin_cross.json -w '%{http_code}' http://procurement.localhost/api/buyer/projects/$project_id -H "Authorization: Bearer $admin_token"` | `404`, `Project not found` |
| PC/H5 project pages | `curl -sS -o /tmp/page.html -w '%{http_code}' http://procurement.localhost/buyer/projects && curl -sS -o /tmp/page.html -w '%{http_code}' http://procurement-h5.localhost/buyer/projects` | `200`, standalone project entrypoints render |

### Clean Baseline Evidence

| Check | Command | Result |
| --- | --- | --- |
| Root Cebu baseline | `git status --short CebuProjects` | empty |
| Page count | `find Ainerwise/modules/procurement/pc/pages -type f \| wc -l` | `59` |
| H5 count | `find Ainerwise/modules/procurement/h5/pages -type f \| wc -l` | `41` |
| Admin count | `find Ainerwise/modules/procurement/admin/src/pages -type f \| wc -l` | `23` |

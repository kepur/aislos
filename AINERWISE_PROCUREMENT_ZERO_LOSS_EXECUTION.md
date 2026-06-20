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
| Copy Legacy Sources | Copy PC/H5/Admin into `Ainerwise/modules/procurement` | READY_FOR_VERIFY | PC 60 pages after restoring the missing forgot-password entrypoint, H5 41 pages, Admin 23 pages |
| Brand Rename | User-visible `ProcurePing` renamed to `AinerWise Procurement` in copied module | READY_FOR_VERIFY | `rg "ProcurePing|>PP<|procureping.local"` only leaves intentional demo credential cases |
| Standalone Entrypoints | Add procurement compose, ports, Nginx host routing, legacy alias redirects | READY_FOR_VERIFY | `Ainerwise/docker-compose.procurement-standalone.yml`, `Ainerwise/nginx/default.conf` |
| Main Site Link | AinerWise PC header/home links to standalone Procurement PC | READY_FOR_VERIFY | `http://procurement.localhost` external link added |
| Core API Migration | Replace transitional Cebu API with AinerWise Core compatible API | IN_PROGRESS | Core bridge V1 is READY_FOR_VERIFY for auth, users, categories, marketplace feed, payment region config, buyer intents, supplier offers/orders/notifications adapters, RFQ / Intent / Offer workflow, PC supplier inbox/offer submission/list, PC supplier orders list/detail delivery workspace, H5 buyer request list/detail candidates/offers, wallet/deposit compatibility, Buyer Projects / AI Project Forge main chain, Orders / Escrow / Delivery compatibility, shipping estimate compatibility, direct marketplace order creation, buyer profile/team, generic uploads, trust profile, account context/type, address book, ranking profiles, order message-thread compatibility, Supplier Catalog / Ads compatibility, Dispute / KYC / Risk compatibility, Admin read-panel gap bridge, Admin AI/Maps config bridge, Admin action compatibility bridge, and Admin audit/notifications/backups bridge; full admin parity still requires ledger gates |
| Ledger-Based Migration | Migrate Marketplace, Project Forge, RFQ, Order, Wallet, Message, KYC, Dispute, Admin panels | IN_PROGRESS | Legacy UI copied; public marketplace/auth/intent bridge verified; RFQ/Intent/Offer, PC Supplier Inbox/Offer Submit/List, PC Supplier Orders List/Detail, H5 Buyer Request List/Detail, Profile/Upload/Direct Order, Address/Ranking, Shipping Estimate, and Dispute/KYC/Risk workflows are READY_FOR_VERIFY; Admin read-panel, AI/Maps config, action, audit, notifications, backups, PC Admin Users no-mock handling, PC Admin Pricing Intelligence real analytics, and PC Admin Offers/Intents real lists are READY_FOR_VERIFY; remaining admin workflows continue module by module |

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
| Public marketplace | PC/H5 | `/marketplace`, `/categories` | Guest, Buyer, Supplier | Browse categories/products/suppliers, direct Buy Now | `Ainerwise/modules/procurement/pc`, `h5` | Core `/api/v1/cebu-compat/categories`, `/marketplace/feed`, `/marketplace/items/*`, `/orders` | READY_FOR_VERIFY for UI copy, public Core read bridge, and direct Core order creation | `curl -X POST http://procurement.localhost/api/orders -H "Authorization: Bearer $buyer_token" -d '{"catalog_item_id":"...","qty":2}'` | `HTTP 201`, creates Core `procurement_requests`, `supplier_offers`, and `commerce_orders`; unrelated buyer read returns `403` |
| Buyer Projects / AI Project Forge | PC/H5 | `/projects`, `/intents`, AI analysis endpoints | Buyer | Create project/request, AI analysis, requirements, compare offers | `Ainerwise/modules/procurement/pc/pages/buyer/projects`, `h5/pages/buyer/projects` | Core `/api/v1/cebu-compat/buyer/projects*` plus `/api/v1/cebu-compat/intents/*` | IN_PROGRESS; main project-analysis chain READY_FOR_VERIFY | `curl -X POST http://procurement.localhost/api/buyer/projects/.../ai/analyze -H "Authorization: Bearer $token"` | Create project, chat, Core rule analysis, line items, report, publish to procurement request, and cross-user 404 verified |
| RFQ / Intent / Offer | PC/H5/Admin | `/intents`, `/offers`, `/requests` | Buyer, Supplier, Admin | Request, match supplier, submit offer, award | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/intents`, `/intents/*/offers`, `/offers/*`, `/supplier/intents/matching`, `/supplier/offers`, `/intents/*/supplier-candidates`, `/admin/intents/*`, `/admin/offers/*` | READY_FOR_VERIFY for create/publish/match/offer/withdraw/award/admin moderation bridge plus PC supplier inbox/offer submission/list and H5 buyer request list/detail candidates/offers UI chains | `curl -X POST http://procurement.localhost/api/intents -H "Authorization: Bearer $buyer_token" -d @intent.json` | Buyer create/publish, supplier matching, PC inbox consumes real pings, PC offer editor loads intent and submits real offer, PC supplier offers list consumes real `/supplier/offers` with no static sample rows, H5 buyer request list uses true Core empty state and real created intents, H5 buyer request detail consumes real candidate `items` and no longer injects mock offers/candidates, buyer offer detail, cross-supplier 403, buyer role denied supplier matching/list 403, unauthenticated request/supplier-offer list 401, unrelated buyer offer submit 403, cross-buyer candidate read/bind 403, duplicate supplier offer denied, supplier withdraw, admin intent flag, admin offer remove, buyer award to order, supplier admin 403, PC/H5/Admin builds pass |
| Orders / Escrow / Wallet | PC/H5/Admin | `/orders`, `/wallet`, admin payments/escrow | Buyer, Supplier, Finance/Admin | Create order, escrow, delivery, accept, release, reviews, payout wallet credit | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*`, `/api/v1/cebu-compat/wallets/*`, and admin `/api/v1/cebu-compat/admin/{escrow,deposits,payouts,payment-events,settlement-events,payment-region-configs}` | READY_FOR_VERIFY for direct marketplace order creation, PC Supplier Orders real list/detail delivery workspace, Wallet/Deposit, Orders/Escrow/Delivery, and admin payment read panels; deeper payout operations remain IN_PROGRESS | `curl -X POST http://procurement.localhost/api/orders/$order_id/pay-from-wallet -H "Authorization: Bearer $buyer_token"` | Direct Buy Now creates Core order, PC Supplier Orders list consumes real `/orders/my` with no static sample row, PC Supplier Order Detail consumes real `/orders/{id}` and writes `/orders/{id}/delivery`, wallet deposit/admin verify, wallet payment, escrow capture, supplier delivery, buyer acceptance, escrow release, supplier wallet credit, buyer/supplier reviews, admin payment read-panel smoke, and cross-supplier/customer 403 verified |
| Messages / Notifications | PC/H5/Admin | `/messages`, `/notifications` | Buyer, Supplier, Support/Admin | In-site order chat, notification center, admin notification ops | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/threads/order/*/messages`, `/api/v1/cebu-compat/notifications/*`, plus commerce messaging services | READY_FOR_VERIFY for buyer/supplier order message threads and user notifications; admin template parity remains IN_PROGRESS | `curl -X POST http://procurement.localhost/api/threads/order/$order_id/messages -H "Authorization: Bearer $buyer_token" -d '{"body":"..."}'` | Buyer post, supplier read/reply, buyer read, cross-supplier 403, notification type mapping, and mark-read verified |
| Supplier Catalog / Ads | PC/H5/Admin | `/catalog`, `/ads`, admin campaigns | Supplier, Admin | Manage products/services, supplier ads | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/supplier/catalog/items`, `/api/v1/cebu-compat/merchant/ad-campaigns`, `/api/v1/cebu-compat/admin/ad-campaigns` | READY_FOR_VERIFY for supplier catalog CRUD, merchant ad campaign workflow, and admin campaign review bridge | `curl -X POST http://procurement.localhost/api/supplier/catalog/items -H "Authorization: Bearer $supplier_token" -d @catalog.json` | Supplier create/list/update/delete, campaign create/submit/admin approve/supplier pause, cross-supplier catalog 404, cross-supplier campaign 404, PC/H5/Admin builds pass |
| Dispute / KYC / Risk | PC/H5/Admin | `/disputes`, `/verification`, `/risk`, KYC/KYB APIs | Buyer, Supplier, Admin, Risk, Verification | Submit dispute, verify company/docs, risk review | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/orders/*/dispute`, `/disputes/*`, `/companies/me/documents`, `/companies/me/verification/*`, `/admin/disputes/*`, `/admin/risk-flags/*`, `/admin/verification/*`, `/admin/kyc-media/*` | READY_FOR_VERIFY for user/admin dispute workflow, KYC submission/review/media flagging, and risk flag workflow | `curl http://procurement-admin.localhost/api/admin/disputes -H "Authorization: Bearer $admin_token"` | Buyer dispute detail, evidence upload, unrelated supplier 403, admin evidence request/resolution, supplier KYC upload/submit, admin verification/media risk flag, admin risk action, PC/H5/Admin builds pass |
| Profile / Upload / Account Context | PC/H5 | `/buyer/company-profile`, `/buyer/team`, `/profile/company`, `/verification`, `/profile/change-password`, supplier onboarding | Buyer, Supplier | Maintain company profile, invite/remove team, upload KYB/assets, view trust, switch supplier account type | `Ainerwise/modules/procurement/pc`, `h5` | Core `/api/v1/cebu-compat/buyer/company-profile`, `/buyer/team/*`, `/uploads`, `/trust/me`, `/maps/reverse-geocode`, `/users/me/password`, plus Core `/api/v1/auth/me/{account-context,account-type}` | READY_FOR_VERIFY for company profile upsert, team member create/remove, MinIO upload, local reverse geocode, trust profile read, password negative, and supplier account-type role switch | `python3 pzl21_smoke.py` against `http://procurement.localhost/api` | New test buyer/company/team/upload/order created in Core; unrelated buyer order read `403`; supplier flow account became `vendor`; PC/H5/Admin builds pass |
| Password Reset Entrypoints | PC/H5 | `/forgot-password`, `/auth/reset-password`, `/auth/request-password-reset` | Guest | Request one-time password reset link without account enumeration | `Ainerwise/modules/procurement/pc/pages/forgot-password.vue`, `h5/pages/auth/reset-password.vue` | Core `/api/v1/auth/request-password-reset` through Procurement hosts | READY_FOR_VERIFY for PC restored route, H5 corrected endpoint, anonymous generic response, and PC/H5 builds | `curl -X POST http://procurement.localhost/api/auth/request-password-reset -d '{"email":"pzl23-reset@example.com"}'` | `HTTP 200`, generic response returned; PC `/forgot-password` and H5 `/auth/reset-password` render `200`; PC/H5 builds pass |
| Address Book / Ranking Profiles | PC/H5/Admin | `/addresses`, `/ranking/profiles`, `/admin/ranking/summary` | Buyer, Supplier, Admin | Manage delivery/billing addresses and tune supplier ranking profiles | `Ainerwise/modules/procurement/*` | Core `/api/v1/cebu-compat/addresses*`, `/api/v1/cebu-compat/ranking/profiles`, `/api/v1/cebu-compat/admin/ranking/summary` | READY_FOR_VERIFY for flat legacy address array shape, address CRUD/default ownership, admin ranking profile read/update/summary, built-in profile protection, and role denial | `python3 pzl22_smoke.py` against `http://procurement.localhost/api` and `http://procurement-admin.localhost/api` | New buyer address create/list/update/default/delete verified; unrelated buyer update returned `404`; admin ranking profile list/update/summary verified; built-in delete returned `409`; buyer ranking access returned `403`; PC/H5/Admin builds pass |
| Shipping Estimate | PC/H5 | `/shipping/estimate`, supplier offer shipping estimate, buyer offer landed-cost compare | Buyer, Supplier | Estimate delivery fee from admin-managed shipping routes/rates during offer creation and offer comparison | `Ainerwise/modules/procurement/pc`, `h5` | Core `/api/v1/cebu-compat/shipping/estimate` with Procurement host proxy override | READY_FOR_VERIFY for legacy `estimates` shape, retained `items` shape, real admin route/rate, authenticated estimate, unauthenticated denial, invalid-weight validation, and PC/H5/Admin builds | `python3 pzl24_smoke.py` against `http://procurement.localhost/api` and `http://procurement-admin.localhost/api` | Admin created PH->PH route/rate; buyer estimate returned `total_shipping_minor=1230`; unauthenticated request returned `401`; weight `0` returned `422`; Nginx `nginx -t`, backend `py_compile`, and PC/H5/Admin builds pass |
| Admin all panels | Admin, PC admin pages | Admin backend APIs | Admin, Super Admin, Ops, Finance, Risk, Support, Auditor | Manage users, companies, orders, payments, regions, settings, audit | `Ainerwise/modules/procurement/admin`, `pc/pages/admin` | Core `/api/v1/admin/cebu/*`, `/api/v1/cebu-compat/admin/*` | IN_PROGRESS; Admin read-panel gap bridge, AI/Maps config bridge, action compatibility bridge, audit/notifications/backups bridge, PC Admin Users no-mock failure handling, PC Admin Pricing Intelligence real analytics, and PC Admin Offers/Intents real lists READY_FOR_VERIFY | `python3 admin_smoke.py` and `GET /admin/offers`, `GET /admin/intents` against `http://procurement.localhost/api` with admin token | Admin positive smoke returned `200` for escrow, deposits, payouts, payment events, settlement events, payment region configs, shipping routes/rates/statistics, regions, coverage estimate, trust users, backups config, maps config/test, AI config/test, KYC AI analysis, users/staff/companies/orders/settings arrays, staff invite/role/status, order status, company verification/status, settings save, audit logs, notification templates/test notification, backup schedules/jobs, schedule create/toggle/delete, PC Admin Users real list, Pricing Intelligence source APIs, and PC Admin Offers/Intents real list APIs; customer/buyer tokens returned `403` on Admin endpoints; unauthenticated admin endpoints returned `401`; PC/H5/Admin builds pass |

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

### Admin Read-Panel Gap Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY` for the read-panel gap bridge only; the broader Admin all-panels migration remains `IN_PROGRESS` until every admin write workflow is independently tested.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Root Cebu baseline | `git status --short CebuProjects` | empty |
| Admin escrow list | `GET http://procurement-admin.localhost/api/admin/escrow` with admin token | `HTTP 200`, legacy array shape, Core `escrow_transactions` rows |
| Admin deposits list | `GET http://procurement-admin.localhost/api/admin/deposits` with admin token | `HTTP 200`, legacy array shape, includes `network`, `payment_method`, `tx_hash` |
| Admin payouts list | `GET http://procurement-admin.localhost/api/admin/payouts` with admin token | `HTTP 200`, legacy array shape, includes `supplier_id` and `method` aliases |
| Admin payment events | `GET http://procurement-admin.localhost/api/admin/payment-events` with admin token | `HTTP 200`, Core `payment_events` rows |
| Admin settlement events | `GET http://procurement-admin.localhost/api/admin/settlement-events` with admin token | `HTTP 200`, Core `settlement_events` rows |
| Admin payment region configs | `GET http://procurement-admin.localhost/api/admin/payment-region-configs` with admin token | `HTTP 200`, legacy array shape from Core `region_payment_configs` |
| Admin shipping read panels | `GET /api/admin/shipping/routes`, `/rates`, `/statistics` with admin token | All `HTTP 200`; routes/rates return arrays; statistics returns totals, active counts, price/ETA summaries |
| Admin regions | `GET http://procurement-admin.localhost/api/admin/regions` with admin token | `HTTP 200`, Core `regions` mapped to legacy `slug/status/radius` fields |
| Admin coverage estimate | `GET http://procurement-admin.localhost/api/maps/coverage/estimate?lat=10.3157&lng=123.8854&radius_km=15` with admin token | `HTTP 200`, returns matching company/branch counts and active regions |
| Admin trust users | `GET http://procurement-admin.localhost/api/admin/trust/users` with admin token | `HTTP 200`, Core `trust_profiles` mapped to legacy score/tier/completion fields |
| Admin backup config | `GET http://procurement-admin.localhost/api/admin/backups/config` with admin token | `HTTP 200`, derived from Core `backup_schedules` and `backup_jobs` |
| Customer negative permission | Customer token requests `/admin/escrow`, `/admin/payment-events`, `/admin/regions`, `/admin/trust/users`, `/admin/backups/config` | All returned `403`, Admin-only boundary holds |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |
| Browser sanity | In-app browser opened `http://procurement-admin.localhost/login` | Title `AinerWise Procurement Admin`, H1 `AinerWise Procurement`, email/password fields present, zero console errors |

### Admin AI / Maps Config Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Maps config read | `GET http://procurement-admin.localhost/api/admin/maps/config` with admin token | `HTTP 200`, returns provider, region, language, TTL, enabled flag |
| Maps config save | `PUT http://procurement-admin.localhost/api/admin/maps/config` with `provider=LOCAL` | `HTTP 200`, persists to Core `integration_settings(category='maps')` |
| Maps connection test | `POST http://procurement-admin.localhost/api/admin/maps/test-connection` with `provider=LOCAL` | `HTTP 200`, `ok=true` |
| AI config read | `GET http://procurement-admin.localhost/api/admin/ai/config` with admin token | `HTTP 200`, returns enabled/provider/model/KYC flags |
| AI config test | `POST http://procurement-admin.localhost/api/admin/ai/test` with admin token | `HTTP 200`, `ok=true` compatibility bridge response |
| KYC batch analysis empty set | `POST http://procurement-admin.localhost/api/admin/ai/batch-analyze-kyc -d '{"document_ids":[]}'` | `HTTP 200`, `ok=true`, empty results |
| KYC single document analysis | `POST http://procurement-admin.localhost/api/admin/ai/analyze-kyc-document -d '{"document_id":"$document_id"}'` | `HTTP 200`, writes Core `kyc_analysis_results`; sample response `analysis.authenticity=SUSPICIOUS` |
| Customer negative permission | Customer token requests `/admin/maps/config`, `/admin/maps/test-connection`, `/admin/ai/config`, `/admin/ai/test` | All returned `403`, Admin-only boundary holds |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Admin Action Compatibility Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Admin legacy arrays | `GET /api/admin/users`, `/staff`, `/companies`, `/orders`, `/settings` with admin token | All `HTTP 200`; all returned copied Admin legacy array shapes; sample counts: users `200`, staff `3280`, companies `200`, orders `200`, settings `47` |
| Staff invite action | `POST http://procurement-admin.localhost/api/admin/staff/invite` with role `ADMIN` | `HTTP 201`, created smoke staff user `d76a9f21-2eae-489e-bc30-9b13d00f3bc7` in Core users |
| Staff role action | `PUT /api/admin/staff/d76a9f21-2eae-489e-bc30-9b13d00f3bc7/role -d '{"role":"SUPPORT_AGENT"}'` | `HTTP 200`, legacy response role `SUPPORT_AGENT`; Core role mapped to internal staff role |
| Staff/user status action | `POST /api/admin/users/d76a9f21-2eae-489e-bc30-9b13d00f3bc7/status -d '{"status":"SUSPENDED"}'` | `HTTP 200`, legacy response status `INACTIVE`, portal access suspended |
| Settings save action | `PUT /api/admin/settings/smoke_codex_route -d '{"value":"20260619235028"}'` | `HTTP 200`, saved value through Core `platform_settings` compatibility shape |
| Order status action | `POST /api/admin/orders/$order_id/status` with current copied Admin legacy status | `HTTP 200`, sample response status `AWAITING_PAYMENT` |
| Company verification/status actions | `PATCH /api/admin/companies/$company_id/verification?level=BUSINESS` and `/status?status=ACTIVE` | Both `HTTP 200`, response `verification_level=BUSINESS`, `status=ACTIVE` |
| Customer negative permission | Customer token requests `/admin/users`, `/admin/settings`, `POST /admin/users/$staff_id/status`, `PUT /admin/settings/smoke_codex_route` | All returned `403`, Admin-only boundary holds |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Admin Audit / Notifications / Backups Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Admin legacy arrays | `GET /api/admin/audit-logs?limit=20`, `/notification-templates`, `/notifications`, `/backups/schedules`, `/backups/jobs?limit=20` with admin token | All `HTTP 200`; all returned copied Admin legacy array shapes; sample counts: audit logs `20`, templates `42`, notifications `100`, schedules `84`, jobs `20` |
| Notification template update | `PUT /api/admin/notification-templates/legacy-order-awarded` with subject/body/active payload | `HTTP 200`, template key `legacy-order-awarded` returned |
| Test notification | `POST /api/admin/notifications/test?channel=IN_APP` with admin token | `HTTP 201`, message `Test notification queued for IN_APP`, Core `portal_notifications` row created |
| Backup schedule create | `POST /api/admin/backups/schedules` with weekly schedule payload | `HTTP 201`, created schedule `580ff651-eb54-4797-99e9-ff3c76bd9a20` |
| Backup schedule toggle | `PATCH /api/admin/backups/schedules/580ff651-eb54-4797-99e9-ff3c76bd9a20 -d '{"enabled":false}'` | `HTTP 200`, response `enabled=false` |
| Backup schedule delete | `DELETE /api/admin/backups/schedules/580ff651-eb54-4797-99e9-ff3c76bd9a20` | `HTTP 204` |
| Customer negative permission | Customer token requests `/admin/audit-logs`, `/admin/notification-templates`, `POST /admin/notifications/test`, `/admin/backups/schedules`, and `POST /admin/backups/schedules` | All returned `403`, Admin-only boundary holds |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Admin Dashboard / Marketplace Management Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Admin dashboard | `GET http://procurement-admin.localhost/api/admin/dashboard` with admin token | `HTTP 200`, real Core counts returned: users `11964`, buyers `6429`, suppliers `2091`, active intents `310`, open disputes `235`, pending company verifications `491`, captured escrow orders `67`, open risk flags `271`, escrow held `146700000` |
| Marketplace filters | `GET http://procurement.localhost/api/marketplace/filters` | `HTTP 200`, returned `1333` Core categories and market modes `B2B/B2C/BOTH` |
| Admin marketplace list | `GET http://procurement-admin.localhost/api/admin/marketplace/items?page_size=5` with admin token | `HTTP 200`, total `1351`, first item `c6c49a24-1244-4f93-a3e4-f905e55ce860`, status `ACTIVE`, company `Security vendor b0fce4f5f2` |
| Admin marketplace status update | `PATCH /api/admin/marketplace/items/c6c49a24-1244-4f93-a3e4-f905e55ce860 -d '{"status":"INACTIVE"}'` then restore to `ACTIVE` | Both `HTTP 200`; status changed to `INACTIVE` then back to `ACTIVE`; audit event emitted through Core compatibility bridge |
| Customer negative permission | Customer token requests `GET /api/admin/dashboard`, `GET /api/admin/marketplace/items`, and `PATCH /api/admin/marketplace/items/{id}` | All returned `403`, Admin-only boundary holds |
| Old brand scan | `rg -n "ProcurePing\|procureping" Ainerwise/modules/procurement -S` | No matches; Admin login default is `admin@ainerwise.com`, PC/H5 local demo helper uses `demo.ainerwise.com` |
| Browser sanity | In-app Browser opened `http://procurement-admin.localhost/login`, logged in as `admin@ainerwise.com`, then opened `/marketplace` | Login and Marketplace rendered AinerWise brand, Marketplace table columns present, `hasOldBrand=false`, console error log empty |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Profile / Upload / Direct Marketplace Order Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py Ainerwise/backend/app/api/v1/endpoints/auth.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Core route import | `curl -sS -o /tmp/pzl21-openapi.json -w '%{http_code}' http://localhost/api/v1/openapi.json` | `200` |
| Account context | `GET http://procurement.localhost/api/auth/me/account-context` with new buyer token | `HTTP 200`, user email `pzl21-buyer-1781938211@example.com` |
| Buyer company profile upsert | `PATCH /api/buyer/company-profile` then `GET /api/buyer/company-profile` | Both `HTTP 200`; Core company `dd77c86e-9d65-4abe-820e-368e4c8e8aea`, registration `REG-1781938211` |
| Buyer team list/invite/remove | `GET /api/buyer/team/members`, `POST /api/buyer/team/invite`, `DELETE /api/buyer/team/members/5e88469f-2118-42ab-b51b-9181427cb34c` | `200`, `201`, `204`; invited member created then suspended through Core portal access |
| Generic upload | `POST /api/uploads` multipart file `pzl21.txt` | `HTTP 201`, returned `minio://ainerwise/uploads/6705131d-6d08-4904-8d58-91d768ecf686/e6159932-fd81-47f5-8783-194397760667/pzl21.txt` |
| Trust profile | `GET /api/trust/me` with buyer token | `HTTP 200`, returned Core trust score envelope |
| Reverse geocode | `GET /api/maps/reverse-geocode?lat=10.3157&lng=123.8854` | `HTTP 200`, local deterministic address contains `Cebu City` |
| Password negative | `PATCH /api/users/me/password -d '{"current_password":"wrong","new_password":"AnotherPass123!"}'` | `400`, `Current password is incorrect` |
| Marketplace direct order | `POST /api/orders -d '{"catalog_item_id":"121d78f3-d28f-460c-b15b-908c94c9b756","qty":2,"delivery_city":"Cebu"}'` | `HTTP 201`, Core order `4f14c735-a551-4c23-be04-e8ea41e222f6` created from active listing |
| Buyer order read | `GET /api/orders/4f14c735-a551-4c23-be04-e8ea41e222f6` with creating buyer token | `HTTP 200`, legacy order id matches |
| Cross-buyer order denial | `GET /api/orders/4f14c735-a551-4c23-be04-e8ea41e222f6` with unrelated buyer token | `403`, `Not a party to this order` |
| Supplier account-type switch | `PATCH /api/auth/me/account-type -d '{"account_type":"BUSINESS"}'` then `GET /api/auth/me` | `HTTP 200`; test account `pzl21-supplierflow-1781938211@example.com` role became `vendor` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Shipping Estimate Compatibility Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Admin creates route | `POST http://procurement-admin.localhost/api/admin/shipping/routes -H "Authorization: Bearer $admin_token" -d '{"origin_country":"PH","dest_country":"PH","shipping_method":"LOCAL_DELIVERY","description":"PZL24 route 1781939519","status":"ACTIVE"}'` | `HTTP 201`, route `8e208612-6231-48f4-b080-ce16b2bd29dd` |
| Admin creates rate | `POST http://procurement-admin.localhost/api/admin/shipping/rates -H "Authorization: Bearer $admin_token" -d '{"route_id":"8e208612-6231-48f4-b080-ce16b2bd29dd","weight_min_kg":0,"weight_max_kg":10000,"price_per_kg_minor":123,"currency":"PHP","min_charge_minor":1000,"estimated_days_min":1,"estimated_days_max":3,"status":"ACTIVE"}'` | `HTTP 201`, rate `2c081e52-2e21-44f1-ac69-4fd160ac2587` |
| Buyer shipping estimate | `POST http://procurement.localhost/api/shipping/estimate -H "Authorization: Bearer $buyer_token" -d '{"origin_country":"Philippines","dest_country":"PH","weight_kg":10,"declared_value_minor":500000,"currency":"PHP"}'` | `HTTP 200`; `estimates[0].total_shipping_minor=1230`; retained `items[0].cost_minor=1230` |
| Unauthenticated denial | `POST http://procurement.localhost/api/shipping/estimate -d '{"origin_country":"PH","dest_country":"PH","weight_kg":10}'` | `401` |
| Invalid weight validation | `POST http://procurement.localhost/api/shipping/estimate -H "Authorization: Bearer $buyer_token" -d '{"origin_country":"PH","dest_country":"PH","weight_kg":0}'` | `422` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Supplier Inbox / Offer Submission Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Buyer creates intent | `POST http://procurement.localhost/api/intents -H "Authorization: Bearer $buyer_token" -d '{"title":"PZL25 real supplier inbox chain","category_id":"00000000-0000-0000-0000-000000000001","qty":12,"unit":"set","budget_max_minor":240000,"currency":"PHP","country":"PH","city":"Cebu City","notes":"Need supplier-visible request for PC inbox."}'` | `HTTP 201`, intent `2624f09f-fcce-45e3-8cae-ebc5f00ab55a` |
| Buyer publishes intent | `POST http://procurement.localhost/api/intents/2624f09f-fcce-45e3-8cae-ebc5f00ab55a/publish -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, intent status becomes supplier-matchable |
| Supplier matching inbox API | `GET http://procurement.localhost/api/supplier/intents/matching -H "Authorization: Bearer $supplier_token"` | `HTTP 200`, matching list contains intent `2624f09f-fcce-45e3-8cae-ebc5f00ab55a` |
| Buyer denied supplier inbox API | `GET http://procurement.localhost/api/supplier/intents/matching -H "Authorization: Bearer $buyer_token"` | `403` |
| Supplier submits offer | `POST http://procurement.localhost/api/intents/2624f09f-fcce-45e3-8cae-ebc5f00ab55a/offers -H "Authorization: Bearer $supplier_token" -d '{"qty_available":12,"unit_price_minor":10000,"delivery_fee_minor":30000,"currency":"PHP","tier":"GOOD","stock_confidence":"FIRM","message":"PZL25 supplier offer","warranty":"7 days"}'` | `HTTP 201`, offer `0ac683ef-6df5-4c73-907c-36cf9652a372`, `total_price_minor=150000` |
| Duplicate supplier offer denial | Repeat supplier submit on same intent | Non-2xx with `offer already exists for this supplier` |
| Buyer sees offer | `GET http://procurement.localhost/api/intents/2624f09f-fcce-45e3-8cae-ebc5f00ab55a/offers -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, buyer-visible offers include `0ac683ef-6df5-4c73-907c-36cf9652a372` |
| Unrelated buyer offer denial | `POST http://procurement.localhost/api/intents/2624f09f-fcce-45e3-8cae-ebc5f00ab55a/offers -H "Authorization: Bearer $other_buyer_token" -d '{...}'` | `403` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### H5 Buyer Request Detail Candidates / Offers Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| H5 mock removal scan | `rg -n "Mock|mock|MOCK_|demoSupplierCandidatesForIntent|isDemoToken|startsWith\\('m'\\)" Ainerwise/modules/procurement/h5/pages/buyer/requests/[id].vue` | No matches |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Supplier company required | `POST http://procurement.localhost/api/supplier/catalog/items -H "Authorization: Bearer $supplier_without_company_token" -d '{"title":"PZL26 H5 Candidate Catalog Item","price_minor":123400,"currency":"PHP"}'` | `403`, `Supplier company required` |
| Supplier company and catalog item | `POST /api/companies` then `POST /api/supplier/catalog/items` with supplier token | `HTTP 201`, catalog listing `95638d77-1333-40f5-a286-0b29f2d99c41` |
| Buyer intent and publish | `POST /api/intents` then `POST /api/intents/6b70d0c8-42e2-4fa5-b51b-1ae25ad3a9e2/publish` with buyer token | `HTTP 201` then `HTTP 200`, request is supplier-matchable |
| Buyer candidate list | `GET http://procurement.localhost/api/intents/6b70d0c8-42e2-4fa5-b51b-1ae25ad3a9e2/supplier-candidates -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, response has `items`, `candidate_total=20`, and includes listing `95638d77-1333-40f5-a286-0b29f2d99c41` |
| Cross-buyer candidate denial | Same candidate list with unrelated buyer token | `403` |
| Buyer binds supplier listing | `POST http://procurement.localhost/api/intents/6b70d0c8-42e2-4fa5-b51b-1ae25ad3a9e2/supplier-candidates/95638d77-1333-40f5-a286-0b29f2d99c41/bind -H "Authorization: Bearer $buyer_token" -d '{"note":"PZL26 bind smoke"}'` | `HTTP 200`, status `matching` |
| Cross-buyer bind denial | Same bind with unrelated buyer token | `403` |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### H5 Buyer Request List Empty-State Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| H5 request-list mock removal scan | `rg -n "MOCK_INTENTS|Mock data fallback|m1|Portland Cement Type I" Ainerwise/modules/procurement/h5/pages/buyer/requests/index.vue` | No matches |
| New buyer empty list | `GET http://procurement.localhost/api/intents/my?page=1&page_size=20 -H "Authorization: Bearer $pzl27_buyer_token"` | `HTTP 200`, initial item count `0` |
| Real intent appears in list | `POST http://procurement.localhost/api/intents -H "Authorization: Bearer $pzl27_buyer_token" -d '{"title":"PZL27 Real H5 Request List Item","qty":1,"unit":"set","budget_max_minor":100000,"currency":"PHP","country":"PH","city":"Cebu City"}'` then repeat list | `HTTP 201`, intent `ecc2d2c6-aedc-40bf-8563-b57d1e6241b9`; list count `1`, returned id matches created intent |
| Unauthenticated list denial | `GET http://procurement.localhost/api/intents/my?page=1&page_size=20` | `401` |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Admin Users No-Mock Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| PC Admin Users mock removal scan | `rg -n "Fallback to mock|Demo Buyer|buyer@procurement\\.localhost|Optimistic update fallback" Ainerwise/modules/procurement/pc/pages/admin/users.vue` | No matches |
| Admin user list | `GET http://procurement.localhost/api/admin/users?page=1&page_size=5 -H "Authorization: Bearer $admin_token"` | `HTTP 200`, legacy flat array shape returned; smoke observed `200` rows in current dev data |
| Buyer denied admin list | `GET http://procurement.localhost/api/admin/users?page=1&page_size=5 -H "Authorization: Bearer $buyer_token"` | `403` |
| Unauthenticated admin list denied | `GET http://procurement.localhost/api/admin/users?page=1&page_size=5` | `401` |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Supplier Order Detail Real Delivery Workspace Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Static order detail removal scan | `rg -n "ORD-82910|Portland Cement|Oceanic Transport|123 Construction Site|2,150|500 x|Awarded Oct|Pending Delivery" 'Ainerwise/modules/procurement/pc/pages/supplier/orders/[id].vue'` | No matches |
| Supplier reads own order detail | Register supplier with `company_name`, create `/supplier/catalog/items`, register buyer, direct create `/orders`, then `GET /orders/{order_id}` with supplier token | `HTTP 200`, returned id matched created order |
| Other supplier denied order detail | `GET http://procurement.localhost/api/orders/{order_id} -H "Authorization: Bearer $other_supplier_token"` | `403` |
| Unauthenticated order detail denial | `GET http://procurement.localhost/api/orders/{order_id}` | `401` |
| Supplier delivery update | `POST http://procurement.localhost/api/orders/{order_id}/delivery -H "Authorization: Bearer $supplier_token" -d '{"status":"DISPATCHED","tracking_number":"PZL33-TRACK"}'` then reload detail | `HTTP 201`, delivery status `DISPATCHED`; reloaded order detail returned tracking number `PZL33-TRACK` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Supplier Orders Real List Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Static sample order removal scan | `rg -n "John Doe Construction|500 bags Portland Cement|ORD-82910|const orders = \\[|id: 1, buyer" Ainerwise/modules/procurement/pc/pages/supplier/orders/index.vue` | No matches |
| Real supplier order chain | Register supplier with `company_name`, create `/supplier/catalog/items`, register buyer, direct create `/orders`, then `GET /orders/my` with supplier token | `HTTP 201/200` chain passed; created order was present in supplier list |
| Other supplier isolation | `GET http://procurement.localhost/api/orders/my -H "Authorization: Bearer $other_supplier_token"` | `HTTP 200`; created order id was not present |
| Unauthenticated orders denial | `GET http://procurement.localhost/api/orders/my` | `401` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Supplier Offers Real List Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Static sample row removal scan | `rg -n "OFF-101|OFF-102|OFF-103|Marine Engine Parts|Office Laptops|John Doe Construction|Oceanic Shipping|Tech Startup XYZ|const offers = \\[" Ainerwise/modules/procurement/pc/pages/supplier/offers/index.vue` | No matches |
| Real supplier offer chain | Register supplier with `company_name`, create `/supplier/catalog/items`, register buyer, create `/intents`, publish intent, submit `/intents/{intent_id}/offers`, then `GET /supplier/offers` with supplier token | `HTTP 201/200` chain passed; created offer was present in supplier list |
| Buyer denied supplier offers | `GET http://procurement.localhost/api/supplier/offers -H "Authorization: Bearer $buyer_token"` | `403` |
| Unauthenticated supplier offers denial | `GET http://procurement.localhost/api/supplier/offers` | `401` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Admin Offers / Intents Real List Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Static sample row removal scan | `rg -n "OFF-101|OFF-102|INT-82910|INT-82911|John Doe Construction|Global Build Supply|Oceanic Shipping|Tech Startup XYZ|500 bags Portland Cement|Office Laptops|const offers = \\[|const intents = \\[" Ainerwise/modules/procurement/pc/pages/admin/offers.vue Ainerwise/modules/procurement/pc/pages/admin/intents.vue` | No matches |
| Admin offers list | `GET http://procurement.localhost/api/admin/offers?limit=5 -H "Authorization: Bearer $admin_token"` | `HTTP 200`, current dev data returned `5` real Core offers |
| Admin intents list | `GET http://procurement.localhost/api/admin/intents?limit=5 -H "Authorization: Bearer $admin_token"` | `HTTP 200`, current dev data returned `5` real Core intents |
| Buyer denied admin offers/intents | Same endpoints with buyer token | Both returned `403` |
| Unauthenticated admin offers/intents denial | Same endpoints without token | Both returned `401` |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### PC Admin Pricing Intelligence Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Static benchmark/placeholder removal scan | `rg -n "placeholder|Chart rendering|Portland Cement|Steel Rebar|benchmark:|actual:" Ainerwise/modules/procurement/pc/pages/admin/pricing-intel.vue` | No matches |
| Admin analytics source APIs | `GET http://procurement.localhost/api/admin/offers?limit=500` and `GET http://procurement.localhost/api/admin/intents?limit=500` with admin token | `HTTP 200`; current dev data returned `500` offers and `500` intents |
| Buyer denied analytics APIs | Same endpoints with buyer token | Both returned `403` |
| Unauthenticated analytics denial | `GET http://procurement.localhost/api/admin/offers?limit=10` | `401` |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

### Password Reset Entrypoint Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Anonymous reset request | `curl -sS -o /tmp/pzl23_reset.json -w '%{http_code}' -X POST http://procurement.localhost/api/auth/request-password-reset -H 'Content-Type: application/json' -d '{"email":"pzl23-reset@example.com"}'` | `HTTP 200`, generic response `If an active account exists for that email, a password reset link has been sent.` |
| PC forgot-password route | `curl -sS -o /tmp/pzl23_pc_forgot.html -w '%{http_code}' http://procurement.localhost/forgot-password` | `HTTP 200`, page size `10865` bytes |
| H5 reset-password route | `curl -sS -o /tmp/pzl23_h5_reset.html -w '%{http_code}' http://procurement-h5.localhost/auth/reset-password` | `HTTP 200`, page size `3985` bytes |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; `forgot-password` chunk emitted |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed; `reset-password` chunk emitted |

### Address / Ranking Compatibility Bridge Evidence

Recorded by implementation agent on 2026-06-20. Status is `READY_FOR_VERIFY`; an independent verification agent must rerun these before marking `VERIFIED`.

| Check | Command | Result |
| --- | --- | --- |
| Backend syntax | `python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py` | PASS |
| Nginx config | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T nginx nginx -t` | PASS |
| Buyer address create | `POST http://procurement.localhost/api/addresses -H "Authorization: Bearer $buyer_token" -d '{"address_type":"DELIVERY_TO","label":"PZL22 Site","contact_name":"PZL22 Buyer","phone":"+639000000000","country":"Philippines","city":"Cebu City","address_line1":"IT Park","is_default":true}'` | `HTTP 201`, Core address `298df768-630b-4a16-b211-bd6dce8af739` |
| Buyer address list | `GET http://procurement.localhost/api/addresses?address_type=DELIVERY_TO -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, legacy flat array shape returned |
| Buyer address update | `PATCH http://procurement.localhost/api/addresses/298df768-630b-4a16-b211-bd6dce8af739 -H "Authorization: Bearer $buyer_token" -d '{"city":"Mandaue City"}'` | `HTTP 200`, city updated |
| Buyer default address | `POST http://procurement.localhost/api/addresses/298df768-630b-4a16-b211-bd6dce8af739/set-default -H "Authorization: Bearer $buyer_token"` | `HTTP 200`, address marked default |
| Cross-buyer address denial | `PATCH http://procurement.localhost/api/addresses/298df768-630b-4a16-b211-bd6dce8af739 -H "Authorization: Bearer $other_buyer_token"` | `404`, `Address not found` |
| Admin ranking profiles | `GET http://procurement-admin.localhost/api/ranking/profiles -H "Authorization: Bearer $admin_token"` | `HTTP 200`, 5 built-in profiles returned |
| Admin ranking update | `PATCH http://procurement-admin.localhost/api/ranking/profiles/default -H "Authorization: Bearer $admin_token" -d '{"weights":{"price":0.35,"trust":0.26,"distance":0.15,"delivery":0.15,"compliance":0.09}}'` | `HTTP 200`, profile weights persisted, then restored to trust `0.25` |
| Admin ranking summary | `GET http://procurement-admin.localhost/api/admin/ranking/summary -H "Authorization: Bearer $admin_token"` | `HTTP 200`, returns profile count and active profile |
| Built-in ranking delete denial | `DELETE http://procurement-admin.localhost/api/ranking/profiles/default -H "Authorization: Bearer $admin_token"` | `409`, built-in profile protected |
| Buyer ranking denial | `GET http://procurement.localhost/api/ranking/profiles -H "Authorization: Bearer $buyer_token"` and `GET /api/admin/ranking/summary` | Both `403` |
| Buyer address delete | `DELETE http://procurement.localhost/api/addresses/298df768-630b-4a16-b211-bd6dce8af739 -H "Authorization: Bearer $buyer_token"` | `204`; later address list no longer contains deleted address |
| Procurement PC build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-pc npm run build` | PASS, Nuxt production build completed; known external asset warnings only |
| Procurement H5 build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-h5 npm run build` | PASS, Nuxt production build completed |
| Procurement Admin build | `docker compose -f docker-compose.yml -f docker-compose.procurement-standalone.yml exec -T procurement-admin npm run build` | PASS, Vite production build completed |

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
| Page count | `find Ainerwise/modules/procurement/pc/pages -type f \| wc -l` | `60` |
| H5 count | `find Ainerwise/modules/procurement/h5/pages -type f \| wc -l` | `41` |
| Admin count | `find Ainerwise/modules/procurement/admin/src/pages -type f \| wc -l` | `23` |

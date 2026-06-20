# AinerWise Task Tracker

Status legend: `TODO` | `IN_PROGRESS` | `READY_FOR_VERIFY` | `DONE` | `VERIFIED` | `FAILED_VERIFY` | `BLOCKED`

---

## Shared Auth & SSO Middleware V1

Principle:

> One AinerWise account can move across PC, H5, Admin, Marketing, and Procurement surfaces without creating another account. Physical backoffice stays as one `frontend-admin`; Marketing, Cebu Admin, Access Center, AI Supervisor, Finance, Field Ops, and other panels are logical workbenches controlled by Membership, Portal Grant, Manifest, Route, Menu, and Permission.

| # | Task | Status | Notes |
|---|------|--------|-------|
| SSO.1 | Write shared auth/SSO/access-control task rules for other agents | READY_FOR_VERIFY | This section is the handoff contract; implementation agents still cannot mark `VERIFIED` |
| SSO.2 | Extract PC/H5/Admin duplicated `useAuth` into shared SDK | READY_FOR_VERIFY | `Ainerwise/shared/auth/useSharedAuth.ts`; wrappers remain in each frontend for local policies |
| SSO.3 | Keep one physical admin frontend and expose Access Center logical workbench | READY_FOR_VERIFY | `/access-center` in `frontend-admin`; route is governed by `admin_audit` manifest |
| SSO.4 | Access Center shows account role, active state, available portal/workspace context, and role-to-portal policy | READY_FOR_VERIFY | Reads real `/users` and `/auth/me/portals`; role editing stays in `/users` |
| SSO.5 | Verify cross-port login reuse for `localhost:4099`, `4098`, `4097`, `4094` | TODO | Needs Browser/E2E verification with real login cookies |
| SSO.6 | Add formal cross-subdomain SSO bridge for `*.localhost` and future production domains | TODO | Host-only cookies work across same `localhost` ports, not across `procurement.localhost` aliases |
| SSO.7 | Add fine-grained Portal Grant admin editor with workspace/region isolation | TODO | Must write positive/negative permission tests before implementation |
| SSO.8 | Cut Procurement copied module auth to AinerWise Core SSO | READY_FOR_VERIFY | Copied PC/H5/Admin auth stores now use Core `/auth/*`; demo buyer login through `procurement.localhost` returns Core JWT; formal cross-subdomain cookie SSO remains SSO.6 |

Strict rules for follow-up agents:

- Do not create separate user tables or isolated login systems for Marketing, Cebu Admin, Procurement, Field Ops, or AI Supervisor.
- Do not add another physical admin app unless the architecture constitution is amended first.
- Do not use static grants in the UI to bypass `/auth/me/portals` and `/auth/portal-switch`.
- Implementation agents may mark only `READY_FOR_VERIFY`; independent verification agents mark `VERIFIED`.

Verification evidence recorded by implementation agent on 2026-06-19:

- `npm run build` passed in `Ainerwise/frontend-pc`.
- `npm run build` passed in `Ainerwise/frontend-h5`.
- `npm run build` passed in `Ainerwise/frontend-admin`.
- `python3 -m py_compile Ainerwise/backend/app/core/portal_registry.py` passed.
- Unauthenticated `http://localhost:4097/access-center` returns `302 /login?redirect=/access-center`.
- Admin Core cookie can load `http://localhost:4097/access-center` with `HTTP 200` and page markers `Access Center`, `Shared Auth`, `Manage User Roles`.
- Same Admin Core cookie can load `http://localhost:4094/marketing` with `HTTP 200`.
- `/api/v1/auth/me/portals` returned `HTTP 200`, `19` portal grants, and `1` membership for the demo admin account.
- `http://procurement.localhost/api/auth/login` with `demo@ainerwise.com / demo123` returns a Core buyer JWT.
- `http://procurement.localhost/api/auth/me`, `/api/users/me`, and `/api/intents/my` work with that Core token.

## AinerWise Procurement Core API Bridge V1

Principle:

> AinerWise Procurement keeps independent PC/H5/Admin entrypoints, but user identity and business data must flow through AinerWise Core middleware, not a separate Cebu backend.

| # | Task | Status | Notes |
|---|------|--------|-------|
| PZL.1 | Keep root `CebuProjects` read-only and copy PC/H5/Admin into `Ainerwise/modules/procurement` | READY_FOR_VERIFY | Root `CebuProjects` status remains clean; current counts: PC 60 after restoring missing forgot-password entrypoint, H5 41, Admin 23 |
| PZL.2 | Remove old user-visible `ProcurePing` brand and old backend API defaults | READY_FOR_VERIFY | `NUXT_PUBLIC_API_BASE=/api`, `VITE_ADMIN_API_BASE=/api`; copied Procurement module scan returns zero `ProcurePing/procureping`; Admin login defaults to `admin@ainerwise.com` |
| PZL.3 | Route standalone Procurement hosts through AinerWise Core | READY_FOR_VERIFY | Nginx maps `/api/auth/*` to Core Auth, `/api/*` to `cebu-compat`, admin routes to Core admin routers |
| PZL.4 | Add Core compatibility bridge for system mode, users, categories, marketplace, payment region config, intents, offers, orders, notifications | READY_FOR_VERIFY | `Ainerwise/backend/app/api/v1/endpoints/cebu_compat.py`; `py_compile` passes |
| PZL.5 | Fix PC SSR `/api` loop by adding Nuxt routeRules and internal Core API target | READY_FOR_VERIFY | PC/H5 routeRules proxy server-side `/api/**`; `NUXT_CORE_API_INTERNAL=http://backend:8000` in standalone compose |
| PZL.6 | Verify standalone Procurement PC/H5/Admin builds | READY_FOR_VERIFY | `npm run build` passes in all three copied module directories |
| PZL.7 | Verify runtime hosts and Core API bridge | READY_FOR_VERIFY | PC/H5/Admin hosts return 200; Core auth/system-mode/payment/marketplace APIs return expected responses; unauthenticated private/admin APIs return 401 |
| PZL.8 | Full admin/KYC/wallet/payment/message parity with positive and negative permission tests | IN_PROGRESS | Do not mark complete until every original Cebu workflow is tested against Core APIs |
| PZL.9 | Wallet and deposit legacy API compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/wallets/me`, `/transactions`, `/deposits`, and `/deposits/{id}/submit-tx` route to Core wallet/deposit tables; PC/H5 wallet APIs pass; unauthenticated wallet is 401; cross-user deposit submit is 404 |
| PZL.10 | Buyer Projects / AI Project Forge main chain through AinerWise Core | READY_FOR_VERIFY | `/api/buyer/projects*` compatibility writes to Core buyer project tables; create, chat, rule-based Core analysis, line items, report, confirm, publish-to-procurement-request, PC/H5 entrypoints, and cross-user 404 verified |
| PZL.11 | Orders / Escrow / Delivery / Reviews compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/orders/*` now supports order detail with real escrow/delivery, wallet payment, supplier delivery status progression, buyer acceptance, escrow release, supplier wallet credit, seller review, buyer review, supplier review summary, and cross-supplier 403 verified |
| PZL.12 | Messages / Notifications compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/threads/order/{order_id}/messages` maps legacy PC/H5 order chat to Core `CommerceThread/CommerceMessage`; buyer post, supplier read/reply, buyer read, notification mapping, mark-read, and cross-supplier 403 verified |
| PZL.13 | Supplier Catalog / Ads compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/supplier/catalog/items`, `/api/merchant/ad-campaigns`, and `/api/admin/ad-campaigns` now route to Core `supplier_listings` and `ad_campaigns`; supplier create/list/update/delete, campaign create/submit/admin approve/supplier pause, cross-supplier 404s, Nginx `nginx -t`, backend `py_compile`, and PC/H5/Admin builds verified |
| PZL.14 | Dispute / KYC / Risk compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/disputes/*`, `/api/orders/{order_id}/dispute`, `/api/companies/me/documents`, `/api/companies/me/verification/*`, `/api/admin/disputes/*`, `/api/admin/risk-flags/*`, `/api/admin/verification/*`, and `/api/admin/kyc-media/*` now route to Core dispute/KYC/risk tables; buyer dispute detail/evidence, unrelated supplier 403, admin evidence request/resolve, supplier KYC upload/submit, admin verification/media risk flag, admin risk action, backend `py_compile`, Nginx `nginx -t`, and PC/H5/Admin builds verified |
| PZL.15 | RFQ / Intent / Offer compatibility through AinerWise Core | READY_FOR_VERIFY | `/api/intents`, `/api/intents/{id}/publish`, `/api/supplier/intents/matching`, `/api/intents/{id}/offers`, `/api/offers/{id}`, `/api/offers/{id}/withdraw`, `/api/offers/{id}/award`, `/api/admin/intents/*`, and `/api/admin/offers/*` now route to Core procurement/offer/order tables; buyer create/publish, supplier matching, two supplier offers, buyer offer detail, cross-supplier 403, supplier withdraw, admin intent flag, admin offer remove, buyer award-to-order, supplier admin 403, backend `py_compile`, Nginx `nginx -t`, and PC/H5/Admin builds verified |
| PZL.16 | Procurement Admin read-panel gap bridge through AinerWise Core | READY_FOR_VERIFY | `/api/admin/escrow`, `/deposits`, `/payouts`, `/payment-events`, `/settlement-events`, `/payment-region-configs`, `/shipping/{routes,rates,statistics}`, `/regions`, `/maps/coverage/estimate`, `/trust/users`, and `/backups/config` now return legacy array/field shapes from Core tables; admin positive smoke all 200, customer negative smoke all 403, backend `py_compile`, Nginx `nginx -t`, PC/H5/Admin builds, and browser login-page sanity pass |
| PZL.17 | Procurement Admin AI and Maps config bridge through AinerWise Core | READY_FOR_VERIFY | `/api/admin/maps/config`, `/api/admin/maps/test-connection`, `/api/admin/ai/config`, `/api/admin/ai/test`, `/api/admin/ai/analyze-kyc-document`, and `/api/admin/ai/batch-analyze-kyc` now route through Core compatibility APIs; maps config persists to `integration_settings`, KYC AI analysis writes `kyc_analysis_results`, admin positive smoke all 200, customer negative smoke all 403, backend `py_compile`, Nginx `nginx -t`, and PC/H5/Admin builds pass |
| PZL.18 | Procurement Admin action compatibility bridge through AinerWise Core | READY_FOR_VERIFY | `/api/admin/users`, `/staff`, `/companies`, `/orders`, and `/settings` now return copied Admin legacy array/field shapes and support old action verbs for staff invite/role/status, user status, company verification/status, order status, and settings save; admin smoke passed, customer negative checks returned `403`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.19 | Procurement Admin audit, notifications, and backups compatibility bridge | READY_FOR_VERIFY | `/api/admin/audit-logs`, `/notification-templates`, `/notifications/test`, `/backups/schedules`, `/backups/jobs`, and `/backups/jobs/{id}/download` now route through Core compatibility APIs; copied Admin pages receive legacy arrays and partial update shapes; admin smoke passed for template update, test notification, schedule create/toggle/delete, customer negatives returned `403`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.20 | Procurement Admin dashboard and marketplace management bridge | READY_FOR_VERIFY | `/api/admin/dashboard`, `/api/marketplace/filters`, `/api/admin/marketplace/items`, and `/api/admin/marketplace/items/{id}` now route through Core compatibility APIs; copied Admin Dashboard uses real Core counts, Marketplace uses Admin-only list/update instead of public feed/supplier mutation, admin smoke passed, customer read/write negatives returned `403`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.21 | Procurement profile, upload, account context, and direct marketplace order bridge | READY_FOR_VERIFY | `/api/buyer/company-profile`, `/api/buyer/team/*`, `/api/uploads`, `/api/trust/me`, `/api/maps/reverse-geocode`, `/api/users/me/password`, `/api/orders`, and `/api/auth/me/{account-context,account-type}` now route to AinerWise Core tables/services; smoke created real buyer/company/team/upload/direct order, unrelated buyer order read returned `403`, supplier account-type flow updated role to `vendor`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.22 | Procurement address book and ranking profile compatibility bridge | READY_FOR_VERIFY | `/api/addresses*`, `/api/ranking/profiles`, and `/api/admin/ranking/summary` now route to AinerWise Core/compatibility tables with legacy shapes; buyer address create/list/update/default/delete passed, unrelated buyer update returned `404`, admin ranking list/update/summary passed, built-in profile delete returned `409`, buyer ranking access returned `403`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.23 | Procurement password reset entrypoints | READY_FOR_VERIFY | PC `/forgot-password` restored as a standalone Procurement page, H5 `/auth/reset-password` now calls Core `/auth/request-password-reset` instead of token-confirm `/auth/reset-password`; anonymous reset request returned `200` with generic anti-enumeration response, PC/H5 reset pages rendered `200`, and Procurement PC/H5 builds pass |
| PZL.24 | Procurement shipping estimate compatibility bridge | READY_FOR_VERIFY | `/api/shipping/estimate` now routes to Core compatibility instead of old `cebu-trade` response shape; admin-created PH route/rate produced buyer estimate with `estimates[0].total_shipping_minor=1230` and retained `items[0].cost_minor`, unauthenticated request returned `401`, invalid weight returned `422`, backend `py_compile`, Nginx `nginx -t`, and Procurement PC/H5/Admin builds pass |
| PZL.25 | Procurement PC supplier inbox and offer submission real chain | READY_FOR_VERIFY | PC Supplier Inbox now loads real `/supplier/intents/matching` pings, opens `/supplier/offers/new?intent_id=...`, loads the buyer intent, calls real `/shipping/estimate`, and submits through `/intents/{intent_id}/offers`; smoke verified buyer create/publish, supplier matching, supplier offer create, buyer offer visibility, buyer role denied supplier matching `403`, unrelated buyer offer submit denied `403`, duplicate supplier offer denied, backend `py_compile`, and Procurement PC/H5/Admin builds pass |
| PZL.26 | Procurement H5 buyer request detail real candidates and offers | READY_FOR_VERIFY | H5 `/buyer/requests/[id]` no longer injects mock offers or mock supplier candidates; it consumes Core `items` from `/intents/{id}/supplier-candidates`, normalizes listing fields for mobile UI, binds via real `/supplier-candidates/{catalog_item_id}/bind`, and shows true empty states; smoke verified supplier company required before catalog create (`403`), real supplier catalog item appears in buyer candidate list, bind writes status `matching`, cross-buyer candidate read and bind both return `403`, backend `py_compile`, and Procurement PC/H5/Admin builds pass |

Follow-up agents:

- Do not reintroduce `localhost:8080`, `localhost:8012`, or a separate Cebu user database as the default runtime.
- Do not mark PZL.8 `READY_FOR_VERIFY` from page rendering alone; it requires workflow, ownership, workspace, and role tests.

## Phase 1: Foundation

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Docker Compose (postgres, redis, minio, backend, celery, frontend, nginx) | VERIFIED | docker-compose.yml |
| 1.2 | Backend core: config, security (JWT+bcrypt), permissions (RBAC) | VERIFIED | app/core/ |
| 1.3 | Database session + base model (UUID + timestamps) | VERIFIED | app/db/ |
| 1.4 | All 22+ SQLAlchemy models | VERIFIED | app/models/ |
| 1.5 | Alembic setup | VERIFIED | alembic/ |
| 1.6 | Auth endpoints (register, login, refresh, me, change-password) | VERIFIED | api/v1/endpoints/auth.py |
| 1.7 | CRUD base class | VERIFIED | crud/base.py |
| 1.8 | Pydantic schemas (auth, user, product, solution, lead, base) | VERIFIED | schemas/ |
| 1.9 | Scripts (create_superadmin, seed_data) | VERIFIED | scripts/ |
| 1.10 | Celery app + notification task placeholder | VERIFIED | tasks/ |
| 1.11 | Nuxt 3 + TailwindCSS + Naive UI + i18n setup | VERIFIED | frontend/ |
| 1.12 | 3 layouts (default, portal, admin) | VERIFIED | layouts/ |
| 1.13 | Auth composable + middleware (auth, admin, guest) | VERIFIED | composables/useAuth.ts |
| 1.14 | Login + Register pages | VERIFIED | pages/login.vue, register.vue |
| 1.15 | AppHeader, AppFooter, AdminSidebar, PortalSidebar | VERIFIED | components/ |
| 1.16 | Home page with hero + sections | VERIFIED | pages/index.vue |
| 1.17 | All public pages (solutions, products, services, about, contact) | VERIFIED | pages/ |
| 1.18 | Submit requirement form (3-step) | VERIFIED | pages/submit-requirement.vue |
| 1.19 | Supplier application form | VERIFIED | pages/supplier-application.vue |
| 1.20 | Admin pages (dashboard, leads, products, vendors, solutions, settings) | VERIFIED | pages/admin/ |
| 1.21 | Portal pages (dashboard, leads, profile) | VERIFIED | pages/portal/ |
| 1.22 | i18n translations (en full, zh/sr partial) | VERIFIED | i18n/ (langDir: '.') |
| 1.23 | nginx config | VERIFIED | nginx/default.conf |

## Phase 2: Core APIs + Data

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Solutions CRUD endpoint | VERIFIED | GET public list, GET by slug, POST/PUT/DELETE admin |
| 2.2 | Products CRUD endpoint | VERIFIED | GET list + filters, GET by slug, POST/PUT admin, PATCH status |
| 2.3 | Product categories endpoint | VERIFIED | GET tree, POST/PUT admin |
| 2.4 | Leads endpoint | VERIFIED | POST create (public), GET list/detail (admin), PATCH status/assign |
| 2.5 | Vendors endpoint | VERIFIED | POST apply (public), GET list/detail (admin), PATCH status |
| 2.6 | Service packages endpoint | VERIFIED | GET public list, POST/PUT/DELETE admin |
| 2.7 | Files endpoint (MinIO presigned URLs) | VERIFIED | POST upload URL, GET download URL |
| 2.8 | Admin dashboard endpoint | VERIFIED | GET aggregated stats + recent leads/vendors |
| 2.9 | Generate + run Alembic initial migration | VERIFIED | All 24 tables created, String instead of Enum |
| 2.10 | Run seed data | VERIFIED | 13 categories, 6 solutions, 5 service packages, 4 regions |
| 2.11 | Vendor schema + CRUD | VERIFIED | VendorApply, VendorRead, VendorStatusUpdate |
| 2.12 | Service package schema | VERIFIED | ServicePackageRead/Create/Update |
| 2.13 | Fix frontend i18n locale loading | VERIFIED | langDir: '.' resolves to i18n/ dir correctly |
| 2.14 | Fix frontend component auto-import | VERIFIED | pathPrefix: false in nuxt.config |
| 2.15 | Verify all public pages render (SSR) | VERIFIED | All 10 pages return HTTP 200 with translations |
| 2.16 | Verify frontend-backend API integration | VERIFIED | API calls work client-side via localhost:8000 |

## Phase 3: Admin Management

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Lead status workflow transitions (admin) | VERIFIED | StatusWorkflow + enhanced [id].vue with notes |
| 3.2 | Product CRUD admin pages (create/edit forms) | VERIFIED | create.vue + [id]/edit.vue with status workflow |
| 3.3 | Vendor approve/reject/suspend admin | VERIFIED | [id].vue detail page with status workflow |
| 3.4 | Solution CRUD admin pages | VERIFIED | create.vue + [id]/edit.vue |
| 3.5 | Service package admin CRUD | VERIFIED | Modal-based CRUD on list page |
| 3.6 | User + Company management pages | VERIFIED | List+filter pages + backend /users, /companies endpoints |
| 3.7 | Category tree management | VERIFIED | Modal-based CRUD on list page |
| 3.8 | StatusWorkflow.vue reusable component | VERIFIED | Supports lead/product/vendor/quote/project/ticket |
| 3.9 | Users/Companies backend endpoints | VERIFIED | CRUD + role/active toggle |
| 3.10 | Lead notes endpoint | VERIFIED | PATCH /leads/{id}/notes |
| 3.11 | Placeholder pages for future features | VERIFIED | projects, quotes, tickets, etc. show "under development" |
| 3.12 | input-field CSS utility class | VERIFIED | Consistent form styling across admin |

## Phase 4: Buyer Portal + Files

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | Quote endpoints (CRUD + workflow) | VERIFIED | /quotes, /quotes/my, status transitions |
| 4.2 | Ticket endpoints (CRUD) | VERIFIED | /tickets, /tickets/my, create with buyer_user_id |
| 4.3 | MinIO file service | VERIFIED | Presigned upload/download URLs (Phase 2) |
| 4.4 | Buyer dashboard page | VERIFIED | Real stats from /leads/my, /quotes/my, /tickets/my, /projects/my |
| 4.5 | My Leads page | VERIFIED | List + detail with status tracking visualization |
| 4.6 | My Quotes page | VERIFIED | List with accept/reject buttons |
| 4.7 | My Projects page | DONE | List + detail with progress timeline (upgraded from placeholder) |
| 4.8 | My Tickets page | VERIFIED | List + create modal with priority/type |
| 4.9 | Profile edit page | VERIFIED | User info edit + change password |
| 4.10 | useFileUpload.ts composable | VERIFIED | XHR upload to MinIO with progress tracking |
| 4.11 | /leads/my endpoint | VERIFIED | Filter by buyer_company_id or contact_email |

## Phase 5: Telegram + AI

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5.1 | Telegram admin notification sender | VERIFIED | Sends when token/chat configured; otherwise skipped |
| 5.2 | Integration event service | VERIFIED | lead.created, vendor.applied, product.submitted, ai.completed |
| 5.3 | AI lead analysis (rule-based MVP) | VERIFIED | Completeness+Classify+Risk+Match+Draft pipeline |
| 5.4 | Celery AI trigger task | VERIFIED | analyze_lead and send_telegram_notification workers |
| 5.5 | Admin notification templates | VERIFIED | Telegram text templates per event type |
| 5.6 | Integration events admin page | VERIFIED | List with type/status filter + retry button |
| 5.7 | AI runs admin page | VERIFIED | List with status filter + entity links |
| 5.8 | Lead detail AI analysis UI | VERIFIED | Run Analysis button + rich result display |
| 5.9 | POST /leads/{id}/analyze endpoint | VERIFIED | Triggers AI analysis from admin |
| 5.10 | GET /ai-runs endpoint | VERIFIED | Admin list with status/entity_type filter |
| 5.11 | GET /integration-events endpoint | VERIFIED | Admin list with status/event_type filter |
| 5.12 | POST /integration-events/{id}/retry | VERIFIED | Retry failed Telegram events |
| 5.13 | schemas/integration.py | VERIFIED | AIRunRead + IntegrationEventRead |
| 5.14 | Full LangGraph orchestrator service | DONE | `services/ai_graph.py` explicit node graph (Normalize→Completeness→Classify→Risk→Match→Recommend→Compat→Draft→Summarize), in-process LangGraph-style executor; opt-in via `analyze_lead(use_graph=True)` / `POST /leads/{id}/analyze?use_graph=true`; output equivalent to MVP + graph_trace; MVP path untouched |
| 5.15 | Telegram admin bot commands | DONE | `services/telegram_bot.py` (/leads, /lead <id>, /help) + `POST /telegram/webhook`; admin-chat-gated; lead list/detail with recurring score + ARR; verified unauthorized-chat ignored |

## AI Smart Building Brain Upgrade

| # | Task | Status | Notes |
|---|------|--------|-------|
| BRAIN.1 | Rewrite public positioning | DONE | Homepage now says AI Smart Building Brain + Lead-to-Solution, not marketplace/e-commerce |
| BRAIN.2 | Add interactive AI brain demo route | DONE | /ai-building-brain-demo with scene switcher and proposal directions |
| BRAIN.3 | Replace flat demo with Three.js rendering | VERIFIED | Full-bleed 3D energy/building brain scene, animated core, nodes, links, particles |
| BRAIN.4 | Add intelligence selector L3-L5 | VERIFIED | User can switch Energy Optimized / AI Assisted / Local AI Brain; page content and 3D scene react |
| BRAIN.5 | Keep future functions bounded | DONE | Available Now, Project Dependent, Advanced Custom, Future-Ready, Concept Demo tags |
| BRAIN.6 | Add scenario-specific demo content | DONE | Villa, School, Apartment, Office, Hotel, Solar + Energy |
| BRAIN.7 | Add visual verification for 3D scene | VERIFIED | Desktop/mobile canvas attached; screenshot pixel variance checked nonblank |
| BRAIN.8 | Rename visible page language from demo to AI Brain page | DONE | Navigation and hero copy now present the page as AI Smart Building Brain; /ai-building-brain alias added; video demo can be added later |
| BRAIN.9 | Make L3-L5 visibly change the 3D world | DONE | Levels now change node density, beam count, city scale, particle atmosphere, ring intensity, and local-AI effects |
| BRAIN.10 | Add immersive smart-building objects | DONE | 3D scene now includes buildings, AI core, portal/person entry, PV panels, EV charger, robots, smart doors/windows, CCTV scan cones, and data beams |
| BRAIN.11 | Prevent 3D readout and scenario controls from overlapping | VERIFIED | Readout moved to upper-right safe zone; scenario controls wrap on desktop; browser geometry check shows no overlap |
| BRAIN.12 | Make scenarios visually different in 3D | DONE | Villa, school, apartment, office, hotel, and energy scenes now use different building layouts, colors, roofs, campus blocks, towers, hotel wings, and battery/control structures |
| BRAIN.13 | Add factory / industrial plant scene | DONE | PC 3D AI Brain now includes factory halls, production line, machinery, PLC cabinet, compressor, robots, PV/EV, and industrial energy links |
| BRAIN.14 | Make factory scenario business meaning explicit | DONE | Scenario content covers PLC/SCADA, OT network, machine energy, compressed air, chillers, motors, VFDs, robots, safety boundaries, and predictive maintenance |

## AI Assessment / Project Forge Upgrade

| # | Task | Status | Notes |
|---|------|--------|-------|
| FORGE.1 | Replace 3-step requirement form with conversational intake | VERIFIED | Chat-style AI information collector like AI Project Forge |
| FORGE.2 | Project creation only selects category first | VERIFIED | Category cards first; no long initial form |
| FORGE.3 | Dynamic questions by project category | DONE | Villa/School/Apartment/Office/Hotel/Energy use different prompts |
| FORGE.4 | Right-side smart building preview/status lights | VERIFIED | Category, Location, Site, Existing Systems, Smart Goals, Identity, Energy, Budget, Contact |
| FORGE.5 | L3-L5 target level in assessment | VERIFIED | Collect desired intelligence level and show delivery boundary |
| FORGE.6 | Submit lead from conversation transcript | DONE | Store category, extracted fields, transcript, level, and estimate-only notice through existing /leads API |
| FORGE.7 | Phase-1 CTA after enough information | DONE | Conversation can submit normal intake or mark paid Phase-1 Proposal intent after intake completion |
| FORGE.8 | Add preliminary proposal directions in Forge | DONE | Budget, Standard, Premium AI, Future Autonomous cards shown with estimate-only boundaries |
| FORGE.9 | Add Lead Score and stage calculation | DONE | Frontend and backend analysis now calculate score/stage and expose it for admin follow-up |
| FORGE.10 | Admin lead conversion panel | DONE | Admin lead detail shows score, stage, Phase-1 intent, and AI proposal tiers |
| FORGE.11 | Add factory / industrial project category | DONE | PC conversational intake now supports Factory / Industrial Plant with production, machine, OT, energy, safety, SLA, and contact questions |
| FORGE.12 | Industrial proposal ranges and summaries | DONE | Factory estimates use larger industrial ranges and explain starter visibility, line-level integration, and Premium AI predictive maintenance |

## Industrial Factory / Plant Automation Coverage

| # | Task | Status | Notes |
|---|------|--------|-------|
| IND.1 | PC AI Brain factory scenario | DONE | Adds factory-specific 3D world, style, readout chips, scenario copy, and L3-L5 behavior |
| IND.2 | H5 industrial entry point | DONE | Mobile AI Brain and submit requirement form include Factory / Industrial Plant and capture machines/protocols |
| IND.3 | Admin industrial lead view | DONE | Lead detail shows production machines, PLC/SCADA/OT systems, energy utilities, and safety/access boundary |
| IND.4 | Backend AI classification | DONE | Rule-based AI now detects factory/industrial/PLC/SCADA/machinery and returns Industrial Factory Automation & Energy |
| IND.5 | Backend industrial missing-info questions | DONE | AI asks for production machines, energy loads, industrial protocols, and safety requirements |
| IND.6 | Backend industrial risk review | DONE | Adds safety, OT network, and machine-level energy risk notes before quote commitment |
| IND.7 | Seed data for industrial capability | DONE | Adds Industrial Automation, PLC/SCADA Gateways, Machine Energy Monitoring categories and Factory Automation solution |
| IND.8 | Product capability tags for industrial protocols | DONE | Seeded 3 industrial products (machine energy meter, VFD/motor/compressor module, PLC/SCADA/robot OPC-UA connector) with OPC-UA/PLC/VFD/compressor/chiller/robot/machine-meter protocol+scenario tags, solution_line factorypulse, recurring-revenue fields |
| IND.9 | Industrial BOM templates | DONE | `services/factorypulse.py build_factorypulse_bom()` (OT gateway, machine meters, utility/compressor/chiller meters, VFD module, PLC/SCADA connector, optional edge AI box, service SLA) + proposal; surfaced in AI analysis when classification is Industrial Factory |

## Phase 6: Advanced

| # | Task | Status | Notes |
|---|------|--------|-------|
| 6.1 | Project management (10-state) | DONE | Backend CRUD + admin list/detail/create + portal list/detail + StatusWorkflow aligned |
| 6.2 | Service partner CRUD | DONE | Backend schema/CRUD/endpoints + admin page with create/detail/verify/suspend |
| 6.3 | Certification records | DONE | Backend schema/CRUD/endpoints + admin page with owner_type/status filters, expiry tracking, CRUD modal |
| 6.4 | Compatibility matrix | DONE | Backend schema/CRUD/endpoints + admin page with protocol filter, level/test_status badges, CRUD modal |
| 6.5 | Warranty policies | DONE | Backend schema/CRUD/endpoints + admin page with region filter, warranty months cards, SLA/spare parts JSON |
| 6.6 | Audit log service + viewer | DONE | services/audit.py + GET /audit-logs endpoint + admin page with filters |
| 6.7 | Region management | DONE | Backend schema/CRUD/endpoints + admin page with create/edit/activate |
| 6.8 | Quote PDF generation | DONE | reportlab service + GET /quotes/{id}/pdf endpoint + PDF download button on admin quotes page |
| 6.9 | Admin quotes management page | DONE | List with status filter + create modal + status actions |
| 6.10 | Admin tickets management page | DONE | List with status filter + status workflow actions |
| 6.11 | Audit logging in status changes | DONE | Lead, product, project status changes logged to audit_logs |
| 6.12 | Portal projects list + detail | DONE | Progress timeline, project details, team view |
| 6.13 | Portal dashboard projects count | DONE | Added /projects/my to Promise.allSettled in portal dashboard |

## P1 Operational Closed Loop (Service Partner + Site Survey + Quote Draft)

| # | Task | Status | Notes |
|---|------|--------|-------|
| P1.1 | Site survey CRUD endpoints | DONE | GET/POST/PUT/DELETE nested under /leads/{id}/surveys |
| P1.2 | Site survey schemas + CRUD | DONE | SiteSurveyRead/Create/Update + crud_site_survey |
| P1.3 | Create project from lead endpoint | DONE | POST /projects/from-lead/{lead_id} — pre-populates fields |
| P1.4 | Assign partner to project endpoint | DONE | POST /projects/{id}/assign-partner with verified check |
| P1.5 | Remove partner from project endpoint | DONE | DELETE /projects/{id}/team/{partner_id} |
| P1.6 | Draft quote from lead endpoint | DONE | POST /quotes/draft-from-lead/{lead_id} — AI-informed line items |
| P1.7 | Admin lead detail: Site Survey UI | DONE | Create survey form + list surveys on lead detail page |
| P1.8 | Admin lead detail: Create Project button | DONE | One-click project creation with link to created project |
| P1.9 | Admin lead detail: Draft Quote button | DONE | One-click quote drafting with link to quotes page |
| P1.10 | Admin project detail: Partner assignment | DONE | Select verified partner, assign role, remove from team |

## Product Capability + Lead Score + Proposal/BOM Data Layer

| # | Task | Status | Notes |
|---|------|--------|-------|
| DATA.1 | Product model: 6 capability columns | DONE | protocol_json, scenario_tags_json, intelligence_level_min/max, feature_status, risk_level |
| DATA.2 | Lead model: 5 score/stage columns | DONE | lead_score, lead_stage, desired_intelligence_level, conversation_json, proposal_tiers_json |
| DATA.3 | ProposalPlan + BOMItem models | DONE | New models with full cost breakdown, tier, intelligence, flags |
| DATA.4 | Alembic migration 002 | DONE | Adds product/lead columns + proposal_plans/bom_items tables |
| DATA.5 | Proposal schemas (Read/Create/Update) | DONE | ProposalPlan + BOMItem Pydantic schemas |
| DATA.6 | Proposal CRUD + endpoints | DONE | Full CRUD for proposals + nested BOM items, registered in api.py |
| DATA.7 | Product schemas updated | DONE | protocol_json, scenario_tags, intelligence, feature_status, risk_level in Read/Create/Update |
| DATA.8 | Lead schemas updated | DONE | lead_score, lead_stage, desired_intelligence_level, conversation/proposal JSON + LeadUpdate schema |
| DATA.9 | Admin proposals list page | DONE | Tier filter, cost range display, complexity badges, create/edit modal |
| DATA.10 | Admin BOM editor page | DONE | Full bill-of-materials table with add/edit/delete items, cost totals, flags (Own/Supply/Install/Design) |
| DATA.11 | Lead detail: intelligence level display | DONE | 3-column score/stage/intelligence panel with native field fallback |
| DATA.12 | Sidebar: Proposals link | DONE | Added under Business section |

## Facility Intelligence + Lifecycle LTV Rebuild

Source plans:

- `ainerwise_ltv_facility_intelligence_rebuild.md`
- `ainerwise_lifecycle_finance_warranty_amc_plan.md`

Execution rule:

> Build a sellable StorageGuard lifecycle loop first. Reuse that foundation for KitchenGuard and AquaGuard before expanding every solution line. Public pages sell outcomes and service packages; admin pages retain supplier, model, cost, margin, warranty, and lifecycle details.

### FI.0 Positioning + Service Boundary

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.0.1 | Replace public service ladder with 3-year included remote assurance, annual lifecycle care, and custom SLA plan | VERIFIED | PC + H5 service pages and seed data updated; on-site visits quoted separately |
| FI.0.2 | Publish warranty, paid on-site service, and controlled spare-parts boundary copy | VERIFIED | Public service page now separates supplier warranty from AinerWise service responsibility |
| FI.0.3 | Remove speculative region-expansion paragraph from About page | VERIFIED | PC + H5 About pages no longer promise expansion regions |
| FI.0.4 | Rewrite homepage positioning from Smart Building only to AI Facility Intelligence | DONE | PC + H5 hero retitled 'AI Facility Intelligence for Buildings, Energy, Storage and Industrial Sites' (en/zh/sr); hero signals + BuildingBrainMap flagship kept |
| FI.0.5 | Add homepage solution matrix with recurring-revenue carriers | DONE | PC homepage 'Solution Matrix' section: 8 lines x {scene, risk, monitored outcome, why-annual-service carrier, availability tag, CTA}; StorageGuard->page, BuildingBrain->AI Brain, others->assessment |
| FI.0.6 | Add public copy guardrails | DONE | Homepage guardrail strip (presents outcomes/points/packages, never supplier part numbers/internal models/device cost); verified public product API leaks none of cost_price/internal_model/supplier_id/margin |

### FI.1 StorageGuard Sellable Vertical Slice (P0)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.1.1 | Add StorageGuard solution seed data and `/solutions/storageguard` content | DONE | Seeded `storageguard` solution (seed_data.py) + PC/H5 demo fallback; `/solutions/storageguard` renders via `[slug].vue` |
| FI.1.2 | Add StorageGuard public landing sections | DONE | New `lifecycle_content_json` (migration 004) renders monitoring points, alert channels, reports, calibration/consumables, recurring charges, AMC options, service boundary on PC + H5 |
| FI.1.3 | Add StorageGuard project type to PC + H5 AI Facility Assessment | DONE | PC chat intake `storage` category + question bank + preview modules; H5 `cold_storage` form block; both map storage fields into site_info_json |
| FI.1.4 | Add StorageGuard rule-based AI classification and missing-info prompts | DONE | ai_analysis `_classify`/`_missing_fields`/`_questions_for` route StorageGuard (precedence over warehouse-factory); services/storageguard.py keywords + questions |
| FI.1.5 | Add StorageGuard proposal template | DONE | `build_storageguard_proposal()`: hardware, install, platform, first-year (included), Compliance AMC, calibration, consumables, first-year + recurring totals, 3yr contract; surfaced in AI output as `lifecycle_proposal` |
| FI.1.6 | Add StorageGuard BOM template | DONE | `build_storageguard_bom()`: gateway, monitoring points, door sensors, outage alert, optional local display, spare kit, calibration line; no supplier cost/model; surfaced as `bom_template` |
| FI.1.7 | Add StorageGuard demo buyer project | DONE | `create_demo_buyer.py` ensures (idempotent) a StorageGuard lead + project for demo@ainerwise.com; project_plan_json carries 24 points, high compliance risk, initial cost, ARR, Compliance AMC, calibration due 2027-01-15, 5-step alert flow, and report preview; rendered in PC + H5 project detail |
| FI.1.8 | Add StorageGuard report preview component | DONE | PC + H5 `StorageGuardReportPreview.vue` components render the monthly compliance summary (per-room compliance %, door/outage/alert totals, calibration status); tagged Sample; shown on both project detail pages |

### FI.2 Lifecycle Data Foundation (P0)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.2.1 | Add `solution_line` taxonomy | DONE | `models/constants.py SOLUTION_LINES` (8 lines) + `solution_line` column on solutions/products/leads/monitoring_points + enum-like constants for warranty/AMC/inventory/maintenance |
| FI.2.2 | Extend Product with recurring-revenue fields | DONE | solution_line, public_name, internal_model, supplier_id (FK companies), recurring_revenue_types_json, consumable/calibration cycle, expected_lifetime, replacement_margin, compliance/AMC flags, service_dependency_level; ProductRead keeps internal_model/supplier_id/margin hidden |
| FI.2.3 | Extend Lead with recurring-revenue qualification fields | DONE | solution_line, recurring_revenue_score, compliance_risk_level, consumable_potential, amc_potential, estimated_arr, estimated_ltv, is_multi_site, monitoring_points_count |
| FI.2.4 | Extend Ticket coverage fields | DONE | affected_device, monitoring_point_id (FK), warranty_related, amc_covered, is_paid_service, coverage_type, estimated_cost, resolution |
| FI.2.5 | Add Supplier Warranty model | DONE | `supplier_warranties` table + schemas (warranty type, shipping responsibility, response days, replacement policy, firmware/debug/API support, region limit) |
| FI.2.6 | Add Customer Warranty model | DONE | `customer_warranties` table + schemas (model, dates, device scope JSON, labor, remote support, on-site quota, spare coverage, annual claim cap) |
| FI.2.7 | Add AMC Contract model | DONE | `amc_contracts` table + schemas (package, pricing_mode, dates, renewal_status, coverage/exclusions JSON, included visits, response target, recurring_fee) |
| FI.2.8 | Add Monitoring Point model | DONE | `monitoring_points` table + schemas (project, solution_line, site, device, point_type, unit, thresholds, calibration cycle + dates, status) |
| FI.2.9 | Add Inventory Item + Stock Movement models | DONE | `inventory_items` + `stock_movements` tables + schemas (location, qty, reserved, reorder, expiry, cost, project allocation, inbound/outbound history) |
| FI.2.10 | Add Maintenance Schedule + Calibration Record models | DONE | `maintenance_schedules` + `calibration_records` tables + schemas (task types, due/frequency, AMC coverage, certificate file FK, technician, result) |
| FI.2.11 | Generate Alembic lifecycle migration and update schemas | DONE | Migration 005 (reversible, round-trip verified): 8 new tables + columns on products/leads/tickets/solutions; schemas in `schemas/lifecycle.py` + product/lead/ticket/solution updated; relational columns queryable, JSONB only for flexible policy details |
| FI.2.12 | Add CRUD endpoints and admin sidebar entries for lifecycle entities | DONE | Admin CRUD for all 8 entities via factory in `endpoints/lifecycle.py` (+ `crud/lifecycle.py`), registered in api.py (stock-movements append-only, no PUT); admin `ResourceManager.vue` component + 7 list/create/edit/delete pages + "Lifecycle" sidebar section; live CRUD round-trip + 401/404 verified |
| FI.2.13 | Add normalized StorageGuard lifecycle demo seed | DONE | `seed_lifecycle_demo.py` idempotently ensures supplier, 4 StorageGuard products, warranties, Compliance AMC, 24 points, inventory movements, maintenance, calibration, finance/LTV, platform fee rule, and warranty/AMC/paid-service tickets |

### FI.3 AMC + Warranty + Spare Parts Operations (P0)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.3.1 | Replace generic service packages with AMC catalog | DONE | `services/amc.py AMC_CATALOG` (Basic/Compliance/Commercial/Premium/Enterprise) + `BASELINE_REMOTE_ASSURANCE` (3yr included, separate); served via `GET /amc-catalog`; existing service packages preserved |
| FI.3.2 | Support AMC pricing formulas | DONE | `amc.amc_annual_fee()` percentage (per solution-line band), point_based (per-point fees), site_based, service_level; `POST /amc-catalog/quote` |
| FI.3.3 | Add recommended spare-kit calculator | DONE | `spare_parts.recommend_spare_kit()` category ratios + reserve-cost %; plans customer_owned/shared_pool/fast_replacement; `POST /spare-kit/recommend` |
| FI.3.4 | Add fast-replacement plan rules | DONE | `spare_parts.FAST_REPLACEMENT_PLAN` (eligible/ineligible categories, annual cap, response promise, refurbished consent, exclusions) + `fast_replacement_eligible()`; `GET /fast-replacement-plan` |
| FI.3.5 | Add admin warranty coverage evaluator | DONE | `warranty.evaluate_coverage()` precedence excluded-cause>AMC>fast>managed>pass-through>paid; `POST /warranty/evaluate-coverage` + `POST /tickets/{id}/evaluate-coverage` (persists coverage_type/is_paid_service) |
| FI.3.6 | Add low-stock, expiring-consumable, warranty-expiry, and calibration-due queries | DONE | `services/lifecycle_alerts.py` (low stock, expiring consumables, warranty expiry, calibration due, AMC renewal due, maintenance due); `GET /lifecycle/alerts` summary |
| FI.3.7 | Add contract-boundary template document | DONE | `amc.CONTRACT_BOUNDARY_TEMPLATE` (supply/integration/platform/warranty-coordination/on-site/exclusions/third-party); `GET /contract-boundary-template` |

### FI.4 Project Finance + Quote Economics (P1)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.4.1 | Add Project Finance model | DONE | `models/finance.py ProjectFinance` (one-time + recurring revenue, all cost lines, derived margin/LTV); migration 006; `/project-finances` CRUD |
| FI.4.2 | Add Platform Fee Rule model | DONE | `models/finance.py PlatformFeeRule` (fixed/percentage/hybrid + min/max by line & size); `finance.compute_platform_fee()`; `/platform-fee-rules` CRUD + `/compute` |
| FI.4.3 | Extend ProposalPlan recurring-cost fields | DONE | proposal_plans + amc_fee/consumable_fee/calibration_fee/reporting_fee/alarm_monitoring_fee/first_year_total/annual_recurring_total/recommended_contract_term_years (migration 006 + schemas) |
| FI.4.4 | Split Quote customer-facing line items | DONE | `finance.build_customer_line_items()` (10 packages incl. optional AMC/fast-replacement); `POST /quotes/{id}/build-customer-view`; stored in customer_line_items_json |
| FI.4.5 | Add internal quote economics view | DONE | quotes.internal_economics_json (admin-only, NOT in QuoteRead) + `GET /quotes/{id}/internal-economics` scaffold (supplier/model/cost/lead-time/warranty/margin/alternatives/risk/spares) |
| FI.4.6 | Add margin and LTV calculations | DONE | `finance.compute_finance()` gross profit/margin, first-year + annual recurring profit, LTV 3/5/8; auto-recomputed on ProjectFinance create/update; `POST /project-finances/compute` what-if |
| FI.4.7 | Update quote PDF | DONE | `quote_pdf.py` renders Solution Packages + first-year/annual recurring totals; supplier cost/internal model never present (QuoteRead omits them); PDF verified (200, %PDF) |
| FI.4.8 | Add admin project finance page | DONE | admin `project-finance` + `platform-fee-rules` pages (ResourceManager) showing margin/LTV columns + editable cost ledger; new 'Finance' sidebar section |

### FI.5 Buyer Portal Lifecycle Workspace (P1)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.5.1 | Expand project workspace navigation | DONE | H5 project detail rebuilt as tabbed workspace (Overview/Monitoring/AMC/Warranty/Reports/Tickets) with badge counts from `GET /portal/projects/{id}/workspace`; lazy-loads each tab |
| FI.5.2 | Add buyer AMC page | DONE | AMC tab + `GET /portal/projects/{id}/amc-contracts` (package, fee, term, visits, response target, includes/exclusions, renewal CTA) |
| FI.5.3 | Add buyer warranty page | DONE | Warranty tab + `GET /portal/projects/{id}/warranties` (model, dates, labor/remote/on-site, spare status, covered devices, supplier-warranty boundary, open-ticket CTA) |
| FI.5.4 | Expand buyer ticket form | DONE | Tickets tab with 8 issue types (device_failure/false_alarm/network/report/expansion/calibration/on_site_service/upgrade) + affected device; list shows coverage_type/paid-service badges; verified create flow |
| FI.5.5 | Add monitoring-points summary | DONE | Monitoring tab + `GET /portal/projects/{id}/monitoring-points` summary (total/active/alerts/calibration-due + per-site grouping with thresholds) |
| FI.5.6 | Add report library | DONE | Reports tab + `GET /portal/projects/{id}/reports` (sample monthly compliance report via StorageGuardReportPreview, calibration certificates, maintenance certificates, project files) |

### FI.6 Admin CRM + Renewal Control Tower (P1)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.6.1 | Implement recurring-revenue scoring service | DONE | `services/recurring_revenue.py score_lead()` with exact weights; persisted to lead columns + AI output during `analyze_lead` (verified: StorageGuard demo lead scores 100) |
| FI.6.2 | Add lead classifications | DONE | `recurring_revenue._classify()` -> Low/Medium/High LTV, Compliance Cashflow, Consumable Cashflow, Enterprise Expansion; in AI output `recurring_revenue.classification` |
| FI.6.3 | Add CRM filters and sort order | DONE | `GET /leads` filters: solution_line, min_recurring_score, compliance_risk, amc_potential, consumable_potential, multi_site + sort (recurring_score/arr/ltv/lead_score); admin leads page filter bar + RR Score/ARR columns |
| FI.6.4 | Add admin lifecycle dashboard | DONE | `GET /admin/lifecycle-dashboard` (ARR pipeline+contracted, high-LTV leads, open tickets, 6 due-date alert counts, top-10 margin ranking); contracted ARR and ranking exclude unlinked finance drafts; admin `lifecycle-dashboard` page |
| FI.6.5 | Add renewal opportunity queue | DONE | `services/renewal_queue.py` + `GET /renewal-queue` (AMC renewal, calibration, probe/battery replacement, report renewal, multi-site expansion) with suggested actions; admin `renewal-queue` page |
| FI.6.6 | Add supplier scorecard extensions | DONE | `models/crm.py SupplierScorecard` (7 dimensions + auto-computed overall); migration 007; `/supplier-scorecards` CRUD; admin page (ResourceManager) |

### FI.7 Solution-Line Expansion (P2)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.7.1 | Add KitchenGuard landing page, assessment flow, proposal template, BOM template, and demo project | DONE | Seeded `kitchenguard` solution (lifecycle_content) → `/solutions/kitchenguard`; PC+H5 assessment category; `lifecycle_lines` proposal+BOM (gas/CO/leak/cutoff/inspection); demo project; verified AI classification+templates |
| FI.7.2 | Add AquaGuard landing page, assessment flow, proposal template, BOM template, and demo project | DONE | Seeded `aquaguard` solution → `/solutions/aquaguard`; assessment category; `lifecycle_lines` proposal+BOM with `professional_partner_required` flag (pH/EC/turbidity/COD, calibration fluid, reports); demo project |
| FI.7.3 | Add EnergyGuard public page and lifecycle proposal | DONE | Seeded `energyguard` solution → `/solutions/energyguard` (solar/battery/EV, health reports, optimization, remote ops); `lifecycle_lines` proposal+BOM; assessment energy category maps to energyguard |
| FI.7.4 | Promote FactoryPulse from industrial demo to recurring-service solution | DONE | Seeded `factorypulse` solution → `/solutions/factorypulse` (OEE, non-invasive points, energy report, algorithm subscription, expansion); `services/factorypulse.py` BOM+proposal; industrial products (IND.8) tagged solution_line factorypulse |
| FI.7.5 | Add AssetPulse public page and recurring model | DONE | Seeded `assetpulse` solution → `/solutions/assetpulse` (BLE/UWB/LoRa tags, geofence, inventory, multi-site reports, tag subscription recurring model); PC+H5 assessment asset category |
| FI.7.6 | Add AgriBrain future-ready page | DONE | Seeded `agribrain` solution → `/solutions/agribrain` tagged future-ready/concept; bounded copy (partner+demand validation required); PC assessment agri category |
| FI.7.7 | Add `/recurring-solutions` page | DONE | PC `pages/recurring-solutions.vue` (why one-time hardware is unstable, why compliance/calibration/consumables/AMC are acceptable B2B charges, recurring carriers, privacy guardrail) |
| FI.7.8 | Add `/services/amc` page | DONE | PC `pages/services/amc.vue` (3-year baseline + Basic/Compliance/Commercial/Premium tiers with includes/excludes, pricing logic, renewal & on-site) |

### FI.8 Notifications + Automation (P2)

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.8.1 | Add lifecycle integration events | DONE | `notification_templates.LIFECYCLE_EVENT_TYPES` (9 types: high_recurring, compliance_cashflow, payment.due, amc.renewal_due, warranty.expiry, calibration.due, probe.replacement, ticket.opened, supplier.claim) emitted via create_integration_event |
| FI.8.2 | Add Telegram admin templates | DONE | `services/notification_templates.py render_telegram()` registry; lifecycle templates include solution line, monitoring points, compliance risk, ARR range, due date, recommended action; integration_events delegates to it |
| FI.8.3 | Add customer notification preferences | DONE | `NotificationPreference` model (migration 008) + `GET/PUT /portal/notification-preferences` (telegram/email/whatsapp channels x alerts/reports/maintenance/renewal categories); buyer self-service upsert |
| FI.8.4 | Add scheduled renewal and maintenance jobs | DONE | `lifecycle_automation.scan_and_notify()` (dedup window) + Celery `scan_lifecycle_due` task + beat schedule (daily 06:00); manual `POST /admin/lifecycle-scan`; verified emit amc/calibration/warranty/low-stock events |
| FI.8.5 | Add report-generation scheduling foundation | DONE | `ReportJob` model (migration 008) + `generate_report_jobs()` (monthly, pending_review) + Celery beat (monthly) + `GET /report-jobs` + `POST /report-jobs/{id}/review`; verified create->approve |

### FI.9 Verification + Release Gates

| # | Task | Status | Notes |
|---|------|--------|-------|
| FI.9.1 | Add lifecycle model/API tests | DONE | `test_release_gates.py` + existing suites: warranty coverage, AMC pricing, finance margin/LTV, inventory stock movement, calibration-due query, ticket coverage (58 tests pass) |
| FI.9.2 | Add StorageGuard end-to-end test | DONE | Pure-function chain (assessment->classify->proposal->BOM->score->customer line items->finance->AMC) + persisted demo-project chain assertion (AMC/warranty/points/renewal queue) |
| FI.9.3 | Verify public privacy boundary | DONE | Test asserts ProductRead hides cost/model/supplier/margin, QuoteRead hides internal_economics_json; quote PDF starts %PDF and contains no supplier secret; live product API leak check = NONE |
| FI.9.4 | Verify customer liability boundary | DONE | Test asserts CONTRACT_BOUNDARY_TEMPLATE distinguishes equipment supply/warranty coordination/on-site/exclusions/third-party + baseline remote assurance separate from AMC tiers; summary names supplier vs managed warranty |
| FI.9.5 | Verify PC + H5 + admin production builds | DONE | `nuxt build` passed for all 3 apps (EXIT=0; PC 2.92MB / admin 3.12MB gzip totals); en/zh/sr lifecycle copy parity verified (heroTitle 'Facility Intelligence'/'设施智能'/'inteligencija' + solutionsTitle in all locales) |

### Phase D Delivery + Channels

| # | Task | Status | Notes |
|---|------|--------|-------|
| D.1 | Upgrade Telegram skeleton into unified channel-gateway | DONE | Internal-only FastAPI process on :8200; adapter contract implements receive/send/normalize; nginx `/webhooks/{channel}` route; outbound idempotency and inbound history use existing `channels.*` tables |
| D.2 | Route RFQ Partner invitations through channel-gateway | DONE | Admin invite creates durable invitation, sends Telegram deep link to Partner H5, records delivery path, and emits `rfq.partner_invited`; direct backend Telegram call removed |
| D.3 | Add Partner role view in frontend-h5 | DONE | Service-partner registration creates pending Partner profile; role-aware navigation; Partner dashboard, RFQ inbox/detail, decline, and one-time bid submission in en/zh/sr |
| D.4 | Add Partner calendar and task dispatch | DONE | Admin-confirmed project dispatch reuses `maintenance_schedules`; Partner H5 task inbox/detail/status flow + calendar combines awarded project start dates and dispatched task due dates; Channel Gateway deep-link notification + outbox/audit trail included. Automatic award-to-task dispatch remains Phase E |
| D.5 | Add WhatsApp Business and email adapters | READY_FOR_VERIFY | Shared channel-gateway adapters, signed inbound webhooks, durable outbound delivery, Admin configuration, and focused adapter/backend tests; requires independent provider replay |

### Phase G Agent Runtime Hardening

| # | Task | Status | Notes |
|---|------|--------|-------|
| G.H1 | Freeze capability vs Agent boundary | DONE | Business modules remain data/tool boundaries; Agents are role identities composing allowlisted capabilities |
| G.H2 | Enforce Agent status and grants at core execution entry points | DONE | Sales chat/quote, marketing content, procurement evaluation, and Business Brain now stop when paused or missing required scopes |
| G.H3 | Add explicit Agent execution attribution | DONE | Migration 019 adds `ai.agent_runs.agent_slug`; existing runs backfilled; Agent Console stats no longer infer identity from workflow names |
| G.H4 | Audit Agent configuration and grant changes | DONE | Agent Console API writes before/after records to `audit_logs` |
| G.H5 | Correct roadmap claims | DONE | Marketplace, tenant isolation, third-party sandbox, and five-ring object authorization are marked as Phase H/I release gates |
| G.H6 | Verify migration, backend tests, and PC/admin builds | VERIFIED | Migration 019 at head; 126 backend tests pass; PC and admin Docker production builds pass; core services healthy |

### Phase H First Customer Operations

| # | Task | Status | Notes |
|---|------|--------|-------|
| H.1 | Deliver Project Space v1 | DONE | H5 project workspace now aggregates authorized Agents, Missions, task queue, project/design files and timeline; customer can request a Mission |
| H.2 | Deliver structured Agent Team orchestration | DONE | Mission → deterministic Planner → project-scoped task queue → allowlisted Workers → reviewer checks → preliminary Final Report; plan and final report both require human gates |
| H.3 | Enforce project-scoped Agent authorization | DONE | Migration 020 adds audited `agent_object_grants`; Mission plan approval and admin project controls grant/revoke exact-project `project_data` access |
| H.4 | Activate Support Agent ticket triage | DONE | Support Agent is active, requires global + exact-project grant, creates review-only triage, and never decides warranty/AMC/paid coverage |
| H.5 | Deliver Marketing Agent weekly report | DONE | Real 7-day operational metrics, scheduled Monday task, manual admin trigger and AI review queue; report remains preliminary |
| H.6 | Add Phase H admin operations | DONE | Mission Control, project Agent access controls, expanded AI Review filters and Marketing weekly report control |
| H.7 | Add Phase H regression coverage | DONE | Object-grant enforcement, Mission plan/grant/run/review gate, Support triage, Marketing report and customer ticket coverage-boundary tests |
| H.8 | Verify migration, tests, builds and live services | VERIFIED | Migration 021 at head; 137 backend tests pass; PC/Admin/H5 production builds pass; services restarted healthy; live Mission + Store + Marketplace verification records present |
| H.9 | Build Smart Building/Solar/Security industry Agent packs | WAITING | Unlock only from the first real customer scope; do not build empty packs |
| H.10 | Deliver full five-ring + tenant/private isolation | READY_FOR_VERIFY | ZL16-ZL30 bind prior tenant roots/children; ZL31 binds remaining AI Conversation, Marketing child, Field Operations and Delivery children with migration 078. Independent verifier must replay cross-Workspace bypass checks before VERIFIED |

### V3 Independent Portal Status

| # | Physical Portal | Status | URL / Shared Codebase |
|---|-----------------|--------|-----------------------|
| PORTAL.1 | AISLOS Website | VERIFIED | `4099` / `frontend-pc` mode `aislos` |
| PORTAL.2 | Ainerwise Store Frontend | VERIFIED | `4096` / `frontend-pc` mode `store` |
| PORTAL.3 | Developer Portal | VERIFIED | `4092` / `frontend-pc` mode `developer` |
| PORTAL.4 | AISLOS Admin Console | VERIFIED | `4097` / `frontend-admin` mode `aislos` |
| PORTAL.5 | Ainerwise Store Admin | VERIFIED | `4095` / `frontend-admin` mode `store` |
| PORTAL.6 | Marketing Portal | VERIFIED | `4094` / `frontend-admin` mode `marketing` |
| PORTAL.7 | Agent Console | VERIFIED | `4093` / `frontend-admin` mode `agent` |
| PORTAL.8 | Customer Project Portal | VERIFIED | `4098` / `frontend-h5` mode `customer`; wrong-role access denied |
| PORTAL.9 | Partner Portal | VERIFIED | `4091` / `frontend-h5` mode `partner`; wrong-role access denied |

### Phase I — Commercial Marketplace Release Gates

| ID | Task | Status | Notes |
|----|------|--------|-------|
| I.1 | Store request/order-intent data asset | VERIFIED | Migration 021 + server-priced requests + admin status workflow |
| I.2 | Developer listing/review data asset | VERIFIED | Submit/resubmit/approve/reject with audit trail |
| I.3 | Agent Marketplace install lifecycle | VERIFIED | Official Agent seed + install/uninstall records |
| I.4 | Third-party default-deny boundary | VERIFIED | Approved third-party Agent remains paused; all eight grants denied; installation grants nothing |
| I.5 | Portal physical split | VERIFIED | 9 independent Portal processes reuse 3 Nuxt codebases and one Core API; browser-verified brand/menu/route and role boundaries |
| I.6 | Tenant/private isolation + data export/delete | READY_FOR_VERIFY | ZL14-ZL31 cover privacy, primary tenant roots, Lead/Showroom children, Procurement/RFQ deep children, Commerce transaction children, Payment ledger children, Cebu payment/fulfillment children, and remaining inherited AI/Marketing/Field/Delivery child gaps. Independent verifier must confirm before VERIFIED |
| I.7 | Third-party Agent execution sandbox | TODO | Delivery Projects now have explicit Workspace binding, but third-party activation and Project grants remain fail-closed until the execution sandbox release gate is complete |
| I.8 | PSP subscriptions and revenue-share settlement | TODO | Never own customer money |

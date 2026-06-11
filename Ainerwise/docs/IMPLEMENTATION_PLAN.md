# AinerWise Implementation Plan

## Phase 1: Skeleton + DB + Auth (Foundation) -- COMPLETED & VERIFIED

Docker Compose running all services, ALL database tables created, auth working, Nuxt shell with 3 layouts.

### Backend
- [x] docker-compose.yml (postgres, redis, minio, backend, celery, frontend, nginx)
- [x] core/config.py (Pydantic BaseSettings)
- [x] core/security.py (JWT + bcrypt)
- [x] core/permissions.py (UserRole enum + RBAC)
- [x] db/session.py (async engine + session)
- [x] db/base.py (import all models)
- [x] ALL 22+ SQLAlchemy models
- [x] Alembic setup (alembic.ini + env.py + script template)
- [x] api/deps.py (get_db, get_current_user, require_role)
- [x] Auth endpoints (register, login, refresh, me, change-password)
- [x] CRUD base class (generic async CRUD)
- [x] entrypoint.sh (alembic upgrade head + uvicorn)
- [x] Celery app setup
- [x] create_superadmin.py script
- [x] seed_data.py script

### Frontend
- [x] Nuxt 3 + TailwindCSS + Naive UI + i18n setup
- [x] 3 layouts (default, portal, admin) with navigation
- [x] Auth composable + middleware (auth, admin, guest)
- [x] Login + Register pages
- [x] Home page skeleton
- [x] i18n files (en.json full, zh.json/sr.json partial)

---

## Phase 2: Public Pages + Core APIs + Seed Data -- COMPLETED & VERIFIED

All public-facing pages work with real data. Visitors can browse solutions, products, services, and submit requirements.

### Backend APIs
- [x] Solutions endpoint (GET public list, GET by slug, POST, PUT, DELETE admin)
- [x] Products endpoint (GET list with filters, GET by slug, POST, PUT, PATCH status admin)
- [x] Product categories endpoint (GET tree, POST, PUT admin)
- [x] Leads endpoint (POST create public, GET list admin, GET by id admin, PATCH status, PATCH assign)
- [x] Vendors endpoint (POST apply public, GET list admin, GET by id admin, PATCH status admin)
- [x] Service packages endpoint (GET public list, POST, PUT, DELETE admin)
- [x] Files endpoint (POST get upload URL, GET download URL)
- [x] Admin dashboard endpoint (GET aggregated stats + recent leads/vendors)
- [x] Generate + run Alembic initial migration (24 tables, String cols not Enum)
- [x] Run seed data (13 categories, 6 solutions, 5 service packages, 4 regions)

### Frontend Fixes
- [x] Fix i18n locale loading (langDir: '.' resolves under i18n/ correctly)
- [x] Fix component auto-import (pathPrefix: false in nuxt.config)
- [x] All public pages SSR render with translations

### Frontend Pages (already built, API connected)
- [x] Home page (hero, solutions, services, CTA)
- [x] Solutions list + detail
- [x] Products list + detail with filters
- [x] Services list
- [x] Submit Requirement (3-step form)
- [x] Supplier Application
- [x] About + Contact
- [x] Admin dashboard
- [x] Admin leads list + detail
- [x] Admin products list
- [x] Admin vendors list
- [x] Admin solutions list

### Verified
- [x] Home renders with API data (SSR + client-side fetch)
- [x] All 10 public pages return HTTP 200 with proper translations
- [x] Backend health check passes
- [x] Seed data loaded (solutions, categories, service packages, regions)
- [x] API endpoints all functional (tested via curl)

---

## Phase 3: Admin Dashboard + Management -- COMPLETED & VERIFIED

Admin can manage all core entities.

### Admin Pages
- [x] Lead management with status workflow transitions + notes
- [x] Product management (full CRUD + approve/reject via StatusWorkflow)
- [x] Vendor management (detail page + approve/reject/suspend)
- [x] Solution management (full CRUD with create + edit)
- [x] Service package management (modal-based CRUD)
- [x] User + Company management (list + filter + activate/deactivate)
- [x] Category tree management (modal-based CRUD)
- [x] StatusWorkflow.vue reusable component (lead/product/vendor/quote/project/ticket)
- [x] Placeholder pages for Phase 4-6 features (no more 404s from sidebar)

### Backend Additions
- [x] Users endpoint (list, get, update, role change, active toggle)
- [x] Companies endpoint (list, get, create, update)
- [x] Lead notes endpoint (PATCH /leads/{id}/notes)
- [x] Solutions & Products: UUID + slug dual lookup (GET /{slug_or_id})

### Verified
- [x] Dashboard shows real counts from API
- [x] All admin pages return 302 (auth redirect) -- correct behavior
- [x] Backend endpoints all functional
- [x] StatusWorkflow defines transitions for 6 entity types
- [x] Non-admins get redirected to /login

---

## Phase 4: Buyer Portal + File Upload -- COMPLETED & VERIFIED

Buyers have a self-service portal. Quote and ticket workflows. MinIO file upload.

### Backend
- [x] Quote endpoints (CRUD + status workflow + /quotes/my)
- [x] Ticket endpoints (CRUD + /tickets/my, auto-sets buyer_user_id)
- [x] MinIO file service (presigned upload/download -- built in Phase 2)
- [x] /leads/my endpoint (filter by company or email)

### Frontend
- [x] Buyer dashboard (real counts from /leads/my, /quotes/my, /tickets/my)
- [x] My Leads (list + detail with visual status tracking)
- [x] My Quotes (list with accept/reject buttons)
- [x] My Projects (placeholder -- activates after quote accepted)
- [x] My Tickets (list + create modal with priority and type)
- [x] Profile (edit user info + change password)
- [x] useFileUpload.ts composable (XHR to MinIO with progress)

### Verified
- [x] All portal pages return 302 (auth redirect) -- correct
- [x] 58+ backend routes registered
- [x] Quote/Ticket/Lead "my" endpoints functional
- [x] Buyer can't access admin (middleware redirect)

---

## Phase 5: Telegram Bot + AI Orchestrator -- MOSTLY COMPLETE

### Telegram Notifications
- [x] Admin group notifications (lead.created, vendor.applied, product.submitted, ai.completed)
- [x] IntegrationEvents persistence with sent/skipped/failed status
- [x] Message templates (formatted Telegram text for each event type)
- [x] Retry mechanism for failed events (POST /integration-events/{id}/retry)
- [ ] Admin Telegram bot commands (/leads, /lead <id>) -- DEFERRED

### AI Analysis (Rule-Based MVP)
- [x] Rule-based pipeline: Completeness -> Classify -> Risk -> Match -> Draft -> Summarize
- [x] Direct service call from lead creation endpoint
- [x] "Run Analysis" button on admin lead detail page
- [x] Results stored in leads.ai_analysis_json + ai_runs table
- [x] All output tagged as preliminary with disclaimer
- [x] Rich admin UI: classification, completeness score, risks, matched solutions, raw JSON

### Backend Endpoints
- [x] POST /leads/{lead_id}/analyze -- trigger AI analysis (admin)
- [x] GET /ai-runs -- list AI runs with status/entity_type filter (admin)
- [x] GET /integration-events -- list events with status/event_type filter (admin)
- [x] POST /integration-events/{id}/retry -- retry failed Telegram event (admin)
- [x] Integration event service (persist + dispatch Telegram admin events)
- [x] Celery tasks: send_telegram_notification + analyze_lead worker

### Frontend Admin Pages
- [x] AI Runs viewer (table with workflow, entity link, model, status, result summary)
- [x] Integration Events viewer (table with type/status filter, payload summary, retry button)
- [x] Lead detail: AI analysis section (classification, completeness, risks, matched solutions, raw JSON toggle)

### Remaining
- [ ] Full LangGraph orchestrator service (replace rule-based MVP with graph workflow)

### Verified
- [x] New lead -> integration event created + Telegram sent/skipped status
- [x] AI analysis populates lead.ai_analysis_json
- [x] AI run recorded in ai_runs table
- [x] Admin can view AI runs and integration events
- [x] Failed events show retry button

---

## Phase 6: Advanced Features -- IN PROGRESS

### Project Management (10-state workflow) -- DONE
- [x] Backend: schemas/project.py (ProjectRead/Create/Update/StatusUpdate)
- [x] Backend: crud/project.py
- [x] Backend: api/v1/endpoints/projects.py (GET list, GET /my, GET /{id}, POST, PUT, PATCH status, PATCH notes)
- [x] Backend: Registered projects router in api.py
- [x] Frontend: Admin project list page (table with status filter, pagination)
- [x] Frontend: Admin project detail page (10-step timeline, StatusWorkflow, notes, team, project plan)
- [x] Frontend: Admin project create page
- [x] Frontend: Portal projects list (progress bars, status)
- [x] Frontend: Portal project detail (visual timeline, team, details)
- [x] Frontend: Portal dashboard now fetches /projects/my count
- [x] StatusWorkflow.vue: project transitions aligned with model (planning -> site_survey -> quotation_confirmed -> procurement -> delivery -> installation -> testing -> handover -> maintenance -> closed)

### Service Partner CRUD -- DONE
- [x] Backend: schemas/service_partner.py (ServicePartnerRead/Create/Update/StatusUpdate)
- [x] Backend: crud/service_partner.py
- [x] Backend: api/v1/endpoints/service_partners.py (GET list, GET /{id}, POST, PUT, PATCH status, DELETE)
- [x] Backend: Registered service_partners router in api.py
- [x] Frontend: Admin service partners page (table + create modal + detail modal + verify/suspend/reactivate actions)

### Audit Log Service + Viewer -- DONE
- [x] Backend: services/audit.py (log_action helper)
- [x] Backend: schemas/audit.py (AuditLogRead)
- [x] Backend: GET /audit-logs endpoint with entity_type/action/actor filters (in integration_events.py)
- [x] Backend: Audit logging wired into lead, product, project status change endpoints
- [x] Frontend: Admin audit logs page (table with entity type/action filter, before/after diffs, pagination)

### Region Management -- DONE
- [x] Backend: schemas/region.py (RegionRead/Create/Update)
- [x] Backend: crud/region.py
- [x] Backend: api/v1/endpoints/regions.py (GET list, GET /{id}, POST, PUT, DELETE)
- [x] Backend: Registered regions router in api.py
- [x] Frontend: Admin regions page (card grid + create/edit modal + activate/deactivate)

### Admin Quotes + Tickets Pages -- DONE
- [x] Frontend: Admin quotes page (table with status filter + create modal + send/accept/reject actions)
- [x] Frontend: Admin tickets page (table with status filter + start/resolve/close/reopen actions)

### P1 Operational Closed Loop (Service Partner + Site Survey + Quote Draft) -- DONE
- [x] Backend: Site survey CRUD endpoints nested under /leads/{id}/surveys (GET, POST, PUT, DELETE)
- [x] Backend: schemas/site_survey.py (SiteSurveyRead/Create/Update)
- [x] Backend: crud/site_survey.py
- [x] Backend: POST /projects/from-lead/{lead_id} -- create project pre-populated from lead data
- [x] Backend: POST /projects/{id}/assign-partner -- assign verified service partner to project team
- [x] Backend: DELETE /projects/{id}/team/{partner_id} -- remove partner from project team
- [x] Backend: POST /quotes/draft-from-lead/{lead_id} -- AI-informed draft quote with line items from systems + matched solutions
- [x] Frontend: Admin lead detail -- Site Survey section (create survey form + list surveys)
- [x] Frontend: Admin lead detail -- "Create Project from Lead" button with link to created project
- [x] Frontend: Admin lead detail -- "Draft Quote from Lead" button with status refresh
- [x] Frontend: Admin project detail -- Partner assignment (select verified partner, choose role, assign/remove)

### Certification Records -- DONE
- [x] Backend: schemas/certification.py (CertificationRecordRead/Create/Update)
- [x] Backend: crud/certification.py (crud_certification)
- [x] Backend: api/v1/endpoints/certifications.py (GET list with owner_type/status filters, GET /{id}, POST, PUT, DELETE)
- [x] Backend: Registered certifications router in api.py
- [x] Frontend: Admin certifications page (table with owner_type/status filters, expiry date highlight, CRUD modal, public visibility flag)

### Product Compatibility Matrix -- DONE
- [x] Backend: schemas/product_compatibility.py (ProductCompatibilityRead/Create/Update)
- [x] Backend: crud/product_compatibility.py (crud_product_compatibility)
- [x] Backend: api/v1/endpoints/product_compatibility.py (GET list with product_id/protocol filters, GET /{id}, POST, PUT, DELETE)
- [x] Backend: Registered product_compatibility router in api.py
- [x] Frontend: Admin compatibility page (table with protocol filter, compatibility_level + test_status badges, CRUD modal with protocol list)

### Warranty Policies -- DONE
- [x] Backend: schemas/certification.py (WarrantyPolicyRead/Create/Update — in same file as certs)
- [x] Backend: crud/certification.py (crud_warranty_policy — in same file as certs)
- [x] Backend: api/v1/endpoints/warranty_policies.py (GET list with product_id/region/active filters, GET /{id}, POST, PUT, DELETE)
- [x] Backend: Registered warranty_policies router in api.py
- [x] Frontend: Admin warranty policies page (card grid with warranty months display, SLA/spare parts JSON editing, region filter)

### Quote PDF Generation -- DONE
- [x] Backend: reportlab added to requirements.txt
- [x] Backend: services/quote_pdf.py (generate_quote_pdf with line items table, cost summary, client info, disclaimer)
- [x] Backend: GET /quotes/{id}/pdf endpoint returning PDF binary with Content-Disposition header
- [x] Frontend: PDF download button on admin quotes list page (fetches blob, triggers browser download)

### Phase 6 -- COMPLETE
All 13 Phase 6 tasks are done. No remaining TODO items.

### Product Capability + Lead Score + Proposal/BOM Data Layer -- DONE
- [x] Backend: Product model extended with 6 capability columns (protocol_json, scenario_tags_json, intelligence_level_min/max, feature_status, risk_level)
- [x] Backend: Lead model extended with 5 score/stage columns (lead_score, lead_stage, desired_intelligence_level, conversation_json, proposal_tiers_json)
- [x] Backend: ProposalPlan model (tier, intelligence levels, 6 cost estimates, total range, complexity, risk, estimate_only flag)
- [x] Backend: BOMItem model (product link, category, qty, unit/device/install/service costs, ownership flags, total)
- [x] Backend: Alembic migration 002 (product + lead columns + proposal_plans + bom_items tables)
- [x] Backend: schemas/proposal.py (ProposalPlanRead/Create/Update + BOMItemRead/Create/Update)
- [x] Backend: schemas/lead.py updated (LeadUpdate schema + lead_score/stage/intelligence/conversation/proposal fields in Read/Create)
- [x] Backend: schemas/product.py updated (protocol_json, scenario_tags, intelligence, feature_status, risk_level in Read/Create/Update)
- [x] Backend: crud/proposal.py (crud_proposal_plan + crud_bom_item)
- [x] Backend: api/v1/endpoints/proposals.py (Proposal CRUD + nested BOM CRUD)
- [x] Backend: Registered proposals router in api.py (20 routers total)
- [x] Frontend: Admin proposals list page (tier filter, cost range, complexity badges, create/edit modal)
- [x] Frontend: Admin proposal BOM editor detail page (bill-of-materials table, add/edit/delete items, cost column totals, flag badges)
- [x] Frontend: Lead detail updated — 3-column score/stage/intelligence display with native field fallback
- [x] Frontend: AdminSidebar updated — Proposals link under Business section

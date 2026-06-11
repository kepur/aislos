# AinerWise Platform Architecture

> **LEGACY PRE-V3 RECORD.** This document describes the original solution-company
> platform and must not override `ARCHITECTURE_CONSTITUTION.md` or
> `AINERWISE_CORE_V3.md`. The current system includes the formal Ainerwise Store
> business line and 9 independent Portal processes backed by one Core.

## Overview

AinerWise is a B2B smart building & energy integration platform for European markets (Serbia first). It is NOT e-commerce -- it's a solution + supply chain + local service + lifecycle maintenance system integrator's digital platform.

**Core business flow:** Visitor browses solutions/products -> submits requirement -> AI analyzes lead -> admin manages quotation -> project lifecycle -> ongoing maintenance.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Nuxt 3 + Vue 3 + TailwindCSS + Naive UI | Single app: public + buyer portal + admin |
| Backend | FastAPI (async) + SQLAlchemy 2.0 + Alembic | REST API server |
| Database | PostgreSQL 16 (pgvector-ready) | Primary data store, JSONB for flexible fields |
| Cache/Queue | Redis 7 + Celery | Task queue (AI analysis, notifications) |
| File Storage | MinIO (S3-compatible) | Documents, images, certificates |
| AI | Rule-based MVP (built-in) + LangGraph orchestrator (planned) | Lead analysis, solution matching |
| Notifications | Telegram Bot API (via httpx) | Admin group alerts |
| i18n | @nuxtjs/i18n v9: English primary + Chinese + Serbian | Multi-language |
| Infra | Docker Compose | All services containerized |

## Single App, Three Layouts

The frontend is ONE Nuxt 3 app serving three audiences via layout switching + middleware:

```
layouts/default.vue  -> Public pages (PC + mobile responsive)
layouts/portal.vue   -> Buyer portal (authenticated buyer)
layouts/admin.vue    -> Admin dashboard (admin/superadmin only)
```

Mobile (H5) is responsive design via TailwindCSS breakpoints, not a separate app.

### Nuxt Config Gotchas (for future AI agents)

- **i18n `langDir`**: Must be `'.'` (not `'i18n/'`). The @nuxtjs/i18n v9 module auto-prepends `i18n/` to the langDir value, so `langDir: '.'` resolves to `/app/i18n/en.json` correctly.
- **Component auto-import**: `components: { dirs: [{ path: '~/components', pathPrefix: false }] }` is required so `components/common/AppHeader.vue` registers as `<AppHeader>` not `<CommonAppHeader>`.
- **CSS utility class**: `input-field` defined in `assets/css/main.css` for consistent form styling.

## Authentication & Authorization

- JWT with access + refresh tokens
- Access token: 60min, Refresh token: 7 days
- bcrypt password hashing (bcrypt==4.0.1 pinned for passlib compatibility)
- 5 roles: super_admin, admin, buyer, vendor, service_partner
- RBAC enforced via FastAPI dependencies (`require_role()`)
- Middleware: `auth.ts` (any logged-in user), `admin.ts` (admin/super_admin), `guest.ts` (redirect if logged in)
- Pydantic schemas use `model_config = ConfigDict(from_attributes=True)` for ORM mode

## Database Design

- UUID primary keys on all tables
- `created_at` / `updated_at` timestamps on all tables
- JSONB for flexible/nested data (specs, site_info, architecture, budget_tiers)
- **String(50) columns for status fields** (NOT PostgreSQL native Enum types) with state machines enforced at app level
- 24 tables created via Alembic initial migration
- Docker: `PYTHONPATH=/app` for backend + celery containers

### Tables (24)

**Core:** users, companies
**Catalog:** products, product_categories, product_compatibility, solutions, solution_packages, service_packages
**Business:** leads, site_surveys, projects, quotes, inquiries, tickets
**Operations:** service_partners, certification_records, warranty_policies, founder_profile
**Platform:** integration_events, ai_runs, file_assets, regions, audit_logs

## Key Entity Relationships

```
User --belongs_to--> Company
Lead --submitted_by--> User/Company (contact_email or buyer_company_id)
Lead --analyzed_by--> AIRun (ai_analysis_json stores output)
Lead --has_many--> SiteSurvey
Lead --becomes--> Quote --becomes--> Project
Project --has_many--> Ticket
Product --belongs_to--> ProductCategory (self-referencing tree)
Product --has_many--> ProductCompatibility
Solution --recommends--> Products (JSONB)
ServicePartner --assigned_to--> Project
FileAsset --attached_to--> any entity (polymorphic via entity_type + entity_id)
IntegrationEvent --triggered_by--> any entity change (lead.created, vendor.applied, product.submitted, ai.completed)
```

## API Structure

All endpoints under `/api/v1/`. 19 router modules, 100+ routes total.

### Router Modules (in registration order)

```
auth.router              - Register, login, refresh, me, change-password
solutions.router         - Public list + admin CRUD, UUID+slug dual lookup
products.router          - Public list with filters + admin CRUD + approve/reject, UUID+slug dual lookup
product_categories.router - Category tree GET + admin CRUD
leads.router             - POST create (public), GET /my (buyer), GET list (admin), GET /{id},
                           PATCH /{id}/status (+ audit log), PATCH /{id}/assign, PATCH /{id}/notes,
                           GET /{id}/surveys, POST /{id}/surveys, PUT /{id}/surveys/{sid}, DELETE /{id}/surveys/{sid}
vendors.router           - POST apply (public), GET list/detail (admin), PATCH status
service_packages.router  - GET public list, POST/PUT/DELETE admin
projects.router          - GET list (admin), GET /my (buyer), GET /{id}, POST, PUT,
                           PATCH status (+ audit log), PATCH notes,
                           POST /from-lead/{lead_id}, POST /{id}/assign-partner, DELETE /{id}/team/{partner_id}
quotes.router            - GET list (admin), GET /my (buyer), GET /{id}, POST, PUT, PATCH status,
                           GET /{id}/pdf, POST /draft-from-lead/{lead_id}
tickets.router           - GET list (admin), GET /my (buyer), GET /{id}, POST (buyer), PUT, PATCH status
service_partners.router  - GET list (admin), GET /{id}, POST, PUT, PATCH status, DELETE
regions.router           - GET list (public), GET /{id}, POST, PUT, DELETE (admin)
files.router             - POST upload URL, GET download URL (MinIO presigned)
users.router             - GET users list, GET/PATCH user, PATCH role/active toggle
                           GET companies list, GET/POST/PUT company
admin.router             - GET /admin/dashboard (aggregated stats + recent leads/vendors)
certifications.router    - GET list (admin), GET /{id}, POST, PUT, DELETE
warranty_policies.router - GET list (admin, with product_id/region/active filters), GET /{id}, POST, PUT, DELETE
product_compatibility.router - GET list (with product_id/protocol filters), GET /{id}, POST, PUT, DELETE
integration_events.router - GET /integration-events, POST retry, GET /ai-runs,
                           POST /leads/{id}/analyze, GET /audit-logs
```

### Route Ordering Notes

- `/leads/my` MUST be defined BEFORE `/{id}` to prevent FastAPI treating "my" as a UUID path parameter
- Same pattern applies to `/quotes/my` and `/tickets/my`

## Frontend Pages

### Public Pages (layouts/default)
- Home (hero, solutions grid, services, CTA)
- Solutions list + `[slug]` detail
- Products list + `[slug]` detail (with category/search filters)
- Services list
- Submit Requirement (3-step form: quick/detailed/professional)
- Supplier Application
- About + Contact
- Login + Register

### Buyer Portal Pages (layouts/portal)
- Dashboard (stats from /leads/my, /quotes/my, /tickets/my, /projects/my)
- My Leads (list + `[id]` detail with visual status tracking)
- My Quotes (list with accept/reject for "sent" quotes)
- My Projects (list with progress bars + `[id]` detail with visual timeline, team, project details)
- My Tickets (list + create modal)
- Profile (edit user info + change password)

### Admin Pages (layouts/admin)
- Dashboard (real-time stats)
- Lead management (list + detail with StatusWorkflow, AI analysis display, notes, assignment, **site survey CRUD**, **create project button**, **draft quote button**)
- Product management (list + create + edit with StatusWorkflow approve/reject)
- Vendor management (list + detail with StatusWorkflow approve/reject/suspend)
- Solution management (list + create + edit)
- Service package management (modal-based CRUD on list)
- User management (list with role filter, activate/deactivate)
- Company management (list with type filter)
- Category tree management (modal-based CRUD)
- Project management (list + detail with 10-step timeline, StatusWorkflow, notes, **partner assignment/removal**)
- Quote management (list with status filter, create modal, send/accept/reject actions)
- Ticket management (list with status filter, start/resolve/close/reopen actions)
- Service partner management (list + create/detail modals, verify/suspend/reactivate)
- Region management (card grid + create/edit modals, activate/deactivate)
- Audit log viewer (table with entity_type/action filter, before/after diffs)
- AI Runs viewer (list with status filter, links to lead detail)
- Integration Events viewer (list with type/status filter, retry for failed)
- Certification records (table with owner_type/status filter, expiry tracking, CRUD modal)
- Warranty policies (card grid with warranty months, SLA JSON editing, region filter)
- Product compatibility matrix (table with protocol filter, level/test_status badges, CRUD modal)
- Placeholder pages: settings, solution-packages, files

### Key Frontend Components
- `StatusWorkflow.vue` -- reusable visual state machine for 6 entity types (lead, product, vendor, quote, project, ticket). Shows current status + allowed transition buttons.
- `StatusBadge.vue` -- colored badge for any status string
- `useFileUpload.ts` -- composable: gets presigned URL from backend, uploads via XHR to MinIO with progress tracking

## Service Architecture (Docker Compose)

```
nginx (80) --------> frontend (3000)    Nuxt 3 SSR server
             |-----> backend (8000)     FastAPI via /api/ proxy
backend -----------> postgres (5432)    Primary database
             |-----> redis (6379)       Celery broker + cache
             |-----> minio (9000/9001)  File storage + console
celery-worker -----> redis              Consumes async tasks
             |-----> postgres           DB access for workers
```

## State Machines

### Lead Status (StatusWorkflow entity="lead")
```
new -> contacted | ai_analyzing | qualified | closed
ai_analyzing -> need_more_info | matched | new (on failure)
need_more_info -> matched | closed
contacted -> qualified | need_more_info | closed
matched -> quotation_drafting | closed
qualified -> quotation_drafting | closed
quotation_drafting -> quotation_sent
quotation_sent -> negotiating | closed
negotiating -> won | lost
won -> converted
```

### Product Status (StatusWorkflow entity="product")
```
draft -> pending_review
pending_review -> approved | rejected
approved -> active | inactive
rejected -> draft
active -> inactive | archived
inactive -> active | archived
```

### Vendor Status (StatusWorkflow entity="vendor")
```
pending -> approved | rejected
approved -> suspended
rejected -> pending (re-review)
suspended -> approved
```

### Quote Status (StatusWorkflow entity="quote")
```
draft -> sent
sent -> accepted | rejected | expired
accepted -> invoiced
rejected -> revised
revised -> sent
```

### Project Status (StatusWorkflow entity="project") [Phase 6]
```
planning -> site_survey
site_survey -> quotation_confirmed
quotation_confirmed -> procurement
procurement -> delivery
delivery -> installation
installation -> testing
testing -> handover
handover -> maintenance
maintenance -> closed
```

### Ticket Status (StatusWorkflow entity="ticket")
```
open -> in_progress -> resolved | escalated
escalated -> in_progress
resolved -> closed | reopened
reopened -> in_progress
```

## P1 Operational Closed Loop

The core business flow from lead intake to project execution:

```
1. Lead submitted (POST /leads)
   -> AI analysis runs automatically (completeness, classification, risk, solution matching)

2. Admin reviews lead
   -> Creates Site Survey (POST /leads/{id}/surveys with area, floors, rooms, building_type)
   -> Multiple surveys can be created per lead (quick/detailed/professional types)

3. Admin creates project from lead
   -> POST /projects/from-lead/{lead_id}
   -> Pre-populates: title, region, buyer_company_id, notes from lead data
   -> Project starts in "planning" status

4. Admin drafts quote from lead
   -> POST /quotes/draft-from-lead/{lead_id}
   -> Auto-generates line items from:
      - lead.systems_needed_json -> device line items
      - AI matched_solutions -> service line items
   -> Includes survey data in notes (area, rooms, floors)
   -> Sets lead status to "quotation_drafting"
   -> Quote valid for 30 days

5. Admin assigns service partners to project
   -> POST /projects/{id}/assign-partner
   -> Only verified partners can be assigned
   -> Roles: installer, surveyor, engineer, commissioning, maintenance
   -> Partners stored in project.team_json

6. Project progresses through 10-state workflow
   -> planning -> site_survey -> quotation_confirmed -> procurement
   -> delivery -> installation -> testing -> handover -> maintenance -> closed
```

### Related API Endpoints
```
POST /leads/{id}/surveys           -- create site survey
GET  /leads/{id}/surveys           -- list surveys for lead
POST /projects/from-lead/{lead_id} -- create project from lead
POST /quotes/draft-from-lead/{lead_id} -- generate draft quote
POST /projects/{id}/assign-partner -- assign verified partner
DELETE /projects/{id}/team/{partner_id} -- remove partner
```

## File Storage Pattern

Files stored in MinIO with S3-compatible API:
1. Frontend calls `useFileUpload.ts` composable
2. Composable requests presigned upload URL from `POST /api/v1/files/upload-url`
3. Frontend uploads directly to MinIO via XHR (progress tracking)
4. Backend creates FileAsset record with metadata
5. Downloads via presigned download URLs from `GET /api/v1/files/download-url`

## AI Integration (Phase 5 -- MVP Complete)

### Current: Rule-Based MVP
The AI analysis runs as a synchronous service call (not a separate microservice):

1. Lead is created via `POST /leads` or admin clicks "Run Analysis" on lead detail
2. `analyze_lead()` in `services/ai_analysis.py` runs the pipeline:
   - **Completeness Check**: scores 10 required fields, generates follow-up questions for missing data
   - **Classification**: keyword-based project type detection (Smart Hotel, CCTV, Solar, KNX, etc.)
   - **Risk Analysis**: flags high/medium/low risks based on missing info and project type
   - **Solution Matching**: scores existing solutions against lead text and classification
   - **Service Package Matching**: same scoring against service packages
   - **Recommendation**: generates recommended_status and next_action
3. Results stored in `leads.ai_analysis_json` JSONB column + `ai_runs` table
4. `IntegrationEvent` with type `ai.completed` is created
5. All output includes disclaimer: "Preliminary recommendation. Final solution requires engineering review."

### Planned: LangGraph Orchestrator (Phase 5.6 -- TODO)
Will replace/extend rule-based MVP with a full graph workflow:
- Separate FastAPI service at port 8001
- Workflow nodes: Normalize -> Completeness -> Classify -> Risk -> Match -> Recommend -> Compat -> Draft -> Summarize
- Triggered via Celery task

## Notification System (Phase 5 -- Complete)

### Architecture
Notifications use an event-sourced pattern with persistence:

1. Business action (lead created, vendor applied, product submitted, AI completed) calls `create_integration_event()`
2. `IntegrationEvent` record created in DB with `status=pending`
3. If Telegram configured (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_ADMIN_CHAT_ID` in env):
   - Sends formatted message via Telegram Bot API (httpx POST)
   - Updates event status to `sent`
4. If Telegram not configured:
   - Event status set to `skipped` with explanation message
5. Failed events can be retried via `POST /integration-events/{id}/retry`

### Event Types
- `lead.created` -- new lead submitted (contact, project type, location, budget)
- `vendor.applied` -- new supplier/partner application (company, location, email)
- `product.submitted` -- product submitted for review (name, brand, status)
- `ai.completed` -- AI analysis finished (classification, completeness score, recommendation)

### Celery Workers
- `send_telegram_notification` task: retries a persisted event
- `analyze_lead` task: runs AI analysis from worker (for async processing)

## Security Principles

- Contact info protection: vendors never see buyer contact info directly
- Admin-controlled: all critical actions require admin approval in MVP
- No online payment: Request Quote -> Bank Transfer -> Manual Confirmation
- AI never auto-commits decisions -- always tagged as preliminary
- CORS restricted to known origins
- All sensitive config via environment variables
- Status String columns (not Enum) to avoid migration pain when adding new statuses

## Seed Data

- 13 product categories (hierarchical tree)
- 6 solutions (Smart Building, CCTV, Solar, KNX, etc.)
- 5 service packages
- 4 regions
- Superadmin user (admin@ainerwise.com / admin123456)

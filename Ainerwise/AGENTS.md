# Ainerwise Core + AISLOS Enterprise AI OS

## Project Overview
Ainerwise is the real-business and data-asset layer. AISLOS is the Enterprise AI
Operating System for solution companies. Ainerwise Agents is the governed AI
employee ecosystem. Store is a formal business line, but customer payment custody
and autonomous high-risk Agent actions remain prohibited.

Read `docs/ARCHITECTURE_CONSTITUTION.md`, `docs/AINERWISE_CORE_V3.md`, and
`docs/PORTAL_FIELD_SERVICE_V1_TASKS.md` before changing architecture. Frozen Portal
rule: only 3 physical Nuxt codebases and one Core API. Logical Portals use separate
layout/menu/routes/theme/manifest/grants; do not create a frontend per role or expose
every menu to every user.

## Tech Stack
- Frontend: Nuxt 3 + Vue 3 + TailwindCSS + Naive UI
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Alembic
- Database: PostgreSQL 16 + JSONB + pgvector extension
- Cache/Queue: Redis 7 + Celery
- File Storage: MinIO
- AI: LangGraph orchestrator (separate service)
- Notifications: Channel Gateway (Telegram first; WhatsApp/email adapters follow)

## Project Structure
- `frontend-pc/` — shared Nuxt base: AISLOS Website, Store Frontend, Developer Portal
- `frontend-admin/` — shared Nuxt base: permissioned Operations, Procurement, Field Ops, Marketing, AI Supervisor, Finance, Audit workspaces
- `frontend-h5/` — shared Nuxt base: Customer, Partner Company, Field Worker, Supplier, Kiosk logical portals
- `frontend/` — legacy monolith, reference only
- `backend/` — FastAPI API server
- `ai_orchestrator/` — LangGraph AI service (Phase 5)
- `channel_gateway/` — unified channel gateway (port 8200, internal only)
- `nginx/` — Reverse proxy config

## Development
```bash
cp .env.example .env
docker compose up -d
```
- AISLOS Website: http://localhost:4099
- Store Frontend: http://localhost:4096
- Developer Portal: http://localhost:4092
- AISLOS Admin: http://localhost:4097
- Store Admin: http://localhost:4095
- Marketing Portal: http://localhost:4094
- Agent Console: http://localhost:4093
- Customer Portal: http://localhost:4098
- Partner Portal: http://localhost:4091
- Experience Center Kiosk: http://localhost:4090
- Backend API: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## Key Conventions
- UUID primary keys on all tables
- JSONB for flexible/semi-structured fields
- All API routes prefixed with /api/v1/
- Role-based access: super_admin, admin, internal staff, buyer/customer_user,
  vendor, developer, service_partner/partner workers
- i18n: English primary, Chinese, Serbian
- All AI output tagged as preliminary — requires admin review
- Every feature must accumulate a unique data asset
- Logical Portal means independent layout, home, menu, route allowlist, theme, PWA manifest and grants; it does not automatically require a new process

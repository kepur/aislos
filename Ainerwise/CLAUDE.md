# AinerWise B2B Smart Building Platform

> **Rule #1: Every feature must accumulate a unique data asset. Otherwise it will never be implemented.**
>
> Architecture is governed by `docs/ARCHITECTURE_CONSTITUTION.md` **v3** (10 articles — binding)
> and `docs/AINERWISE_CORE_V3.md` (one Core, many Portals, Agent ecosystem; Phases G–I).
> v1/v2 docs remain as Core implementation records (Phases A–E delivered).
> Brand triple: **Ainerwise** (real business + products + data source) · **AISLOS**
> (Enterprise AI Operating System with a governed Agent Marketplace) ·
> **Ainerwise Agents** (official Agents plus reviewed third-party listings).
> Business modules remain capability and data-ownership boundaries. Agents are
> least-privilege roles that compose allowlisted tools. AI recommends, human approves.

## Project Overview
B2B smart building & energy integration platform evolving into an Enterprise AI OS with an Agent ecosystem. Nine independent Portal processes reuse 3 Nuxt codebases and one Core API. Ainerwise Store captures reviewed order intent without taking payment. Developer Portal and Marketplace capture listings/reviews/installations; third-party execution, billing and data access remain blocked until the Phase I release gates pass.

## Tech Stack
- Frontend: Nuxt 3 + Vue 3 + TailwindCSS + Naive UI
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Alembic
- Database: PostgreSQL 16 + JSONB + pgvector extension
- Cache/Queue: Redis 7 + Celery
- File Storage: MinIO
- AI: LangGraph orchestrator (separate service)
- Notifications: Channel Gateway (Telegram first; WhatsApp/email adapters follow)

## Project Structure
- `frontend-pc/` — shared Nuxt base for AISLOS Website, Store Frontend, Developer Portal
- `frontend-h5/` — shared Nuxt base for Customer Project Portal and Partner Portal
- `frontend-admin/` — shared Nuxt base for AISLOS Console, Store Admin, Marketing, Agent Console
- `frontend/` — Legacy monolith (deprecated, kept for reference)
- `backend/` — FastAPI API server
- `ai_orchestrator/` — LangGraph AI service (Phase 5)
- `channel_gateway/` — unified channel gateway (port 8200, internal only)
- `nginx/` — Reverse proxy config

## Development
```bash
cp .env.example .env
docker compose up -d
```
- Portal ports: AISLOS 4099, Store 4096, Developer 4092, Customer 4098, Partner 4091, Kiosk 4090
- Operations ports: AISLOS Admin 4097, Store Admin 4095, Marketing 4094, Agent 4093
- Backend API: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## Key Conventions
- UUID primary keys on all tables
- JSONB for flexible/semi-structured fields
- All API routes prefixed with /api/v1/
- Role-based access: super_admin, admin, buyer (=customer in UI), vendor, service_partner
- i18n: English primary, Chinese, Serbian
- All AI output tagged as preliminary — requires admin review
- Never describe roadmap capabilities (Marketplace, tenant isolation, third-party
  Agent sandbox, five-ring memory isolation) as delivered before their release gates pass
- Frozen Portal rule: independent process, entry URL, brand, home, menu and route allowlist.
  Reuse the 3 Nuxt codebases and one Core; never put every menu back into one running Portal.
- Current status reporting must distinguish 9 Portal processes, 3 shared UI codebases,
  one Core API, and Phase I commercial/permission release gates
- UI calls "buyer" role "Customer" — backend keeps `buyer` as the role value

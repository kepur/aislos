# AinerWise

**AISLOS installs governed AI employees for solution companies.**

> Rule #1: Every feature must accumulate a unique data asset.
> Otherwise it will never be implemented.

```
Outcome → AI → Knowledge → Partner → Delivery → Maintenance → Data → Continuous Improvement
```

AI General Contractor Platform for European smart building, solar, security,
KNX and automation companies. We connect customers, AI solution design,
certified local partners and premium suppliers into one intelligent delivery
platform. Customers buy outcomes — never software.

## Governance

- [Architecture Constitution v3](docs/ARCHITECTURE_CONSTITUTION.md) — 10 binding articles. Read first.
- [Ainerwise Core V3](docs/AINERWISE_CORE_V3.md) — one Core, many Portals, Agent ecosystem (Phases G–I).
- [v2 General Contractor](docs/AISLOS_V2_GENERAL_CONTRACTOR.md) and [v1 Infrastructure](docs/AISLOS_ENTERPRISE_ARCHITECTURE.md) — Core implementation records (Phases A–E, delivered).

Brand triple: **Ainerwise** (real business + data) · **AISLOS** (Enterprise AI OS
with a governed Agent Marketplace) · **Ainerwise Agents** (official AI employees plus
reviewed third-party listings). Real business → data → agents → platform → marketplace.

## Development

```bash
cp .env.example .env
./scripts/shared-platform/up-core.sh
# 或：docker compose up -d
```

共享中间件与 Cebu legacy profile：见 [docs/shared-platform/LOCAL_DEV_PROFILES.md](docs/shared-platform/LOCAL_DEV_PROFILES.md)。

| Service | URL |
|---------|-----|
| AISLOS Website | http://localhost:4099 |
| Ainerwise Store Frontend | http://localhost:4096 |
| AISLOS Admin Console | http://localhost:4097 |
| Ainerwise Store Admin | http://localhost:4095 |
| Marketing Portal | http://localhost:4094 |
| Agent Console | http://localhost:4093 |
| Developer Portal | http://localhost:4092 |
| Customer Project Portal | http://localhost:4098 |
| Partner Portal | http://localhost:4091 |
| Experience Center Kiosk | http://localhost:4090 |
| Backend API | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |

The frozen Portal boundary is **9 independent entry processes backed by 3 shared
Nuxt codebases and one Core API**. Store frontend/admin are separate operational
surfaces. The Experience Center Kiosk is an additional pilot process on the shared
H5 base; it does not change or merge the frozen nine business Portal boundaries.
This is physical UX and route isolation, not copied systems.
Commercial third-party Agent execution, settlement, full tenant isolation, and
fine-grained operator roles remain Phase I release gates.

Tests run inside the backend container:
`docker compose exec backend sh -c "pip install -q pytest pytest-asyncio && python -m pytest tests/"`

Portal process and route-boundary smoke test:
`./scripts/verify_portals.sh`

# Ainerwise Unified Module Migration Architecture

Status: ACTIVE  
Effective date: 2026-06-12

## Frozen Decision

`Ainerwise/` is the only target runtime and product codebase.

`CebuProjects/` is a read-only reference source until zero-loss migration is
verified and the founder approves retirement. New code must never import,
mount, or depend on `CebuProjects/` at runtime.

The migration rule is:

```text
CebuProjects capability
  -> parity ledger entry
  -> Ainerwise domain implementation
  -> role and object-permission tests
  -> portal implementation
  -> independent verification
  -> VERIFIED
```

Copying an old page without its workflow, permissions, data, background jobs,
and integrations does not count as migration.

## Physical Runtime

The physical runtime remains deliberately small:

```text
Ainerwise/
  backend/                 One Core API and business data owner
  frontend-pc/             All PC logical portals
  frontend-h5/             All H5/PWA logical portals
  frontend-admin/          All internal workbenches
  ai_orchestrator/         Shared AI execution satellite
  channel_gateway/         Shared channel/message satellite
  sdk/                     External integration SDKs
```

Do not create a separate Cebu backend, Cebu database, Supplier app, Worker
app, Partner app, or Marketing app inside the unified runtime. Those are
logical portals and business modules, not deployments.

## Backend Target Boundary

Migration is incremental. Existing flat packages remain operational while
domain rules move into `app/modules`.

```text
backend/app/
  api/                     HTTP transport only
  core/                    Auth, policy, audit, events, config, tenancy
  modules/
    identity/
    portal/
    commerce/              Store + Cebu marketplace/trade capabilities
    procurement/           Facts, BOQ, packages, RFQ
    field_service/         Work packages, crews, tasks, evidence
    project_delivery/
    lifecycle/
    crm/
    marketing/
  integrations/            AinerN2D, PSP, email, storage, external systems
  models/                  Transitional SQLAlchemy registry
  schemas/                 Transitional shared API schemas
  services/                Transitional shared/domain services
```

Rules:

1. New domain authorization and workflow rules belong in `app/modules/<domain>`.
2. API endpoints validate transport data and call domain functions; they do
   not implement ownership rules inline.
3. Shared infrastructure belongs in `core` or `integrations`, never in a
   brand-specific module.
4. SQLAlchemy models remain in the current registry until a separately
   verified migration moves them; do not mass-move models during feature work.
5. `cebu_compat` is a temporary adapter. It must call the same Core domain
   functions as the new Ainerwise portals.

## Shared Middleware

The following are single shared platform capabilities:

| Capability | Owner |
|---|---|
| Authentication and account | Core Identity |
| Workspace membership and Portal Grant | Core Portal Access |
| Object authorization | Owning business module |
| PostgreSQL and migrations | Ainerwise Core |
| Object storage and upload policy | Core Integration |
| Audit events | Core Audit |
| Integration events and outbox | Core Event Bus |
| Notifications | Core Notification |
| AI execution and confidence gates | AI Orchestrator + owning module |
| External media generation | AinerN2D adapter/SDK only |
| Payments | Ledger + PSP adapters |

Portal Grant does not replace object authorization. A menu grant may reveal a
screen; every request must still validate workspace, company, project, and
object ownership.

## Frontend Target Boundary

Nuxt filesystem routes remain under `pages/`. Reusable domain UI and API
clients migrate gradually into feature folders:

```text
frontend-*/
  pages/                    Route entry points
  layouts/                  Logical portal layouts
  features/
    commerce/
    procurement/
    field-service/
    project-delivery/
    marketing/
  portal/                   Manifest, grants, menus, themes, switching
```

Customer, Cebu Buyer, Supplier, Partner Company, and Field Worker must have
different manifests, layouts, menus, route allowlists, and permissions while
sharing the same physical frontend.

## Migration Order

1. Security foundation: workspace scope and object authorization.
2. Build/release foundation: all three frontend production builds and CI.
3. Portal foundation: manifest, membership, switching, layouts, menus.
4. Cebu buyer/supplier commerce capability migration.
5. Field Operations and Worker PWA.
6. Remaining Cebu Admin, payment, dispute, messaging, KYC, and operations.

Every migrated item stays `READY_FOR_VERIFY` until an independent verifier
provides repeatable evidence. Implementing agents may not mark their own work
`VERIFIED`.

## Release Build Gate

The three physical frontends share one supported Node toolchain. Use the
version declared by `Ainerwise/.nvmrc` or another compatible Node version:

```text
Node 20.19+ or Node 22.12+
```

The repository lock files are authoritative. A stale or mixed `node_modules`
tree is not valid verification.

```bash
cd Ainerwise
./scripts/verify_frontend_builds.sh install-build
```

All three production builds must pass before a portal or migration column can
move to `READY_FOR_VERIFY`.

# ZL07 Partner Company PC And H5 Implementation Report

Status: `IMPLEMENTED_AWAITING_ZL01_ZL02_ZL03_ZL04_ZL05_ZL06_INDEPENDENT_VERIFY`

This is implementation evidence only. ZL07 remains `LOCKED`; the implementing
Agent does not authorize `READY_FOR_VERIFY` or `VERIFIED`.

## Delivered

- Added a distinct `partner-workspace` PC layout inside the existing
  `frontend-pc` physical build.
- Added real Partner Company PC pages for overview, RFQs, bid submission,
  task list/detail, photo evidence upload, completion submission, customer
  acceptance link, schedule, and performance.
- Added real Partner Company PC and H5 WorkPackage, Crew, Worker, FieldTask,
  Assignment, and Evidence workspaces backed by exact company/workspace scope.
- Added Crew Lead auto-membership and exact `crew_lead_h5` grant provisioning
  when a worker is promoted to crew lead or supervisor.
- Reused the same authenticated `/partner/*` Core contracts already used by
  Partner H5. No fourth frontend deployment or duplicate backend was created.
- Partner PC routes remain protected by the `partner_company_pc` manifest,
  Membership, Portal Grant, route allowlist, and service-partner role checks.

## Routes

- `/partner`
- `/partner/rfqs`
- `/partner/rfqs/{id}`
- `/partner/tasks`
- `/partner/tasks/{id}`
- `/partner/calendar`
- `/partner/performance`
- `/partner/work-packages`
- `/partner/work-packages/{id}`
- `/partner/crews`
- `/partner/workers`

## Verification Evidence

```text
frontend-pc production build: passed
feature parity ledger: 5176 entries
runtime API coverage: 676 / 676
parity implementation checks: passed
```

## Known Gaps And Dependency Gates

- The earlier Service / AMC task workflow remains available for compatibility;
  construction delivery now uses WorkPackage -> Crew -> FieldTask -> Evidence.
- Independent browser E2E, cross-partner isolation, upload, completion, and
  acceptance-flow verification remain required.
- ZL01 through ZL06 must be independently verified before ZL07 can be unlocked.

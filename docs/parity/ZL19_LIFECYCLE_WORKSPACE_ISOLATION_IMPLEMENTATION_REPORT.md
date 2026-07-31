# ZL19 Lifecycle Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Sites, Assets, Customer Warranties, AMC
  Contracts, Monitoring Points, Inventory Items, Stock Movements, Maintenance
  Schedules, and Calibration Records.
- Backfilled Sites from their uniquely linked Project Workspace before falling
  back to company membership or the default Workspace.
- Migration fails closed when a Site or linked lifecycle resource spans
  multiple Workspaces.
- New lifecycle CRUD resolves Workspace from linked Project/Site/Asset records
  and rejects mixed-Workspace links.
- Acceptance-created Sites/Assets and partner-dispatched maintenance work now
  inherit the Delivery Project Workspace.
- Customer Project lifecycle views no longer include same-company AMC or
  warranty records from another Workspace.
- Kept `CebuProjects` unchanged.

## Migration

- `066_lifecycle_workspace_scope.py`
- Current local schema head: `066`.

## Verification Evidence

```text
focused lifecycle/Project/Customer tests: 38 passed, 3 warnings
alembic current: 066 (head)
alembic check: No new upgrade operations detected
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Asset creation rejects a Site and Project from different Workspaces.
- [ ] Maintenance creation rejects mixed Project, Monitoring Point, and Asset Workspaces.
- [ ] Customer Project lifecycle pages cannot expose same-company records from another Workspace.
- [ ] A Site containing Assets from multiple Project Workspaces blocks migration.
- [ ] Re-run migration `066` against a representative production export.


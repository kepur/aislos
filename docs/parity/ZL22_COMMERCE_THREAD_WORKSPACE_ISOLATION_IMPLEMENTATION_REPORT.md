# ZL22 Commerce Thread Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Commerce Threads.
- Threads inherit Workspace from their Procurement Request or Commerce Order.
- Migration fails closed when a Thread's Request and Order use different
  Workspaces.
- Same-company buyers can list/read/post only when they own the Request/Order
  inside an accessible Workspace.
- Supplier companies remain explicit transaction parties and can access their
  own buyer-facing Threads without joining the buyer Workspace.
- Cross-Workspace message posting now returns an authorization failure rather
  than a generic conflict.
- Legacy Cebu message import assigns the linked Request/Order Workspace.
- Kept `CebuProjects` unchanged.

## Migration

- `069_commerce_thread_workspace_scope.py`
- Current local schema head: `069`.

## Verification Evidence

```text
focused Commerce/Cebu/thread tests: 22 passed, 2 warnings
alembic current: 069 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Same-company Buyer A cannot list/read/post to Buyer B's Workspace Thread.
- [ ] A supplier explicitly participating in both Orders can access both Threads.
- [ ] A Thread linked to mismatched Request and Order Workspaces blocks migration.
- [ ] Re-run migration `069` against a representative production export.


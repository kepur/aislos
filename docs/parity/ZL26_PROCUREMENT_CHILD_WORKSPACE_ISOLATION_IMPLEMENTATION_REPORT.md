# ZL26 Procurement Child Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Procurement Facts, BOQ Versions,
  Procurement Packages, and Commercial Snapshots.
- Generated Facts, BOQ Versions, Packages, Snapshots, and RFQs inherit the
  parent Procurement Project Workspace.
- Fact, BOQ, and Package reads fail closed when a child Workspace does not
  match the authorized parent project.
- RFQ publishing rejects mixed Project, Package, BOQ, or Snapshot Workspaces.
- Corrected Procurement RFQ creation so it no longer falls back to the default
  Workspace.
- Migration backfills children from their parent project, repairs generated RFQ
  scope, and fails closed when linked Project/BOQ/Package records disagree.
- Kept `CebuProjects` unchanged.

## Migration

- `073_procurement_child_workspace_scope.py`
- Current local schema head: `073`.

## Verification Evidence

```text
focused Procurement workspace and regression tests: 41 passed, 2 warnings
full backend suite: 405 passed, 3 warnings
alembic current: 073 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
frontend-pc production build: passed
frontend-h5 production build: passed
12 Portal/website HTTP entry checks: all 200
browser checks for public PC/H5/Admin entries: 0 console errors
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] A mismatched Procurement Fact is not listed or patchable through Project A.
- [ ] A mismatched BOQ Version is not returned through Project A.
- [ ] A mismatched Procurement Package is not listed, patched, or published.
- [ ] Generated Commercial Snapshot and RFQ inherit the exact Project Workspace.
- [ ] RFQ publish rejects mixed Project, BOQ, Package, and Snapshot Workspaces.
- [ ] Re-run migration `073` against a representative production export.

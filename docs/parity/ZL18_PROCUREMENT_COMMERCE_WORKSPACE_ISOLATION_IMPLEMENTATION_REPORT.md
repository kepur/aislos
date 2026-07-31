# ZL18 Procurement Commerce Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Procurement Projects, Procurement
  Requests, and Commerce Orders.
- New Procurement Projects require an exact Workspace when a user has multiple
  active memberships.
- New Commerce Requests resolve an exact active Workspace and reject a forged
  Workspace.
- Commerce Orders inherit the awarded Procurement Request Workspace.
- Same-company customer members cannot list, read, approve delivery, or act on
  another Workspace's Requests and Orders.
- Preserved supplier access to Orders where the supplier company is a real
  transaction party.
- Legacy Cebu bridge and historical importer assign a Workspace without
  changing `CebuProjects`.

## Migration

- `065_procurement_commerce_workspace_scope.py`
- Current local schema head: `065`.

## Verification Evidence

```text
focused Procurement/Commerce/Customer/security tests: 25 passed, 2 warnings
alembic current: 065 (head)
alembic check: No new upgrade operations detected
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Same-company Workspace A customer cannot list or read Workspace B Requests.
- [ ] Same-company Workspace A customer cannot list, read, approve, pay, or dispute Workspace B Orders.
- [ ] Supplier company parties can still operate their awarded Orders.
- [ ] Awarding an Offer creates an Order in the Request Workspace.
- [ ] Multi-membership Procurement Project creation requires an explicit Workspace.
- [ ] Re-run migration `065` against a representative production export.


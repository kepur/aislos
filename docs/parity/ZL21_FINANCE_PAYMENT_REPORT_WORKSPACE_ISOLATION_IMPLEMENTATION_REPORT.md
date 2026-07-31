# ZL21 Finance Payment Report Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Project Finances, Payment Plans, and
  Report Jobs.
- Finance operators list/read/create/update/delete only inside exact
  `admin_finance` Workspace grants.
- Project Finance creation rejects forged Workspace IDs and mixed
  Project/customer links.
- Payment Plans inherit Workspace from Quote, Project, or Commerce Order.
- Compliance Report Jobs inherit Workspace from their Project.
- Migration fails closed when a Payment Plan links a Quote and Project from
  different Workspaces.
- Kept `CebuProjects` unchanged.

## Migration

- `068_finance_payment_report_workspace_scope.py`

## Verification Evidence

```text
focused finance/payment/report/lifecycle tests: 38 passed, 2 warnings
alembic check after 068: No new upgrade operations detected
python -m compileall -q app tests: passed
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] A Finance operator granted only Workspace A cannot list/read/update/delete Workspace B finance records.
- [ ] A Finance operator cannot create a record with a forged Workspace ID.
- [ ] A Payment Plan inherits the exact Quote/Order Workspace.
- [ ] A Report Job inherits the exact Project Workspace.
- [ ] Re-run migration `068` against a representative production export.


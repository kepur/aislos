# ZL20 CRM Support Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Inquiries, Proposal Plans, and Tickets.
- Backfilled records from linked Lead, Project, Asset, Monitoring Point,
  uniquely resolvable customer membership, or the active default Workspace.
- Migration fails closed when linked Proposal or Ticket resources span
  different Workspaces.
- Sales Managers can list, read, update, and change status only inside their
  exact CRM Workspace grants.
- Customer Inquiry and Ticket lists no longer expose same-company records from
  another Workspace.
- Customer Ticket creation rejects forged Workspace selection.
- Ticket creation/update rejects mixed Project, Asset, and Monitoring Point
  Workspaces.
- Proposal creation rejects mixed Lead and Project Workspaces.
- Customer workspace summary counts only Tickets in accessible Workspaces.
- Kept `CebuProjects` unchanged.

## Migration

- `067_inquiry_proposal_ticket_workspace_scope.py`
- Current local schema head: `067`.

## Verification Evidence

```text
focused CRM/support/Project/Customer tests: 14 passed, 2 warnings
alembic current: 067 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] A Sales Manager granted only Workspace A cannot list/read/update/status-change Workspace B Tickets.
- [ ] A customer in Workspace A cannot list same-company Workspace B Inquiries or Tickets.
- [ ] A customer cannot create a Ticket using a forged Workspace ID.
- [ ] A Ticket linked to Project A and Monitoring Point B is rejected.
- [ ] A Proposal linked to Lead A and Project B is rejected.
- [ ] Re-run migration `067` against a representative production export.


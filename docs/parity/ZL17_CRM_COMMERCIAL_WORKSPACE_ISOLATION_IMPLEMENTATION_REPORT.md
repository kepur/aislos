# ZL17 CRM Commercial Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Leads, Quotes, and RFQs.
- Backfilled Leads from linked Projects, an unambiguous buyer-company
  membership, or the default Workspace.
- Backfilled Quotes and RFQs from their linked Project or Lead and reject a
  migration when those links disagree.
- Restricted Sales Manager Lead operations and customer Lead/Quote views to
  exact active Workspaces.
- Prevented Quote and RFQ creation from linking a Lead and Project in different
  Workspaces.
- Scoped Customer Workspace quote approvals to the customer's Workspaces.
- Kept `CebuProjects` unchanged.

## Migrations

- `063_lead_workspace_scope.py`
- `064_quote_rfq_workspace_scope.py`

## Verification Evidence

```text
focused CRM/Project/RFQ/Customer tests: 22 passed, 2 warnings
alembic current after slice: 064 (head)
alembic check: No new upgrade operations detected
git diff --check: passed
```

## Independent Verification Checklist

- [ ] A Sales Manager granted only Workspace A cannot read or mutate Workspace B Leads.
- [ ] Same-company customers in different Workspaces cannot read each other's Leads or Quotes.
- [ ] Quote/RFQ creation rejects mixed-Workspace Lead and Project links.
- [ ] Re-run migrations `063` and `064` against a representative production export.


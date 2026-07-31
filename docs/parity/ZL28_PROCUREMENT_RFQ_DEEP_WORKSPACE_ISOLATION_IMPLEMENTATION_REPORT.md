# ZL28 Procurement and RFQ Deep Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to BOQ Items, BOQ Item Options, Solution
  Plans, Procurement Package Items, RFQ Invitations, and Partner Bids.
- BOQ children inherit BOQ Version Workspace.
- Package Items inherit Procurement Package Workspace and are checked against
  linked BOQ Item/Option scope.
- RFQ Invitations and Partner Bids inherit RFQ Workspace.
- Customer Procurement and Partner Portal reads filter mismatched deep children.
- RFQ invite, bid evaluation, and award paths only operate on exact-Workspace
  child records.
- Kept `CebuProjects` unchanged.

## Migration

- `075_procurement_rfq_deep_workspace_scope.py`
- Current local schema head: `075`.

## Verification Evidence

```text
focused Procurement/RFQ regression tests: 53 passed, 2 warnings
full backend suite after ZL28: 406 passed, 3 warnings
alembic current: 075 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] BOQ Item, Option, and Solution Plan Workspace matches BOQ Version.
- [ ] Package Item Workspace matches Package, BOQ Item, and selected Option.
- [ ] RFQ Invitation and Partner Bid Workspace matches RFQ.
- [ ] Partner Portal cannot list or submit against a mismatched Invitation.
- [ ] Bid evaluation and award ignore mismatched Partner Bids.
- [ ] Re-run migration `075` against a representative production export.

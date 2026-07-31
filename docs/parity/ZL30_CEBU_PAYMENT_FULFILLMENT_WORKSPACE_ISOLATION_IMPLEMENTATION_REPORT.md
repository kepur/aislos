# ZL30 Cebu Payment/Fulfillment Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cases before changing the status to `VERIFIED`.

## Delivered

- Added nullable indexed `workspace_id` FK to:
  - `order_shipping`
  - `escrow_transactions`
  - `payouts`
  - `provider_payment_intents`
  - `payment_events`
- Cebu trade service now derives child Workspace from `commerce_orders`.
- Escrow capture/release/refund and payout processing reject child/order
  Workspace mismatch.
- Cebu historical migration imports now bind shipping, escrow, payout,
  payment intent and payment event rows to the migrated order Workspace.
- Cebu Trade admin escrow/payout actions require an exact Workspace grant.
- Cebu Admin payment workbench filters Workspace-bound rows by accessible
  admin Workspaces.
- Kept `CebuProjects` unchanged.

## Migration

- `077_cebu_payment_fulfillment_workspace_scope.py`
- Current local schema head: `077`.

## Verification Evidence

```text
focused Cebu/Commerce tests: 17 passed, 2 warnings
single regression retry: 1 passed, 2 warnings
full backend suite after ZL30: 409 passed, 3 warnings
alembic current: 077 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
12 Portal/website HTTP entry checks: all 200
recent backend/frontend error log scan: clean
Cebu payment/fulfillment tables with workspace_id: 5/5
remaining inherited child gaps: 13
```

## Independent Verification Checklist

- [ ] Escrow inherits exact order Workspace.
- [ ] Escrow refund/capture/release reject mismatched child/order Workspace.
- [ ] Payout inherits exact order Workspace and rejects mismatched escrow/order.
- [ ] Order shipping, provider payment intent and payment event imports inherit
  order Workspace.
- [ ] Admin user without a Workspace grant cannot mutate escrow/payout rows in
  that Workspace.
- [ ] Admin payment lists do not expose rows from inaccessible Workspaces.
- [ ] Re-run migration `077` against a representative production export.

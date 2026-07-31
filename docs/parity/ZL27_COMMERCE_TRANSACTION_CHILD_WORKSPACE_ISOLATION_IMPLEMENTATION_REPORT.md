# ZL27 Commerce Transaction Child Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Supplier Offers, Order Deliveries,
  Order Disputes, Transaction Reviews, Commerce Payment Intents, Commerce
  Messages, and Commerce Settlements.
- Offers inherit Procurement Request Workspace.
- Deliveries, Disputes, Reviews, Payment Intents, and Settlements inherit
  Commerce Order Workspace.
- Messages inherit Commerce Thread Workspace.
- Transaction services reject mixed parent/child Workspaces.
- Parent-scoped Offer, Delivery, Dispute, Review, Payment Intent, and Message
  reads fail closed on mismatched child scope.
- Cebu historical migration imports now preserve the linked parent Workspace.
- Kept global/reusable Supplier Listings, Trust Profiles, and reconciliation
  runs outside forced tenant scope.
- Kept `CebuProjects` unchanged.

## Migration

- `074_commerce_transaction_child_workspace_scope.py`
- Current local schema head: `074`.

## Verification Evidence

```text
focused Commerce/Cebu transaction tests: 33 passed, 2 warnings
alembic current: 074 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Offer Workspace always matches its Procurement Request.
- [ ] Delivery, Dispute, Review, Payment Intent, and Settlement Workspaces
      always match their Commerce Order.
- [ ] Message Workspace always matches its Commerce Thread.
- [ ] Mismatched transaction children cannot be read or mutated through the
      authorized parent.
- [ ] Cebu historical imports preserve transaction child Workspace scope.
- [ ] Re-run migration `074` against a representative production export.

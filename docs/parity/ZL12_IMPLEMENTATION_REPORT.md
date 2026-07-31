# ZL12 Supplier Access And Matching Rules Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementing Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay the tests,
Portal behavior, and migration.

## Delivered

- Split supplier company administration from daily supplier operations:
  - the first supplier membership for a company becomes `supplier_owner`;
  - invited supplier users remain `supplier_operator`;
  - Operators retain catalog, RFQ, quote, order, message, and notification work;
  - only Owners may edit company fields, invite members, or deactivate/restore
    team access.
- Added a zero-loss migration that promotes one existing supplier operator per
  company/workspace to Owner without deleting the original Operator membership.
- Added Owner/Operator-aware PC and H5 supplier settings and team screens.
- Split Customer Owner from Customer Member company-profile authority:
  Customer Members can update their own profile but cannot mutate company
  fields; first-time buyer company creation synchronizes the Owner Membership
  to the new company.
- Added Owner/Member-aware Buyer PC and H5 company-profile screens.
- Added persisted supplier category and region matching preferences.
- Added explicit `region_id` to Core Commerce procurement requests.
- Connected Buyer PC/H5 request creation to active Core Regions.
- Connected Supplier PC/H5 matching rule pages to real category/region data.
- Applied category/region rules to Supplier Pings and region rules to supplier
  candidate matching.
- Changed auth brute-force protection so only failed credentials consume
  limits, using both IP-spray and IP-plus-account buckets. Successful logins do
  not lock out valid users or shared-NAT operators.

## Migrations

- `056_supplier_owner_membership.py`
- `057_supplier_matching_rules.py`

Current local schema head: `057`.

## Security Rules

- Cross-company Supplier Team access remains denied.
- A Supplier Operator receives `403` when attempting company profile or team
  administration.
- A Customer Member receives `403` when attempting buyer company profile
  administration.
- Supplier Owner and Operator remain the same application role (`vendor`) but
  have different Workspace Membership authority.
- Unknown or inactive category/region preference IDs are rejected with `422`.
- Matching rules never trust supplier-supplied company identity.

## Verification Evidence

```text
supplier/customer ownership + matching + auth focused regression: 13 passed
backend full suite: 385 passed, 3 warnings
frontend-pc production build: passed
frontend-h5 production build: passed
frontend-admin production build: passed
alembic current: 057 (head)
alembic check: No new upgrade operations detected
feature parity ledger: 5470 entries
runtime API coverage: 683 / 683
git diff --check: passed
CebuProjects working tree: unchanged
```

## Independent Verification Checklist

- [ ] Re-run backend full suite from a clean process.
- [ ] Verify Owner sees team/company controls in Supplier PC and H5.
- [ ] Verify Operator sees read-only company/team UI and receives backend `403`
      on direct write attempts.
- [ ] Verify Customer Member sees read-only company UI, can update personal
      fields, and receives backend `403` on direct company writes.
- [ ] Verify a request in a selected category/region enters Supplier Pings.
- [ ] Verify an otherwise matching request outside selected regions is absent.
- [ ] Verify a region-scoped listing is not returned as a candidate in another
      region.
- [ ] Verify migrations `056` and `057` on a representative production export.
- [ ] Confirm rollback/reconciliation behavior before production cutover.

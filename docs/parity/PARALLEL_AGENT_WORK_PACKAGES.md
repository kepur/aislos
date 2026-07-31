# Parallel Agent Work Packages
Generated at: 2026-06-13T06:56:30.367984+00:00

The work packages below are derived from the current zero-loss inventory and preserve the single-migration-lock rule.

## Shared Preconditions

- Root of truth: /Users/mac/Code_Start/Aislos
- Status flow: TODO -> IN_PROGRESS -> READY_FOR_VERIFY -> VERIFIED or FAILED_VERIFY
- No agent may self-mark VERIFIED
- Backend schema migrations remain serialized behind a global lock

## Agent 1: Security and Permissions

- Scope: Ainerwise/backend and Cebu compatibility ownership paths only
- Primary inputs: compatibility APIs, portal grants, procurement ownership, field permissions
- File ownership: Ainerwise/backend/app, Ainerwise/backend/tests
- Cannot overlap with any other backend migration package

## Agent 2: Frontend Build and CI

- Scope: frontend-pc, frontend-h5, frontend-admin, lockfiles, CI definitions
- Guardrail: no business behavior changes
- Parallel-safe with Agent 1 because it must not touch backend business logic

## Agent 3: Portal Foundation

- Scope: shared portal manifest state, portal switch, route/menu/layout grant enforcement
- Depends on: ZL01 inventory and the security contract that defines valid grants
- File ownership: frontend-pc, frontend-h5, frontend-admin portal infrastructure files plus supporting auth endpoints

## Agent 4: Field Operations and Worker PWA

- Scope: field operations admin models and worker H5 real-device flows
- Depends on: Agent 3 portal foundation
- Validation must include photo, scan, signature, location, offline queue, and conflict recovery evidence

## Agent 5: Cebu Zero-Loss Migration

- Inventory baseline: Cebu PC 655 entries, H5 430 entries, Admin 357 entries
- Migration batches: Marketplace, RFQ, Offer, Order, Message, Wallet, Dispute, KYC, Buyer, Supplier, Admin, Notifications
- Each batch must link old route, new route, new API, permission rule, tests, and screenshots before READY_FOR_VERIFY

## Agent 6: Independent Verification

- Scope: read-only verification and reproducible failure evidence only
- Must reject placeholder data, fake completion, early-return tests, and privilege-escalation paths
- Can move tasks from READY_FOR_VERIFY to VERIFIED or FAILED_VERIFY only

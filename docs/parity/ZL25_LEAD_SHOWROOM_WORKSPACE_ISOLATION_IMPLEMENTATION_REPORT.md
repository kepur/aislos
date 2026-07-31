# ZL25 Lead and Showroom Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Site Surveys, AI Conversations, Stores,
  Kiosk Devices, Showroom Sessions, and Showroom Orders.
- Site Surveys and AI Conversations inherit their linked Lead Workspace.
- Kiosk Devices inherit Store Workspace; Showroom Sessions inherit Device
  Workspace; Showroom Orders inherit Session/Store Workspace.
- Mixed linked Workspaces are rejected or hidden from scoped APIs.
- Migration fails closed when linked legacy records disagree.
- Kept `CebuProjects` unchanged.

## Migration

- `072_lead_showroom_workspace_scope.py`
- Current local schema head at implementation completion: `072`.

## Verification Evidence

```text
focused Lead/Showroom workspace tests: 10 passed
full backend suite: 403 passed, 3 warnings
alembic current: 072 (head)
alembic check: No new upgrade operations detected
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Site Survey A cannot be read or updated through Lead A when its Workspace is B.
- [ ] Showroom Session cannot link a Lead from a different Workspace.
- [ ] Showroom Order cannot mix Session and Store Workspaces.
- [ ] AI Conversation inherits the linked Lead or Showroom Session Workspace.
- [ ] Re-run migration `072` against a representative production export.

# ZL14 Privacy Data Requests Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementing Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay the
privacy and retention behavior. This report covers the data export/delete
part of I.6 only. Full tenant/private isolation remains `IN_PROGRESS`.

## Delivered

- Added an auditable `PrivacyRequest` lifecycle for export and deletion
  requests without persisting another copy of the exported PII.
- Added owned self-service APIs to create and download a seven-day export,
  request deletion, list requests, and cancel a pending request.
- Added Admin review APIs and a Privacy Requests workbench.
- Added Customer PC and H5 Privacy & Data controls.
- Added a current user export covering profile, memberships, Portal grants,
  notifications, customer work, procurement, commerce, field work, Agent
  installations, conversations, and user-attributed audit activity.
- Added recursive JSON-safe serialization for nested structured data.
- Added verified anonymization that revokes memberships, Portal grants, crew
  memberships, active task assignments, notification contacts, watchlist
  items, notifications, and password reset tokens while retaining required
  business, finance, project, and audit evidence.
- Kept `CebuProjects` unchanged.

## Security Rules

- Export downloads return `404` to non-owners and expired requests.
- Exports exclude password hashes and audit before/after snapshots.
- A normal user cannot complete a deletion request.
- An administrator cannot approve their own deletion.
- A normal administrator cannot anonymize an Admin or Super Admin account;
  a different Super Admin is required.
- Completed deletion randomizes credentials, anonymizes direct identity,
  deactivates login, and revokes all known access paths without physically
  deleting retained business evidence.
- Every request, download, cancellation, rejection, and completion is audited.

## Migration

- `058_privacy_requests.py`
- Current local schema head: `058`.

## Verification Evidence

```text
privacy focused tests: 4 passed, 2 warnings
backend full suite: 389 passed, 3 warnings
frontend-pc production build: passed
frontend-h5 production build: passed
frontend-admin production build: passed
alembic current: 058 (head)
alembic check: No new upgrade operations detected
feature parity ledger: 5511 entries
runtime API coverage: 691 / 691
git diff --check: passed
CebuProjects working tree: unchanged
```

## Independent Verification Checklist

- [ ] Download a populated export and inspect every included data family.
- [ ] Confirm another user cannot download the export by guessing its ID.
- [ ] Confirm expired exports cannot be downloaded.
- [ ] Confirm an Admin cannot self-approve deletion or delete a Super Admin.
- [ ] Complete deletion for a representative customer with multiple
      Workspaces, Portal grants, notifications, field assignments, orders,
      projects, and audit events.
- [ ] Confirm login and all memberships/grants are revoked after completion.
- [ ] Confirm required finance, order, project, and audit evidence remains.
- [ ] Review production retention/legal requirements before enabling the
      completion action outside development.
- [ ] Verify migration `058` on a representative production export.

# ZL16 Delivery Project Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementing Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay the
cross-Workspace cases. Full tenant/private isolation remains `IN_PROGRESS`
because Lead, Quote, RFQ, and several lifecycle resource families do not yet
carry an explicit Workspace binding.

## Delivered

- Added explicit Workspace binding to Delivery `Project`.
- Backfilled existing Projects from WorkPackages, an unambiguous buyer-company
  membership, or the active default Workspace.
- Made all API-created Projects resolve an active Workspace.
- Restricted Project Manager list, read, update, status, notes, partner
  assignment, dispatch, and create operations to exact Workspace grants.
- Restricted customer Project lists, Project Space, lifecycle views,
  installations, assets, summary counts, and project-linked tickets to active
  customer Workspace memberships.
- Prevented a Field WorkPackage from linking to a Project in another
  Workspace.
- Made RFQ-award Project creation resolve an unambiguous Workspace and fail
  closed for companies with multiple active Workspaces.
- Changed Agent Project object grants to require both exact Workspace and exact
  Project; a global Project object grant cannot authorize a Workspace-bound
  Project.
- Backfilled existing Project Agent object grants to the Project Workspace.
- Added Workspace selectors to Admin Project create/list and aligned Field
  Operations Project choices with the selected Workspace.
- Kept `CebuProjects` unchanged.

## Security Rules

- A Project Manager cannot list, read, create, or mutate a Project outside an
  exact granted Workspace.
- Two customer users from the same company do not automatically share Projects
  across Workspaces.
- A cross-Workspace WorkPackage/Project link returns `409`.
- Legacy unscoped Projects are visible to global Admins and their owning
  customer only; non-global Project Managers cannot operate them.
- Third-party Agent activation and Project grants remain blocked until the
  execution sandbox release gate is complete.

## Migrations

- `061_project_workspace_scope.py`
- `062_project_agent_object_grant_scope.py`
- Current local schema head: `062`.

## Verification Evidence

```text
focused Project/Agent/Field/Customer/RFQ tests: 32 passed, 2 warnings
alembic current: 062 (head)
alembic check: No new upgrade operations detected
git diff --check: passed
```

Full regression evidence will be appended after this implementation slice is
replayed with the complete repository gates.

## Independent Verification Checklist

- [ ] Confirm a Project Manager with Workspace A access cannot list, read,
      create, update, dispatch, or assign against Workspace B.
- [ ] Confirm customers in the same company but different Workspaces cannot
      see each other's Projects, installations, assets, or linked tickets.
- [ ] Confirm a WorkPackage cannot link across Project Workspaces.
- [ ] Confirm RFQ award fails closed when the buyer company has multiple
      possible Workspaces.
- [ ] Confirm a global Agent Project object grant cannot authorize a
      Workspace-bound Project.
- [ ] Confirm the exact Workspace + Project object grant authorizes an
      official Core Agent.
- [ ] Verify migrations `061` and `062` on a representative production export.
- [ ] Review and resolve every legacy-unscoped Project before production
      third-party Agent execution.

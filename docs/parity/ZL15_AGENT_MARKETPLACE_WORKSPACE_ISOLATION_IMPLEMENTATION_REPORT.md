# ZL15 Agent Marketplace Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementing Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay all
cross-Workspace negative cases. Full tenant/private isolation remains
`IN_PROGRESS`, and the third-party execution sandbox remains `TODO`.

## Delivered

- Scoped every Agent Marketplace installation to an explicit active
  Workspace.
- Required an active manager membership to install or uninstall an Agent.
- Required callers with multiple memberships to select an exact Workspace.
- Scoped Agent capability and object grants to a Workspace.
- Created all eight third-party capability grants as denied when installed.
- Required third-party runtime calls to provide an exact Workspace, have an
  active installation there, and pass exact-Workspace capability and object
  grants.
- Kept official Core Agent grants global.
- Blocked third-party Agent activation and Project object grants until
  Project Workspace binding and the execution sandbox release gate are
  complete.
- Added Admin Workspace selection and fail-closed error presentation.
- Added downgrade preconditions so migrations never silently delete or merge
  multi-Workspace installation/grant data.
- Kept `CebuProjects` unchanged.

## Security Rules

- A global grant cannot authorize a third-party Agent in any Workspace.
- A Workspace A grant cannot authorize execution in Workspace B.
- A revoked or inactive membership cannot manage an installation.
- Ordinary customer members cannot install or uninstall Agents.
- A third-party Agent cannot be activated or receive a Project grant while
  the remaining sandbox and Project binding gates are incomplete.

## Migrations

- `059_agent_installation_workspace_scope.py`
- `060_agent_grant_workspace_scope.py`
- Current local schema head: `060`.

## Verification Evidence

```text
focused Agent/API/security tests: 25 passed, 2 warnings
frontend-admin production build: passed
frontend-pc production build: passed
alembic current: 060 (head)
alembic check: No new upgrade operations detected
```

Full regression evidence will be appended after this implementation slice is
replayed with the complete repository gates.

## Independent Verification Checklist

- [ ] Install the same listing for the same user in two Workspaces and confirm
      the installations remain distinct.
- [ ] Confirm a customer member without a manager membership cannot install
      or uninstall an Agent.
- [ ] Revoke an installer membership and confirm uninstall is denied.
- [ ] Confirm a global grant cannot authorize a third-party Agent.
- [ ] Confirm Workspace A capability/object grants cannot authorize execution
      in Workspace B.
- [ ] Confirm a third-party Agent with an exact installation but denied grant
      cannot execute.
- [ ] Confirm third-party activation and Project grants return a fail-closed
      release-gate response.
- [ ] Verify migrations `059` and `060` on a representative production export.
- [ ] Confirm downgrade refuses to collapse distinct Workspace data.

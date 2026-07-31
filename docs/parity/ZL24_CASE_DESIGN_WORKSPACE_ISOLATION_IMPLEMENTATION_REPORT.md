# ZL24 Living Case and Design Revision Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Living Cases and Design Revisions.
- Living Cases inherit their Delivery Project Workspace.
- Acceptance-created Living Cases inherit the accepted Project Workspace.
- Design Revisions inherit their Project or Site Workspace.
- Mixed Project/Site Workspace Design Revisions are rejected.
- Forged Living Case Workspace IDs are rejected.
- Migration fails closed when legacy Design Revisions link Sites and Projects
  from different Workspaces.
- Kept `CebuProjects` unchanged.

## Migration

- `071_case_design_workspace_scope.py`
- Current local schema head: `071`.

## Verification Evidence

```text
focused case/design workspace tests: 14 passed, 2 warnings
alembic current: 071 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Living Case A cannot be created with Project A and forged Workspace B.
- [ ] Design Revision A cannot link Project A and Site B across Workspaces.
- [ ] Acceptance-created Living Cases inherit the accepted Project Workspace.
- [ ] Public Living Case responses expose only public-visible records and fields.
- [ ] Re-run migration `071` against a representative production export.

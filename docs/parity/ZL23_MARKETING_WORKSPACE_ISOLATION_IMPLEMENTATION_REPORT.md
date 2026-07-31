# ZL23 Marketing Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. An independent verification Agent must
replay the cross-Workspace cases before changing the status to `VERIFIED`.

## Delivered

- Added explicit Workspace binding to Campaigns, Contacts, Activities,
  Creative Briefs, Media Requests, and Media Assets.
- Marketing Operators list/read/create/update/delete only inside exact
  Marketing Portal Workspace grants.
- Campaign draft preparation selects only opted-in Contacts in the Campaign
  Workspace.
- Lead and Inquiry follow-up Contacts/Activities inherit their source
  Workspace.
- Creative Briefs inherit the selected Campaign Workspace; Media Requests and
  imported AinerN2D assets inherit the Brief Workspace.
- Marketing asset generation, review, scheduling, and publish-job lists now
  enforce Workspace access.
- Forged Workspace IDs and mixed Campaign/Contact/Lead/Inquiry links are
  rejected.
- AinerN2D remains an external system using the approved Brief export and
  Media Asset import contract only.
- Kept `CebuProjects` unchanged.

## Migration

- `070_marketing_workspace_scope.py`
- Current local schema head: `070`.

## Verification Evidence

```text
focused Marketing/V4/media integration tests: 57 passed, 2 warnings
alembic current: 070 (head)
alembic check: No new upgrade operations detected
python -m compileall -q app tests: passed
git diff --check: passed
CebuProjects status: unchanged
```

## Independent Verification Checklist

- [ ] Marketing Operator A cannot list/read/update Campaign/Contact/Activity/Brief/Asset B.
- [ ] Marketing Operator A cannot use a forged Workspace ID.
- [ ] Mixed Campaign A and Contact B activity creation is rejected.
- [ ] AinerN2D receives only approved provider-neutral Brief exports and imports Assets without internal-system access.
- [ ] Re-run migration `070` against a representative production export.


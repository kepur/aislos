# ZL31 Remaining Child Workspace Isolation Implementation Report

Status: `READY_FOR_VERIFY`

This is implementation evidence only. The implementation Agent does not mark
this work `VERIFIED`; an independent verification Agent must replay the checks
and attempt cross-Workspace bypasses before changing status.

## Scope

Bound the final database-detected inherited child gaps to `workspace_id`:

- AI Conversation children:
  - `ai.messages`
  - `ai.agent_runs`
  - `ai.memories`
  - `channels.channel_threads`
- Marketing children:
  - `publish_jobs`
  - `marketing_creative_brief_versions`
  - `marketing_media_uploads`
- Field Operations and Delivery children:
  - `crew_memberships`
  - `field_tasks`
  - `task_assignments`
  - `agent_missions`
  - `agent_mission_tasks`
  - `bom_items`

## Implementation

- Added indexed `workspace_id` foreign keys through migration `078`.
- Backfilled child workspaces from their authorized parent objects.
- Failed closed in migration on parent/child Workspace disagreement.
- Kept Field Operations child `workspace_id` columns non-null and added ORM
  inheritance hooks so direct model inserts still inherit from Crew,
  WorkPackage, and FieldTask parents.
- Updated runtime create/import paths:
  - Showroom/Kiosk transcript messages inherit session Workspace.
  - Agent Mission and Mission Task inherit Project Workspace.
  - Mission, Support, Procurement, RFQ, and publish AgentRun records carry
    Workspace when source object has one.
  - Marketing Creative Brief versions inherit Brief Workspace.
  - Marketing media uploads inherit Media Request Workspace.
  - Publish jobs inherit Marketing Asset Workspace.
  - BOM items inherit Proposal Plan Workspace.
  - Field assignments and crew memberships validate parent Workspace.
- Tightened reads:
  - Conversation messages are filtered by the conversation Workspace.
  - Publish jobs filter by both job and asset Workspace for scoped marketing
    users.
  - Field task assignment reads require assignment/task Workspace consistency.
  - Project Space mission/task reads require Project Workspace consistency.
  - BOM list/update/delete requires item/plan Workspace consistency.

## Key Files

- `Ainerwise/backend/alembic/versions/078_remaining_child_workspace_scope.py`
- `Ainerwise/backend/app/models/ai.py`
- `Ainerwise/backend/app/models/channels.py`
- `Ainerwise/backend/app/models/content.py`
- `Ainerwise/backend/app/models/field_service.py`
- `Ainerwise/backend/app/models/marketing.py`
- `Ainerwise/backend/app/models/mission.py`
- `Ainerwise/backend/app/models/proposal.py`
- `Ainerwise/backend/app/services/field_service.py`
- `Ainerwise/backend/app/services/agent_team.py`
- `Ainerwise/backend/app/services/marketing_briefs.py`
- `Ainerwise/backend/app/services/media_integration.py`
- `Ainerwise/backend/app/services/procurement_ai.py`
- `Ainerwise/backend/app/services/support_agent.py`
- `Ainerwise/backend/app/api/v1/endpoints/ai_reviews.py`
- `Ainerwise/backend/app/api/v1/endpoints/ai_workflows.py`
- `Ainerwise/backend/app/api/v1/endpoints/agent_missions.py`
- `Ainerwise/backend/app/api/v1/endpoints/field_service.py`
- `Ainerwise/backend/app/api/v1/endpoints/proposals.py`
- `Ainerwise/backend/app/api/v1/endpoints/rfqs.py`
- `Ainerwise/backend/app/api/v1/endpoints/showroom.py`
- `Ainerwise/backend/app/tasks/publishing_tasks.py`

## Verification Run By Implementation Agent

Commands:

```bash
docker exec ainerwise-backend-1 alembic upgrade head
docker exec ainerwise-backend-1 alembic current
docker exec ainerwise-backend-1 alembic check
docker exec ainerwise-backend-1 pytest tests/test_customer_workspace_e2e.py::test_customer_workspace_is_company_scoped_and_quote_safe tests/test_field_service_e2e.py::test_partner_company_field_ops_is_company_scoped tests/test_security_boundaries.py::test_field_worker_assignment_does_not_bypass_workspace_grant
docker exec ainerwise-backend-1 pytest
```

Results:

- Alembic current: `078 (head)`
- Alembic check: `No new upgrade operations detected.`
- Focused regression: `3 passed`
- Full backend suite: `409 passed, 3 warnings`

## Independent Verification Checklist

- Attempt to forge a `field_tasks.workspace_id` different from its
  `work_packages.workspace_id`.
- Attempt to assign a FieldTask to a Crew from another Workspace.
- Attempt to list a conversation's messages after inserting a mismatched
  `ai.messages.workspace_id`.
- Attempt to list Marketing publish jobs through a scoped user when the job
  and asset Workspaces differ.
- Attempt to mutate a BOM item whose `workspace_id` does not match its
  Proposal Plan.
- Re-run Alembic upgrade/check on a clean database and on a database with
  deliberately mismatched child records.

## CebuProjects

`CebuProjects` was not modified. All implementation landed in `Ainerwise`.

# Deep Workspace Isolation Handoff

Status: `READY_FOR_VERIFY`

Implementation Agents may claim one remaining group at a time. They may only
mark their group `READY_FOR_VERIFY`; an independent verifier owns `VERIFIED`.

## Completed In This Run

- ZL25: Lead and Showroom children, migration `072`
- ZL26: Procurement Project children and generated RFQs, migration `073`
- ZL27: Commerce transaction children, migration `074`
- ZL28: Procurement/RFQ deep children, migration `075`
- ZL29: Payment Milestones and Ledger Entries, migration `076`
- ZL30: Cebu payment and fulfillment children, migration `077`
- ZL31: AI Conversation, Marketing child, Field Operations and Delivery children, migration `078`

## Remaining Database-Detected Child Gaps

### AI Conversation Children

- `ai.agent_runs.conversation_id -> ai.conversations` - READY_FOR_VERIFY in ZL31
- `ai.memories.source_conversation_id -> ai.conversations` - READY_FOR_VERIFY in ZL31
- `ai.messages.conversation_id -> ai.conversations` - READY_FOR_VERIFY in ZL31
- `channels.channel_threads.conversation_id -> ai.conversations` - READY_FOR_VERIFY in ZL31

### Marketing Children

- `publish_jobs.asset_id -> marketing_assets` - READY_FOR_VERIFY in ZL31
- `marketing_creative_brief_versions.brief_id -> marketing_creative_briefs` - READY_FOR_VERIFY in ZL31
- `marketing_media_uploads.media_request_id -> marketing_media_requests` - READY_FOR_VERIFY in ZL31

### Field Operations and Delivery

- `crew_memberships.crew_id -> partner_crews` - READY_FOR_VERIFY in ZL31
- `task_assignments.crew_id -> partner_crews` - READY_FOR_VERIFY in ZL31
- `field_tasks.work_package_id -> work_packages` - READY_FOR_VERIFY in ZL31
- `agent_missions.project_id -> projects` - READY_FOR_VERIFY in ZL31
- `agent_mission_tasks.project_id -> projects` - READY_FOR_VERIFY in ZL31
- `bom_items.proposal_plan_id -> proposal_plans` - READY_FOR_VERIFY in ZL31

Remaining count after ZL31 implementation: `0`.

Independent verification still owns the move from `READY_FOR_VERIFY` to
`VERIFIED`.

## Required Implementation Pattern

1. Add nullable indexed `workspace_id` FK to each child model.
2. Set Workspace from the authorized parent in every create/import path.
3. Filter parent-scoped reads by exact child Workspace.
4. Reject mutation when parent and child Workspaces differ.
5. Add an Alembic migration that backfills from the parent and fails closed on
   linked-parent disagreement.
6. Add positive inheritance and negative cross-Workspace tests.
7. Run focused tests, `alembic check`, `compileall`, and the full backend suite.
8. Keep `CebuProjects` unchanged.

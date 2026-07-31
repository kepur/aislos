# Marketing Integration V4 Runbook

## External media producer flow

```text
Campaign (optional)
  → Creative Brief draft
  → Human Brief approval
  → Create Media Requests
  → Integration Client claim
  → Heartbeat / fail / complete
  → Presigned upload → submit asset
  → MarketingAsset in_review
  → Human asset approval
  → Schedule PublishJob
```

## Local verification

```bash
cd Ainerwise/backend
alembic heads          # expect single head
pytest -q tests/test_media_integration_*.py
pytest -q tests/test_marketing*.py
```

## Deprecated paths

- `POST /api/v1/admin/marketing/generate-image` → **202** + `brief_id` (MI06). Use Brief + Media Integration API instead.

## Integration Client scopes

`briefs:read`, `briefs:claim`, `briefs:progress`, `assets:upload`, `assets:submit`

## Security rules

- User JWT cannot call `/api/v1/media-integration/v1/*`
- Unapproved Brief versions are not exported
- Assets must be human-approved before scheduling
- External responses must not include `source_refs`, CRM, or margin data

# AISLOS Media Integration Python SDK (V1)

Vendor-neutral client for external media systems. Requires an Integration Client bearer token.

## Install (development)

```bash
cd sdk/media-integration-python
pip install httpx
export PYTHONPATH=.
```

## Quick start

```python
from media_integration import MediaIntegrationClient

with MediaIntegrationClient("http://localhost:8000/api/v1", token="mic_...") as client:
    items = client.list_requests(status="available")
    req_id = items["items"][0]["id"]
    client.claim(req_id, idempotency_key="claim-1")
```

## Error handling & retries

- `MediaIntegrationError.retryable` indicates whether a safe retry is suggested.
- Always pass explicit `Idempotency-Key` on mutating calls for at-least-once safety.
- Do not use user JWTs — the API rejects them.

See `examples/full_flow.py` for claim → heartbeat → upload → submit → complete.

# AISLOS Media Integration TypeScript SDK (V1)

## Build

```bash
cd sdk/media-integration-typescript
npm install
npm run build
```

## Usage

```typescript
import { MediaIntegrationClient } from "@aislos/media-integration";

const client = new MediaIntegrationClient({
  baseUrl: "http://localhost:8000/api/v1",
  token: process.env.MEDIA_INTEGRATION_TOKEN!,
});

const { items } = await client.listRequests({ status: "available" });
await client.claim(items[0].id as string, "claim-1");
```

Mutating methods require `Idempotency-Key` — pass an explicit key for safe retries.
`MediaIntegrationError.retryable` matches Python SDK semantics.

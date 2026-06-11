/**
 * Example: claim → heartbeat → upload → submit → complete
 * Run with: MEDIA_INTEGRATION_TOKEN=... npx tsx examples/full-flow.ts
 */
import { MediaIntegrationClient } from "../src/client.js";

async function main() {
  const baseUrl = process.env.MEDIA_INTEGRATION_BASE_URL ?? "http://localhost:8000/api/v1";
  const token = process.env.MEDIA_INTEGRATION_TOKEN;
  if (!token) throw new Error("MEDIA_INTEGRATION_TOKEN required");

  const client = new MediaIntegrationClient({ baseUrl, token });
  const listed = await client.listRequests({ status: "available" });
  const requestId = process.env.MEDIA_REQUEST_ID ?? (listed.items[0] as { id: string }).id;

  await client.claim(requestId, "example-claim");
  await client.heartbeat(requestId, { progress_percent: 25, progress_message: "Rendering" }, "example-hb");

  const upload = await client.createUpload(
    requestId,
    { file_name: "hero.png", mime_type: "image/png", size_bytes: 1024, sha256: "a".repeat(64) },
    "example-upload",
  );

  console.log("upload slot", upload);
  // PUT file to upload.upload_url, then submit and complete
}

main().catch(console.error);

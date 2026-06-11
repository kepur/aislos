#!/usr/bin/env python3
"""Example: claim → heartbeat → upload slot → submit asset → complete.

Set MEDIA_INTEGRATION_TOKEN and optionally MEDIA_INTEGRATION_BASE_URL.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from media_integration import MediaIntegrationClient, MediaIntegrationError


def main() -> None:
  base = os.environ.get("MEDIA_INTEGRATION_BASE_URL", "http://localhost:8000/api/v1")
  token = os.environ["MEDIA_INTEGRATION_TOKEN"]
  request_id = os.environ.get("MEDIA_REQUEST_ID")

  with MediaIntegrationClient(base, token) as client:
    if not request_id:
      listed = client.list_requests(status="available")
      if not listed["items"]:
        print("No available requests")
        return
      request_id = listed["items"][0]["id"]

    claimed = client.claim(request_id, idempotency_key="example-claim")
    print("claimed:", claimed["status"])

    client.heartbeat(
      request_id,
      progress_percent=10,
      progress_message="Starting render",
      idempotency_key="example-heartbeat",
    )

    dummy = b"\x89PNG\r\n\x1a\n"
    upload = client.create_upload(
      request_id,
      file_name="hero.png",
      mime_type="image/png",
      size_bytes=len(dummy),
      sha256=hashlib.sha256(dummy).hexdigest(),
      idempotency_key="example-upload",
    )
    print("upload_url:", upload["upload_url"][:60], "...")

    # PUT binary to upload_url with your HTTP client, then:
    asset = client.submit_asset(
      request_id,
      upload_id=upload["upload_id"],
      mime_type="image/png",
      sha256=hashlib.sha256(dummy).hexdigest(),
      idempotency_key="example-submit",
    )
    print("asset:", asset["asset_id"])

    done = client.complete(request_id, idempotency_key="example-complete")
    print("complete:", done["status"])


if __name__ == "__main__":
  try:
    main()
  except MediaIntegrationError as exc:
    print(f"API error [{exc.code}] retryable={exc.retryable}: {exc.message}")
    raise SystemExit(1) from exc

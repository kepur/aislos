"""Lightweight HTTP client for AISLOS Media Integration API V1."""
from __future__ import annotations

import uuid
from typing import Any

import httpx


class MediaIntegrationError(Exception):
  """Raised when the API returns a structured error envelope."""

  def __init__(self, code: str, message: str, *, correlation_id: str | None = None, retryable: bool = False, status_code: int = 400):
    super().__init__(message)
    self.code = code
    self.message = message
    self.correlation_id = correlation_id
    self.retryable = retryable
    self.status_code = status_code


class MediaIntegrationClient:
  """External media producer client. Uses Integration Client bearer token only."""

  API_VERSION = "v1"

  def __init__(
    self,
    base_url: str,
    token: str,
    *,
    timeout: float = 30.0,
    transport: httpx.BaseTransport | None = None,
  ):
    root = base_url.rstrip("/")
    if not root.endswith("/media-integration/v1"):
      root = f"{root}/media-integration/v1"
    self._base_url = root
    self._token = token
    self._client = httpx.Client(
      base_url=self._base_url,
      timeout=timeout,
      transport=transport,
      headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

  def close(self) -> None:
    self._client.close()

  def __enter__(self) -> MediaIntegrationClient:
    return self

  def __exit__(self, *args: object) -> None:
    self.close()

  def _raise_for_response(self, response: httpx.Response) -> None:
    if response.is_success:
      return
    try:
      body = response.json()
      err = body.get("error") or body.get("detail", {}).get("error") or {}
      if isinstance(err, dict) and "code" in err:
        raise MediaIntegrationError(
          err["code"],
          err.get("message", response.text),
          correlation_id=err.get("correlation_id"),
          retryable=bool(err.get("retryable", False)),
          status_code=response.status_code,
        )
    except (ValueError, AttributeError):
      pass
    raise MediaIntegrationError("http_error", response.text, status_code=response.status_code)

  def _idempotency_headers(self, idempotency_key: str | None) -> dict[str, str]:
    key = idempotency_key or str(uuid.uuid4())
    return {"Idempotency-Key": key}

  def list_requests(self, **params: Any) -> dict:
    response = self._client.get("/requests", params=params)
    self._raise_for_response(response)
    return response.json()

  def get_request(self, request_id: str | uuid.UUID) -> dict:
    response = self._client.get(f"/requests/{request_id}")
    self._raise_for_response(response)
    return response.json()

  def claim(self, request_id: str | uuid.UUID, *, idempotency_key: str | None = None) -> dict:
    response = self._client.post(
      f"/requests/{request_id}/claim",
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

  def heartbeat(
    self,
    request_id: str | uuid.UUID,
    *,
    progress_percent: int,
    external_job_ref: str | None = None,
    progress_message: str | None = None,
    idempotency_key: str | None = None,
  ) -> dict:
    payload = {
      "progress_percent": progress_percent,
      "external_job_ref": external_job_ref,
      "progress_message": progress_message,
    }
    response = self._client.post(
      f"/requests/{request_id}/heartbeat",
      json=payload,
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

  def fail(
    self,
    request_id: str | uuid.UUID,
    *,
    failure_code: str,
    failure_message: str,
    retryable: bool = True,
    idempotency_key: str | None = None,
  ) -> dict:
    payload = {
      "failure_code": failure_code,
      "failure_message": failure_message,
      "retryable": retryable,
    }
    response = self._client.post(
      f"/requests/{request_id}/fail",
      json=payload,
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

  def create_upload(
    self,
    request_id: str | uuid.UUID,
    *,
    file_name: str,
    mime_type: str,
    size_bytes: int,
    sha256: str,
    idempotency_key: str | None = None,
  ) -> dict:
    payload = {
      "file_name": file_name,
      "mime_type": mime_type,
      "size_bytes": size_bytes,
      "sha256": sha256,
    }
    response = self._client.post(
      f"/requests/{request_id}/uploads",
      json=payload,
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

  def submit_asset(
    self,
    request_id: str | uuid.UUID,
    *,
    upload_id: str | uuid.UUID,
    mime_type: str,
    sha256: str,
    external_asset_ref: str | None = None,
    variant_key: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration_seconds: int | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
  ) -> dict:
    payload: dict[str, Any] = {
      "upload_id": str(upload_id),
      "mime_type": mime_type,
      "sha256": sha256,
      "external_asset_ref": external_asset_ref,
      "variant_key": variant_key,
      "width": width,
      "height": height,
      "duration_seconds": duration_seconds,
      "metadata": metadata,
    }
    response = self._client.post(
      f"/requests/{request_id}/assets",
      json=payload,
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

  def complete(self, request_id: str | uuid.UUID, *, idempotency_key: str | None = None) -> dict:
    response = self._client.post(
      f"/requests/{request_id}/complete",
      headers=self._idempotency_headers(idempotency_key),
    )
    self._raise_for_response(response)
    return response.json()

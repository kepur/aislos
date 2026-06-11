"""External media integration: clients, request export, claim lifecycle, idempotency."""
from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import PurePosixPath

from minio.commonconfig import CopySource

from app.core.config import settings
from app.core.media_integration_auth import hash_integration_secret
from app.models.ai import AIReview
from app.models.audit import AuditLog
from app.models.marketing import (
    ALLOWED_UPLOAD_EXTENSIONS,
    ALLOWED_UPLOAD_MIMES,
    CLAIM_LEASE_MINUTES,
    INTEGRATION_SCOPES,
    MARKETING_ASSETS_BUCKET,
    MAX_UPLOAD_BYTES,
    UPLOAD_EXPIRE_MINUTES,
    MarketingAsset,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
    MarketingIntegrationClient,
    MarketingIntegrationIdempotency,
    MarketingMediaRequest,
    MarketingMediaUpload,
)
from app.services.knowledge import get_minio_client
from app.models.user import User
from app.services.event_bus import emit_event
from app.services.marketing_briefs import build_export_payload


class MediaIntegrationError(ValueError):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _request_hash(payload: dict | None) -> str:
    normalized = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def _append_audit(
    db: AsyncSession,
    *,
    client_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before,
            after_json=after,
        )
    )
    await db.flush()


def _find_deliverable(version: MarketingCreativeBriefVersion, key: str) -> dict | None:
    for item in version.deliverables_json or []:
        if isinstance(item, dict) and item.get("key") == key:
            return item
    return None


def serialize_external_request(
    request: MarketingMediaRequest,
    version: MarketingCreativeBriefVersion,
    brief: MarketingCreativeBrief,
) -> dict[str, Any]:
    deliverable = _find_deliverable(version, request.deliverable_key) or {}
    export = build_export_payload(brief, version)
    return {
        "id": str(request.id),
        "status": request.status,
        "deliverable_key": request.deliverable_key,
        "deliverable": deliverable,
        "brief": {
            "brief_id": str(brief.id),
            "title": brief.title,
            "objective": brief.objective,
            "version": version.version,
            "content_hash": version.content_hash,
            "copy_block": export["copy"],
            "audience": export["audience"],
            "brand_constraints": export["brand_constraints"],
            "channel_specs": export["channel_specs"],
            "compliance": export["compliance"],
        },
        "progress_percent": request.progress_percent,
        "progress_message": request.progress_message,
        "claim_expires_at": request.claim_expires_at.isoformat() if request.claim_expires_at else None,
    }


def _region_allowed(client: MarketingIntegrationClient, region_id: uuid.UUID | None) -> bool:
    allowed = client.allowed_region_ids_json
    if not allowed:
        return True
    if region_id is None:
        return False
    return str(region_id) in {str(r) for r in allowed}


async def expire_stale_claims(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(MarketingMediaRequest).where(
            MarketingMediaRequest.status.in_(("claimed", "in_progress")),
            MarketingMediaRequest.claim_expires_at.is_not(None),
            MarketingMediaRequest.claim_expires_at < now,
        )
    )
    count = 0
    for req in result.scalars().all():
        req.status = "available"
        req.claimed_by_client_id = None
        req.claim_expires_at = None
        req.external_job_ref = None
        req.progress_percent = None
        req.progress_message = None
        count += 1
    if count:
        await db.flush()
    return count


async def _load_request_bundle(
    db: AsyncSession, request_id: uuid.UUID
) -> tuple[MarketingMediaRequest, MarketingCreativeBriefVersion, MarketingCreativeBrief] | None:
    row = (
        await db.execute(
            select(MarketingMediaRequest, MarketingCreativeBriefVersion, MarketingCreativeBrief)
            .join(
                MarketingCreativeBriefVersion,
                MarketingMediaRequest.brief_version_id == MarketingCreativeBriefVersion.id,
            )
            .join(MarketingCreativeBrief, MarketingCreativeBriefVersion.brief_id == MarketingCreativeBrief.id)
            .where(MarketingMediaRequest.id == request_id)
        )
    ).first()
    if not row:
        return None
    request, version, brief = row
    if version.status != "approved":
        return None
    return request, version, brief


async def list_external_requests(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    *,
    status: str = "available",
    media_type: str | None = None,
    channel: str | None = None,
    language: str | None = None,
    region_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[dict], int]:
    await expire_stale_claims(db)

    query = (
        select(MarketingMediaRequest, MarketingCreativeBriefVersion, MarketingCreativeBrief)
        .join(
            MarketingCreativeBriefVersion,
            MarketingMediaRequest.brief_version_id == MarketingCreativeBriefVersion.id,
        )
        .join(MarketingCreativeBrief, MarketingCreativeBriefVersion.brief_id == MarketingCreativeBrief.id)
        .where(
            MarketingCreativeBriefVersion.status == "approved",
            MarketingMediaRequest.status == status,
        )
    )
    if region_id:
        query = query.where(MarketingCreativeBrief.region_id == region_id)

    rows = (await db.execute(query.order_by(MarketingMediaRequest.created_at.asc()))).all()
    items: list[dict] = []
    for request, version, brief in rows:
        if not _region_allowed(client, brief.region_id):
            continue
        deliverable = _find_deliverable(version, request.deliverable_key)
        if not deliverable:
            continue
        if media_type and deliverable.get("media_type") != media_type:
            continue
        if channel and deliverable.get("channel") != channel:
            continue
        if language and deliverable.get("language") != language:
            continue
        items.append(serialize_external_request(request, version, brief))

    total = len(items)
    return items[skip : skip + limit], total


async def get_external_request(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
) -> dict:
    await expire_stale_claims(db)
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    if not _region_allowed(client, brief.region_id):
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    return serialize_external_request(request, version, brief)


async def claim_request(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
) -> dict:
    await expire_stale_claims(db)
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    if not _region_allowed(client, brief.region_id):
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)

    now = datetime.now(timezone.utc)
    if request.status == "available":
        request.status = "claimed"
        request.claimed_by_client_id = client.id
        request.claim_expires_at = now + timedelta(minutes=CLAIM_LEASE_MINUTES)
        await db.flush()
        await _append_audit(
            db,
            client_id=client.id,
            action="marketing.media_request.claimed",
            entity_type="marketing_media_request",
            entity_id=request.id,
            after={"status": "claimed", "client_id": str(client.id)},
        )
        await emit_event(
            db,
            "marketing.media_request.claimed",
            {"media_request_id": str(request.id), "client_id": str(client.id)},
            aggregate_type="marketing_media_request",
            aggregate_id=request.id,
        )
    elif request.claimed_by_client_id == client.id and request.claim_expires_at and request.claim_expires_at >= now:
        pass  # idempotent re-claim by same client within lease
    else:
        raise MediaIntegrationError("request_already_claimed", "Media request is already claimed.", retryable=False)

    return serialize_external_request(request, version, brief)


async def heartbeat_request(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
    *,
    external_job_ref: str | None,
    progress_percent: int,
    progress_message: str | None,
) -> dict:
    await expire_stale_claims(db)
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    now = datetime.now(timezone.utc)
    if request.claimed_by_client_id != client.id or not request.claim_expires_at or request.claim_expires_at < now:
        raise MediaIntegrationError("claim_required", "Active claim required for heartbeat", retryable=False)

    request.status = "in_progress"
    request.claim_expires_at = now + timedelta(minutes=CLAIM_LEASE_MINUTES)
    request.external_job_ref = external_job_ref
    request.progress_percent = progress_percent
    request.progress_message = progress_message
    await db.flush()
    await emit_event(
        db,
        "marketing.media_request.progressed",
        {"media_request_id": str(request.id), "progress_percent": progress_percent},
        aggregate_type="marketing_media_request",
        aggregate_id=request.id,
    )
    return serialize_external_request(request, version, brief)


async def fail_request(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
    *,
    failure_code: str,
    failure_message: str,
) -> dict:
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    now = datetime.now(timezone.utc)
    if request.claimed_by_client_id != client.id:
        raise MediaIntegrationError("claim_required", "Active claim required", retryable=False)

    request.status = "failed"
    request.failure_code = failure_code
    request.failure_message = failure_message
    request.claimed_by_client_id = None
    request.claim_expires_at = None
    await db.flush()
    await emit_event(
        db,
        "marketing.media_request.failed",
        {"media_request_id": str(request.id), "failure_code": failure_code},
        aggregate_type="marketing_media_request",
        aggregate_id=request.id,
    )
    return serialize_external_request(request, version, brief)


async def complete_request(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
) -> dict:
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    if request.claimed_by_client_id != client.id:
        raise MediaIntegrationError("claim_required", "Active claim required", retryable=False)

    request.status = "completed"
    request.completed_at = datetime.now(timezone.utc)
    request.claimed_by_client_id = None
    request.claim_expires_at = None
    await db.flush()
    await emit_event(
        db,
        "marketing.media_request.completed",
        {"media_request_id": str(request.id)},
        aggregate_type="marketing_media_request",
        aggregate_id=request.id,
    )
    return serialize_external_request(request, version, brief)


# --- Idempotency ---


async def check_idempotency(
    db: AsyncSession,
    client_id: uuid.UUID,
    operation: str,
    idempotency_key: str,
    payload: dict | None,
) -> tuple[int, dict] | None:
    req_hash = _request_hash(payload)
    existing = (
        await db.execute(
            select(MarketingIntegrationIdempotency).where(
                MarketingIntegrationIdempotency.client_id == client_id,
                MarketingIntegrationIdempotency.operation == operation,
                MarketingIntegrationIdempotency.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        return None
    if existing.request_hash != req_hash:
        raise MediaIntegrationError("idempotency_conflict", "Idempotency key reused with different payload", retryable=False)
    return existing.response_status, existing.response_json


async def store_idempotency(
    db: AsyncSession,
    client_id: uuid.UUID,
    operation: str,
    idempotency_key: str,
    payload: dict | None,
    response_status: int,
    response_body: dict,
) -> None:
    db.add(
        MarketingIntegrationIdempotency(
            client_id=client_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_hash=_request_hash(payload),
            response_status=response_status,
            response_json=response_body,
        )
    )
    await db.flush()


# --- Integration Client admin ---


def _validate_scopes(scopes: list[str]) -> None:
    unknown = [s for s in scopes if s not in INTEGRATION_SCOPES]
    if unknown:
        raise MediaIntegrationError("invalid_scopes", f"Unknown scopes: {unknown}")


async def create_integration_client(
    db: AsyncSession,
    *,
    actor: User,
    name: str,
    scopes: list[str],
    allowed_region_ids: list[uuid.UUID] | None,
) -> tuple[MarketingIntegrationClient, str]:
    _validate_scopes(scopes)
    raw_secret = secrets.token_urlsafe(32)
    prefix = f"mic_{secrets.token_hex(4)}"
    client = MarketingIntegrationClient(
        name=name,
        key_prefix=prefix,
        secret_hash=hash_integration_secret(raw_secret),
        status="active",
        scopes_json=scopes,
        allowed_region_ids_json=[str(r) for r in allowed_region_ids] if allowed_region_ids else None,
        created_by=actor.id,
    )
    db.add(client)
    await db.flush()
    return client, raw_secret


async def suspend_client(db: AsyncSession, client_id: uuid.UUID) -> MarketingIntegrationClient:
    client = await db.get(MarketingIntegrationClient, client_id)
    if not client:
        raise MediaIntegrationError("not_found", "Integration client not found")
    client.status = "suspended"
    await db.flush()
    return client


async def revoke_client(db: AsyncSession, client_id: uuid.UUID) -> MarketingIntegrationClient:
    client = await db.get(MarketingIntegrationClient, client_id)
    if not client:
        raise MediaIntegrationError("not_found", "Integration client not found")
    client.status = "revoked"
    await db.flush()
    return client


async def rotate_client_secret(db: AsyncSession, client_id: uuid.UUID) -> tuple[MarketingIntegrationClient, str]:
    client = await db.get(MarketingIntegrationClient, client_id)
    if not client:
        raise MediaIntegrationError("not_found", "Integration client not found")
    if client.status == "revoked":
        raise MediaIntegrationError("client_revoked", "Cannot rotate secret for revoked client")
    raw_secret = secrets.token_urlsafe(32)
    client.secret_hash = hash_integration_secret(raw_secret)
    await db.flush()
    return client, raw_secret


# --- Secure upload & asset import (MI03) ---


def _validate_upload_file(file_name: str, mime_type: str, size_bytes: int) -> None:
    ext = PurePosixPath(file_name).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise MediaIntegrationError("invalid_extension", f"Extension {ext!r} not allowed", retryable=False)
    if mime_type not in ALLOWED_UPLOAD_MIMES:
        raise MediaIntegrationError("invalid_mime", f"MIME type {mime_type!r} not allowed", retryable=False)
    if size_bytes > MAX_UPLOAD_BYTES:
        raise MediaIntegrationError("file_too_large", "File exceeds maximum upload size", retryable=False)


def _ensure_marketing_bucket(client) -> None:
    if not client.bucket_exists(MARKETING_ASSETS_BUCKET):
        client.make_bucket(MARKETING_ASSETS_BUCKET)


def _assert_active_claim(request: MarketingMediaRequest, client_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    if request.claimed_by_client_id != client_id:
        raise MediaIntegrationError("claim_required", "Active claim required", retryable=False)
    if not request.claim_expires_at or request.claim_expires_at < now:
        raise MediaIntegrationError("claim_expired", "Claim lease expired", retryable=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def create_upload_slot(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
    *,
    file_name: str,
    mime_type: str,
    size_bytes: int,
    sha256: str,
) -> dict[str, Any]:
    await expire_stale_claims(db)
    _validate_upload_file(file_name, mime_type, size_bytes)
    if len(sha256) != 64:
        raise MediaIntegrationError("invalid_checksum", "sha256 must be a 64-char hex string", retryable=False)

    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, _version, brief = bundle
    if not _region_allowed(client, brief.region_id):
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    _assert_active_claim(request, client.id)

    minio = get_minio_client()
    _ensure_marketing_bucket(minio)
    object_key = f"incoming/{request_id}/{uuid.uuid4()}{PurePosixPath(file_name).suffix.lower()}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=UPLOAD_EXPIRE_MINUTES)
    upload = MarketingMediaUpload(
        media_request_id=request.id,
        integration_client_id=client.id,
        file_name=file_name,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256_expected=sha256.lower(),
        object_key=object_key,
        bucket=MARKETING_ASSETS_BUCKET,
        status="pending",
        expires_at=expires_at,
    )
    db.add(upload)
    await db.flush()

    upload_url = minio.presigned_put_object(
        MARKETING_ASSETS_BUCKET,
        object_key,
        expires=timedelta(minutes=UPLOAD_EXPIRE_MINUTES),
    )
    return {
        "upload_id": str(upload.id),
        "upload_url": upload_url,
        "object_key": object_key,
        "expires_at": expires_at.isoformat(),
    }


async def submit_imported_asset(
    db: AsyncSession,
    client: MarketingIntegrationClient,
    request_id: uuid.UUID,
    *,
    upload_id: uuid.UUID,
    external_asset_ref: str | None,
    variant_key: str | None,
    mime_type: str,
    width: int | None,
    height: int | None,
    duration_seconds: int | None,
    sha256: str,
    metadata: dict | None,
) -> dict[str, Any]:
    await expire_stale_claims(db)
    bundle = await _load_request_bundle(db, request_id)
    if bundle is None:
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    request, version, brief = bundle
    if not _region_allowed(client, brief.region_id):
        raise MediaIntegrationError("not_found", "Media request not found", retryable=False)
    _assert_active_claim(request, client.id)

    if external_asset_ref:
        existing_asset = (
            await db.execute(
                select(MarketingAsset).where(
                    MarketingAsset.integration_client_id == client.id,
                    MarketingAsset.external_asset_ref == external_asset_ref,
                )
            )
        ).scalar_one_or_none()
        if existing_asset:
            return {
                "asset_id": str(existing_asset.id),
                "status": existing_asset.status,
                "media_request_id": str(request.id),
                "review_id": str(existing_asset.review_id) if existing_asset.review_id else None,
            }

    upload = (
        await db.execute(
            select(MarketingMediaUpload).where(
                MarketingMediaUpload.id == upload_id,
                MarketingMediaUpload.media_request_id == request.id,
                MarketingMediaUpload.integration_client_id == client.id,
            )
        )
    ).scalar_one_or_none()
    if upload is None:
        raise MediaIntegrationError("upload_not_found", "Upload slot not found", retryable=False)
    if upload.status != "pending":
        raise MediaIntegrationError("upload_consumed", "Upload already consumed", retryable=False)
    if upload.expires_at < datetime.now(timezone.utc):
        upload.status = "expired"
        await db.flush()
        raise MediaIntegrationError("upload_expired", "Upload slot expired", retryable=False)
    if upload.mime_type != mime_type:
        raise MediaIntegrationError("mime_mismatch", "MIME type does not match upload slot", retryable=False)
    if sha256.lower() != upload.sha256_expected:
        raise MediaIntegrationError("checksum_mismatch", "SHA-256 does not match upload slot", retryable=False)

    minio = get_minio_client()
    try:
        stat = minio.stat_object(upload.bucket, upload.object_key)
    except Exception as exc:
        raise MediaIntegrationError("object_missing", "Uploaded object not found in storage", retryable=True) from exc

    if stat.size != upload.size_bytes:
        raise MediaIntegrationError("size_mismatch", "Uploaded object size does not match", retryable=False)

    response = minio.get_object(upload.bucket, upload.object_key)
    try:
        data = response.read()
    finally:
        response.close()
        response.release_conn()

    actual_hash = _sha256_bytes(data)
    if actual_hash != upload.sha256_expected:
        raise MediaIntegrationError("checksum_mismatch", "SHA-256 verification failed", retryable=False)

    deliverable = _find_deliverable(version, request.deliverable_key) or {}
    asset_id = uuid.uuid4()
    final_key = f"assets/{asset_id}/{upload.file_name}"
    minio.copy_object(
        upload.bucket,
        final_key,
        CopySource(upload.bucket, upload.object_key),
    )
    minio.remove_object(upload.bucket, upload.object_key)

    review = AIReview(
        target_type="external_marketing_media",
        target_id=asset_id,
        draft_json={
            "media_request_id": str(request.id),
            "deliverable_key": request.deliverable_key,
            "variant_key": variant_key,
            "metadata": metadata or {},
        },
        status="preliminary",
    )
    db.add(review)
    await db.flush()

    asset = MarketingAsset(
        id=asset_id,
        region_id=brief.region_id,
        campaign_id=brief.campaign_id,
        brief_version_id=version.id,
        media_request_id=request.id,
        integration_client_id=client.id,
        external_asset_ref=external_asset_ref,
        variant_key=variant_key,
        mime_type=mime_type,
        size_bytes=upload.size_bytes,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        sha256=actual_hash,
        source_metadata_json=metadata,
        kind=deliverable.get("media_type", "image"),
        channel=deliverable.get("channel"),
        lang=deliverable.get("language", "en"),
        title=f"{brief.title} — {request.deliverable_key}",
        media_minio_key=f"{upload.bucket}/{final_key}",
        ai_generated=False,
        review_id=review.id,
        status="in_review",
    )
    db.add(asset)
    upload.status = "consumed"
    request.submitted_asset_count += 1
    if request.status in ("claimed", "in_progress"):
        request.status = "submitted"
    await db.flush()

    await _append_audit(
        db,
        client_id=client.id,
        action="marketing.media_asset.imported",
        entity_type="marketing_asset",
        entity_id=asset.id,
        after={
            "status": "in_review",
            "media_request_id": str(request.id),
            "integration_client_id": str(client.id),
        },
    )
    await emit_event(
        db,
        "marketing.media_asset.imported",
        {
            "asset_id": str(asset.id),
            "media_request_id": str(request.id),
            "integration_client_id": str(client.id),
        },
        aggregate_type="marketing_asset",
        aggregate_id=asset.id,
    )

    return {
        "asset_id": str(asset.id),
        "status": asset.status,
        "media_request_id": str(request.id),
        "review_id": str(review.id),
    }

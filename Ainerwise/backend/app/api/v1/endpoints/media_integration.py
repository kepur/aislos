"""External media integration API (V4) and internal Integration Client admin."""
import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from app.api.deps import AdminUser, DB
from app.core.media_integration_auth import (
    ClaimClientDep,
    ProgressClientDep,
    ReadClientDep,
    SubmitClientDep,
    UploadClientDep,
)
from app.schemas.media_integration import (
    AssetSubmitRequest,
    AssetSubmitResponse,
    FailRequest,
    HeartbeatRequest,
    IntegrationClientCreate,
    IntegrationClientCreated,
    IntegrationClientRead,
    MediaRequestExternal,
    MediaRequestListResponse,
    UploadCreateRequest,
    UploadCreateResponse,
)
from app.services.media_integration import (
    MediaIntegrationError,
    check_idempotency,
    claim_request,
    complete_request,
    create_integration_client,
    create_upload_slot,
    fail_request,
    get_external_request,
    heartbeat_request,
    list_external_requests,
    revoke_client,
    rotate_client_secret,
    store_idempotency,
    submit_imported_asset,
    suspend_client,
)

router = APIRouter(prefix="/media-integration/v1", tags=["media-integration"])
admin_router = APIRouter(prefix="/admin/marketing/integration-clients", tags=["media-integration-admin"])


def _integration_error(exc: MediaIntegrationError, request: Request) -> HTTPException:
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    status_code = {
        "not_found": 404,
        "upload_not_found": 404,
        "request_already_claimed": 409,
        "idempotency_conflict": 409,
        "claim_required": 409,
        "claim_expired": 409,
        "upload_consumed": 409,
        "checksum_mismatch": 422,
        "mime_mismatch": 422,
        "size_mismatch": 422,
        "object_missing": 422,
        "invalid_scopes": 422,
        "client_revoked": 409,
        "file_too_large": 413,
        "invalid_extension": 422,
        "invalid_mime": 422,
    }.get(exc.code, 422)
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "correlation_id": correlation_id,
                "retryable": exc.retryable,
            }
        },
    )


async def _idempotent_write(
    db: DB,
    ctx: ClaimClientDep | ProgressClientDep,
    request: Request,
    operation: str,
    idempotency_key: str | None,
    payload: dict | None,
    handler,
):
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "missing_idempotency_key", "message": "Idempotency-Key header required"}},
        )
    try:
        cached = await check_idempotency(db, ctx.client.id, operation, idempotency_key, payload)
        if cached:
            status_code, body = cached
            return body
        result = await handler()
        await store_idempotency(db, ctx.client.id, operation, idempotency_key, payload, 200, result)
        await db.commit()
        return result
    except MediaIntegrationError as exc:
        await db.rollback()
        raise _integration_error(exc, request) from exc


@router.get("/requests", response_model=MediaRequestListResponse)
async def list_requests(
    db: DB,
    ctx: ReadClientDep,
    request: Request,
    status_filter: str = Query("available", alias="status"),
    media_type: str | None = None,
    channel: str | None = None,
    language: str | None = None,
    region_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    try:
        items, total = await list_external_requests(
            db,
            ctx.client,
            status=status_filter,
            media_type=media_type,
            channel=channel,
            language=language,
            region_id=region_id,
            skip=skip,
            limit=limit,
        )
        await db.commit()
        return {"items": items, "total": total}
    except MediaIntegrationError as exc:
        await db.rollback()
        raise _integration_error(exc, request) from exc


@router.get("/requests/{request_id}", response_model=MediaRequestExternal)
async def get_request(request_id: uuid.UUID, db: DB, ctx: ReadClientDep, request: Request):
    try:
        result = await get_external_request(db, ctx.client, request_id)
        await db.commit()
        return result
    except MediaIntegrationError as exc:
        await db.rollback()
        raise _integration_error(exc, request) from exc


@router.post("/requests/{request_id}/claim", response_model=MediaRequestExternal)
async def claim_media_request(
    request_id: uuid.UUID,
    db: DB,
    ctx: ClaimClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    return await _idempotent_write(
        db,
        ctx,
        request,
        "claim",
        idempotency_key,
        {"request_id": str(request_id)},
        lambda: claim_request(db, ctx.client, request_id),
    )


@router.post("/requests/{request_id}/heartbeat", response_model=MediaRequestExternal)
async def heartbeat_media_request(
    request_id: uuid.UUID,
    data: HeartbeatRequest,
    db: DB,
    ctx: ProgressClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    payload = data.model_dump()
    return await _idempotent_write(
        db,
        ctx,
        request,
        "heartbeat",
        idempotency_key,
        payload | {"request_id": str(request_id)},
        lambda: heartbeat_request(
            db,
            ctx.client,
            request_id,
            external_job_ref=data.external_job_ref,
            progress_percent=data.progress_percent,
            progress_message=data.progress_message,
        ),
    )


@router.post("/requests/{request_id}/fail", response_model=MediaRequestExternal)
async def fail_media_request(
    request_id: uuid.UUID,
    data: FailRequest,
    db: DB,
    ctx: ProgressClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    payload = data.model_dump()
    return await _idempotent_write(
        db,
        ctx,
        request,
        "fail",
        idempotency_key,
        payload | {"request_id": str(request_id)},
        lambda: fail_request(
            db,
            ctx.client,
            request_id,
            failure_code=data.failure_code,
            failure_message=data.failure_message,
        ),
    )


@router.post("/requests/{request_id}/uploads", response_model=UploadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_media_upload(
    request_id: uuid.UUID,
    data: UploadCreateRequest,
    db: DB,
    ctx: UploadClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    payload = data.model_dump()
    return await _idempotent_write(
        db,
        ctx,
        request,
        "upload",
        idempotency_key,
        payload | {"request_id": str(request_id)},
        lambda: create_upload_slot(
            db,
            ctx.client,
            request_id,
            file_name=data.file_name,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
            sha256=data.sha256,
        ),
    )


@router.post("/requests/{request_id}/assets", response_model=AssetSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_media_asset(
    request_id: uuid.UUID,
    data: AssetSubmitRequest,
    db: DB,
    ctx: SubmitClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    payload = data.model_dump(mode="json")
    return await _idempotent_write(
        db,
        ctx,
        request,
        "submit_asset",
        idempotency_key,
        payload | {"request_id": str(request_id)},
        lambda: submit_imported_asset(
            db,
            ctx.client,
            request_id,
            upload_id=data.upload_id,
            external_asset_ref=data.external_asset_ref,
            variant_key=data.variant_key,
            mime_type=data.mime_type,
            width=data.width,
            height=data.height,
            duration_seconds=data.duration_seconds,
            sha256=data.sha256,
            metadata=data.metadata,
        ),
    )


@router.post("/requests/{request_id}/complete", response_model=MediaRequestExternal)
async def complete_media_request(
    request_id: uuid.UUID,
    db: DB,
    ctx: ProgressClientDep,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    return await _idempotent_write(
        db,
        ctx,
        request,
        "complete",
        idempotency_key,
        {"request_id": str(request_id)},
        lambda: complete_request(db, ctx.client, request_id),
    )


# --- Admin Integration Client management ---


@admin_router.post("", response_model=IntegrationClientCreated, status_code=status.HTTP_201_CREATED)
async def admin_create_client(data: IntegrationClientCreate, db: DB, admin: AdminUser):
    try:
        client, secret = await create_integration_client(
            db,
            actor=admin,
            name=data.name,
            scopes=data.scopes,
            allowed_region_ids=data.allowed_region_ids,
        )
        await db.commit()
        await db.refresh(client)
        return IntegrationClientCreated(
            id=client.id,
            name=client.name,
            key_prefix=client.key_prefix,
            status=client.status,
            scopes_json=client.scopes_json,
            allowed_region_ids_json=client.allowed_region_ids_json,
            last_used_at=client.last_used_at,
            created_by=client.created_by,
            created_at=client.created_at,
            updated_at=client.updated_at,
            client_secret=secret,
        )
    except MediaIntegrationError as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.get("")
async def admin_list_clients(db: DB, admin: AdminUser):
    from sqlalchemy import select

    from app.models.marketing import MarketingIntegrationClient

    rows = (await db.execute(select(MarketingIntegrationClient).order_by(MarketingIntegrationClient.created_at.desc()))).scalars().all()
    return {
        "items": [IntegrationClientRead.model_validate(c) for c in rows],
        "total": len(rows),
    }


@admin_router.post("/{client_id}/suspend", response_model=IntegrationClientRead)
async def admin_suspend_client(client_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        client = await suspend_client(db, client_id)
        await db.commit()
        await db.refresh(client)
        return client
    except MediaIntegrationError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@admin_router.post("/{client_id}/revoke", response_model=IntegrationClientRead)
async def admin_revoke_client(client_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        client = await revoke_client(db, client_id)
        await db.commit()
        await db.refresh(client)
        return client
    except MediaIntegrationError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@admin_router.post("/{client_id}/rotate-secret", response_model=IntegrationClientCreated)
async def admin_rotate_secret(client_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        client, secret = await rotate_client_secret(db, client_id)
        await db.commit()
        await db.refresh(client)
        return IntegrationClientCreated(
            id=client.id,
            name=client.name,
            key_prefix=client.key_prefix,
            status=client.status,
            scopes_json=client.scopes_json,
            allowed_region_ids_json=client.allowed_region_ids_json,
            last_used_at=client.last_used_at,
            created_by=client.created_by,
            created_at=client.created_at,
            updated_at=client.updated_at,
            client_secret=secret,
        )
    except MediaIntegrationError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DB
from app.models.privacy import PrivacyRequest
from app.models.user import User
from app.schemas.privacy import PrivacyRequestRead, PrivacyReview
from app.services.audit import append_audit_event
from app.services.privacy import anonymize_user, build_user_export

router = APIRouter(tags=["privacy"])


def _active_export(row: PrivacyRequest) -> bool:
    return (
        row.request_type == "export"
        and row.status == "ready"
        and row.expires_at is not None
        and row.expires_at > datetime.now(timezone.utc)
    )


@router.get("/privacy/requests", response_model=list[PrivacyRequestRead])
async def list_my_privacy_requests(db: DB, user: CurrentUser):
    rows = (
        await db.execute(
            select(PrivacyRequest)
            .where(PrivacyRequest.user_id == user.id)
            .order_by(PrivacyRequest.created_at.desc())
        )
    ).scalars().all()
    return rows


@router.post("/privacy/export", response_model=PrivacyRequestRead)
async def request_export(db: DB, user: CurrentUser):
    existing = (
        await db.execute(
            select(PrivacyRequest)
            .where(
                PrivacyRequest.user_id == user.id,
                PrivacyRequest.request_type == "export",
                PrivacyRequest.status == "ready",
            )
            .order_by(PrivacyRequest.created_at.desc())
        )
    ).scalars().first()
    if existing and _active_export(existing):
        return existing
    row = PrivacyRequest(
        user_id=user.id,
        request_type="export",
        status="ready",
        completed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(row)
    await db.flush()
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        action="privacy.export.requested",
        entity_type="privacy_request",
        entity_id=row.id,
        after={"status": row.status, "expires_at": row.expires_at.isoformat()},
        source="privacy.self_service",
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/privacy/exports/{request_id}")
async def download_export(request_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(PrivacyRequest, request_id)
    if row is None or row.user_id != user.id or not _active_export(row):
        raise HTTPException(status_code=404, detail="Active export request not found")
    payload = await build_user_export(db, user)
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        action="privacy.export.downloaded",
        entity_type="privacy_request",
        entity_id=row.id,
        source="privacy.self_service",
    )
    await db.commit()
    return Response(
        content=json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="ainerwise-data-{user.id}.json"'},
    )


@router.post("/privacy/delete-request", response_model=PrivacyRequestRead)
async def request_deletion(db: DB, user: CurrentUser):
    existing = (
        await db.execute(
            select(PrivacyRequest)
            .where(
                PrivacyRequest.user_id == user.id,
                PrivacyRequest.request_type == "delete",
                PrivacyRequest.status == "requested",
            )
            .order_by(PrivacyRequest.created_at.desc())
        )
    ).scalars().first()
    if existing:
        return existing
    row = PrivacyRequest(user_id=user.id, request_type="delete", status="requested")
    db.add(row)
    await db.flush()
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        action="privacy.delete.requested",
        entity_type="privacy_request",
        entity_id=row.id,
        source="privacy.self_service",
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/privacy/requests/{request_id}/cancel", response_model=PrivacyRequestRead)
async def cancel_privacy_request(request_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(PrivacyRequest, request_id)
    if row is None or row.user_id != user.id or row.status != "requested":
        raise HTTPException(status_code=404, detail="Cancellable privacy request not found")
    row.status = "cancelled"
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=user.id,
        action="privacy.request.cancelled",
        entity_type="privacy_request",
        entity_id=row.id,
        source="privacy.self_service",
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/admin/privacy/requests", response_model=list[PrivacyRequestRead])
async def admin_list_privacy_requests(db: DB, admin: AdminUser, status: str | None = None):
    query = select(PrivacyRequest).order_by(PrivacyRequest.created_at.desc())
    if status:
        query = query.where(PrivacyRequest.status == status)
    return (await db.execute(query)).scalars().all()


@router.post("/admin/privacy/requests/{request_id}/reject", response_model=PrivacyRequestRead)
async def reject_privacy_request(
    request_id: uuid.UUID,
    data: PrivacyReview,
    db: DB,
    admin: AdminUser,
):
    row = await db.get(PrivacyRequest, request_id)
    if row is None or row.status != "requested":
        raise HTTPException(status_code=404, detail="Pending privacy request not found")
    now = datetime.now(timezone.utc)
    row.status = "rejected"
    row.reviewed_by_user_id = admin.id
    row.reviewed_at = now
    row.completed_at = now
    row.review_reason = data.reason
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        action="privacy.request.rejected",
        entity_type="privacy_request",
        entity_id=row.id,
        after={"status": row.status, "user_id": str(row.user_id)},
        reason=data.reason,
        source="privacy.admin",
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/admin/privacy/requests/{request_id}/complete", response_model=PrivacyRequestRead)
async def complete_privacy_request(
    request_id: uuid.UUID,
    data: PrivacyReview,
    db: DB,
    admin: AdminUser,
):
    row = await db.get(PrivacyRequest, request_id)
    if row is None or row.request_type != "delete" or row.status != "requested":
        raise HTTPException(status_code=404, detail="Pending deletion request not found")
    target = await db.get(User, row.user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="Administrators cannot approve their own deletion")
    if target.role in {"admin", "super_admin"} and admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin approval required for staff deletion")
    await anonymize_user(db, target)
    now = datetime.now(timezone.utc)
    row.status = "completed"
    row.reviewed_by_user_id = admin.id
    row.reviewed_at = now
    row.completed_at = now
    row.review_reason = data.reason
    await append_audit_event(
        db,
        actor_type="user",
        actor_user_id=admin.id,
        action="privacy.delete.completed",
        entity_type="privacy_request",
        entity_id=row.id,
        before={"user_id": str(target.id), "role": target.role},
        after={"status": "completed", "account_active": False},
        reason=data.reason,
        source="privacy.admin",
    )
    await db.commit()
    await db.refresh(row)
    return row

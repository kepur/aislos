"""Service-partner role view: RFQ inbox, bid submission, and response metrics."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import DB, ServicePartnerUser
from app.models.lifecycle import MaintenanceSchedule
from app.models.project import Project
from app.models.rfq import PartnerBid, PartnerMetric, RFQ, RFQInvitation
from app.models.service import ServicePartner
from app.services.event_bus import emit_event
from app.services.partner_dispatch import change_partner_task_status, partner_task_dict
from app.services.rfq import EVENT_RFQ_PARTNER_DECLINED, record_bid, supplier_safe_scope

router = APIRouter(prefix="/partner", tags=["partner-portal"])


class PartnerBidCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str | None = Field(default=None, max_length=10)
    lead_time_days: int | None = Field(default=None, ge=0, le=3650)
    notes: str | None = Field(default=None, max_length=5000)


class PartnerTaskStatusUpdate(BaseModel):
    status: str


async def _partner_for_user(db: DB, user: ServicePartnerUser) -> ServicePartner:
    partner = (
        await db.execute(select(ServicePartner).where(ServicePartner.user_id == user.id))
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(status_code=404, detail="Service partner profile is not linked to this account")
    return partner


def _bid_dict(bid: PartnerBid | None) -> dict | None:
    if bid is None:
        return None
    return {
        "id": str(bid.id),
        "amount": float(bid.amount),
        "currency": bid.currency,
        "lead_time_days": bid.lead_time_days,
        "notes": bid.notes,
        "status": bid.status,
        "created_at": bid.created_at.isoformat(),
    }


def _rfq_dict(rfq: RFQ, invitation: RFQInvitation, bid: PartnerBid | None = None) -> dict:
    return {
        "id": str(rfq.id),
        "title": rfq.title,
        "trade": rfq.trade,
        "scope_json": supplier_safe_scope(rfq.scope_json),
        "budget_hint": float(rfq.budget_hint) if rfq.budget_hint is not None else None,
        "currency": rfq.currency,
        "status": rfq.status,
        "bid_deadline": rfq.bid_deadline.isoformat() if rfq.bid_deadline else None,
        "invitation_id": str(invitation.id),
        "invitation_status": invitation.status,
        "sent_via": invitation.sent_via,
        "responded_at": invitation.responded_at.isoformat() if invitation.responded_at else None,
        "created_at": rfq.created_at.isoformat(),
        "bid": _bid_dict(bid),
    }


async def _invited_rfq(db: DB, partner_id: uuid.UUID, rfq_id: uuid.UUID) -> tuple[RFQ, RFQInvitation]:
    row = (
        await db.execute(
            select(RFQ, RFQInvitation)
            .join(RFQInvitation, RFQInvitation.rfq_id == RFQ.id)
            .where(RFQ.id == rfq_id, RFQInvitation.partner_id == partner_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="RFQ invitation not found")
    return row[0], row[1]


async def _latest_bid(db: DB, partner_id: uuid.UUID, rfq_id: uuid.UUID) -> PartnerBid | None:
    return (
        await db.execute(
            select(PartnerBid)
            .where(PartnerBid.partner_id == partner_id, PartnerBid.rfq_id == rfq_id)
            .order_by(PartnerBid.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


@router.get("/dashboard")
async def partner_dashboard(db: DB, user: ServicePartnerUser):
    partner = await _partner_for_user(db, user)
    counts = dict(
        (
            await db.execute(
                select(RFQInvitation.status, func.count())
                .where(RFQInvitation.partner_id == partner.id)
                .group_by(RFQInvitation.status)
            )
        ).all()
    )
    metric = (
        await db.execute(select(PartnerMetric).where(PartnerMetric.partner_id == partner.id))
    ).scalar_one_or_none()
    task_counts = dict(
        (
            await db.execute(
                select(MaintenanceSchedule.status, func.count())
                .where(MaintenanceSchedule.assigned_to == user.id)
                .group_by(MaintenanceSchedule.status)
            )
        ).all()
    )
    return {
        "partner": {
            "id": str(partner.id),
            "partner_type": partner.partner_type,
            "verification_status": partner.verification_status,
            "availability_status": partner.availability_status,
            "city": partner.city,
            "country": partner.country,
        },
        "counts": {
            "open": counts.get("sent", 0) + counts.get("viewed", 0),
            "bid_submitted": counts.get("bid_submitted", 0),
            "declined": counts.get("declined", 0),
            "total": sum(counts.values()),
        },
        "metric": {
            "composite_score": float(metric.composite_score) if metric and metric.composite_score is not None else None,
            "response_hours_avg": float(metric.response_hours_avg) if metric and metric.response_hours_avg is not None else None,
            "completion_rate": float(metric.completion_rate) if metric and metric.completion_rate is not None else None,
        },
        "tasks": {
            "open": task_counts.get("scheduled", 0) + task_counts.get("due", 0) + task_counts.get("in_progress", 0),
            "in_progress": task_counts.get("in_progress", 0),
            "done": task_counts.get("done", 0),
            "total": sum(task_counts.values()),
        },
    }


@router.get("/rfqs")
async def list_partner_rfqs(
    db: DB,
    user: ServicePartnerUser,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    partner = await _partner_for_user(db, user)
    query = (
        select(RFQ, RFQInvitation)
        .join(RFQInvitation, RFQInvitation.rfq_id == RFQ.id)
        .where(RFQInvitation.partner_id == partner.id)
        .order_by(RFQInvitation.created_at.desc())
    )
    count_query = select(func.count()).select_from(RFQInvitation).where(
        RFQInvitation.partner_id == partner.id
    )
    if status:
        query = query.where(RFQInvitation.status == status)
        count_query = count_query.where(RFQInvitation.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).all()
    items = []
    for rfq, invitation in rows:
        items.append(_rfq_dict(rfq, invitation, await _latest_bid(db, partner.id, rfq.id)))
    return {"items": items, "total": total}


@router.get("/rfqs/{id}")
async def get_partner_rfq(id: uuid.UUID, db: DB, user: ServicePartnerUser):
    partner = await _partner_for_user(db, user)
    rfq, invitation = await _invited_rfq(db, partner.id, id)
    if invitation.status == "sent":
        invitation.status = "viewed"
        db.add(invitation)
        await db.commit()
    return _rfq_dict(rfq, invitation, await _latest_bid(db, partner.id, rfq.id))


@router.post("/rfqs/{id}/decline")
async def decline_partner_rfq(id: uuid.UUID, db: DB, user: ServicePartnerUser):
    partner = await _partner_for_user(db, user)
    rfq, invitation = await _invited_rfq(db, partner.id, id)
    if rfq.status in {"awarded", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"RFQ already {rfq.status}")
    if invitation.status == "bid_submitted":
        raise HTTPException(status_code=409, detail="A bid has already been submitted")
    if invitation.status == "declined":
        return {"status": invitation.status}
    invitation.status = "declined"
    invitation.responded_at = datetime.now(timezone.utc)
    db.add(invitation)
    await emit_event(
        db,
        EVENT_RFQ_PARTNER_DECLINED,
        {"rfq_id": str(rfq.id), "partner_id": str(partner.id), "invitation_id": str(invitation.id)},
        aggregate_type="rfq",
        aggregate_id=rfq.id,
    )
    await db.commit()
    return {"status": invitation.status}


@router.post("/rfqs/{id}/bids", status_code=201)
async def submit_partner_bid(id: uuid.UUID, data: PartnerBidCreate, db: DB, user: ServicePartnerUser):
    partner = await _partner_for_user(db, user)
    rfq, invitation = await _invited_rfq(db, partner.id, id)
    if rfq.status in {"awarded", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"RFQ already {rfq.status}")
    if invitation.status == "declined":
        raise HTTPException(status_code=409, detail="Invitation was declined")
    if await _latest_bid(db, partner.id, rfq.id):
        raise HTTPException(status_code=409, detail="A bid has already been submitted")
    bid = await record_bid(
        db,
        rfq,
        partner_id=partner.id,
        amount=data.amount,
        currency=data.currency,
        lead_time_days=data.lead_time_days,
        notes=data.notes,
    )
    await db.commit()
    await db.refresh(bid)
    return _bid_dict(bid)


async def _partner_task(db: DB, user_id: uuid.UUID, task_id: uuid.UUID) -> tuple[MaintenanceSchedule, Project | None]:
    row = (
        await db.execute(
            select(MaintenanceSchedule, Project)
            .outerjoin(Project, Project.id == MaintenanceSchedule.project_id)
            .where(MaintenanceSchedule.id == task_id, MaintenanceSchedule.assigned_to == user_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Partner task not found")
    return row[0], row[1]


@router.get("/tasks")
async def list_partner_tasks(
    db: DB,
    user: ServicePartnerUser,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = (
        select(MaintenanceSchedule, Project)
        .outerjoin(Project, Project.id == MaintenanceSchedule.project_id)
        .where(MaintenanceSchedule.assigned_to == user.id)
        .order_by(MaintenanceSchedule.due_date.asc().nullslast(), MaintenanceSchedule.created_at.desc())
    )
    count_query = select(func.count()).select_from(MaintenanceSchedule).where(
        MaintenanceSchedule.assigned_to == user.id
    )
    if status:
        query = query.where(MaintenanceSchedule.status == status)
        count_query = count_query.where(MaintenanceSchedule.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).all()
    return {"items": [partner_task_dict(task, project) for task, project in rows], "total": total}


@router.get("/tasks/{id}")
async def get_partner_task(id: uuid.UUID, db: DB, user: ServicePartnerUser):
    task, project = await _partner_task(db, user.id, id)
    return partner_task_dict(task, project)


@router.patch("/tasks/{id}/status")
async def update_partner_task_status(
    id: uuid.UUID,
    data: PartnerTaskStatusUpdate,
    db: DB,
    user: ServicePartnerUser,
):
    task, project = await _partner_task(db, user.id, id)
    try:
        await change_partner_task_status(db, task=task, status=data.status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    await db.refresh(task)
    return partner_task_dict(task, project)


@router.get("/calendar")
async def partner_calendar(
    db: DB,
    user: ServicePartnerUser,
    from_date: date | None = None,
    to_date: date | None = None,
):
    partner = await _partner_for_user(db, user)
    task_query = (
        select(MaintenanceSchedule, Project)
        .outerjoin(Project, Project.id == MaintenanceSchedule.project_id)
        .where(MaintenanceSchedule.assigned_to == user.id, MaintenanceSchedule.due_date.is_not(None))
    )
    if from_date:
        task_query = task_query.where(MaintenanceSchedule.due_date >= from_date)
    if to_date:
        task_query = task_query.where(MaintenanceSchedule.due_date <= to_date)
    task_rows = (await db.execute(task_query)).all()

    award_rows = (
        await db.execute(
            select(RFQ, Project)
            .join(PartnerBid, PartnerBid.id == RFQ.awarded_bid_id)
            .outerjoin(Project, Project.id == RFQ.project_id)
            .where(PartnerBid.partner_id == partner.id, PartnerBid.status == "awarded")
        )
    ).all()
    items = [
        {
            "id": f"task:{task.id}",
            "type": "task",
            "date": task.due_date.isoformat(),
            "title": (task.task_type or "Service task").replace("_", " ").title(),
            "subtitle": project.title if project else task.device_name,
            "status": task.status,
            "href": f"/partner/tasks/{task.id}",
        }
        for task, project in task_rows
    ]
    for rfq, project in award_rows:
        project_date = project.start_date if project else None
        if project_date is None:
            continue
        if from_date and project_date < from_date:
            continue
        if to_date and project_date > to_date:
            continue
        items.append(
            {
                "id": f"project:{project.id}",
                "type": "project",
                "date": project_date.isoformat(),
                "title": project.title,
                "subtitle": rfq.trade,
                "status": project.status,
                "href": f"/partner/rfqs/{rfq.id}",
            }
        )
    items.sort(key=lambda item: (item["date"], item["type"]))
    return {"items": items, "total": len(items)}


class TaskCompletionRequest(BaseModel):
    notes: str | None = None
    photos: list[str] = Field(default_factory=list)  # MinIO object names from /files upload flow
    devices: list[dict] = Field(default_factory=list)  # [{name, serial, room, floor, product_id?}]
    test_results: str | None = None


@router.post("/tasks/{id}/complete")
async def complete_partner_task(
    id: uuid.UUID,
    data: TaskCompletionRequest,
    db: DB,
    user: ServicePartnerUser,
):
    """Field completion: store the work record, then auto-send the acceptance
    document to the customer for signature. The signed document closes the
    loop (milestone release, asset registry, case draft) via the event bus."""
    from app.services.acceptance import create_acceptance_request

    task, project = await _partner_task(db, user.id, id)
    if task.status == "done":
        raise HTTPException(status_code=409, detail="Task already closed")
    if project is None:
        raise HTTPException(status_code=409, detail="Task has no project — ask admin to link it")

    completion = {
        "notes": data.notes,
        "photos": data.photos,
        "devices": data.devices,
        "test_results": data.test_results,
        "completed_by": str(user.id),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    task.completion_json = completion
    db.add(task)
    if task.status != "completed_pending_acceptance":
        await change_partner_task_status(db, task=task, status="completed_pending_acceptance")

    document, url = await create_acceptance_request(db, task, project, completion)
    await db.commit()
    return {
        "task_status": task.status,
        "acceptance_document_id": str(document.id),
        "customer_signing_url": url,
    }

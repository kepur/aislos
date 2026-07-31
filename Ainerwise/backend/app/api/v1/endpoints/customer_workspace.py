"""Customer Workspace aggregate and delivery views.

These endpoints expose customer-safe projections of Core data. Every query is
scoped through the current user's buyer company; internal worker assignments,
supplier economics, and unrelated workspace data are never returned.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DB
from app.models.asset import Asset, Site
from app.models.commerce import CommerceOrder, OrderDelivery, ProcurementRequest
from app.models.field_service import FieldTask, TaskEvidence, WorkPackage
from app.models.lead import Lead
from app.models.project import Project
from app.models.quote import Quote
from app.models.ticket import Ticket
from app.schemas.quote import QuoteRead
from app.services.project_access import customer_project_ids_query, require_customer_project_access
from app.services.crm_access import customer_workspace_ids

router = APIRouter(prefix="/customer/workspace", tags=["customer-workspace"])


def _company_id(user) -> uuid.UUID:
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Customer company membership required")
    return user.company_id


async def _owned_project(db, user, project_id: uuid.UUID) -> Project:
    company_id = _company_id(user)
    project = await db.get(Project, project_id)
    if project is None or project.buyer_company_id != company_id:
        raise HTTPException(status_code=404, detail="Customer project not found")
    await require_customer_project_access(db, user, project)
    return project


async def _owned_package(db, user, package_id: uuid.UUID) -> tuple[WorkPackage, Project]:
    company_id = _company_id(user)
    row = (
        await db.execute(
            select(WorkPackage, Project)
            .join(Project, Project.id == WorkPackage.project_id)
            .where(
                WorkPackage.id == package_id,
                Project.buyer_company_id == company_id,
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer installation not found")
    await require_customer_project_access(db, user, row[1])
    return row[0], row[1]


def _package_dict(package: WorkPackage, project: Project, *, tasks: list[dict] | None = None) -> dict:
    return {
        "id": str(package.id),
        "project_id": str(project.id),
        "project_title": project.title,
        "title": package.title,
        "trade": package.trade,
        "scope_json": package.scope_json,
        "site_json": package.site_json,
        "planned_start": package.planned_start,
        "planned_end": package.planned_end,
        "status": package.status,
        "tasks": tasks or [],
        "created_at": package.created_at,
    }


def _task_dict(task: FieldTask, *, evidence_count: int = 0, evidence: list[dict] | None = None) -> dict:
    return {
        "id": str(task.id),
        "work_package_id": str(task.work_package_id),
        "task_type": task.task_type,
        "title": task.title,
        "site_json": task.site_json,
        "checklist_json": task.checklist_json,
        "schedule_start": task.schedule_start,
        "schedule_end": task.schedule_end,
        "status": task.status,
        "evidence_count": evidence_count,
        "evidence": evidence or [],
    }


def _customer_evidence_payload(row: TaskEvidence) -> dict:
    payload = row.payload_json if isinstance(row.payload_json, dict) else {}
    allowed_keys = {
        "notes",
        "device_label",
        "signer_name",
        "captured_at",
        "bound_at",
        "submitted_at",
    }
    result = {key: payload[key] for key in allowed_keys if payload.get(key) is not None}
    if row.evidence_type == "photo" and payload.get("object_key"):
        result["photo_captured"] = True
    if row.evidence_type == "signature" and payload.get("signature_data_url"):
        result["signature_captured"] = True
    if row.evidence_type == "qr" and payload.get("qr_code"):
        result["device_bound"] = True
    return result


@router.get("/summary")
async def customer_workspace_summary(db: DB, user: CurrentUser):
    company_id = _company_id(user)

    async def count(model, *where) -> int:
        value = await db.scalar(select(func.count()).select_from(model).where(*where))
        return int(value or 0)

    project_ids = await customer_project_ids_query(db, user)
    workspace_ids = await customer_workspace_ids(db, user)
    commerce_workspace_scope = (
        or_(
            ProcurementRequest.workspace_id.in_(workspace_ids),
            ProcurementRequest.workspace_id.is_(None),
        )
        if workspace_ids
        else ProcurementRequest.workspace_id.is_(None)
    )
    order_workspace_scope = (
        or_(CommerceOrder.workspace_id.in_(workspace_ids), CommerceOrder.workspace_id.is_(None))
        if workspace_ids
        else CommerceOrder.workspace_id.is_(None)
    )
    quote_workspace_scope = (
        or_(Quote.workspace_id.in_(workspace_ids), Quote.workspace_id.is_(None))
        if workspace_ids
        else Quote.workspace_id.is_(None)
    )
    lead_workspace_scope = (
        or_(Lead.workspace_id.in_(workspace_ids), Lead.workspace_id.is_(None))
        if workspace_ids
        else Lead.workspace_id.is_(None)
    )
    ticket_workspace_scope = (
        or_(Ticket.workspace_id.in_(workspace_ids), Ticket.workspace_id.is_(None))
        if workspace_ids
        else Ticket.workspace_id.is_(None)
    )
    package_ids = select(WorkPackage.id).where(WorkPackage.project_id.in_(project_ids))
    lead_ids = select(Lead.id).where(
        Lead.buyer_company_id == company_id,
        lead_workspace_scope,
    )
    order_ids = select(CommerceOrder.id).where(
        CommerceOrder.buyer_company_id == company_id,
        order_workspace_scope,
    )

    return {
        "requirements": await count(
            Lead,
            Lead.buyer_company_id == company_id,
            lead_workspace_scope,
        ),
        "procurement_requests": await count(
            ProcurementRequest,
            ProcurementRequest.buyer_company_id == company_id,
            commerce_workspace_scope,
        ),
        "projects": await count(Project, Project.id.in_(project_ids)),
        "pending_quote_approvals": await count(
            Quote,
            Quote.lead_id.in_(lead_ids),
            quote_workspace_scope,
            Quote.status.in_(("sent", "revised", "client_questions")),
        ),
        "pending_delivery_approvals": await count(
            OrderDelivery,
            OrderDelivery.commerce_order_id.in_(order_ids),
            OrderDelivery.status == "delivered",
        ),
        "installations": await count(WorkPackage, WorkPackage.project_id.in_(project_ids)),
        "installation_tasks_open": await count(
            FieldTask,
            FieldTask.work_package_id.in_(package_ids),
            FieldTask.status.not_in(("done", "cancelled")),
        ),
        "assets": await count(Asset, Asset.project_id.in_(project_ids)),
        "open_tickets": await count(
            Ticket,
            Ticket.buyer_company_id == company_id,
            ticket_workspace_scope,
            or_(Ticket.project_id.is_(None), Ticket.project_id.in_(project_ids)),
            Ticket.status.not_in(("resolved", "closed")),
        ),
    }


@router.get("/approvals")
async def customer_approvals(db: DB, user: CurrentUser):
    company_id = _company_id(user)
    workspace_ids = await customer_workspace_ids(db, user)
    order_workspace_scope = (
        or_(CommerceOrder.workspace_id.in_(workspace_ids), CommerceOrder.workspace_id.is_(None))
        if workspace_ids
        else CommerceOrder.workspace_id.is_(None)
    )
    quote_workspace_scope = (
        or_(Quote.workspace_id.in_(workspace_ids), Quote.workspace_id.is_(None))
        if workspace_ids
        else Quote.workspace_id.is_(None)
    )
    quote_rows = list(
        (
            await db.execute(
                select(Quote)
                .join(Lead, Lead.id == Quote.lead_id)
                .where(
                    Lead.buyer_company_id == company_id,
                    quote_workspace_scope,
                    Quote.status.in_(("sent", "revised", "client_questions")),
                )
                .order_by(Quote.created_at.desc())
            )
        ).scalars()
    )
    delivery_rows = (
        await db.execute(
            select(OrderDelivery, CommerceOrder, ProcurementRequest)
            .join(CommerceOrder, CommerceOrder.id == OrderDelivery.commerce_order_id)
            .join(ProcurementRequest, ProcurementRequest.id == CommerceOrder.procurement_request_id)
            .where(
                CommerceOrder.buyer_company_id == company_id,
                order_workspace_scope,
                OrderDelivery.status == "delivered",
            )
            .order_by(OrderDelivery.delivered_at.desc().nullslast(), OrderDelivery.created_at.desc())
        )
    ).all()
    return {
        "quotes": [QuoteRead.model_validate(row) for row in quote_rows],
        "deliveries": [
            {
                "id": str(delivery.id),
                "order_id": str(order.id),
                "request_title": request.title,
                "status": delivery.status,
                "carrier": delivery.carrier,
                "tracking_number": delivery.tracking_number,
                "delivered_at": delivery.delivered_at,
                "proof_json": delivery.proof_json,
            }
            for delivery, order, request in delivery_rows
        ],
    }


@router.get("/installations")
async def customer_installations(
    db: DB,
    user: CurrentUser,
    project_id: uuid.UUID | None = Query(default=None),
):
    company_id = _company_id(user)
    project_ids = await customer_project_ids_query(db, user)
    if project_id:
        await _owned_project(db, user, project_id)
    query = (
        select(WorkPackage, Project)
        .join(Project, Project.id == WorkPackage.project_id)
        .where(Project.buyer_company_id == company_id, Project.id.in_(project_ids))
        .order_by(WorkPackage.planned_start.asc().nullslast(), WorkPackage.created_at.desc())
    )
    if project_id:
        query = query.where(WorkPackage.project_id == project_id)
    rows = (await db.execute(query)).all()
    return {
        "items": [_package_dict(package, project) for package, project in rows],
        "total": len(rows),
    }


@router.get("/installations/{package_id}")
async def customer_installation_detail(package_id: uuid.UUID, db: DB, user: CurrentUser):
    package, project = await _owned_package(db, user, package_id)
    tasks = list(
        (
            await db.execute(
                select(FieldTask)
                .where(FieldTask.work_package_id == package.id)
                .order_by(FieldTask.schedule_start.asc().nullslast(), FieldTask.created_at.asc())
            )
        ).scalars()
    )
    evidence_by_task: dict[uuid.UUID, list[dict]] = {task.id: [] for task in tasks}
    if tasks:
        evidence_rows = list(
            (
                await db.execute(
                    select(TaskEvidence)
                    .where(TaskEvidence.field_task_id.in_([task.id for task in tasks]))
                    .order_by(TaskEvidence.created_at.desc())
                )
            ).scalars()
        )
        for row in evidence_rows:
            evidence_by_task[row.field_task_id].append(
                {
                    "id": str(row.id),
                    "evidence_type": row.evidence_type,
                    "payload_json": _customer_evidence_payload(row),
                    "sync_status": row.sync_status,
                    "created_at": row.created_at,
                }
            )
    task_items = [
        _task_dict(
            task,
            evidence_count=len(evidence_by_task[task.id]),
            evidence=evidence_by_task[task.id],
        )
        for task in tasks
    ]
    return _package_dict(package, project, tasks=task_items)


@router.get("/assets")
async def customer_assets(
    db: DB,
    user: CurrentUser,
    project_id: uuid.UUID | None = Query(default=None),
):
    company_id = _company_id(user)
    project_ids = await customer_project_ids_query(db, user)
    if project_id:
        await _owned_project(db, user, project_id)
    query = (
        select(Asset, Site, Project)
        .join(Site, Site.id == Asset.site_id)
        .join(Project, Project.id == Asset.project_id)
        .where(Project.buyer_company_id == company_id, Project.id.in_(project_ids))
        .order_by(Site.name.asc(), Asset.floor.asc().nullslast(), Asset.room.asc().nullslast(), Asset.name.asc())
    )
    if project_id:
        query = query.where(Asset.project_id == project_id)
    rows = (await db.execute(query)).all()
    items = [
        {
            "id": str(asset.id),
            "project_id": str(project.id),
            "project_title": project.title,
            "site_id": str(site.id),
            "site_name": site.name,
            "site_address": site.address,
            "name": asset.name,
            "floor": asset.floor,
            "room": asset.room,
            "serial_no": asset.serial_no,
            "installed_at": asset.installed_at,
            "status": asset.status,
            "customer_warranty_id": str(asset.customer_warranty_id) if asset.customer_warranty_id else None,
            "amc_contract_id": str(asset.amc_contract_id) if asset.amc_contract_id else None,
        }
        for asset, site, project in rows
    ]
    return {"items": items, "total": len(items)}

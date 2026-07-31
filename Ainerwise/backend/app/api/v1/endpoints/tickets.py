import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, or_

from app.api.deps import CRMUser, CurrentUser, DB
from app.core.permissions import UserRole
from app.crud.ticket import crud_ticket
from app.models.project import Project
from app.models.ticket import Ticket
from app.schemas.ticket import (
    TicketCreate,
    TicketCustomerRead,
    TicketRead,
    TicketStatusUpdate,
    TicketUpdate,
)
from app.services.event_bus import EventType, emit_event
from app.modules.commerce.access import CommerceAccessDenied, resolve_commerce_workspace
from app.services.crm_access import (
    crm_workspace_ids,
    customer_workspace_ids,
    require_crm_workspace_access,
    require_customer_workspace_resource,
)
from app.services.lifecycle_access import resolve_lifecycle_workspace
from app.services.support_agent import create_ticket_triage
from app.services.project_access import customer_project_ids_query, require_customer_project_access

router = APIRouter(prefix="/tickets", tags=["tickets"])

SUPPORT_ROLES = {
    UserRole.SUPER_ADMIN.value,
    UserRole.ADMIN.value,
    UserRole.SALES_MANAGER.value,
}
GLOBAL_SUPPORT_ROLES = {
    UserRole.SUPER_ADMIN.value,
    UserRole.ADMIN.value,
}
CUSTOMER_EDITABLE_FIELDS = {
    "issue_type",
    "priority",
    "title",
    "description",
    "affected_device",
    "monitoring_point_id",
}


async def _require_ticket_access(db, ticket: Ticket, user) -> None:
    if user.role in GLOBAL_SUPPORT_ROLES:
        return
    if user.role == UserRole.SALES_MANAGER.value:
        await require_crm_workspace_access(db, user, ticket.workspace_id)
        return
    if ticket.buyer_user_id != user.id:
        if not user.company_id or ticket.buyer_company_id != user.company_id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        await require_customer_workspace_resource(db, user, workspace_id=ticket.workspace_id)
    if ticket.project_id is not None:
        project = await db.get(Project, ticket.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        await require_customer_project_access(db, user, project)


@router.get("")
async def list_tickets(
    db: DB,
    admin: CRMUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = []
    accessible_workspace_ids = await crm_workspace_ids(db, admin)
    if accessible_workspace_ids is not None:
        filters.append(Ticket.workspace_id.in_(accessible_workspace_ids))
    if status_filter:
        filters.append(Ticket.status == status_filter)
    items, total = await crud_ticket.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [TicketRead.model_validate(i) for i in items], "total": total}


@router.get("/my")
async def list_my_tickets(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    workspace_ids = await customer_workspace_ids(db, current_user)
    project_ids = await customer_project_ids_query(db, current_user)
    company_workspace_scope = (
        or_(Ticket.workspace_id.in_(workspace_ids), Ticket.workspace_id.is_(None))
        if workspace_ids
        else Ticket.workspace_id.is_(None)
    )
    filters = (
        [
            or_(
                and_(
                    Ticket.buyer_user_id == current_user.id,
                    or_(Ticket.project_id.is_(None), Ticket.project_id.in_(project_ids)),
                ),
                and_(
                    Ticket.project_id.is_(None),
                    Ticket.buyer_company_id == current_user.company_id,
                    company_workspace_scope,
                ),
                Ticket.project_id.in_(project_ids),
            )
        ]
        if current_user.company_id
        else [Ticket.buyer_user_id == current_user.id]
    )
    items, total = await crud_ticket.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [TicketCustomerRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=None)
async def get_ticket(id: uuid.UUID, db: DB, current_user: CurrentUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await _require_ticket_access(db, ticket, current_user)
    if current_user.role in SUPPORT_ROLES:
        return TicketRead.model_validate(ticket)
    return TicketCustomerRead.model_validate(ticket)


@router.post("", response_model=TicketCustomerRead, status_code=201)
async def create_ticket(data: TicketCreate, db: DB, current_user: CurrentUser):
    project = None
    if data.project_id:
        project = await db.get(Project, data.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if current_user.role not in SUPPORT_ROLES:
            await require_customer_project_access(db, current_user, project)
    obj = data.model_dump()
    buyer_company_id = project.buyer_company_id if project else current_user.company_id
    try:
        requested_workspace_id = data.workspace_id
        if current_user.role not in SUPPORT_ROLES:
            requested_workspace_id = await resolve_commerce_workspace(
                db,
                user=current_user,
                requested_workspace_id=requested_workspace_id,
            )
        obj["workspace_id"] = await resolve_lifecycle_workspace(
            db,
            requested_workspace_id=requested_workspace_id,
            company_id=buyer_company_id,
            project_id=data.project_id,
            asset_id=data.asset_id,
            monitoring_point_id=data.monitoring_point_id,
        )
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    if current_user.role == UserRole.SALES_MANAGER.value:
        await require_crm_workspace_access(db, current_user, obj["workspace_id"])
    obj["buyer_user_id"] = current_user.id
    obj["buyer_company_id"] = buyer_company_id
    obj["status"] = "open"
    ticket = Ticket(**obj)
    db.add(ticket)
    await db.flush()
    await create_ticket_triage(db, ticket)
    await emit_event(
        db,
        EventType.TICKET_OPENED,
        {
            "ticket_id": str(ticket.id),
            "project_id": str(ticket.project_id) if ticket.project_id else None,
            "title": ticket.title,
            "issue_type": ticket.issue_type,
            "affected_device": ticket.affected_device,
        },
        aggregate_type="ticket",
        aggregate_id=ticket.id,
        target_channel="telegram_admin",
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.put("/{id}", response_model=None)
async def update_ticket(id: uuid.UUID, data: TicketUpdate, db: DB, current_user: CurrentUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await _require_ticket_access(db, ticket, current_user)
    updates = data.model_dump(exclude_unset=True)
    if current_user.role not in SUPPORT_ROLES:
        protected = sorted(set(updates) - CUSTOMER_EDITABLE_FIELDS)
        if protected:
            raise HTTPException(
                status_code=403,
                detail=f"Admin review required for fields: {', '.join(protected)}",
            )
    if "monitoring_point_id" in updates:
        try:
            await resolve_lifecycle_workspace(
                db,
                requested_workspace_id=ticket.workspace_id,
                company_id=ticket.buyer_company_id,
                project_id=ticket.project_id,
                asset_id=ticket.asset_id,
                monitoring_point_id=updates["monitoring_point_id"],
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
    updated = await crud_ticket.update(db, db_obj=ticket, obj_in=updates)
    if current_user.role in SUPPORT_ROLES:
        return TicketRead.model_validate(updated)
    return TicketCustomerRead.model_validate(updated)


@router.patch("/{id}/status", response_model=TicketRead)
async def update_ticket_status(id: uuid.UUID, data: TicketStatusUpdate, db: DB, admin: CRMUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await _require_ticket_access(db, ticket, admin)
    return await crud_ticket.update(db, db_obj=ticket, obj_in={"status": data.status})

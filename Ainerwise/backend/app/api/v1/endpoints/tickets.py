import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, CurrentUser, DB
from app.core.permissions import UserRole
from app.crud.ticket import crud_ticket
from app.models.project import Project
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketRead, TicketStatusUpdate, TicketUpdate
from app.services.event_bus import EventType, emit_event
from app.services.support_agent import create_ticket_triage

router = APIRouter(prefix="/tickets", tags=["tickets"])

ADMIN_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}
CUSTOMER_EDITABLE_FIELDS = {
    "issue_type",
    "priority",
    "title",
    "description",
    "affected_device",
    "monitoring_point_id",
}


def _can_access(ticket: Ticket, user) -> bool:
    return user.role in ADMIN_ROLES or ticket.buyer_user_id == user.id or (
        user.company_id is not None and ticket.buyer_company_id == user.company_id
    )


@router.get("")
async def list_tickets(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = []
    if status_filter:
        from app.models.ticket import Ticket

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
    from app.models.ticket import Ticket

    filters = [Ticket.buyer_user_id == current_user.id]
    items, total = await crud_ticket.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [TicketRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=TicketRead)
async def get_ticket(id: uuid.UUID, db: DB, current_user: CurrentUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not _can_access(ticket, current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return ticket


@router.post("", response_model=TicketRead, status_code=201)
async def create_ticket(data: TicketCreate, db: DB, current_user: CurrentUser):
    project = None
    if data.project_id:
        project = await db.get(Project, data.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if current_user.role not in ADMIN_ROLES and (
            not current_user.company_id or project.buyer_company_id != current_user.company_id
        ):
            raise HTTPException(status_code=403, detail="Not your project")
    obj = data.model_dump()
    obj["buyer_user_id"] = current_user.id
    obj["buyer_company_id"] = (
        project.buyer_company_id if data.project_id and project else current_user.company_id
    )
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


@router.put("/{id}", response_model=TicketRead)
async def update_ticket(id: uuid.UUID, data: TicketUpdate, db: DB, current_user: CurrentUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not _can_access(ticket, current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    updates = data.model_dump(exclude_unset=True)
    if current_user.role not in ADMIN_ROLES:
        protected = sorted(set(updates) - CUSTOMER_EDITABLE_FIELDS)
        if protected:
            raise HTTPException(
                status_code=403,
                detail=f"Admin review required for fields: {', '.join(protected)}",
            )
    return await crud_ticket.update(db, db_obj=ticket, obj_in=updates)


@router.patch("/{id}/status", response_model=TicketRead)
async def update_ticket_status(id: uuid.UUID, data: TicketStatusUpdate, db: DB, admin: AdminUser):
    ticket = await crud_ticket.get(db, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return await crud_ticket.update(db, db_obj=ticket, obj_in={"status": data.status})

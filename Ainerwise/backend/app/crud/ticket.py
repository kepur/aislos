from app.crud.base import CRUDBase
from app.models.ticket import Ticket

crud_ticket = CRUDBase[Ticket](Ticket)

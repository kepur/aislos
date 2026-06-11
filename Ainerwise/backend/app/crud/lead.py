from app.crud.base import CRUDBase
from app.models.lead import Lead

crud_lead = CRUDBase[Lead](Lead)

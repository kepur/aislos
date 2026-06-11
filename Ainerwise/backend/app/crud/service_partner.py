from app.crud.base import CRUDBase
from app.models.service import ServicePartner

crud_service_partner = CRUDBase[ServicePartner](ServicePartner)

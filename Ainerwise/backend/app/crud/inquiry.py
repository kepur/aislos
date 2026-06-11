from app.crud.base import CRUDBase
from app.models.inquiry import Inquiry

crud_inquiry = CRUDBase[Inquiry](Inquiry)

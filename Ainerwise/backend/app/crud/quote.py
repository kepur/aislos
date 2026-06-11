from app.crud.base import CRUDBase
from app.models.quote import Quote

crud_quote = CRUDBase[Quote](Quote)

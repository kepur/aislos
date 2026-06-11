from app.crud.base import CRUDBase
from app.models.region import Region

crud_region = CRUDBase[Region](Region)

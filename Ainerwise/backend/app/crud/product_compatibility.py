from app.crud.base import CRUDBase
from app.models.product import ProductCompatibility

crud_product_compatibility = CRUDBase[ProductCompatibility](ProductCompatibility)

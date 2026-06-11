from app.crud.base import CRUDBase
from app.models.user import Company, User

crud_user = CRUDBase[User](User)
crud_company = CRUDBase[Company](Company)

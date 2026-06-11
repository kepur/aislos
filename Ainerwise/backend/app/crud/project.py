from app.crud.base import CRUDBase
from app.models.project import Project

crud_project = CRUDBase[Project](Project)

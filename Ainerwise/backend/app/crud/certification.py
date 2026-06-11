from app.crud.base import CRUDBase
from app.models.certification import CertificationRecord, WarrantyPolicy

crud_certification = CRUDBase[CertificationRecord](CertificationRecord)
crud_warranty_policy = CRUDBase[WarrantyPolicy](WarrantyPolicy)

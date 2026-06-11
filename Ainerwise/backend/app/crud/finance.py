from app.crud.base import CRUDBase
from app.models.finance import PlatformFeeRule, ProjectFinance

crud_project_finance = CRUDBase[ProjectFinance](ProjectFinance)
crud_platform_fee_rule = CRUDBase[PlatformFeeRule](PlatformFeeRule)

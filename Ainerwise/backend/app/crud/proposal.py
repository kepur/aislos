from app.crud.base import CRUDBase
from app.models.proposal import ProposalPlan, BOMItem

crud_proposal_plan = CRUDBase[ProposalPlan](ProposalPlan)
crud_bom_item = CRUDBase[BOMItem](BOMItem)

from app.crud.base import CRUDBase
from app.models.lead import SiteSurvey

crud_site_survey = CRUDBase[SiteSurvey](SiteSurvey)

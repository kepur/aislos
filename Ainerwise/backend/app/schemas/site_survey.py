import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class SiteSurveyRead(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID
    survey_type: str
    survey_json: dict | None = None
    uploaded_files_json: list | None = None
    completeness_score: float | None = None
    risk_score: float | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class SiteSurveyCreate(BaseSchema):
    lead_id: uuid.UUID
    survey_type: str = "quick"
    survey_json: dict | None = None
    uploaded_files_json: list | None = None
    completeness_score: float | None = None
    risk_score: float | None = None


class SiteSurveyUpdate(BaseSchema):
    survey_type: str | None = None
    survey_json: dict | None = None
    uploaded_files_json: list | None = None
    completeness_score: float | None = None
    risk_score: float | None = None

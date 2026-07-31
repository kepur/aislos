"""KYC & verification schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CompanyDocumentCreate(BaseModel):
    doc_type: str
    file_url: str
    original_filename: str | None = None


class CompanyDocumentRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    doc_type: str
    file_url: str
    original_filename: str | None = None
    status: str = "PENDING"
    reviewer_note: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentReviewRequest(BaseModel):
    status: str = Field(..., pattern="^(ACCEPTED|REJECTED)$")
    reviewer_note: str | None = None


class KYCAnalysisRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    document_id: uuid.UUID
    ai_provider: str
    ai_model: str
    authenticity: str
    confidence: float
    overall_risk_score: float
    recommended_action: str
    tamper_suspected: bool
    photoshop_suspected: bool
    extracted_fields: dict | None = None
    detected_issues: list | None = None
    concerns: list | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VerificationReviewRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    decision: str | None = None
    decision_reason: str | None = None
    user_facing_note: str | None = None
    decided_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VerificationDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVE_BASIC|APPROVE_BUSINESS|REQUEST_MORE_INFO|REJECT|ESCALATE_TO_RISK)$")
    decision_reason: str | None = None
    internal_note: str | None = None
    user_facing_note: str | None = None

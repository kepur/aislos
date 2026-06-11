import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.company import BranchStatus, CompanyStatus, VerificationLevel
from app.models.company_document import DocumentStatus, DocumentType
from app.models.verification_review import VerificationDecision, VerificationQueueStatus


class CompanyCreate(BaseModel):
    name: str
    tax_id: str | None = None
    country: str
    city: str | None = None
    address: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    tax_id: str | None
    country: str
    city: str | None
    address: str | None
    verification_level: VerificationLevel
    status: CompanyStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    name: str
    country: str
    city: str
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int = 30
    delivery_methods: list[str] = []


class BranchUpdate(BaseModel):
    name: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_km: int | None = None
    delivery_methods: list[str] | None = None
    status: BranchStatus | None = None


class BranchResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    country: str
    city: str
    address: str | None
    lat: float | None
    lng: float | None
    radius_km: int
    delivery_methods: list | None
    status: BranchStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyDocumentCreate(BaseModel):
    doc_type: DocumentType
    file_url: str
    original_filename: str | None = None


class CompanyDocumentResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    doc_type: DocumentType
    file_url: str
    original_filename: str | None
    status: DocumentStatus
    reviewer_note: str | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationSubmitResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    status: VerificationQueueStatus
    decision: VerificationDecision | None
    user_facing_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

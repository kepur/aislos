"""Pydantic schemas for procurement projects, facts and file attachments."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class ProcurementProjectCreate(BaseSchema):
    project_type: str
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    region: str | None = None
    country: str | None = None
    city: str | None = None


class ProcurementProjectRead(BaseSchema):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    company_id: uuid.UUID | None
    portal_key: str
    portal_policy_id: uuid.UUID
    policy_snapshot_json: dict
    project_type: str
    title: str
    description: str | None
    region: str | None
    country: str | None
    city: str | None
    status: str
    facts_score: Decimal
    boq_score: Decimal
    overall_confidence: Decimal
    current_boq_version_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProcurementProjectList(BaseSchema):
    items: list[ProcurementProjectRead]
    total: int


class TransferPortalRequest(BaseSchema):
    target_portal_key: str = Field(..., min_length=1, max_length=50)
    reason: str = Field(..., min_length=1, max_length=2000)


class ProcurementFileAttach(BaseSchema):
    original_name: str = Field(..., min_length=1, max_length=500)
    storage_path: str = Field(..., min_length=1, max_length=1000)
    mime_type: str | None = None
    size_bytes: int | None = None
    file_type: str | None = None


class ProcurementFileRead(BaseSchema):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    file_type: str | None
    original_name: str
    storage_path: str
    mime_type: str | None
    size_bytes: int | None
    uploaded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ProcurementFactRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    template_key: str
    label: str
    value_json: dict | list | str | int | float | bool | None
    required: bool
    critical: bool
    weight: Decimal
    source: str
    source_ref_json: dict | None
    confidence: Decimal
    user_confirmed: bool
    assumption: str | None
    created_at: datetime
    updated_at: datetime


class ProcurementFactPatch(BaseSchema):
    value_json: dict | list | str | int | float | bool | None = None
    user_confirmed: bool | None = None
    assumption: str | None = None


class BoqItemOptionDraft(BaseSchema):
    tier: str
    capability: str
    recommended_brand: str | None = None
    unit_price_min: Decimal
    unit_price_max: Decimal
    currency: str = "USD"
    supply_included: bool = True
    install_included: bool = False
    maintain_included: bool = False
    notes: str | None = None


class BoqItemDraft(BaseSchema):
    category: str
    trade: str | None = None
    name: str
    description: str | None = None
    specs: str | None = None
    qty: Decimal = Decimal("1")
    unit: str = "ea"
    quantity_basis: str | None = None
    assumptions: str | None = None
    confidence: Decimal = Decimal("0.9")
    source: str = "system"
    source_ref_json: dict | None = None
    critical: bool = False
    weight: Decimal = Decimal("1")
    included: bool = True
    sort_order: int = 0
    options: list[BoqItemOptionDraft]


class BoqDraftCreate(BaseSchema):
    items: list[BoqItemDraft]
    disclaimer: str | None = None
    source_run_id: uuid.UUID | None = None


class BoqReviewSubmit(BaseSchema):
    boq_version_id: uuid.UUID | None = None


class BoqFreezeRequest(BaseSchema):
    boq_version_id: uuid.UUID | None = None


class AnalyzeRequest(BaseSchema):
    """Optional test scenario for confidence branch tests (dev/test only)."""
    test_scenario: str | None = None


class AnalyzeResponse(BaseSchema):
    run_id: str
    status: str
    facts_score: str
    boq_score: str
    overall_confidence: str
    missing_questions: list
    boq_version_id: str | None
    review_id: str | None
    solution_plans: list
    disclaimer: str | None


class PartnerCandidateSummary(BaseSchema):
    partner_id: uuid.UUID
    partner_type: str
    country: str | None
    trade: str
    commercial_type: str
    capability_keys: list = Field(default_factory=list)


class ProcurementPackageItemRead(BaseSchema):
    id: uuid.UUID
    boq_item_id: uuid.UUID
    boq_item_option_id: uuid.UUID | None
    quantity: str


class ProcurementPackageRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    boq_version_id: uuid.UUID
    title: str
    trade: str
    commercial_type: str
    procurement_mode: str
    region: str | None
    compatibility_json: dict | None
    delivery_constraints_json: dict | None
    status: str
    revision: int
    items: list[ProcurementPackageItemRead]
    candidate_partners: list[PartnerCandidateSummary]


class PackageGenerateResponse(BaseSchema):
    project_status: str
    packages: list[ProcurementPackageRead]


class ProcurementPackagePatch(BaseSchema):
    title: str | None = Field(None, min_length=1, max_length=500)
    procurement_mode: str | None = None
    status: str | None = None


class PublishRfqRequest(BaseSchema):
    currency: str = Field(..., min_length=3, max_length=10)
    exchange_rate_snapshot_json: dict
    tax_mode: str = Field(..., min_length=1, max_length=50)
    margin_rule_json: dict
    service_fee_json: dict
    warranty_rule_json: dict
    delivery_region_json: dict
    quote_expiry: datetime
    payment_terms_json: dict
    bid_deadline: datetime | None = None


class CommercialSnapshotCustomerRead(BaseSchema):
    id: uuid.UUID
    portal_key: str
    package_id: uuid.UUID
    package_revision: int
    currency: str
    exchange_rate_snapshot_json: dict
    tax_mode: str
    warranty_rule_json: dict
    delivery_region_json: dict
    quote_expiry: datetime
    terms_hash: str
    created_at: datetime
    payment_terms_json: dict | None = None
    service_fee_json: dict | None = None


class PublishRfqCustomerResponse(BaseSchema):
    project_status: str
    package_status: str
    created: bool
    rfq: dict
    supplier_view: dict

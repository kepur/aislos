import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


class CertificationRecordRead(BaseSchema):
    id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    certification_name: str
    issuer: str | None = None
    country: str | None = None
    status: str
    issue_date: date | None = None
    expiry_date: date | None = None
    certificate_file_url: str | None = None
    public_visible: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CertificationRecordCreate(BaseSchema):
    owner_type: str
    owner_id: uuid.UUID
    certification_name: str
    issuer: str | None = None
    country: str | None = None
    status: str = "planned"
    issue_date: date | None = None
    expiry_date: date | None = None
    certificate_file_url: str | None = None
    public_visible: bool = False
    notes: str | None = None


class CertificationRecordUpdate(BaseSchema):
    certification_name: str | None = None
    issuer: str | None = None
    country: str | None = None
    status: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    certificate_file_url: str | None = None
    public_visible: bool | None = None
    notes: str | None = None


class WarrantyPolicyRead(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    region: str | None = None
    manufacturer_warranty_months: int | None = None
    platform_support_months: int | None = None
    local_installation_warranty_months: int | None = None
    spare_parts_policy_json: dict | None = None
    response_sla_json: dict | None = None
    exclusions_text: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class WarrantyPolicyCreate(BaseSchema):
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    region: str | None = None
    manufacturer_warranty_months: int | None = None
    platform_support_months: int | None = None
    local_installation_warranty_months: int | None = None
    spare_parts_policy_json: dict | None = None
    response_sla_json: dict | None = None
    exclusions_text: str | None = None
    active: bool = True


class WarrantyPolicyUpdate(BaseSchema):
    product_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    region: str | None = None
    manufacturer_warranty_months: int | None = None
    platform_support_months: int | None = None
    local_installation_warranty_months: int | None = None
    spare_parts_policy_json: dict | None = None
    response_sla_json: dict | None = None
    exclusions_text: str | None = None
    active: bool | None = None

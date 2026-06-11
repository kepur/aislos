import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class IntegrationClientCreate(BaseSchema):
    name: str
    scopes: list[str]
    allowed_region_ids: list[uuid.UUID] | None = None


class IntegrationClientRead(BaseSchema):
    id: uuid.UUID
    name: str
    key_prefix: str
    status: str
    scopes_json: list[str]
    allowed_region_ids_json: list | None = None
    last_used_at: datetime | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class IntegrationClientCreated(IntegrationClientRead):
    client_secret: str


class MediaRequestExternalBrief(BaseSchema):
    brief_id: uuid.UUID
    title: str
    objective: str | None = None
    version: int
    content_hash: str | None = None
    copy_block: dict = Field(serialization_alias="copy")
    audience: dict
    brand_constraints: dict
    channel_specs: dict
    compliance: dict


class MediaRequestDeliverable(BaseSchema):
    key: str
    media_type: str
    channel: str
    language: str
    format: str
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    variant_count: int | None = None
    required_text: list[str] | None = None
    notes: str | None = None


class MediaRequestExternal(BaseSchema):
    id: uuid.UUID
    status: str
    deliverable_key: str
    deliverable: MediaRequestDeliverable
    brief: MediaRequestExternalBrief
    progress_percent: int | None = None
    progress_message: str | None = None
    claim_expires_at: datetime | None = None


class MediaRequestListResponse(BaseSchema):
    items: list[MediaRequestExternal]
    total: int


class HeartbeatRequest(BaseSchema):
    external_job_ref: str | None = None
    progress_percent: int = Field(ge=0, le=100)
    progress_message: str | None = None


class FailRequest(BaseSchema):
    failure_code: str
    failure_message: str
    retryable: bool = True


class IntegrationErrorBody(BaseSchema):
    code: str
    message: str
    correlation_id: str
    retryable: bool = False


class UploadCreateRequest(BaseSchema):
    file_name: str
    mime_type: str
    size_bytes: int = Field(gt=0)
    sha256: str


class UploadCreateResponse(BaseSchema):
    upload_id: uuid.UUID
    upload_url: str
    object_key: str
    expires_at: datetime


class AssetSubmitRequest(BaseSchema):
    upload_id: uuid.UUID
    external_asset_ref: str | None = None
    variant_key: str | None = None
    mime_type: str
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    sha256: str
    metadata: dict | None = None


class AssetSubmitResponse(BaseSchema):
    asset_id: uuid.UUID
    status: str
    media_request_id: uuid.UUID
    review_id: uuid.UUID

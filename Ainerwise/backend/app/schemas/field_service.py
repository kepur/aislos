import uuid
from datetime import date, datetime

from app.schemas.base import BaseSchema


class WorkPackageCreate(BaseSchema):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    partner_company_id: uuid.UUID | None = None
    title: str
    trade: str | None = None
    scope_json: dict | None = None
    site_json: dict | None = None
    planned_start: date | None = None
    planned_end: date | None = None


class WorkPackageRead(WorkPackageCreate):
    id: uuid.UUID
    status: str
    created_at: datetime


class FieldTaskCreate(BaseSchema):
    work_package_id: uuid.UUID
    task_type: str
    title: str
    site_json: dict | None = None
    checklist_json: dict | None = None
    required_skill: str | None = None
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    safety_notes: str | None = None


class FieldTaskRead(FieldTaskCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID
    status: str
    offline_version: int


class TaskAssignmentCreate(BaseSchema):
    assignee_user_id: uuid.UUID
    crew_id: uuid.UUID | None = None
    reason: str | None = None


class TaskAssignmentRead(TaskAssignmentCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID
    field_task_id: uuid.UUID
    status: str


class QrBindRequest(BaseSchema):
    qr_code: str
    device_label: str | None = None


class SignatureCaptureRequest(BaseSchema):
    signature_data_url: str
    signer_name: str | None = None
    idempotency_key: str | None = None


class TaskEvidenceCreate(BaseSchema):
    evidence_type: str
    payload_json: dict | None = None
    idempotency_key: str | None = None


class TaskEvidenceRead(TaskEvidenceCreate):
    id: uuid.UUID
    field_task_id: uuid.UUID
    sync_status: str


class PartnerCrewCreate(BaseSchema):
    workspace_id: uuid.UUID
    partner_company_id: uuid.UUID | None = None
    name: str
    trade: str | None = None


class PartnerCrewRead(PartnerCrewCreate):
    id: uuid.UUID
    status: str


class CrewMembershipCreate(BaseSchema):
    user_id: uuid.UUID
    role_in_crew: str = "worker"


class CrewMembershipRead(CrewMembershipCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID
    crew_id: uuid.UUID
    status: str


class FieldTaskDetailRead(FieldTaskRead):
    site_contact_phone: str | None = None
    assignment_id: uuid.UUID | None = None


class FieldTaskStatusUpdate(BaseSchema):
    status: str
    offline_version: int
    note: str | None = None


class OfflineSyncItem(BaseSchema):
    type: str
    task_id: uuid.UUID
    idempotency_key: str
    offline_version: int | None = None
    status: str | None = None
    evidence_type: str | None = None
    payload_json: dict | None = None


class OfflineSyncRequest(BaseSchema):
    items: list[OfflineSyncItem]


class OfflineSyncResult(BaseSchema):
    idempotency_key: str
    status: str
    conflict: bool = False
    server_offline_version: int | None = None
    detail: str | None = None

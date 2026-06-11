"""Pydantic schemas for AI Project Forge (buyer projects)."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.buyer_project import (
    AIRunStatus,
    LineItemSource,
    LineItemStatus,
    MetricValueSource,
    ProjectFileStatus,
    ProjectMessageRole,
    ProjectReportPatchStatus,
    ProjectReportVersionStatus,
    ProjectStatus,
    ProjectType,
    ProjectWorkflowNode,
    QualityPreference,
    QualityTier,
)


# ─── Project ───────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=500)
    project_type: ProjectType = ProjectType.GENERAL
    country: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    area_value: float | None = None
    area_unit: str | None = None
    scale_jsonb: dict | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    currency: str = "PHP"
    quality_preference: QualityPreference = QualityPreference.NOT_SURE
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    project_type: ProjectType | None = None
    country: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    area_value: float | None = None
    area_unit: str | None = None
    scale_jsonb: dict | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    currency: str | None = None
    quality_preference: QualityPreference | None = None
    description: str | None = None


class ProjectFileResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    url: str
    file_name: str
    content_type: str
    file_size: int
    extracted_text: str | None
    vision_summary: str | None
    status: ProjectFileStatus
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LineItemResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    ai_run_id: uuid.UUID | None
    category_id: uuid.UUID | None
    intent_id: uuid.UUID | None
    name: str
    description: str | None
    specs_jsonb: dict | None
    qty: float
    unit: str
    quality_tier: QualityTier
    estimated_unit_price: float | None
    estimated_total_price: float | None
    currency: str
    confidence: float | None
    sourcing_notes: str | None
    price_tiers_jsonb: dict | None
    include_in_estimate: bool = True
    category_hint: str | None
    source: LineItemSource
    status: LineItemStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIRunResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    provider: str | None
    model: str | None
    prompt_version: str | None
    status: AIRunStatus
    input_snapshot_jsonb: dict | None
    raw_output: str | None
    structured_output_jsonb: dict | None
    token_usage_jsonb: dict | None
    estimated_cost: float | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    title: str
    project_type: ProjectType
    status: ProjectStatus
    country: str | None
    city: str | None
    lat: float | None
    lng: float | None
    area_value: float | None
    area_unit: str | None
    scale_jsonb: dict | None
    budget_min: int | None
    budget_max: int | None
    currency: str
    quality_preference: QualityPreference
    description: str | None
    ai_summary: str | None
    missing_questions_jsonb: list | None
    assumptions_jsonb: list | None
    risk_notes_jsonb: list | None
    acceptance_criteria_jsonb: list | None
    estimated_budget_jsonb: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """Full project detail including files, line items and latest AI run."""
    files: list[ProjectFileResponse] = []
    line_items: list[LineItemResponse] = []
    latest_ai_run: AIRunResponse | None = None


class LineItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    specs_jsonb: dict | None = None
    qty: float | None = None
    unit: str | None = None
    quality_tier: QualityTier | None = None
    estimated_unit_price: float | None = None
    estimated_total_price: float | None = None
    currency: str | None = None
    category_id: uuid.UUID | None = None
    include_in_estimate: bool | None = None
    status: LineItemStatus | None = None


class PublishResult(BaseModel):
    project_id: uuid.UUID
    published_count: int
    intents_created: list[uuid.UUID]
    skipped_count: int


class AIProjectConfigResponse(BaseModel):
    ai_project_estimation_enabled: bool = False
    ai_project_model: str = ""
    ai_multimodal_enabled: bool = False
    ai_multimodal_model: str = ""
    ai_project_prompt_version: str = "v1"
    ai_project_max_files: int = 10
    ai_project_max_file_size_mb: int = 10


class ProjectMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    file_ids: list[uuid.UUID] = []


class ProjectMessageResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    role: ProjectMessageRole
    workflow_node: ProjectWorkflowNode | None
    content: str
    file_ids_jsonb: list | None
    structured_delta_jsonb: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectMetricTemplateCreate(BaseModel):
    project_type: ProjectType = ProjectType.GENERAL
    key: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    data_type: str = "text"
    unit_options_jsonb: list | None = None
    required: bool = False
    sort_order: int = 0
    prompt: str | None = None
    active: bool = True


class ProjectMetricTemplateUpdate(BaseModel):
    project_type: ProjectType | None = None
    key: str | None = None
    label: str | None = None
    data_type: str | None = None
    unit_options_jsonb: list | None = None
    required: bool | None = None
    sort_order: int | None = None
    prompt: str | None = None
    active: bool | None = None


class ProjectMetricTemplateResponse(BaseModel):
    id: uuid.UUID
    project_type: ProjectType
    key: str
    label: str
    data_type: str
    unit_options_jsonb: list | None
    required: bool
    sort_order: int
    prompt: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMetricValuePatch(BaseModel):
    key: str
    label: str | None = None
    value: Any
    source: MetricValueSource = MetricValueSource.USER
    confidence: float | None = None


class ProjectMetricsUpdate(BaseModel):
    metrics: list[ProjectMetricValuePatch]


class ProjectMetricValueResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    template_id: uuid.UUID | None
    key: str
    label: str | None
    value_jsonb: dict | None
    source: MetricValueSource
    confidence: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMetricsResponse(BaseModel):
    project_id: uuid.UUID
    project_type: ProjectType
    templates: list[ProjectMetricTemplateResponse]
    values: list[ProjectMetricValueResponse]
    missing_required: list[dict]


class ProjectPriceSnapshotResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    line_item_id: uuid.UUID
    currency: str
    sample_count: int
    min_unit_price: float | None
    avg_unit_price: float | None
    median_unit_price: float | None
    p20_unit_price: float | None
    p80_unit_price: float | None
    price_tiers_jsonb: dict | None
    samples_jsonb: list | None
    source_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Versioned Report Sheet ────────────────────────────────────

class ProjectReportColumnResponse(BaseModel):
    id: uuid.UUID
    report_version_id: uuid.UUID
    key: str
    label: str
    data_type: str
    sort_order: int
    editable: bool
    system: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectReportRowResponse(BaseModel):
    id: uuid.UUID
    report_version_id: uuid.UUID
    project_id: uuid.UUID
    line_item_id: uuid.UUID | None
    category_id: uuid.UUID | None
    name: str
    description: str | None
    specs_jsonb: dict | None
    qty: float
    unit: str
    currency: str
    quality_tier: QualityTier
    selected_tier: str
    include_in_total: bool
    selected_for_purchase: bool
    price_tiers_jsonb: dict | None
    custom_values_jsonb: dict | None
    match_status: str
    samples_jsonb: list | None
    price_source: str
    notes: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectReportVersionResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    project_id: uuid.UUID
    version_number: int
    status: ProjectReportVersionStatus
    source: str
    title: str | None
    summary_jsonb: dict | None
    totals_jsonb: dict | None
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectReportResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    current_version_id: uuid.UUID | None
    frozen_version_id: uuid.UUID | None
    current_version: ProjectReportVersionResponse | None
    columns: list[ProjectReportColumnResponse] = []
    rows: list[ProjectReportRowResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectReportCellPatch(BaseModel):
    row_id: uuid.UUID
    field: str
    value: Any


class ProjectReportCellsUpdate(BaseModel):
    changes: list[ProjectReportCellPatch]
    message: str | None = None


class ProjectReportColumnCreate(BaseModel):
    key: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    data_type: str = "text"


class ProjectReportRowCreate(BaseModel):
    name: str = Field(..., max_length=500)
    qty: float = 1
    unit: str = "pcs"
    currency: str = "PHP"
    selected_tier: str = "MID_RANGE"
    include_in_total: bool = True
    selected_for_purchase: bool = True
    price_tiers_jsonb: dict | None = None
    custom_values_jsonb: dict | None = None
    notes: str | None = None


class ProjectReportChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class ProjectReportChangeLogResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    report_id: uuid.UUID
    version_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    change_type: str
    status: ProjectReportPatchStatus
    user_message: str | None
    patch_jsonb: dict | None
    before_jsonb: dict | None
    after_jsonb: dict | None
    error_message: str | None
    created_at: datetime
    applied_at: datetime | None

    model_config = {"from_attributes": True}

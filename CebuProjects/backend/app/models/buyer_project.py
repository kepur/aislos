"""Buyer Project models for AI Project Forge.

A BuyerProject is a master order that groups multiple line items.
AI analysis generates project_line_items which, once confirmed,
are published as individual Intent records reusing existing flows.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Enumerations ──────────────────────────────────────────────

class ProjectType(str, enum.Enum):
    CONSTRUCTION = "CONSTRUCTION"
    SOLAR = "SOLAR"
    TECH_BUILD = "TECH_BUILD"
    RENOVATION = "RENOVATION"
    GENERAL = "GENERAL"


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COLLECTING_INFO = "COLLECTING_INFO"
    ANALYZING = "ANALYZING"
    AI_ANALYZED = "AI_ANALYZED"
    READY_FOR_SOURCING = "READY_FOR_SOURCING"
    SOURCING = "SOURCING"
    ORDERING = "ORDERING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class QualityPreference(str, enum.Enum):
    BUDGET = "BUDGET"
    MID_RANGE = "MID_RANGE"
    PREMIUM = "PREMIUM"
    NOT_SURE = "NOT_SURE"


class ProjectFileStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"


class AIRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LineItemStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SOURCING = "SOURCING"
    MATCHED = "MATCHED"
    QUOTED = "QUOTED"
    ORDERED = "ORDERED"
    REMOVED = "REMOVED"


class LineItemSource(str, enum.Enum):
    AI = "AI"
    USER = "USER"


class QualityTier(str, enum.Enum):
    BUDGET = "BUDGET"
    MID_RANGE = "MID_RANGE"
    PREMIUM = "PREMIUM"


class ProjectMessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class ProjectWorkflowNode(str, enum.Enum):
    INTAKE_CHAT = "intake_chat"
    METRIC_EXTRACT = "metric_extract"
    GAP_QUESTION = "gap_question"
    FILE_MULTIMODAL_EXTRACT = "file_multimodal_extract"
    LINE_ITEM_PLAN = "line_item_plan"
    PRICE_TIER_ESTIMATE = "price_tier_estimate"
    SUPPLIER_MATCH = "supplier_match"
    FORM_FREEZE = "form_freeze"


class MetricValueSource(str, enum.Enum):
    USER = "USER"
    AI = "AI"
    FILE = "FILE"
    SYSTEM = "SYSTEM"


class ProjectReportVersionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ESTIMATED = "ESTIMATED"
    USER_REVIEWED = "USER_REVIEWED"
    FROZEN = "FROZEN"
    PUBLISHED = "PUBLISHED"


class ProjectReportPatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


# ─── Models ────────────────────────────────────────────────────

class BuyerProject(Base):
    __tablename__ = "buyer_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(500))
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, name="project_type", create_type=False),
        default=ProjectType.GENERAL,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", create_type=False),
        default=ProjectStatus.DRAFT,
        index=True,
    )
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    area_value: Mapped[float | None] = mapped_column(Float)
    area_unit: Mapped[str | None] = mapped_column(String(50))
    scale_jsonb: Mapped[dict | None] = mapped_column(JSON)
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    quality_preference: Mapped[QualityPreference] = mapped_column(
        Enum(QualityPreference, name="quality_preference", create_type=False),
        default=QualityPreference.NOT_SURE,
    )
    description: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    missing_questions_jsonb: Mapped[list | None] = mapped_column(JSON)
    assumptions_jsonb: Mapped[list | None] = mapped_column(JSON)
    risk_notes_jsonb: Mapped[list | None] = mapped_column(JSON)
    acceptance_criteria_jsonb: Mapped[list | None] = mapped_column(JSON)
    estimated_budget_jsonb: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectFile(Base):
    __tablename__ = "project_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    file_name: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(200))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    vision_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectFileStatus] = mapped_column(
        Enum(ProjectFileStatus, name="project_file_status", create_type=False),
        default=ProjectFileStatus.UPLOADED,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectAIRun(Base):
    __tablename__ = "project_ai_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(200))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[AIRunStatus] = mapped_column(
        Enum(AIRunStatus, name="ai_run_status", create_type=False),
        default=AIRunStatus.PENDING,
        index=True,
    )
    input_snapshot_jsonb: Mapped[dict | None] = mapped_column(JSON)
    raw_output: Mapped[str | None] = mapped_column(Text)
    structured_output_jsonb: Mapped[dict | None] = mapped_column(JSON)
    token_usage_jsonb: Mapped[dict | None] = mapped_column(JSON)
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectLineItem(Base):
    __tablename__ = "project_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    specs_jsonb: Mapped[dict | None] = mapped_column(JSON)
    qty: Mapped[float] = mapped_column(Float, default=1)
    unit: Mapped[str] = mapped_column(String(50), default="pcs")
    quality_tier: Mapped[QualityTier] = mapped_column(
        Enum(QualityTier, name="quality_tier", create_type=False),
        default=QualityTier.MID_RANGE,
    )
    estimated_unit_price: Mapped[float | None] = mapped_column(Float)
    estimated_total_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    confidence: Mapped[float | None] = mapped_column(Float)
    sourcing_notes: Mapped[str | None] = mapped_column(Text)
    price_tiers_jsonb: Mapped[dict | None] = mapped_column(JSON)  # {BUDGET: {unit_price, total_price, notes}, MID_RANGE: ..., PREMIUM: ...}
    include_in_estimate: Mapped[bool] = mapped_column(Boolean, default=True)
    category_hint: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[LineItemSource] = mapped_column(
        Enum(LineItemSource, name="line_item_source", create_type=False),
        default=LineItemSource.AI,
    )
    status: Mapped[LineItemStatus] = mapped_column(
        Enum(LineItemStatus, name="line_item_status", create_type=False),
        default=LineItemStatus.DRAFT,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectMessage(Base):
    __tablename__ = "project_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    role: Mapped[ProjectMessageRole] = mapped_column(
        Enum(ProjectMessageRole, name="project_message_role", create_type=False),
        default=ProjectMessageRole.USER,
        index=True,
    )
    workflow_node: Mapped[ProjectWorkflowNode | None] = mapped_column(
        Enum(
            ProjectWorkflowNode,
            name="project_workflow_node",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        )
    )
    content: Mapped[str] = mapped_column(Text)
    file_ids_jsonb: Mapped[list | None] = mapped_column(JSON)
    structured_delta_jsonb: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectMetricTemplate(Base):
    __tablename__ = "project_metric_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, name="project_type", create_type=False),
        default=ProjectType.GENERAL,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(200))
    data_type: Mapped[str] = mapped_column(String(50), default="text")
    unit_options_jsonb: Mapped[list | None] = mapped_column(JSON)
    required: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    prompt: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectMetricValue(Base):
    __tablename__ = "project_metric_values"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    key: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str | None] = mapped_column(String(200))
    value_jsonb: Mapped[dict | None] = mapped_column(JSON)
    source: Mapped[MetricValueSource] = mapped_column(
        Enum(MetricValueSource, name="metric_value_source", create_type=False),
        default=MetricValueSource.USER,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectPriceSnapshot(Base):
    __tablename__ = "project_price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    line_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    min_unit_price: Mapped[float | None] = mapped_column(Float)
    avg_unit_price: Mapped[float | None] = mapped_column(Float)
    median_unit_price: Mapped[float | None] = mapped_column(Float)
    p20_unit_price: Mapped[float | None] = mapped_column(Float)
    p80_unit_price: Mapped[float | None] = mapped_column(Float)
    price_tiers_jsonb: Mapped[dict | None] = mapped_column(JSON)
    samples_jsonb: Mapped[list | None] = mapped_column(JSON)
    source_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectReport(Base):
    __tablename__ = "project_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    frozen_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectReportVersion(Base):
    __tablename__ = "project_report_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[ProjectReportVersionStatus] = mapped_column(
        Enum(ProjectReportVersionStatus, name="project_report_version_status", create_type=False),
        default=ProjectReportVersionStatus.DRAFT,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(50), default="SYSTEM")
    title: Mapped[str | None] = mapped_column(String(500))
    summary_jsonb: Mapped[dict | None] = mapped_column(JSON)
    totals_jsonb: Mapped[dict | None] = mapped_column(JSON)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectReportColumn(Base):
    __tablename__ = "project_report_columns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(200))
    data_type: Mapped[str] = mapped_column(String(50), default="text")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    editable: Mapped[bool] = mapped_column(Boolean, default=True)
    system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectReportRow(Base):
    __tablename__ = "project_report_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    line_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    specs_jsonb: Mapped[dict | None] = mapped_column(JSON)
    qty: Mapped[float] = mapped_column(Float, default=1)
    unit: Mapped[str] = mapped_column(String(50), default="pcs")
    currency: Mapped[str] = mapped_column(String(10), default="PHP")
    quality_tier: Mapped[QualityTier] = mapped_column(
        Enum(QualityTier, name="quality_tier", create_type=False),
        default=QualityTier.MID_RANGE,
    )
    selected_tier: Mapped[str] = mapped_column(String(20), default="MID_RANGE")
    include_in_total: Mapped[bool] = mapped_column(Boolean, default=True)
    selected_for_purchase: Mapped[bool] = mapped_column(Boolean, default=True)
    price_tiers_jsonb: Mapped[dict | None] = mapped_column(JSON)
    custom_values_jsonb: Mapped[dict | None] = mapped_column(JSON)
    match_status: Mapped[str] = mapped_column(String(50), default="UNMATCHED")
    samples_jsonb: Mapped[list | None] = mapped_column(JSON)
    price_source: Mapped[str] = mapped_column(String(50), default="AI_ESTIMATE")
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProjectReportChangeLog(Base):
    __tablename__ = "project_report_change_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    change_type: Mapped[str] = mapped_column(String(50), default="MANUAL_EDIT")
    status: Mapped[ProjectReportPatchStatus] = mapped_column(
        Enum(ProjectReportPatchStatus, name="project_report_patch_status", create_type=False),
        default=ProjectReportPatchStatus.PENDING,
        index=True,
    )
    user_message: Mapped[str | None] = mapped_column(Text)
    patch_jsonb: Mapped[dict | None] = mapped_column(JSON)
    before_jsonb: Mapped[dict | None] = mapped_column(JSON)
    after_jsonb: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
